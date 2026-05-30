#!/usr/bin/env python3
"""Build classroom installer ZIP files for GitHub Releases."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import zipfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DIST_DIR = REPO_ROOT / "dist"
PACKAGE_NAME = "medsci-skills-classroom"
INCLUDE_PATHS = [
    "README_FIRST.md",
    "installers",
    "skills",
]

EXCLUDE_DIR_NAMES = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", "node_modules", ".git"}
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


def build_zip(platform: str, version: str) -> Path:
    root_name = f"{PACKAGE_NAME}-{version}"
    out = DIST_DIR / f"{PACKAGE_NAME}-{platform}.zip"
    if out.exists():
        out.unlink()
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as zipf:
        for rel in INCLUDE_PATHS:
            path = REPO_ROOT / rel
            if path.exists():
                add_path(zipf, path, root_name)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Build classroom release ZIPs.")
    parser.add_argument("--version", default="latest", help="Version label embedded in the ZIP root folder.")
    args = parser.parse_args()

    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    DIST_DIR.mkdir(parents=True)

    outputs = [build_zip("windows", args.version), build_zip("macos", args.version)]
    for out in outputs:
        print(out)
    print("\nUpload these files as GitHub Release assets:")
    for out in outputs:
        print(f"- {out.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
