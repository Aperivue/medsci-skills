#!/usr/bin/env python3
"""Generate the two deterministic distribution manifests (v4.x self-update foundation).

Two tracked, byte-deterministic files (no build timestamps / sha-of-build), each CI
`--check`-gated:

  metadata/distribution_manifest.json
    Small ownership/version manifest: {schema_version, version, owned_skills}.
    `version` is copied from CITATION.cff (the canonical version SSOT); a separate
    consistency check (scripts/check_version_consistency.py) asserts
    CITATION.cff == package.json == this file.

  metadata/distribution_files.json
    Deterministic inventory [{path, size, sha256}] of the **classroom/common install
    payload** — the file set the classroom ZIP ships (README_FIRST.md, installers/,
    skills/, and these two metadata manifests). It is the SSOT for (a) this CI check
    (the on-disk payload matches the inventory) and (b) the updater's ZIP
    safe-extraction allowlist + per-file hash (PR-1b). It deliberately **excludes
    itself** and the build-time `provenance.json` (injected by the release workflow,
    not tracked). It describes the *common* payload, not every file in any one
    channel (npm ships extra files such as bin/ and package.json that are NOT here).

Stdlib-only, deterministic (sorted, POSIX paths). Usage:
  python3 scripts/gen_distribution_manifest.py          # write both files
  python3 scripts/gen_distribution_manifest.py --check   # verify in sync; exit 1 on drift (CI gate)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = ROOT / "skills"
MANIFEST = ROOT / "metadata" / "distribution_manifest.json"
FILES = ROOT / "metadata" / "distribution_files.json"

SCHEMA_VERSION = 1

# The classroom/common install payload roots (the files the classroom ZIP ships
# that get installed/run). distribution_files.json inventories every file under
# these, minus the exclusions. The two metadata manifests + the build-time
# provenance.json are intentionally NOT inventoried (they are control files, and a
# files-manifest cannot contain its own hash) — the updater (PR-1b) allowlists those
# by name in addition to this inventory.
PAYLOAD_ROOTS = [
    "README_FIRST.md",
    # The licence and the third-party notices ship in the ZIP, so they must be in the
    # allowlist too — update.safe_extract rejects any entry the inventory does not name.
    "LICENSE",
    "THIRD-PARTY-NOTICES.md",
    "installers",
    "skills",
]

# Never inventoried: the metadata manifests (control files / self-reference), the
# build-time provenance file (release-injected, not tracked), and junk.
EXCLUDE_RELPATHS = {
    "metadata/distribution_manifest.json",
    "metadata/distribution_files.json",
    "provenance.json",
    "metadata/provenance.json",
}
# ".logs" excludes installers/.logs/ — the gitignored, per-machine install logs
# install.py writes; without this, running install.py locally then regenerating would
# add a machine-specific log path to the manifest (local `--check` drift, or an
# accidental commit of a log path).
EXCLUDE_DIR_NAMES = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", "node_modules", ".git", "tests", ".logs"}
EXCLUDE_SUFFIXES = (".pyc",)
EXCLUDE_NAMES = {".DS_Store"}


def citation_version() -> str:
    text = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
    m = re.search(r'^version:\s*"?([0-9]+\.[0-9]+\.[0-9]+)"?\s*$', text, re.MULTILINE)
    if not m:
        raise SystemExit("ERROR: could not read version from CITATION.cff")
    return m.group(1)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _included(rel: str, name: str) -> bool:
    if rel in EXCLUDE_RELPATHS or name in EXCLUDE_NAMES:
        return False
    if name.endswith(EXCLUDE_SUFFIXES):
        return False
    parts = set(Path(rel).parts)
    return not (parts & EXCLUDE_DIR_NAMES)


def iter_payload_files() -> list[Path]:
    out: list[Path] = []
    for root in PAYLOAD_ROOTS:
        p = ROOT / root
        if p.is_file():
            out.append(p)
        elif p.is_dir():
            for f in p.rglob("*"):
                if f.is_file():
                    out.append(f)
    files: list[Path] = []
    for f in out:
        rel = f.relative_to(ROOT).as_posix()
        if _included(rel, f.name):
            files.append(f)
    # de-dup + deterministic order
    uniq = sorted({f.relative_to(ROOT).as_posix(): f for f in files}.items())
    return [f for _rel, f in uniq]


def build_owned_skills() -> list[str]:
    return sorted(p.name for p in SKILLS_DIR.iterdir() if p.is_dir() and (p / "SKILL.md").is_file())


def build_manifest() -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "version": citation_version(),
        "owned_skills": build_owned_skills(),
    }


def build_files() -> dict:
    inv = []
    for f in iter_payload_files():
        rel = f.relative_to(ROOT).as_posix()
        inv.append({"path": rel, "size": f.stat().st_size, "sha256": sha256_file(f)})
    inv.sort(key=lambda e: e["path"])
    return {"schema_version": SCHEMA_VERSION, "files": inv}


def dumps(obj: dict) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=False) + "\n"


def _explain_drift(fresh_files_json: str, limit: int = 8) -> None:
    """Name the files that moved, so the failure is a fact and not an accusation.

    "The manifest is out of date" tells someone nothing. "You added these ten files" tells them
    they did exactly what the issue asked, and that this check is bookkeeping.
    """
    try:
        old = {e["path"]: e["sha256"] for e in json.loads(FILES.read_text(encoding="utf-8"))["files"]}
    except (OSError, ValueError, KeyError):
        return  # no readable previous manifest: the prose below is all we can honestly say
    new = {e["path"]: e["sha256"] for e in json.loads(fresh_files_json)["files"]}

    added = sorted(set(new) - set(old))
    removed = sorted(set(old) - set(new))
    changed = sorted(p for p in set(old) & set(new) if old[p] != new[p])

    for label, paths in (("added", added), ("removed", removed), ("changed", changed)):
        if not paths:
            continue
        print(f"  {len(paths)} file(s) {label}:", file=sys.stderr)
        for p in paths[:limit]:
            print(f"    {p}", file=sys.stderr)
        if len(paths) > limit:
            print(f"    ... and {len(paths) - limit} more", file=sys.stderr)


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate/verify the distribution manifests.")
    ap.add_argument("--check", action="store_true", help="verify on-disk files match; exit 1 on drift")
    args = ap.parse_args()

    manifest = dumps(build_manifest())
    # files manifest must be generated AFTER excluding itself; build it from a tree that
    # may already contain a stale files-manifest (excluded), so it is self-consistent.
    files = dumps(build_files())

    if args.check:
        drift = []
        for path, want in ((MANIFEST, manifest), (FILES, files)):
            have = path.read_text(encoding="utf-8") if path.exists() else None
            if have != want:
                drift.append(path.relative_to(ROOT).as_posix())
        if drift:
            # This gate protects the self-updater, which verifies a downloaded release against
            # these hashes. A stale manifest is a broken update, so the gate is strict and stays
            # strict.
            #
            # But the people who trip it are mostly FIRST-TIME contributors adding a shipped file —
            # a journal profile, a reference doc — because adding a file *is* the whole of a good
            # first issue. And our own CONTRIBUTING invites them through a browser-only path with
            # no git and no terminal: someone who accepted that invitation **cannot run this
            # generator at all**. "Run python3 scripts/…" is not an instruction to them, it is a
            # dead end, and a red X on a stranger's first contribution is how you lose them.
            #
            # So: name what moved, say what to do, and say plainly that if they cannot do it, their
            # PR is not wrong and a maintainer will finish it.
            print(f"DISTRIBUTION_MANIFEST_DRIFT: {', '.join(drift)} out of date.\n", file=sys.stderr)
            _explain_drift(files)
            print(
                "\nWhat this is: these files list every file we ship, with its hash, so the\n"
                "self-updater can verify a download. Adding or editing a shipped file changes that\n"
                "list. Nothing is wrong with your change — the list just has to be refreshed.\n"
                "\n"
                "  To refresh it:  python3 scripts/gen_distribution_manifest.py\n"
                "                  then commit the changed file(s) under metadata/\n"
                "\n"
                "If you contributed through the GitHub website and cannot run Python: that is fine,\n"
                "and expected. Leave it — say so in the pull request and a maintainer will refresh\n"
                "the manifest before merging. This check being red is not a rejection.",
                file=sys.stderr,
            )
            return 1
        print(f"OK: distribution manifests in sync (version {build_manifest()['version']}, "
              f"{len(build_files()['files'])} payload files, {len(build_owned_skills())} owned skills).")
        return 0

    MANIFEST.write_text(manifest, encoding="utf-8")
    FILES.write_text(files, encoding="utf-8")
    print(f"wrote {MANIFEST.relative_to(ROOT)} + {FILES.relative_to(ROOT)} "
          f"(version {build_manifest()['version']}, {len(build_files()['files'])} files).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
