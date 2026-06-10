#!/usr/bin/env python3
"""
check_checklist_version.py — detect a reporting checklist that is stale relative
to the current manuscript (A4b).

A reporting checklist is frequently generated against an *older* manuscript
version: its section/line references and version label no longer match the
submitted manuscript, and a reviewer who cross-checks the line numbers sees the
mismatch. This detector compares an existing checklist's target metadata against
the current manuscript and flags a regenerate-needed condition.

It reads the version contract emitted by check-reporting (v1.1+):
`target_manuscript`, `target_version`, `source_sha256` — from a JSON checklist
(`qc/reporting_checklist.json`) or from the text header / embedded JSON of a
Markdown report. Comparison precedence:

  1. `source_sha256` present and != current manuscript hash  → STALE (content changed)
  2. else `target_version` present and != current version    → STALE (version bump)
  3. else `target_manuscript` present and != current filename → STALE (different file)
  4. no version metadata at all                               → UNVERIFIABLE (regen w/ v1.1)

Exit: 0 = in sync, 1 = stale / unverifiable, 2 = usage/error. Stdlib-only.

Usage:
    python3 check_checklist_version.py --checklist qc/reporting_checklist.json \
        --manuscript manuscript_v8.md [--manuscript-version v8] \
        [--out qc/checklist_version.json] [--quiet]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

FILENAME_VERSION_RE = re.compile(r"[_\-.]v(\d{1,3})\b", re.IGNORECASE)
HEADER_TARGET_FILE_RE = re.compile(r"Target manuscript file:\s*([^\n]+)", re.IGNORECASE)
HEADER_TARGET_VER_RE = re.compile(r"Target version:\s*v?(\d{1,3})\b", re.IGNORECASE)
JSON_BLOCK_RE = re.compile(r"```json\s*(\{.*?\})\s*```", re.DOTALL)


def manuscript_identity(path: Path, explicit_version: str | None) -> dict:
    data = path.read_bytes()
    sha = hashlib.sha256(data).hexdigest()[:12]
    version = None
    if explicit_version:
        m = re.search(r"\d+", explicit_version)
        version = int(m.group(0)) if m else None
    if version is None:
        m = FILENAME_VERSION_RE.search(path.name)
        version = int(m.group(1)) if m else None
    return {"file": path.name, "version": version, "sha256": sha}


def parse_checklist(path: Path) -> dict:
    """Extract target_manuscript / target_version / source_sha256 from a JSON or
    Markdown checklist. Returns a dict with those keys (values may be None)."""
    text = path.read_text(encoding="utf-8", errors="replace")
    out = {"target_manuscript": None, "target_version": None, "source_sha256": None}

    obj = None
    if path.suffix.lower() == ".json":
        try:
            obj = json.loads(text)
        except Exception:
            obj = None
    if obj is None:
        m = JSON_BLOCK_RE.search(text)
        if m:
            try:
                obj = json.loads(m.group(1))
            except Exception:
                obj = None
    if isinstance(obj, dict):
        out["target_manuscript"] = obj.get("target_manuscript")
        out["source_sha256"] = obj.get("source_sha256")
        tv = obj.get("target_version")
        if tv is not None:
            mm = re.search(r"\d+", str(tv))
            out["target_version"] = int(mm.group(0)) if mm else None

    # Markdown header fallbacks (only fill what JSON did not provide)
    if out["target_manuscript"] is None:
        m = HEADER_TARGET_FILE_RE.search(text)
        if m:
            out["target_manuscript"] = m.group(1).strip()
    if out["target_version"] is None:
        m = HEADER_TARGET_VER_RE.search(text)
        if m:
            out["target_version"] = int(m.group(1))
    return out


def evaluate(current: dict, checklist: dict) -> list[dict]:
    findings: list[dict] = []
    ck_sha = checklist.get("source_sha256")
    ck_ver = checklist.get("target_version")
    ck_file = checklist.get("target_manuscript")

    if ck_sha and current["sha256"] and ck_sha != current["sha256"]:
        findings.append({
            "type": "checklist_content_stale", "severity": "stale",
            "detail": f"checklist source_sha256 {ck_sha} != current {current['sha256']} "
                      "— manuscript content changed since the checklist was generated"})
    elif ck_ver is not None and current["version"] is not None and ck_ver != current["version"]:
        findings.append({
            "type": "checklist_version_stale", "severity": "stale",
            "detail": f"checklist targets v{ck_ver} but current is v{current['version']}"})
    elif ck_file and ck_file != current["file"]:
        findings.append({
            "type": "checklist_file_mismatch", "severity": "stale",
            "detail": f"checklist targets '{ck_file}' but current is '{current['file']}'"})

    if ck_sha is None and ck_ver is None and ck_file is None:
        findings.append({
            "type": "checklist_no_version_metadata", "severity": "unverifiable",
            "detail": "checklist carries no target_manuscript/target_version/source_sha256 "
                      "(pre-v1.1 contract) — cannot verify; regenerate with current check-reporting"})
    return findings


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Flag a reporting checklist that is stale vs the current manuscript.")
    ap.add_argument("--checklist", type=Path, required=True,
                    help="qc/reporting_checklist.json or the .md report.")
    ap.add_argument("--manuscript", type=Path, required=True, help="Current manuscript file.")
    ap.add_argument("--manuscript-version", default=None,
                    help="Current version token (else inferred from filename).")
    ap.add_argument("--out", type=Path, default=None, help="Write JSON report here.")
    ap.add_argument("--quiet", action="store_true", help="Suppress stdout summary.")
    args = ap.parse_args(argv)

    if not args.checklist.is_file():
        print(f"ERROR: --checklist not a file: {args.checklist}", file=sys.stderr)
        return 2
    if not args.manuscript.is_file():
        print(f"ERROR: --manuscript not a file: {args.manuscript}", file=sys.stderr)
        return 2

    current = manuscript_identity(args.manuscript, args.manuscript_version)
    checklist = parse_checklist(args.checklist)
    findings = evaluate(current, checklist)
    safe = not findings

    report = {"submission_safe": safe, "current": current,
              "checklist": checklist, "findings": findings}
    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2), encoding="utf-8")

    if not args.quiet:
        if safe:
            print(f"PASS: checklist matches current manuscript (v{current['version']}, "
                  f"{current['sha256']}).")
        else:
            print("FAIL: checklist is stale or unverifiable:")
            for f in findings:
                print(f"  - [{f['severity']}] {f['type']}: {f['detail']}")

    return 0 if safe else 1


if __name__ == "__main__":
    sys.exit(main())
