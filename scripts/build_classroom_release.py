#!/usr/bin/env python3
"""Build classroom installer ZIP files for GitHub Releases.

When invoked by the release workflow with ``--tag`` (and optionally ``--git-sha`` /
``--built-at``), a deterministic ``provenance.json`` ``{schema_version, tag, version,
git_sha, built_at}`` is injected at the ZIP root. The self-updater validates that the
provenance ``tag``/``version`` match the release tag and the bundled
``distribution_manifest.json`` before installing. ``provenance.json`` is a control file:
it is intentionally **not** part of ``distribution_files.json`` (the safe-extract
inventory), so injecting it never breaks the inventory's path/size/sha256 round-trip.

Local builds without ``--tag`` produce provenance-free ZIPs (the updater tolerates the
absence); only the release workflow, which knows the authoritative tag, injects it.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import zipfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DIST_DIR = REPO_ROOT / "dist"
PACKAGE_NAME = "medsci-skills-classroom"
MANIFEST_PATH = REPO_ROOT / "metadata" / "distribution_manifest.json"
INCLUDE_PATHS = [
    "README_FIRST.md",
    "installers",
    "skills",
    # Self-update foundation: the version/ownership manifest + the file inventory the
    # updater (PR-1b) uses as its safe-extraction allowlist. Deterministic, tracked.
    "metadata/distribution_manifest.json",
    "metadata/distribution_files.json",
]

# "tests" excluded so installer dev tests are not shipped to classroom users; this keeps the
# ZIP payload identical to metadata/distribution_files.json (which also excludes tests).
EXCLUDE_DIR_NAMES = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", "node_modules", ".git", "tests"}
EXCLUDE_FILE_NAMES = {
    ".DS_Store",
    "Thumbs.db",
    # Personal session/dev scratchpads — should never reach a classroom ZIP.
    "HANDOFF.md",
    "FOLLOWUPS.md",
    "IMPROVEMENT_QUEUE.md",
}
EXCLUDE_NAME_PREFIXES = ("TODO_", "HANDOFF_", "PLAN_", "PLANNED_")
EXCLUDE_SUFFIXES = {".pyc", ".pyo", ".swp"}


def _is_excluded(path: Path) -> bool:
    if path.name in EXCLUDE_FILE_NAMES:
        return True
    if path.name.startswith(EXCLUDE_NAME_PREFIXES):
        return True
    if path.suffix in EXCLUDE_SUFFIXES:
        return True
    if any(part in EXCLUDE_DIR_NAMES for part in path.parts):
        return True
    return False


def _git_tracked_files() -> set[Path]:
    """Return the set of repo-relative paths tracked by git (no untracked or ignored)."""
    try:
        out = subprocess.check_output(
            ["git", "-C", str(REPO_ROOT), "ls-files"],
            text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return set()
    return {REPO_ROOT / line.strip() for line in out.splitlines() if line.strip()}


TRACKED_FILES: set[Path] = _git_tracked_files()


def add_path(zipf: zipfile.ZipFile, path: Path, root_name: str) -> None:
    if path.is_file():
        if _is_excluded(path) or (TRACKED_FILES and path not in TRACKED_FILES):
            return
        zipf.write(path, Path(root_name) / path.relative_to(REPO_ROOT))
        return
    for item in sorted(path.rglob("*")):
        if not item.is_file():
            continue
        if _is_excluded(item):
            continue
        if TRACKED_FILES and item not in TRACKED_FILES:
            continue
        zipf.write(item, Path(root_name) / item.relative_to(REPO_ROOT))


def manifest_version() -> str:
    """The version recorded in the tracked distribution_manifest.json (CITATION-derived SSOT)."""
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))["version"]


def build_zip(platform: str, version: str, provenance: dict | None = None) -> Path:
    root_name = f"{PACKAGE_NAME}-{version}"
    out = DIST_DIR / f"{PACKAGE_NAME}-{platform}.zip"
    if out.exists():
        out.unlink()
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as zipf:
        for rel in INCLUDE_PATHS:
            path = REPO_ROOT / rel
            if path.exists():
                add_path(zipf, path, root_name)
        if provenance is not None:
            # Deterministic bytes (sorted keys); a control file, NOT in distribution_files.json.
            # Force a forward-slash arcname so the ZIP path is correct regardless of build OS
            # (the updater's _zip_root / _reject_unsafe_name split on '/' and reject '\\').
            zipf.writestr(
                f"{root_name}/provenance.json",
                json.dumps(provenance, indent=2, sort_keys=True) + "\n",
            )
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Build classroom release ZIPs.")
    parser.add_argument("--version", default="latest", help="Version label for the ZIP root folder (ignored when --tag is given).")
    parser.add_argument("--tag", default=None, help="Release tag (e.g. v4.7.0). Injects a verified provenance.json and pins the root version.")
    parser.add_argument("--git-sha", default=None, help="Commit SHA to record in provenance.json (release workflow supplies ${{ github.sha }}).")
    parser.add_argument("--built-at", default=None, help="Build timestamp (ISO-8601 UTC) to record in provenance.json.")
    args = parser.parse_args()

    provenance: dict | None = None
    version = args.version
    if args.tag:
        tag = args.tag
        version = tag[1:] if tag.startswith("v") else tag
        # The manifest version is the CITATION-derived SSOT (gen_distribution_manifest copies it from
        # CITATION.cff). This gate pins the tag to that single source; the full three-way check
        # (CITATION == package.json == manifest) runs as its own release.yml step before the build.
        man_ver = manifest_version()
        if version != man_ver:
            raise SystemExit(
                f"release tag {tag!r} (version {version!r}) != distribution_manifest version "
                f"{man_ver!r}; bump CITATION.cff/package.json/manifest before tagging "
                f"(scripts/check_version_consistency.py)."
            )
        provenance = {
            "schema_version": 1,
            "tag": tag,
            "version": version,
            "git_sha": args.git_sha or "",
            "built_at": args.built_at or "",
        }

    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    DIST_DIR.mkdir(parents=True)

    outputs = [build_zip("windows", version, provenance), build_zip("macos", version, provenance)]
    for out in outputs:
        print(out)
    if provenance is not None:
        print(f"\nInjected provenance.json: tag={provenance['tag']} version={provenance['version']} "
              f"git_sha={provenance['git_sha'][:12]} built_at={provenance['built_at']}")
    print("\nUpload these files as GitHub Release assets:")
    for out in outputs:
        print(f"- {out.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
