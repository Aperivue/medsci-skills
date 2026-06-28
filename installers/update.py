#!/usr/bin/env python3
"""Self-update core for MedSci Skills (PR-1b).

Physicians install once and never update. This fetches the latest classroom release ZIP
from GitHub and re-installs it through the PR-1a transactional installer — no GitHub UI, no
git, no terminal. The `.command` / `.cmd` launchers are thin wrappers around this file.

Security posture (see the repo's update privacy/threat notes): downloading a release ZIP and
running its bundled installer **is remote code execution within the GitHub trust boundary**.
The release-asset `digest` (read from the github.com API) detects **download corruption / asset
tampering in flight** — it does NOT defend against a compromised publisher account. So:

  * `api.github.com` is the ONLY metadata endpoint; **fail closed** if the API has no sha256 digest.
  * download over HTTPS; verify the asset's sha256 == the API digest, the expected asset name, and
    the release tag.
  * **never `extractall()`** — extract per entry, rejecting path traversal (POSIX + Windows),
    symlink/hardlink/junction/reparse, duplicate paths, and zip-bombs (file-count / total-size /
    ratio caps); every payload entry must match `metadata/distribution_files.json` (path + size +
    sha256); only a short metadata allowlist (the two manifests + provenance.json) may differ.
  * validate the bundled `provenance.json` tag/version against the release tag + the manifest.

Network is injectable (`get_json` / `get_bytes`) so tests run fully offline.
Stdlib-only. No telemetry / analytics / unique id; only a plain GitHub GET is ever sent.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import platform
import re
import sys
import tempfile
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import medsci_txn  # noqa: E402  (PR-1a transactional core; reused for state/version helpers)

OWNER_REPO = "Aperivue/medsci-skills"
API_LATEST = f"https://api.github.com/repos/{OWNER_REPO}/releases/latest"
USER_AGENT = "medsci-skills-updater"
HTTP_TIMEOUT = 30

# zip-bomb caps for the classroom payload (generous vs the real ~700-file payload).
MAX_ENTRIES = 20000
MAX_TOTAL_UNCOMPRESSED = 500 * 1024 * 1024
MAX_RATIO = 200  # uncompressed / compressed per entry

# metadata files allowed in the ZIP but NOT in distribution_files.json (control files).
METADATA_ALLOWLIST = {
    "metadata/distribution_manifest.json",
    "metadata/distribution_files.json",
    "provenance.json",
}
SEMVER = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")


class UpdateError(Exception):
    """A user-facing updater failure; the existing install is left untouched."""


# ----------------------------------------------------------------- network (injectable)

def _real_get_json(url: str, timeout: int = HTTP_TIMEOUT):
    import urllib.request
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:  # noqa: S310 (https only, fixed host)
        return json.loads(r.read().decode("utf-8"))


def _real_get_bytes(url: str, cap: int = MAX_TOTAL_UNCOMPRESSED) -> bytes:
    import urllib.request
    if not url.lower().startswith("https://"):
        raise UpdateError("refusing non-HTTPS download URL")
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    buf = bytearray()
    with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as r:  # noqa: S310
        while True:
            chunk = r.read(65536)
            if not chunk:
                break
            buf += chunk
            if len(buf) > cap:
                raise UpdateError("download exceeds size cap")
    return bytes(buf)


# ----------------------------------------------------------------- release resolution

def _require(cond: bool, msg: str) -> None:
    if not cond:
        raise UpdateError(msg)


def os_asset_name() -> str:
    sysname = platform.system().lower()
    if sysname == "darwin":
        return "medsci-skills-classroom-macos.zip"
    if sysname == "windows":
        return "medsci-skills-classroom-windows.zip"
    raise UpdateError(f"no classroom updater asset for this OS ({sysname}); use 'npx medsci-skills@latest install'")


def resolve_latest(get_json, asset_name: str) -> dict:
    """Return {tag, asset_name, url, sha256} for the latest non-draft/non-prerelease release.
    Fail closed if the API lacks a sha256 digest for the asset."""
    rel = get_json(API_LATEST)
    _require(not rel.get("draft") and not rel.get("prerelease"), "latest release is a draft/prerelease")
    tag = rel.get("tag_name") or ""
    _require(bool(tag), "release has no tag_name")
    assets = {a.get("name"): a for a in rel.get("assets", [])}
    a = assets.get(asset_name)
    _require(a is not None, f"release {tag} has no asset '{asset_name}'")
    digest = (a.get("digest") or "")
    _require(digest.startswith("sha256:") and len(digest) == 71, f"fail closed: asset '{asset_name}' has no sha256 digest")
    url = a.get("browser_download_url") or ""
    _require(url.lower().startswith("https://"), "asset download URL is not HTTPS")
    return {"tag": tag, "asset_name": asset_name, "url": url, "sha256": digest.split(":", 1)[1]}


def resolve_latest_tag(get_json) -> str:
    """Return just the latest non-draft/non-prerelease tag — for an availability CHECK only
    (installs nothing). Unlike resolve_latest it needs no OS-specific asset/digest, so the
    notifier works on every OS (a Linux user who installed via npm/git can still be told a newer
    version exists, even though the classroom ZIP is macOS/Windows only)."""
    rel = get_json(API_LATEST)
    _require(not rel.get("draft") and not rel.get("prerelease"), "latest release is a draft/prerelease")
    tag = rel.get("tag_name") or ""
    _require(bool(tag), "release has no tag_name")
    return tag


# ----------------------------------------------------------------- verify + safe-extract

def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _zip_root(zf: zipfile.ZipFile) -> str:
    roots = {(name.split("/", 1)[0]) for name in zf.namelist() if name and not name.startswith("__MACOSX")}
    roots.discard("")
    _require(len(roots) == 1, f"ZIP must have exactly one top-level dir, found {sorted(roots)}")
    return roots.pop()


def _reject_unsafe_name(name: str) -> None:
    # POSIX + Windows traversal / absolute / drive / UNC / backslash.
    bad = ("\\" in name or name.startswith("/") or name.startswith("\\\\")
           or re.match(r"^[A-Za-z]:", name) or ".." in Path(name.replace("\\", "/")).parts)
    _require(not bad, f"unsafe path in ZIP: {name!r}")


def safe_extract(zip_bytes: bytes, dest: Path, inventory: dict[str, dict]) -> str:
    """Extract a verified classroom ZIP into `dest` (a fresh temp dir), per entry, rejecting
    traversal/symlink/duplicate/zip-bomb and enforcing the distribution_files.json allowlist+hash.
    Returns the (stripped) single root name. Never uses extractall()."""
    seen_lower: set[str] = set()
    total = 0
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        names = zf.namelist()
        _require(len(names) <= MAX_ENTRIES, "ZIP has too many entries (possible zip-bomb)")
        root = _zip_root(zf)
        for info in zf.infolist():
            name = info.filename
            if name.startswith("__MACOSX") or name.endswith("/"):
                continue
            _reject_unsafe_name(name)
            # reject symlink / non-regular: external_attr high bits encode unix mode.
            mode = (info.external_attr >> 16) & 0o170000
            _require(mode != 0o120000, f"symlink entry rejected: {name}")
            lower = name.lower()
            _require(lower not in seen_lower, f"duplicate (case-insensitive) path: {name}")
            seen_lower.add(lower)
            # zip-bomb ratio + total
            total += info.file_size
            _require(total <= MAX_TOTAL_UNCOMPRESSED, "ZIP uncompressed size exceeds cap")
            if info.compress_size > 0:
                _require(info.file_size / info.compress_size <= MAX_RATIO, f"suspicious compression ratio: {name}")
            # strip the single root; classify against the inventory / metadata allowlist
            rel = name.split("/", 1)[1] if "/" in name else ""
            _require(bool(rel), f"entry at ZIP root not allowed: {name}")
            data = zf.read(info)
            if rel in inventory:
                want = inventory[rel]
                _require(len(data) == want["size"], f"size mismatch for {rel}")
                _require(sha256_bytes(data) == want["sha256"], f"hash mismatch for {rel}")
            else:
                _require(rel in METADATA_ALLOWLIST, f"unexpected file not in inventory: {rel}")
            out = dest / rel
            _resolve_within(out, dest)
            out.parent.mkdir(parents=True, exist_ok=True)
            with open(out, "wb") as f:
                f.write(data)
        # every inventory file must be present
        missing = [rel for rel in inventory if not (dest / rel).is_file()]
        _require(not missing, f"ZIP missing {len(missing)} inventory file(s), e.g. {missing[:3]}")
    return root


def _resolve_within(child: Path, parent: Path) -> None:
    cp, pp = os.path.realpath(str(child.parent)), os.path.realpath(str(parent))
    _require(cp == pp or cp.startswith(pp + os.sep), f"extraction escapes dest: {child}")




# ----------------------------------------------------------------- provenance

def validate_provenance(extracted_root: Path, tag: str, manifest_version: str) -> None:
    prov = extracted_root / "provenance.json"
    if not prov.exists():
        return  # provenance is release-injected; absence is tolerated (older builds), not fatal
    try:
        p = json.loads(prov.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise UpdateError(f"corrupt provenance.json: {exc}")
    if p.get("tag") and p["tag"] != tag:
        raise UpdateError(f"provenance tag {p['tag']!r} != release tag {tag!r}")
    if p.get("version") and p["version"] != manifest_version:
        raise UpdateError(f"provenance version {p['version']!r} != manifest version {manifest_version!r}")


# ----------------------------------------------------------------- version / check-update

def parse_semver(v: str):
    m = SEMVER.match(v.strip())
    return tuple(int(x) for x in m.groups()) if m else None


def installed_version(home: Path) -> str:
    """Best installed version across targets, or 'unknown'."""
    best = None
    tdir = home / "targets"
    if tdir.is_dir():
        for t in tdir.iterdir():
            sp = t / "state.json"
            if sp.is_file():
                try:
                    v = json.loads(sp.read_text(encoding="utf-8")).get("installed_version")
                except (OSError, json.JSONDecodeError):
                    continue
                pv = parse_semver(v or "")
                if pv and (best is None or pv > best[0]):
                    best = (pv, v)
    return best[1] if best else "unknown"


def read_inventory_from_zip(zip_bytes: bytes) -> tuple[str, dict[str, dict]]:
    """Read <root>/metadata/distribution_files.json from a (sha-verified) ZIP."""
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        root = _zip_root(zf)
        try:
            raw = zf.read(f"{root}/metadata/distribution_files.json")
        except KeyError:
            raise UpdateError("ZIP has no metadata/distribution_files.json inventory")
        inv = json.loads(raw.decode("utf-8"))
    return root, {e["path"]: e for e in inv.get("files", [])}


def read_manifest_version_from_zip(zip_bytes: bytes, root: str) -> str:
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        try:
            return json.loads(zf.read(f"{root}/metadata/distribution_manifest.json").decode("utf-8")).get("version", "unknown")
        except (KeyError, json.JSONDecodeError):
            return "unknown"


# Exit codes for --check-update (distinct, scriptable).
CHK_UP_TO_DATE = 0
CHK_UPDATE_AVAILABLE = 10
CHK_NETWORK_FAILURE = 20
CHK_UNKNOWN_LOCAL = 30

CACHE_MAX_AGE = 24 * 3600
CACHE_SANITY_FUTURE = 300          # tolerate small clock skew
CACHE_SANITY_PAST = 400 * 24 * 3600  # >400 days old => treat as corrupt/stale


def _now() -> float:
    import time
    return time.time()


def _cache_path(home: Path) -> Path:
    return home / "update_check.json"


def _cache_fresh(home: Path) -> str | None:
    """Return a cached latest tag if the cache is fresh and clock-sane, else None."""
    p = _cache_path(home)
    if not p.is_file():
        return None
    try:
        c = json.loads(p.read_text(encoding="utf-8"))
        last = float(c["checked_at"])
        tag = str(c["latest_tag"])
    except (OSError, json.JSONDecodeError, KeyError, ValueError, TypeError):
        return None
    now = _now()
    if last - now > CACHE_SANITY_FUTURE:          # cache in the future -> corrupt clock
        return None
    age = now - last
    if age < 0 or age > CACHE_SANITY_PAST:        # backwards / implausibly old
        return None
    return tag if age <= CACHE_MAX_AGE else None


def _cache_store(home: Path, tag: str) -> None:
    try:
        medsci_txn.atomic_write_json(_cache_path(home), {"checked_at": _now(), "latest_tag": tag})
    except OSError:
        pass


def check_update(home: Path, get_json=_real_get_json, asset_name: str | None = None, force: bool = False) -> int:
    """Compare the installed version with the latest release. Silent when up to date.
    Returns a distinct exit code (CHK_*). Uses a clock-sane 24h cache."""
    inst = installed_version(home)
    inst_v = parse_semver(inst)
    if inst_v is None:
        print("MedSci Skills: installed version unknown (run the installer once).")
        return CHK_UNKNOWN_LOCAL

    tag = None if force else _cache_fresh(home)
    if tag is None:
        try:
            rel = resolve_latest(get_json, asset_name or os_asset_name())
            tag = rel["tag"]
            _cache_store(home, tag)
        except UpdateError as exc:
            print(f"MedSci Skills: could not check for updates ({exc}).", file=sys.stderr)
            return CHK_NETWORK_FAILURE
        except Exception as exc:  # noqa: BLE001 - network/JSON/anything -> treat as a check failure
            print(f"MedSci Skills: update check failed ({exc}).", file=sys.stderr)
            return CHK_NETWORK_FAILURE

    latest_v = parse_semver(tag[1:] if tag.startswith("v") else tag)
    if latest_v is None:
        return CHK_NETWORK_FAILURE
    if latest_v > inst_v:
        print(f"MedSci Skills: update available — installed {inst}, latest {tag}. "
              f"Run the updater (double-click 'Update MedSci Skills' or ~/.medsci-skills/updater/).")
        return CHK_UPDATE_AVAILABLE
    return CHK_UP_TO_DATE  # silent-ish: up to date


def do_update(home: Path, log, get_json=_real_get_json, get_bytes=_real_get_bytes,
              asset_name: str | None = None, run_install=None) -> dict:
    """Resolve -> download -> verify digest -> safe-extract -> validate provenance -> install.
    Returns a result dict. Raises UpdateError; the existing install is left untouched on failure."""
    asset = asset_name or os_asset_name()
    rel = resolve_latest(get_json, asset)
    log(f"latest release {rel['tag']} (asset {asset})")
    data = get_bytes(rel["url"])
    got = sha256_bytes(data)
    _require(got == rel["sha256"], f"digest mismatch: downloaded {got[:12]}… != expected {rel['sha256'][:12]}…")
    log(f"verified download ({len(data)} bytes, sha256 ok)")

    root, inventory = read_inventory_from_zip(data)
    man_version = read_manifest_version_from_zip(data, root)

    with tempfile.TemporaryDirectory(prefix="medsci-update-") as tmp:
        extract = Path(tmp) / "payload"
        extract.mkdir()
        safe_extract(data, extract, inventory)
        log(f"safe-extracted {len(inventory)} payload files + metadata")
        validate_provenance(extract, rel["tag"], man_version)

        installer = extract / "installers" / "install.py"
        _require(installer.is_file(), "extracted payload has no installers/install.py")
        rc = (run_install or _run_install)(installer)
        _require(rc == 0, f"transactional install failed (exit {rc})")

        install_updater_home(extract, home, log)
    log(f"updated to {rel['tag']}")
    return {"tag": rel["tag"], "version": man_version}


def _run_install(installer: Path) -> int:
    import subprocess
    return subprocess.run([sys.executable, str(installer), "--target", "all"]).returncode


def install_updater_home(source_root: Path, home: Path, log, desktop: bool = False) -> None:
    """Copy the updater (update.py + medsci_txn.py + launchers) from <source_root>/installers/ to
    ~/.medsci-skills/updater/ so a future update is one-click even if the original folder is gone.
    Windows-safe staged swap (never overwrites a running file in place). Optionally (with explicit
    consent) places a Desktop launcher that runs the updater home."""
    import shutil
    udir = home / "updater"
    pid = os.getpid()
    staging = home / f"updater.new-{pid}"
    if staging.exists():
        shutil.rmtree(staging, ignore_errors=True)
    staging.mkdir(parents=True, exist_ok=True)
    src = source_root / "installers"
    for name in ("update.py", "medsci_txn.py", "update-macos.command", "update-windows.cmd",
                 SESSION_HOOK_SCRIPT):
        s = src / name
        if s.is_file():
            shutil.copy2(s, staging / name)
    backup = home / f"updater.old-{pid}"
    if udir.exists():
        os.replace(udir, backup)
    os.replace(staging, udir)
    if backup.exists():
        shutil.rmtree(backup, ignore_errors=True)
    log(f"installed updater to {udir}")
    if desktop:
        _place_desktop_launcher(udir, log)


def _place_desktop_launcher(udir: Path, log) -> None:
    """Place a Desktop launcher (with the user's explicit --desktop-launcher consent) that runs the
    updater home. Best-effort; never fatal."""
    try:
        desktop = Path.home() / "Desktop"
        if not desktop.is_dir():
            return
        if platform.system().lower() == "windows":
            launcher = desktop / "Update MedSci Skills.cmd"
            launcher.write_text(f'@echo off\r\npython "{udir / "update.py"}" %*\r\npause\r\n', encoding="utf-8")
        else:
            launcher = desktop / "Update MedSci Skills.command"
            launcher.write_text(f'#!/usr/bin/env bash\ncd "{udir}"\npython3 update.py "$@"\nread -r -p "Press Enter to close..."\n', encoding="utf-8")
            os.chmod(launcher, 0o755)
        log(f"placed Desktop launcher: {launcher}")
    except OSError as exc:
        log(f"could not place Desktop launcher ({exc})")


# ----------------------------------------------------------------- opt-in SessionStart notify hook

SESSION_HOOK_SCRIPT = "session_update_check.py"


def default_settings_path() -> Path:
    """~/.claude/settings.json (Claude Code), overridable via MEDSCI_CLAUDE_SETTINGS for tests."""
    override = os.environ.get("MEDSCI_CLAUDE_SETTINGS")
    return Path(override) if override else Path.home() / ".claude" / "settings.json"


def session_hook_command(home: Path) -> str:
    """Absolute interpreter + absolute script path (quoted) so the hook runs cross-platform."""
    return f'"{sys.executable}" "{home / "updater" / SESSION_HOOK_SCRIPT}"'


def _load_settings(settings_path: Path):
    """Parse settings.json. Absent/empty/`null` -> {}. A non-dict JSON value is returned as-is so the
    caller can refuse it. Raises UpdateError only on genuinely unreadable/invalid JSON (never `[] or {}`
    style collapsing, which would silently treat a JSON array as empty and clobber it)."""
    if not settings_path.is_file():
        return {}
    raw = settings_path.read_text(encoding="utf-8")
    if not raw.strip():
        return {}
    try:
        obj = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        raise UpdateError(f"cannot parse {settings_path}: {exc}; leaving it unchanged")
    return {} if obj is None else obj


def _managed_hook_path(home: Path) -> str:
    """The home-anchored script path our hook command embeds. Matching on THIS (not the bare
    filename) is precise: it cannot collide with an unrelated user hook whose command merely
    contains the substring 'session_update_check.py' (e.g. '.../run_session_update_check.py_wrapper'),
    nor with a hook pointing at a DIFFERENT MEDSCI_HOME, and it survives the interpreter path changing
    between enable and disable (we match the script, not the python)."""
    return str(home / "updater" / SESSION_HOOK_SCRIPT)


def _hook_is_ours(h: object, home: Path) -> bool:
    return (isinstance(h, dict) and isinstance(h.get("command"), str)
            and _managed_hook_path(home) in h["command"])


def _entry_owns_hook(entry: object, home: Path) -> bool:
    return (isinstance(entry, dict) and isinstance(entry.get("hooks"), list)
            and any(_hook_is_ours(h, home) for h in entry["hooks"]))


def _write_settings(settings_path: Path, settings: dict) -> None:
    """Atomically write settings.json, preserving the destination's file mode if it already exists
    (so a user who restricted it, e.g. chmod 600, does not get it silently widened to umask default)."""
    prev_mode = os.stat(settings_path).st_mode & 0o777 if settings_path.is_file() else None
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    medsci_txn.atomic_write_json(settings_path, settings)
    if prev_mode is not None:
        try:
            os.chmod(settings_path, prev_mode)
        except OSError:
            pass


def register_session_hook(home: Path, settings_path: Path) -> str:
    """Opt-in: MERGE a SessionStart update-notify hook into settings.json. Idempotent (no duplicate);
    preserves every existing hook/setting. Returns 'enabled' or 'already-enabled'. Refuses (raises)
    rather than clobber a settings.json it cannot parse or whose shape is unexpected."""
    settings = _load_settings(settings_path)  # {} for absent/empty/null
    if not isinstance(settings, dict):
        raise UpdateError(f"{settings_path} is not a JSON object; leaving it unchanged")
    hooks = settings.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        raise UpdateError(f"{settings_path} 'hooks' is not an object; leaving it unchanged")
    ss = hooks.setdefault("SessionStart", [])
    if not isinstance(ss, list):
        raise UpdateError(f"{settings_path} 'hooks.SessionStart' is not a list; leaving it unchanged")
    if any(_entry_owns_hook(e, home) for e in ss):
        return "already-enabled"
    ss.append({"hooks": [{"type": "command", "command": session_hook_command(home), "timeout": 10}]})
    _write_settings(settings_path, settings)
    return "enabled"


def session_hook_enabled(home: Path, settings_path: Path) -> bool:
    """Read-only: True iff our SessionStart update-notify hook is currently registered in
    settings.json. Never writes; tolerant of an absent/empty/unreadable settings file (False).
    Used by the installer to decide whether to print the one-time enable-reminders nudge."""
    try:
        if not settings_path.is_file():
            return False
        settings = _load_settings(settings_path)
        if not isinstance(settings, dict):
            return False
        hooks = settings.get("hooks")
        ss = hooks.get("SessionStart") if isinstance(hooks, dict) else None
        if not isinstance(ss, list):
            return False
        return any(_entry_owns_hook(e, home) for e in ss)
    except Exception:  # noqa: BLE001 - read-only nudge gate, never block install
        return False


def unregister_session_hook(home: Path, settings_path: Path) -> str:
    """Opt-out: remove ONLY our SessionStart hook (even if it shares an entry with other hooks),
    preserving everything else; drop emptied containers. Returns 'disabled' or 'not-enabled'."""
    if not settings_path.is_file():
        return "not-enabled"
    settings = _load_settings(settings_path)  # {} for empty/null; raises only if unreadable JSON
    if not isinstance(settings, dict) or not isinstance(settings.get("hooks"), dict):
        return "not-enabled"
    hooks = settings["hooks"]
    ss = hooks.get("SessionStart")
    if not isinstance(ss, list):
        return "not-enabled"
    changed = False
    new_ss: list = []
    for e in ss:
        if isinstance(e, dict) and isinstance(e.get("hooks"), list):
            kept = [h for h in e["hooks"] if not _hook_is_ours(h, home)]
            if len(kept) != len(e["hooks"]):
                changed = True
                if not kept:
                    continue  # drop a now-empty entry instead of leaving {"hooks": []}
                e = {**e, "hooks": kept}
        new_ss.append(e)
    if not changed:
        return "not-enabled"
    if new_ss:
        hooks["SessionStart"] = new_ss
    else:
        hooks.pop("SessionStart", None)
    if not hooks:
        settings.pop("hooks", None)
    _write_settings(settings_path, settings)
    return "disabled"


# ----------------------------------------------------------------- cli

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Update MedSci Skills from the latest GitHub release.")
    ap.add_argument("--check-update", action="store_true", help="report whether an update is available (no install)")
    ap.add_argument("--force", action="store_true", help="ignore the 24h check cache")
    args = ap.parse_args(argv)
    home = medsci_txn.state_home()
    if args.check_update:
        return check_update(home, force=args.force)
    log_lines: list[str] = []
    def log(m):  # noqa: E306
        print(m); log_lines.append(m)
    try:
        do_update(home, log)
    except UpdateError as exc:
        print(f"\nUpdate failed: {exc}\nYour current installation is unchanged.", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"\nUpdate failed: {exc}\nYour current installation is unchanged.", file=sys.stderr)
        return 1
    print("\nDone. Restart Claude Code, Codex, or Cursor.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
