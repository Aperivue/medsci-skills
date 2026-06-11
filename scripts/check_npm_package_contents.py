#!/usr/bin/env python3
"""npm tarball content audit (allowlist/denylist gate).

Parses the file list that `npm pack` would publish and asserts that
(1) no private / dev / heavy / copyright-bearing path leaks into the tarball, and
(2) the required public files are present.

This is defense-in-depth on top of the `files` allowlist in package.json: if the
allowlist is ever loosened, this gate still blocks the dangerous paths.

Usage:
    python3 scripts/check_npm_package_contents.py            # dry-run (default)
    python3 scripts/check_npm_package_contents.py --real     # real `npm pack`, then clean up
    python3 scripts/check_npm_package_contents.py --json-file pack.json   # parse a saved file list

Exit codes: 0 = clean, 1 = violation (denied path present or required path missing),
2 = usage/parse error.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# Denied path prefixes (matched after stripping a leading "package/").
DENY_PREFIXES = (
    "_corpus/",
    "_improvement_plans/",
    "dist/",
    "demo/",
    "evaluation/",
    "tests/",
    "metrics/",
    "docs/",
    "assets/",
    ".git/",
    ".github/",
)
# Denied path substrings (anywhere in the normalized path). Includes OS/editor junk
# (.DS_Store) and tool caches that can hide inside the allowlisted skills/ subtree.
DENY_SUBSTRINGS = (
    "__pycache__",
    "/.git/",
    ".pyc",
    ".DS_Store",
    ".pytest_cache",
    ".ipynb_checkpoints",
)
# Denied exact root files (private scratch / handoff / dev-only docs).
DENY_ROOT_FILES = {
    "paper.md",
    "MEDSCI_AUDIT.md",
    "IMPACT.md",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "CODE_OF_CONDUCT.md",
}
# Denied root-file prefixes (HANDOFF.md, HANDOFF_LESSONS_*, HANDOFF_LETTER_*, PLAN_*).
DENY_ROOT_PREFIXES = ("HANDOFF", "PLAN_")

# Required paths (normalized). Prefix entries match the start of a path.
REQUIRED_PREFIXES = ("skills/",)
REQUIRED_FILES = (
    "installers/install.py",
    "LICENSE",
    "bin/medsci-skills.js",
    "README.md",
)


def normalize(p: str) -> str:
    p = p.replace("\\", "/")
    if p.startswith("./"):
        p = p[2:]
    if p.startswith("package/"):
        p = p[len("package/"):]
    return p


def get_file_list(args) -> tuple[list[str], dict[str, int]]:
    """Return (normalized paths, {normalized path: mode}). Mode is npm's decimal mode or -1."""
    if args.json_file:
        with open(args.json_file, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    else:
        cmd = ["npm", "pack", "--json"]
        if not args.real:
            cmd.append("--dry-run")
        # Anchor to the repo root so the audit packs the right package regardless of cwd.
        proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(REPO_ROOT))
        if proc.returncode != 0:
            sys.stderr.write("npm pack failed:\n" + proc.stderr + "\n")
            sys.exit(2)
        out = proc.stdout.strip()
        start = out.find("[")
        if start == -1:
            start = out.find("{")
        if start == -1:
            sys.stderr.write("Could not locate JSON in npm pack output.\n")
            sys.exit(2)
        data = json.loads(out[start:])
        if args.real:
            # `npm pack` (no dry-run) writes a .tgz in the repo root; remove it to avoid churn.
            entries = data if isinstance(data, list) else [data]
            for entry in entries:
                if not isinstance(entry, dict):
                    continue
                tgz = entry.get("filename")
                if tgz:
                    tgz_path = REPO_ROOT / tgz
                    if tgz_path.exists():
                        try:
                            tgz_path.unlink()
                        except OSError:
                            pass

    # npm versions differ: --json may emit a single object instead of an array.
    if isinstance(data, dict):
        data = [data]

    paths: list[str] = []
    modes: dict[str, int] = {}
    for entry in data:
        if not isinstance(entry, dict):
            continue
        for f in entry.get("files", []):
            np = normalize(f.get("path", ""))
            if not np:
                continue
            paths.append(np)
            modes[np] = f.get("mode", -1)
    return paths, modes


def is_denied(p: str) -> bool:
    if any(p.startswith(pre) for pre in DENY_PREFIXES):
        return True
    if any(sub in p for sub in DENY_SUBSTRINGS):
        return True
    if "/" not in p:  # root file
        if p in DENY_ROOT_FILES:
            return True
        if any(p.startswith(pre) for pre in DENY_ROOT_PREFIXES):
            return True
    return False


def main() -> int:
    ap = argparse.ArgumentParser(description="npm tarball content audit.")
    ap.add_argument("--real", action="store_true", help="Run a real `npm pack` (then delete the tarball).")
    ap.add_argument("--json-file", help="Parse a saved `npm pack --json` file list instead of running npm.")
    args = ap.parse_args()

    paths, modes = get_file_list(args)
    if not paths:
        sys.stderr.write("No files reported by npm pack — refusing to pass.\n")
        return 2

    violations = [p for p in sorted(set(paths)) if is_denied(p)]

    present = set(paths)
    missing_files = [f for f in REQUIRED_FILES if f not in present]
    missing_prefixes = [pre for pre in REQUIRED_PREFIXES if not any(p.startswith(pre) for p in paths)]

    # Executable-bit check on the CLI (warn only — npm mode reporting varies).
    bin_mode = modes.get("bin/medsci-skills.js", -1)
    bin_warn = bin_mode != -1 and not (bin_mode & 0o111)

    print(f"npm tarball audit — {len(set(paths))} files")
    if violations:
        print("\nDENIED paths present in tarball:")
        for v in violations:
            print(f"  ! {v}")
    if missing_files or missing_prefixes:
        print("\nREQUIRED paths missing from tarball:")
        for m in missing_files + [f"{pre}*" for pre in missing_prefixes]:
            print(f"  ? {m}")
    if bin_warn:
        print(f"\nWARN: bin/medsci-skills.js mode {oct(bin_mode)} has no exec bit "
              "(npm may still set it; verify with `test -x`).")

    if violations or missing_files or missing_prefixes:
        print("\nFAIL")
        return 1
    print("\nOK: allowlist clean, required files present.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
