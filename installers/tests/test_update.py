#!/usr/bin/env python3
"""Updater tests for installers/update.py — fully offline (network + install injected).

Builds a synthetic classroom ZIP (single root, skills + installers + a matching
distribution_files.json), fakes the GitHub API (digest = the ZIP's sha256) and the byte
download, and mocks the install step (so no real host dir is touched). Covers the happy
path + the supply-chain guards (digest mismatch, fail-closed no-digest, traversal, symlink,
duplicate, unexpected file, hash/size mismatch, zip-bomb caps, draft/prerelease) and the
check_update cache/semver logic. Run: python3 installers/tests/test_update.py
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import sys
import tempfile
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import update as U  # noqa: E402
import medsci_txn  # noqa: E402

PASS = 0
FAIL = 0
ROOT = "medsci-skills-classroom-2.0.0"


def check(label, cond):
    global PASS, FAIL
    print(f"  {'PASS' if cond else 'FAIL'}  {label}")
    PASS += (1 if cond else 0)
    FAIL += (0 if cond else 1)


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def build_payload(tmp: Path) -> dict[str, bytes]:
    """Return {relpath: bytes} for a minimal valid classroom payload (skills + installers +
    README_FIRST), with metadata/distribution_files.json matching the skills/installers/readme."""
    files: dict[str, bytes] = {}
    files["README_FIRST.md"] = b"# MedSci Skills\n"
    files["skills/demo/SKILL.md"] = b"# demo\n"
    files["skills/demo/x.txt"] = b"data\n"
    # ship the real installer modules so an extracted install.py would be runnable + the updater
    # can self-install (update.py + medsci_txn.py) from the payload.
    for n in ("install.py", "medsci_txn.py", "update.py"):
        files[f"installers/{n}"] = (HERE.parent / n).read_bytes()
    # inventory excludes the metadata manifests themselves (matches gen scope)
    inv = [{"path": p, "size": len(b), "sha256": _sha(b)} for p, b in sorted(files.items())]
    files["metadata/distribution_files.json"] = (json.dumps({"schema_version": 1, "files": inv}) + "\n").encode()
    files["metadata/distribution_manifest.json"] = (json.dumps(
        {"schema_version": 1, "version": "2.0.0", "owned_skills": ["demo"]}) + "\n").encode()
    return files


def make_zip(files: dict[str, bytes], root: str = ROOT, extra: dict[str, bytes] | None = None,
             symlink: str | None = None, dup: bool = False) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for rel, b in files.items():
            zf.writestr(f"{root}/{rel}", b)
        for rel, b in (extra or {}).items():
            zf.writestr(f"{root}/{rel}", b)
        if symlink:
            info = zipfile.ZipInfo(f"{root}/{symlink}")
            info.external_attr = (0o120777 << 16)  # symlink mode
            zf.writestr(info, "skills/demo")
        if dup:
            zf.writestr(f"{root}/skills/DEMO/SKILL.md", b"dup\n")  # case-insensitive dup of skills/demo
    return buf.getvalue()


def fake_api(zip_bytes: bytes, asset="medsci-skills-classroom-macos.zip", tag="v2.0.0",
             draft=False, prerelease=False, digest=True):
    def get_json(_url):
        a = {"name": asset, "browser_download_url": "https://release-assets.githubusercontent.com/x.zip"}
        if digest:
            a["digest"] = "sha256:" + _sha(zip_bytes)
        return {"tag_name": tag, "draft": draft, "prerelease": prerelease, "assets": [a]}
    return get_json


def run():
    asset = "medsci-skills-classroom-macos.zip"
    with tempfile.TemporaryDirectory(prefix="medsci-upd-") as tmp:
        base = Path(tmp)
        files = build_payload(base)
        zbytes = make_zip(files)

        # --- happy path: resolve + verify + safe-extract + install (mocked) + updater home ---
        home = base / "home"
        installs = []
        rc = U.do_update(home, lambda m: None,
                         get_json=fake_api(zbytes, asset=asset),
                         get_bytes=lambda url: zbytes,
                         asset_name=asset,
                         run_install=lambda inst: installs.append(inst) or 0)
        check("happy path returns tag v2.0.0", rc["tag"] == "v2.0.0")
        check("happy path called the extracted installer", len(installs) == 1 and installs[0].name == "install.py")
        check("updater installed to ~/.medsci-skills/updater/", (home / "updater" / "update.py").is_file())

        # --- fail closed: no digest ---
        try:
            U.resolve_latest(fake_api(zbytes, asset=asset, digest=False), asset)
            check("no-digest fails closed", False)
        except U.UpdateError:
            check("no-digest fails closed", True)

        # --- draft/prerelease excluded ---
        for flag in ("draft", "prerelease"):
            try:
                U.resolve_latest(fake_api(zbytes, asset=asset, **{flag: True}), asset)
                check(f"{flag} release rejected", False)
            except U.UpdateError:
                check(f"{flag} release rejected", True)

        # --- digest mismatch (tampered bytes) ---
        try:
            U.do_update(home, lambda m: None, get_json=fake_api(zbytes, asset=asset),
                        get_bytes=lambda url: zbytes + b"X", asset_name=asset, run_install=lambda i: 0)
            check("digest mismatch aborts", False)
        except U.UpdateError:
            check("digest mismatch aborts", True)

        # --- safe_extract guards (extract a verified zip's bytes directly) ---
        _, inv = U.read_inventory_from_zip(zbytes)

        def extracts_ok(zb):
            d = base / ("ex-%d" % len(os.listdir(base)))
            d.mkdir()
            U.safe_extract(zb, d, U.read_inventory_from_zip(zb)[1])

        def rejects(label, zb):
            try:
                d = base / ("rej-%d" % len(os.listdir(base)))
                d.mkdir()
                U.safe_extract(zb, d, inv)
                check(label, False)
            except U.UpdateError:
                check(label, True)

        check("clean zip extracts", (extracts_ok(zbytes) is None))
        rejects("traversal entry rejected", make_zip(files, extra={"../evil.txt": b"x"}))
        rejects("unexpected file (not in inventory) rejected", make_zip(files, extra={"skills/demo/EXTRA.bin": b"x"}))
        rejects("symlink entry rejected", make_zip(files, symlink="link"))
        rejects("case-insensitive duplicate rejected", make_zip(files, dup=True))
        # hash/size mismatch: change a payload file's bytes but keep the old inventory
        tampered = dict(files)
        tampered["skills/demo/x.txt"] = b"TAMPERED-DIFFERENT-LENGTH"
        rejects("payload hash/size mismatch rejected", make_zip(tampered))

        # zip-bomb caps
        old_entries, old_total = U.MAX_ENTRIES, U.MAX_TOTAL_UNCOMPRESSED
        try:
            U.MAX_TOTAL_UNCOMPRESSED = 10
            rejects("total-size cap rejects", zbytes)
        finally:
            U.MAX_TOTAL_UNCOMPRESSED = old_total
        try:
            U.MAX_ENTRIES = 1
            rejects("entry-count cap rejects", zbytes)
        finally:
            U.MAX_ENTRIES = old_entries

        # --- check_update semver + cache ---
        h2 = base / "home2"
        medsci_txn.atomic_write_json(h2 / "targets" / "claude" / "state.json", {"installed_version": "1.0.0"})
        rc = U.check_update(h2, get_json=fake_api(zbytes, asset=asset, tag="v2.0.0"), asset_name=asset, force=True)
        check("check_update: newer -> UPDATE_AVAILABLE", rc == U.CHK_UPDATE_AVAILABLE)
        rc = U.check_update(h2, get_json=fake_api(zbytes, asset=asset, tag="v1.0.0"), asset_name=asset, force=True)
        check("check_update: same -> UP_TO_DATE", rc == U.CHK_UP_TO_DATE)
        # cache fresh -> no network call
        called = {"n": 0}
        def counting(_u):
            called["n"] += 1
            return fake_api(zbytes, asset=asset, tag="v2.0.0")(_u)
        U.check_update(h2, get_json=counting, asset_name=asset, force=True)   # populates cache
        U.check_update(h2, get_json=counting, asset_name=asset)              # should use cache
        check("check_update: fresh cache avoids 2nd network call", called["n"] == 1)
        # unknown local
        rc = U.check_update(base / "home_empty", get_json=fake_api(zbytes, asset=asset), asset_name=asset, force=True)
        check("check_update: unknown install -> UNKNOWN_LOCAL", rc == U.CHK_UNKNOWN_LOCAL)
        # network failure
        def boom(_u):
            raise U.UpdateError("offline")
        rc = U.check_update(h2, get_json=boom, asset_name=asset, force=True)
        check("check_update: network failure -> NETWORK_FAILURE", rc == U.CHK_NETWORK_FAILURE)

        # install.py --dry-run --check-update: still checks, but writes no cache (a dry run writes
        # nothing). resolve_latest is the network step; it is replaced, so this stays offline.
        import install  # noqa: PLC0415
        h3 = base / "home3"
        medsci_txn.atomic_write_json(h3 / "targets" / "claude" / "state.json", {"installed_version": "1.0.0"})
        real_resolve, real_argv, prev_home = U.resolve_latest, sys.argv, os.environ.get("MEDSCI_HOME")
        U.resolve_latest = lambda _get_json, _asset: {"tag": "v2.0.0"}
        sys.argv, os.environ["MEDSCI_HOME"] = ["install.py", "--dry-run", "--check-update"], str(h3)
        try:
            rc = install.main()
        finally:
            U.resolve_latest, sys.argv = real_resolve, real_argv
            if prev_home is None:
                os.environ.pop("MEDSCI_HOME", None)
            else:
                os.environ["MEDSCI_HOME"] = prev_home
        check("install.py --dry-run --check-update reports the update",
              rc == U.CHK_UPDATE_AVAILABLE)
        check("...and writes no update cache", not U._cache_path(h3).exists())

    print("----")
    print(f"test_update: {PASS} passed, {FAIL} failed")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(run())
