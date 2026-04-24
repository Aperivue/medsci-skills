#!/usr/bin/env python3
"""Build classroom installer ZIP files for GitHub Releases."""

from __future__ import annotations

import argparse
import shutil
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


def add_path(zipf: zipfile.ZipFile, path: Path, root_name: str) -> None:
    if path.is_file():
        zipf.write(path, Path(root_name) / path.relative_to(REPO_ROOT))
        return
    for item in sorted(path.rglob("*")):
        if item.is_file():
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
