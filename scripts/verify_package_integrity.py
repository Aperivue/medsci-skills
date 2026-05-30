#!/usr/bin/env python3
"""Submission package integrity verifier (SPD drift control).

Per-journal folder checksum to detect silent drift between the master
manuscript and previously-built journal packages. Implements the
`SUBMISSION/{journal}/` discipline from
`skills/meta-analysis/references/submission_package_drift.md`.

Three modes:
  1. `--record`: compute checksums and write MANIFEST.checksums.json
  2. `--verify` (default): compare current state against recorded manifest
  3. `--assert-vN-docx-changed`: assert v_(N+1) docx MD5 ≠ v_N docx MD5

Usage:
    python3 scripts/verify_package_integrity.py --record \\
        [--submission-root SUBMISSION] [--journal <name>]
    python3 scripts/verify_package_integrity.py --verify \\
        [--submission-root SUBMISSION] [--journal <name>] [--json]
    python3 scripts/verify_package_integrity.py --assert-vN-docx-changed \\
        --vN-docx old/manuscript.docx --new-docx new/manuscript.docx

Per SPD-2, these files are journal-editable and excluded from drift checks:
cover_letter.docx, title_page.docx, highlights.txt, checklist.md,
response_to_reviewers.docx, MANIFEST.md, MANIFEST.checksums.json,
DO_NOT_EDIT_HERE.md.

v_(N+1) docx regeneration gate
==============================
Cross-project precedent (anonymized): an outcome-MA submission package at
v_(N+1) carried a markdown body change with a 2-paragraph edit, but the
v_(N+1) docx in the submission folder was byte-identical (MD5 collision)
to the v_N docx — a silent copy of the v_N seed that never went through
the pandoc / Zotero CWYW regeneration step. When uploaded to the EM
portal, the markdown change would have silently reverted at peer review.

The `--assert-vN-docx-changed` mode is a defense-in-depth gate: if a new
submission is being built from a prior version, the v_(N+1) docx MUST
have a different MD5 than the v_N docx. Identity = unmodified seed copy
= block submission.

Exit codes: 0 clean, 1 drift / assertion fail, 2 bad args / missing root.
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


def md5_file(path: Path) -> str:
    """MD5 of file bytes. Used for v_N ↔ v_(N+1) docx identity check.

    MD5 collisions are irrelevant here — we use it because the precedent
    failure mode is a literal `cp` of v_N over v_(N+1), which a byte-stable
    hash detects with any algorithm. MD5 is faster and produces shorter
    log lines than SHA256.
    """
    h = hashlib.md5()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def assert_vN_docx_changed(vN_docx: Path, new_docx: Path) -> int:
    """Defense-in-depth: v_(N+1) docx MUST differ from v_N docx.

    Returns:
        0 — different (PASS)
        1 — identical (FAIL, block submission)
        2 — file missing
    """
    if not vN_docx.is_file():
        print(f"ERROR: v_N docx not found: {vN_docx}", file=sys.stderr)
        return 2
    if not new_docx.is_file():
        print(f"ERROR: new docx not found: {new_docx}", file=sys.stderr)
        return 2
    vN_hash = md5_file(vN_docx)
    new_hash = md5_file(new_docx)
    if vN_hash == new_hash:
        print(
            "FAIL: v_(N+1) docx is byte-identical to v_N docx "
            f"(MD5={new_hash[:12]}...). The v_(N+1) docx appears to be an "
            "unmodified seed copy from v_N. Regenerate via pandoc citeproc "
            "OR Zotero CWYW field-code-safe re-patch before submission.",
            file=sys.stderr,
        )
        return 1
    print(
        f"PASS: v_N MD5={vN_hash[:12]}...  v_(N+1) MD5={new_hash[:12]}...  "
        "(different, OK)"
    )
    return 0


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
    mode.add_argument(
        "--assert-vN-docx-changed",
        action="store_true",
        help=(
            "Assert v_(N+1) docx MD5 != v_N docx MD5. Requires --vN-docx and "
            "--new-docx. Fails with exit 1 if identical (silent seed copy)."
        ),
    )
    ap.add_argument("--submission-root", default="SUBMISSION", help="Submission root dir")
    ap.add_argument("--journal", default=None, help="Single journal (default: all)")
    ap.add_argument("--json", action="store_true", help="Emit JSON report (verify mode)")
    ap.add_argument(
        "--vN-docx",
        type=Path,
        default=None,
        help="Path to v_N docx (frozen previous submission).",
    )
    ap.add_argument(
        "--new-docx",
        type=Path,
        default=None,
        help="Path to v_(N+1) docx (current submission candidate).",
    )
    args = ap.parse_args()

    if args.assert_vN_docx_changed:
        if args.vN_docx is None or args.new_docx is None:
            print(
                "ERROR: --assert-vN-docx-changed requires --vN-docx AND --new-docx",
                file=sys.stderr,
            )
            return 2
        return assert_vN_docx_changed(args.vN_docx, args.new_docx)

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
