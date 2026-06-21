#!/usr/bin/env python3
"""Transactional, crash-recoverable skill installer core (self-update foundation, PR-1a).

The legacy installer did per-skill ``copytree(dirs_exist_ok=True)`` — it merged into
the destination (never pruned renamed/removed skills) and left a partial state if it
died mid-copy. This module replaces that with a journaled transaction so an interrupted
update is recovered to a consistent state on the next run, and with a per-target record
(installed manifest + per-skill file hashes) that enables pruning, user-edit detection,
and partial-success reporting.

Design (no network here — PR-1a):

State home: ``$MEDSCI_HOME`` or ``~/.medsci-skills``. Per target ``<state>/targets/<t>/``
holds ``journal.json``, ``installed-manifest.json``, ``state.json``. Permanent user
backups live at ``<state>/backups/<ts>/<target>/`` and are NEVER auto-deleted.

Journal = durable state machine, atomically written (temp + ``os.replace``) and fsync'd,
with a transaction id and phases::

    prepared -> old_moved -> new_installed -> committed

Recovery on every run, before any new work:
  * ``prepared`` (nothing moved): discard staging, clear journal.
  * ``old_moved`` (old set aside, new not yet placed): move old back, discard staging — ROLLBACK.
  * ``new_installed`` (new placed + validated, manifest not yet written): write the manifest
    from the journal's intended set and clean up — ROLL FORWARD (the content is already valid).
  * ``committed``: forward-cleanup only.
  * corrupt / unreadable journal: FAIL CLOSED (raise) — do not auto-proceed; the holding
    dir + backups are intact for manual recovery.

Two backup kinds, never conflated: *transaction temp* = the displaced dirs the journal
keeps under ``<dest>/.medsci-txn/<id>/old`` until commit, then deleted; *user permanent* =
``<state>/backups/...`` snapshots of legacy collisions and user-modified owned skills.

Stdlib-only. Cross-platform (POSIX + Windows). ``os.replace`` is atomic within a filesystem,
so staging + holding dirs are kept on the destination's filesystem.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
import time
from pathlib import Path

JOURNAL_PHASES = ("prepared", "old_moved", "new_installed", "committed")
TXN_DIRNAME = ".medsci-txn"


class TxnError(Exception):
    """A transaction/recovery error that must surface to the user (e.g. corrupt journal)."""


# ---------------------------------------------------------------- paths / state

def state_home() -> Path:
    env = os.environ.get("MEDSCI_HOME")
    return Path(env).expanduser() if env else Path.home() / ".medsci-skills"


def target_state_dir(target: str, home: Path | None = None) -> Path:
    return (home or state_home()) / "targets" / target


def _canonical(p: Path) -> Path:
    # realpath without requiring existence (resolve strict=False); also collapses .. and symlinks.
    return Path(os.path.realpath(str(p)))


def assert_contained(path: Path, container: Path) -> None:
    """Canonical-home containment: `path` (resolved) must be inside `container` (resolved).
    Does NOT blanket-reject a junction/symlink higher up the system tree (a home legitimately
    under a junction must still work) — it only rejects when the resolved path escapes."""
    cpath, ccont = _canonical(path), _canonical(container)
    try:
        cpath.relative_to(ccont)
    except ValueError:
        raise TxnError(f"path escapes its container: {path} not within {container}")


# ---------------------------------------------------------------- json io

def atomic_write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + f".tmp.{os.getpid()}")
    data = (json.dumps(obj, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    with open(tmp, "wb") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)
    # fsync the directory so the rename is durable.
    try:
        dfd = os.open(str(path.parent), os.O_RDONLY)
        try:
            os.fsync(dfd)
        finally:
            os.close(dfd)
    except (OSError, AttributeError):
        pass  # directory fsync unsupported (e.g. Windows) — os.replace is still atomic.


def read_json_strict(path: Path):
    """Read JSON; raise TxnError on a corrupt/unreadable file (callers fail closed)."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise TxnError(f"corrupt or unreadable {path}: {exc}")


# ---------------------------------------------------------------- hashing

def skill_inventory(skill_dir: Path) -> dict[str, str]:
    """Deterministic {relpath(posix): sha256} over every file in a skill dir."""
    inv: dict[str, str] = {}
    for f in sorted(skill_dir.rglob("*")):
        if f.is_file() and not f.is_symlink():
            h = hashlib.sha256()
            with f.open("rb") as fh:
                for chunk in iter(lambda: fh.read(65536), b""):
                    h.update(chunk)
            inv[f.relative_to(skill_dir).as_posix()] = h.hexdigest()
    return inv


def _dir_size(p: Path) -> int:
    return sum(f.stat().st_size for f in p.rglob("*") if f.is_file() and not f.is_symlink())


# ---------------------------------------------------------------- backups

def _timestamp() -> str:
    # wall-clock; only used as a backup folder label (uniqueness via pid suffix).
    return time.strftime("%Y%m%d-%H%M%S", time.localtime()) + f"-{os.getpid()}"

def permanent_backup(skill_path: Path, target: str, home: Path, reason: str, log) -> Path:
    dest = home / "backups" / _timestamp() / target / skill_path.name
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(skill_path, dest)
    log(f"  backed up {skill_path.name} ({reason}) -> {dest}")
    return dest


# ---------------------------------------------------------------- recovery

def recover_target(target: str, home: Path, log) -> bool:
    """Run journal recovery for a target before any new transaction. Returns True if a
    recovery was performed. Raises TxnError (fail closed) on a corrupt journal."""
    tdir = target_state_dir(target, home)
    jpath = tdir / "journal.json"
    if not jpath.exists():
        return False
    j = read_json_strict(jpath)  # corrupt -> TxnError (fail closed)
    phase = j.get("phase")
    if phase not in JOURNAL_PHASES:
        raise TxnError(f"journal {jpath} has unknown phase {phase!r}; manual recovery required")
    dest = Path(j["dest"])
    holding = Path(j["holding"])      # <dest>/.medsci-txn/<id>/old
    moved_old = j.get("moved_old", [])   # names moved into holding
    placed_new = j.get("placed_new", [])  # names moved into dest
    owned = j.get("owned_skills", [])
    log(f"[{target}] recovering interrupted transaction {j.get('txn_id')} at phase '{phase}'")

    # Point of no return = all new skills actually placed in dest. Roll FORWARD only when the
    # new content is fully in place (committed, or new_installed with every skill placed);
    # otherwise ROLL BACK (the new content is still partly in staging).
    fully_placed = len(placed_new) == len(owned) and len(owned) > 0
    roll_forward = phase == "committed" or (phase == "new_installed" and fully_placed)

    if roll_forward:
        atomic_write_json(tdir / "installed-manifest.json", j["intended_manifest"])
        atomic_write_json(tdir / "state.json", j["intended_state"])
    else:
        for name in placed_new:          # undo any partially-placed new dirs
            _rm(dest / name)
        for name in moved_old:           # restore old dirs set aside
            src = holding / name
            if src.exists():
                _rm(dest / name)
                os.replace(src, dest / name)

    _rm(Path(j["txn_root"]))             # discard the whole .medsci-txn/<id> (staging + holding)
    try:
        (dest / TXN_DIRNAME).rmdir()     # remove the now-empty parent
    except OSError:
        pass
    jpath.unlink()
    log(f"[{target}] recovery complete ({'rolled forward' if roll_forward else 'rolled back'})")
    return True


def _rm(p: Path) -> None:
    if p.is_symlink() or p.is_file():
        p.unlink(missing_ok=True)
    elif p.is_dir():
        shutil.rmtree(p, ignore_errors=True)


# ---------------------------------------------------------------- install

def install_target(
    source_skills_dir: Path,
    dest: Path,
    target: str,
    owned_skills: list[str],
    home: Path,
    log,
    min_free_bytes_extra: int = 50 * 1024 * 1024,
    crash_hook=None,
) -> dict:
    """Transactionally install `owned_skills` from source into dest. Returns a result dict.
    Recovery for this target is run first. Raises TxnError on fail-closed conditions.
    `crash_hook(journal)` (test-only) is called after every journal write and may raise to
    simulate a SIGKILL at a consistent point; recovery is then exercised on the next run."""
    home.mkdir(parents=True, exist_ok=True)
    tdir = target_state_dir(target, home)
    tdir.mkdir(parents=True, exist_ok=True)

    recover_target(target, home, log)  # may raise (fail closed)

    dest.mkdir(parents=True, exist_ok=True)
    # Canonical-home containment (production only). When MEDSCI_HOME is set (tests / a custom
    # install root) the dest + state live under that root by construction, so the real-home guard
    # is skipped; assert_contained() itself is unit-tested for the symlink-escape case.
    if os.environ.get("MEDSCI_HOME") is None:
        home_root = _canonical(Path.home())
        for managed in (dest, tdir, home):
            assert_contained(managed, home_root)

    # prior installed manifest (for prune + user-edit detection)
    prior_path = tdir / "installed-manifest.json"
    prior = read_json_strict(prior_path) if prior_path.exists() else {"skills": {}}
    prior_skills: dict[str, dict] = prior.get("skills", {})

    # disk preflight: staged copy + holding ~ 2x source owned size + margin
    src_size = sum(_dir_size(source_skills_dir / s) for s in owned_skills if (source_skills_dir / s).is_dir())
    free = shutil.disk_usage(str(dest)).free
    if free < src_size * 2 + min_free_bytes_extra:
        raise TxnError(f"insufficient disk space at {dest}: need ~{src_size * 2 + min_free_bytes_extra} bytes, free {free}")

    # backups: user-modified owned skills + legacy/third-party collisions with an owned name
    new_inventories: dict[str, dict[str, str]] = {}
    for name in owned_skills:
        src = source_skills_dir / name
        if not (src / "SKILL.md").is_file():
            raise TxnError(f"source skill missing SKILL.md: {src}")
        new_inventories[name] = skill_inventory(src)
        d = dest / name
        if d.exists():
            if name in prior_skills:
                if skill_inventory(d) != prior_skills[name].get("inventory", {}):
                    permanent_backup(d, target, home, "user-modified", log)
            else:
                permanent_backup(d, target, home, "legacy-collision", log)

    prune = [n for n in prior_skills if n not in set(owned_skills)]
    for name in prune:  # a removed/renamed owned skill: back up before pruning, then remove in txn
        d = dest / name
        if d.exists() and skill_inventory(d) != prior_skills[name].get("inventory", {}):
            permanent_backup(d, target, home, "user-modified-pruned", log)

    # ---- transaction ----
    txn_id = _timestamp()
    txn_root = dest / TXN_DIRNAME / txn_id
    staging = txn_root / "new"
    holding = txn_root / "old"
    staging.mkdir(parents=True, exist_ok=True)
    holding.mkdir(parents=True, exist_ok=True)

    intended_manifest = {
        "schema_version": 1,
        "target": target,
        "skills": {n: {"inventory": new_inventories[n]} for n in owned_skills},
    }
    intended_state = {
        "installed_version": _read_source_version(source_skills_dir),
        "installed_at": _timestamp(),
        "path": str(dest),
        "source_channel": os.environ.get("MEDSCI_SOURCE_CHANNEL", "classroom"),
    }
    journal = {
        "txn_id": txn_id, "target": target, "phase": "prepared",
        "dest": str(dest), "txn_root": str(txn_root), "staging": str(staging), "holding": str(holding),
        "owned_skills": owned_skills, "prune": prune,
        "moved_old": [], "placed_new": [],
        "intended_manifest": intended_manifest, "intended_state": intended_state,
    }
    jpath = tdir / "journal.json"

    def _bump() -> None:
        atomic_write_json(jpath, journal)
        if crash_hook is not None:
            crash_hook(dict(journal))

    _bump()

    # stage new skills (copy) + validate discoverability in staging
    for name in owned_skills:
        shutil.copytree(source_skills_dir / name, staging / name)
        if not (staging / name / "SKILL.md").is_file():
            raise TxnError(f"staged skill not discoverable: {name}")

    # phase old_moved: move existing dest dirs (replaced + pruned) into holding
    to_move = [n for n in owned_skills if (dest / n).exists()] + [n for n in prune if (dest / n).exists()]
    journal["phase"] = "old_moved"
    _bump()
    for name in to_move:
        os.replace(dest / name, holding / name)
        journal["moved_old"].append(name)
        _bump()

    # phase new_installed: move staged skills into dest, then validate
    journal["phase"] = "new_installed"
    _bump()
    for name in owned_skills:
        os.replace(staging / name, dest / name)
        journal["placed_new"].append(name)
        _bump()
    missing = [n for n in owned_skills if not (dest / n / "SKILL.md").is_file()]
    if missing:
        raise TxnError(f"post-install discoverability failed: {', '.join(missing)}")

    # commit: write manifest + state, then forward-cleanup
    atomic_write_json(prior_path, intended_manifest)
    atomic_write_json(tdir / "state.json", intended_state)
    journal["phase"] = "committed"
    _bump()
    _rm(txn_root)
    # remove the now-empty .medsci-txn parent if empty
    try:
        (dest / TXN_DIRNAME).rmdir()
    except OSError:
        pass
    jpath.unlink()

    log(f"[{target}] installed {len(owned_skills)} skills, pruned {len(prune)} (transaction {txn_id} committed)")
    return {"target": target, "installed": len(owned_skills), "pruned": len(prune), "txn_id": txn_id}


def _read_source_version(source_skills_dir: Path) -> str:
    """version from the sibling distribution_manifest.json if present, else 'unknown'."""
    cand = source_skills_dir.parent / "metadata" / "distribution_manifest.json"
    if cand.exists():
        try:
            return json.loads(cand.read_text(encoding="utf-8")).get("version", "unknown")
        except (OSError, json.JSONDecodeError):
            return "unknown"
    return "unknown"
