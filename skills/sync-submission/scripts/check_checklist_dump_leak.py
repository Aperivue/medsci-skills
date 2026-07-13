#!/usr/bin/env python3
"""
check_checklist_dump_leak.py — catch an internal audit dump that leaked into a
reviewer-facing submission file.

`/check-reporting` and `/self-review` emit an *internal audit* report: an
item-by-item working document carrying auto-fix annotations, a raw JSON block
(`compliance_pct`, `fixable_by_ai`, `check_reporting_version`), pipeline-log
paths, and "Action Items". That report is a development artifact — it is NOT the
official reporting checklist a journal expects ("Item | Recommendation | Reported
in page/section").

A near-miss: a prior project's `STROBE_checklist_v4.pdf` was actually the
`/check-reporting` audit dump, reused by filename into a later submission and
compiled into the reviewer-visible proof — exposing auto-fix notes, the raw JSON,
and a stale old title. Body-text PII scans miss it (the tokens are tooling
jargon, not names); the stale-checklist detector misses it (it checks version
metadata, not whether the file is a dump). This detector closes that gap.

It scans a submission directory for files whose extracted text carries
audit-dump tokens that must never reach a reviewer:

  - check-reporting JSON keys: ``compliance_pct``, ``fixable_by_ai``,
    ``check_reporting_version``, ``checked_items``
  - auto-fix annotations: ``Auto-fix:``, ``auto-fixed``, ``[PARTIAL→auto-fixed]``,
    ``suggested_fix``
  - working-doc headers: ``Action Items``
  - pipeline/tooling paths: ``_pipeline_log``, ``qc/`` audit JSON references,
    ``check_reporting`` / ``check-reporting`` self-reference
  - from-memory / contract markers: ``NON-AUTHORITATIVE``,
    ``MISSING_CHECKLIST_CONTRACT_VIOLATION``

Every hit is severity ``leak`` — these tokens are tooling output, never legitimate
content of a submission-facing checklist or supplement. Exit 0 = clean, 1 =
leak(s) found, 2 = usage/error. Degrades gracefully without poppler: .md/.txt and
.docx are always scanned; .pdf is reported as skipped (poppler_available:false)
rather than silently passing.

Stdlib-only.

Usage:
    python3 check_checklist_dump_leak.py --dir submission/ [--out qc/checklist_dump_leak.json] [--quiet]
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import zipfile
from dataclasses import dataclass, field, asdict
from pathlib import Path

# Audit-dump tokens. Each is tooling output that must never appear in a
# reviewer-facing file. Patterns are specific (underscore JSON keys, arrow
# annotations, header phrases) to keep false positives near zero against a
# legitimate official checklist ("Item | Recommendation | Reported in …").
DUMP_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("compliance_pct", re.compile(r"\bcompliance_pct\b")),
    ("fixable_by_ai", re.compile(r"\bfixable_by_ai\b")),
    ("check_reporting_version", re.compile(r"\bcheck_reporting_version\b")),
    ("checked_items_json", re.compile(r'"checked_items"\s*:')),
    ("auto_fix_annotation", re.compile(r"Auto-fix\s*:", re.IGNORECASE)),
    ("auto_fixed_marker", re.compile(r"auto-?fixed", re.IGNORECASE)),
    ("partial_autofix_marker", re.compile(r"\[\s*PARTIAL\s*[→\-]+\s*auto", re.IGNORECASE)),
    ("suggested_fix", re.compile(r"\bsuggested_fix\b")),
    ("action_items_header", re.compile(r"^#{0,6}\s*Action Items\b", re.IGNORECASE | re.MULTILINE)),
    ("pipeline_log_path", re.compile(r"_pipeline_log(?:\.md)?\b")),
    ("check_reporting_selfref", re.compile(r"\bcheck[_-]reporting\b", re.IGNORECASE)),
    ("non_authoritative", re.compile(r"\bNON-AUTHORITATIVE\b")),
    ("missing_checklist_contract", re.compile(r"\bMISSING_CHECKLIST_CONTRACT_VIOLATION\b")),
]

TEXT_SUFFIXES = (".md", ".txt", ".markdown")


@dataclass
class Finding:
    type: str
    severity: str  # always "leak"
    path: str
    detail: str


@dataclass
class Report:
    findings: list[Finding] = field(default_factory=list)
    scanned: dict[str, int] = field(default_factory=dict)
    poppler_available: bool = False
    skipped: list[str] = field(default_factory=list)

    @property
    def has_leak(self) -> bool:
        return any(f.severity == "leak" for f in self.findings)

    def as_dict(self) -> dict:
        return {
            "submission_safe": not self.has_leak,
            "poppler_available": self.poppler_available,
            "scanned": self.scanned,
            "skipped": self.skipped,
            "summary": {"leak": sum(1 for f in self.findings if f.severity == "leak")},
            "findings": [asdict(f) for f in self.findings],
        }


def _first_snippet(text: str, pat: re.Pattern) -> str:
    m = pat.search(text)
    if not m:
        return ""
    line_start = text.rfind("\n", 0, m.start()) + 1
    line_end = text.find("\n", m.end())
    if line_end == -1:
        line_end = len(text)
    return text[line_start:line_end].strip()[:140]


def _scan_text(text: str, rel: str, rep: Report) -> None:
    for name, pat in DUMP_PATTERNS:
        if pat.search(text):
            rep.findings.append(Finding(
                "checklist_dump_token", "leak", rel,
                f"audit-dump token '{name}' present (internal /check-reporting "
                f"or /self-review output, not a submission checklist): "
                f"{_first_snippet(text, pat)}"))


def _pdftotext(pdf: Path) -> str | None:
    try:
        r = subprocess.run(["pdftotext", "-q", str(pdf), "-"],
                           capture_output=True, text=True, timeout=60)
        return r.stdout
    except Exception:
        return None


def _docx_text(docx: Path) -> str | None:
    try:
        with zipfile.ZipFile(docx) as z:
            names = [n for n in z.namelist()
                     if n.startswith("word/") and n.endswith(".xml")]
            chunks = []
            for n in names:
                xml = z.read(n).decode("utf-8", errors="replace")
                chunks.append(re.sub(r"<[^>]+>", " ", xml))
            return " ".join(chunks)
    except Exception:
        return None


def build_report(root: Path, poppler: bool) -> Report:
    rep = Report(poppler_available=poppler)
    text_files = docx_files = pdf_files = 0

    for p in sorted(root.rglob("*")):
        if not p.is_file() or "__pycache__" in p.parts:
            continue
        suffix = p.suffix.lower()
        rel = str(p.relative_to(root))

        if suffix in TEXT_SUFFIXES:
            text_files += 1
            _scan_text(p.read_text(encoding="utf-8", errors="replace"), rel, rep)

        elif suffix == ".docx":
            docx_files += 1
            txt = _docx_text(p)
            if txt is None:
                rep.skipped.append(f"docx unreadable: {rel}")
            else:
                _scan_text(txt, rel, rep)

        elif suffix == ".pdf":
            pdf_files += 1
            if poppler:
                txt = _pdftotext(p)
                if txt is None:
                    rep.skipped.append(f"pdftotext failed: {rel}")
                else:
                    _scan_text(txt, rel, rep)
            else:
                rep.skipped.append(f"poppler unavailable, PDF not scanned: {rel}")

    rep.scanned = {"text": text_files, "docx": docx_files, "pdf": pdf_files}
    return rep


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Catch an internal /check-reporting or /self-review audit dump "
                    "leaked into a reviewer-facing submission file.")
    ap.add_argument("--dir", type=Path, default=Path.cwd(),
                    help="Submission directory to scan (default: cwd).")
    ap.add_argument("--out", type=Path, default=None, help="Write JSON report here.")
    ap.add_argument("--quiet", action="store_true", help="Suppress stdout summary.")
    args = ap.parse_args(argv)

    if not args.dir.is_dir():
        print(f"ERROR: --dir not a directory: {args.dir}", file=sys.stderr)
        return 2

    poppler = shutil.which("pdftotext") is not None
    rep = build_report(args.dir, poppler)
    safe = not rep.has_leak

    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps({"detector": "check_checklist_dump_leak", **rep.as_dict()}, indent=2), encoding="utf-8")

    if not args.quiet:
        if not poppler:
            print("NOTE: poppler (pdftotext) not found — PDF files not scanned; "
                  "install poppler-utils for full coverage.")
        if safe:
            print(f"PASS: no audit-dump leak ({rep.scanned}).")
        else:
            print(f"FAIL: audit-dump leak — {rep.as_dict()['summary']}")
            for f in rep.findings:
                print(f"  - [{f.severity}] {f.type} {f.path}: {f.detail}")

    return 0 if safe else 1


if __name__ == "__main__":
    sys.exit(main())
