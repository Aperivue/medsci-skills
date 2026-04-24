#!/usr/bin/env python3
"""Submission package integrity verifier (SPD drift control).

Per-journal folder checksum to detect silent drift between the master
manuscript and previously-built journal packages. Implements the
`SUBMISSION/{journal}/` discipline from
`skills/meta-analysis/references/submission_package_drift.md`.

Two modes:
  1. `--record`: compute checksums and write MANIFEST.checksums.json
  2. `--verify` (default): compare current state against recorded manifest

Usage:
    python3 scripts/verify_package_integrity.py --record \\
        [--submission-root SUBMISSION] [--journal <name>]
    python3 scripts/verify_package_integrity.py --verify \\
        [--submission-root SUBMISSION] [--journal <name>] [--json]

Per SPD-2, these files are journal-editable and excluded from drift checks:
cover_letter.docx, title_page.docx, highlights.txt, checklist.md,
response_to_reviewers.docx, MANIFEST.md, MANIFEST.checksums.json,
DO_NOT_EDIT_HERE.md.

Exit codes: 0 clean, 1 drift detected, 2 bad args / missing root.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import sys
from pathlib import Path

EXCLUDE_FILES = {
    "cover_letter.docx",
    "title_page.docx",
    "highlights.txt",
    "checklist.md",
    "response_to_reviewers.docx",
    "MANIFEST.md",
    "MANIFEST.checksums.json",
    "DO_NOT_EDIT_HERE.md",
}

MANIFEST_NAME = "MANIFEST.checksums.json"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def scan_journal_dir(journal_dir: Path) -> dict[str, str]:
    checksums: dict[str, str] = {}
    for p in sorted(journal_dir.rglob("*")):
        if not p.is_file():
            continue
        if p.name in EXCLUDE_FILES:
            continue
        if p.name.startswith("."):
            continue
        rel = p.relative_to(journal_dir).as_posix()
        checksums[rel] = sha256_file(p)
    return checksums


def discover_journals(root: Path, journal: str | None) -> list[Path]:
    if journal:
        target = root / journal
        return [target] if target.is_dir() else []
    return [p for p in sorted(root.iterdir()) if p.is_dir() and not p.name.startswith("_")]


def record(journals: list[Path]) -> int:
    for jd in journals:
        checksums = scan_journal_dir(jd)
        manifest = {
            "journal": jd.name,
            "recorded_at": _dt.datetime.now().isoformat(timespec="seconds"),
            "file_count": len(checksums),
            "checksums": checksums,
        }
        out = jd / MANIFEST_NAME
        out.write_text(json.dumps(manifest, indent=2))
        print(f"Recorded: {out} ({len(checksums)} files)")
    return 0


def verify(journals: list[Path], emit_json: bool) -> int:
    report: dict[str, dict] = {}
    overall_clean = True

    for jd in journals:
        manifest_path = jd / MANIFEST_NAME
        if not manifest_path.exists():
            report[jd.name] = {"status": "missing_manifest", "path": str(manifest_path)}
            overall_clean = False
            continue

        recorded = json.loads(manifest_path.read_text())["checksums"]
        current = scan_journal_dir(jd)

        missing = sorted(set(recorded) - set(current))
        added = sorted(set(current) - set(recorded))
        modified = sorted(
            f for f in set(recorded) & set(current) if recorded[f] != current[f]
        )

        status = "clean" if not (missing or added or modified) else "drift"
        report[jd.name] = {
            "status": status,
            "missing": missing,
            "added": added,
            "modified": modified,
            "recorded_at": json.loads(manifest_path.read_text()).get("recorded_at"),
        }
        if status != "clean":
            overall_clean = False

    if emit_json:
        print(json.dumps({"clean": overall_clean, "journals": report}, indent=2))
    else:
        for name, info in report.items():
            status = info["status"]
            print(f"[{status.upper()}] {name}")
            if status == "missing_manifest":
                print(f"    No manifest at {info['path']} — run --record first.")
            elif status == "drift":
                for label in ("missing", "added", "modified"):
                    files = info.get(label, [])
                    if files:
                        print(f"    {label}: {len(files)} file(s)")
                        for f in files[:10]:
                            print(f"      - {f}")
                        if len(files) > 10:
                            print(f"      ... and {len(files) - 10} more")
        print()
        print("Overall:", "CLEAN" if overall_clean else "DRIFT DETECTED")

    return 0 if overall_clean else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="Submission package integrity (SPD)")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--record", action="store_true", help="Record checksums")
    mode.add_argument("--verify", action="store_true", help="Verify checksums (default)")
    ap.add_argument("--submission-root", default="SUBMISSION", help="Submission root dir")
    ap.add_argument("--journal", default=None, help="Single journal (default: all)")
    ap.add_argument("--json", action="store_true", help="Emit JSON report (verify mode)")
    args = ap.parse_args()

    root = Path(args.submission_root).resolve()
    if not root.is_dir():
        print(f"ERROR: submission root not found: {root}", file=sys.stderr)
        return 2

    journals = discover_journals(root, args.journal)
    if not journals:
        print(f"ERROR: no journal subdirs under {root}", file=sys.stderr)
        return 2

    if args.record:
        return record(journals)
    return verify(journals, args.json)


if __name__ == "__main__":
    sys.exit(main())
