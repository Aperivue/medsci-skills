#!/usr/bin/env python3
"""
cross_document_n_check.py — Phase 5 cross-document N consistency gate.

Scans a submission package for cohort-size claims ("N patients", "k studies
included", "n excluded", "M nodules", etc.) across manuscript body, abstract,
PROSPERO record, cover letter, supplementary materials, INDEX, and PRISMA flow
caption. Emits a drift report when the same logical quantity disagrees between
documents.

Why this gate exists
====================
Multi-document N drift is a high-frequency reviewer/editor desk-reject pattern.
When a manuscript ships with k=63 in the abstract but k=64 in the supplementary
extraction sheet, reviewers treat it as either a data-integrity failure or a
late-edit failure. Either reading is fatal at peer review.

Cross-project observations (anonymized):
- Project (LLM reporting-quality SR example): five documents disagreed
  INCLUDE=63 vs 64, EXCLUDE=108/109/111. Three EXCLUDE entries existed in the
  extraction sheet without matching INCLUDE.
- Project (DTA-MA example): Results prose PRISMA cascade
  151+108+39+1+1+4=304 vs prose total "305" — off-by-one in the same paragraph.
- Project (outcome-MA example): TS denominator 331 in prose vs 326 computed
  from extraction table; Major complications 434 vs 439.
- Project (intervention-MA example): "1,847 nodules" hallucinated in v3
  against Results "881 + 402".

Usage
=====

    python cross_document_n_check.py \\
        --root path/to/project \\
        --out qc/cross_document_n.json

    python cross_document_n_check.py \\
        --files manuscript.md abstract.md supplementary/s1.md \\
        --out qc/cross_document_n.json

Optional pool-lock anchor:

    python cross_document_n_check.py \\
        --root path/to/project \\
        --pool-lock 2_Data/FINAL_POOL_LOCK.yaml \\
        --out qc/cross_document_n.json

When --pool-lock is supplied, every N value tied to a "locked" category
(include_count / exclude_count / mixed_count) is asserted to match the lock
exactly. Mismatches are P0 failures.

Output (qc/cross_document_n.json):

    {
      "submission_safe": false,
      "drift_count": 3,
      "drifts": [
        {
          "category": "included",
          "values": [63, 64],
          "locations": [
            {"file": "abstract.md",     "line": 4,  "value": 63, "context": "..."},
            {"file": "supplementary/s1.md", "line": 12, "value": 64, "context": "..."}
          ],
          "severity": "MAJOR"
        }
      ],
      "categories_scanned": ["patients", "studies", "included", "excluded", ...],
      "files_scanned": ["abstract.md", "manuscript.md", ...]
    }

Exit codes:
    0 = no drift
    1 = drift detected
    2 = invocation error (missing files, bad arguments)

This script does not modify source files. It is read-only.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterable


# --------------------------------------------------------------------------
# Pattern catalog
# --------------------------------------------------------------------------

# Each pattern maps to a normalized category label. The capture group is the
# numeric value (commas removed downstream). We intentionally keep the unit
# noun in the same alternation block so a single regex captures both "studies
# included" and "included studies" variants.
#
# Category keys are stable and downstream consumers (lock files, drift
# reports) reference them by name.
PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "included",
        re.compile(
            r"(?:\b(?:included|including|we\s+included)\s+(\d{1,3}(?:,\d{3})*|\d+)\s+(?:studies|records|reports|articles|trials|papers)\b"
            r"|\b(\d{1,3}(?:,\d{3})*|\d+)\s+(?:studies?\s+(?:were\s+)?included|included\s+studies?|"
            r"records?\s+(?:were\s+)?included|included\s+records?|"
            r"reports?\s+(?:were\s+)?included|included\s+reports?|"
            r"articles?\s+(?:were\s+)?included|included\s+articles?)\b)",
            re.IGNORECASE,
        ),
    ),
    (
        "excluded",
        re.compile(
            r"(?:\b(?:excluded|excluding|we\s+excluded)\s+(\d{1,3}(?:,\d{3})*|\d+)\s+(?:studies|records|reports|articles|trials|papers)\b"
            r"|\b(\d{1,3}(?:,\d{3})*|\d+)\s+(?:studies?\s+(?:were\s+)?excluded|excluded\s+studies?|"
            r"records?\s+(?:were\s+)?excluded|excluded\s+records?|"
            r"reports?\s+(?:were\s+)?excluded|excluded\s+reports?|"
            r"articles?\s+(?:were\s+)?excluded|excluded\s+articles?)\b)",
            re.IGNORECASE,
        ),
    ),
    (
        "patients",
        re.compile(
            r"\b(\d{1,3}(?:,\d{3})*|\d+)\s+patients?\b",
            re.IGNORECASE,
        ),
    ),
    (
        "cases",
        re.compile(
            r"\b(\d{1,3}(?:,\d{3})*|\d+)\s+cases?\b",
            re.IGNORECASE,
        ),
    ),
    (
        "nodules",
        re.compile(
            r"\b(\d{1,3}(?:,\d{3})*|\d+)\s+nodules?\b",
            re.IGNORECASE,
        ),
    ),
    (
        "tumors",
        re.compile(
            r"\b(\d{1,3}(?:,\d{3})*|\d+)\s+(?:tumou?rs?|lesions?)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "studies_total",
        re.compile(
            r"\b(\d{1,3}(?:,\d{3})*|\d+)\s+studies\b(?!\s+(?:were\s+)?(?:included|excluded))",
            re.IGNORECASE,
        ),
    ),
]

# File globs to scan when --root is supplied. Order is for output
# determinism only; the algorithm is glob-then-sort.
DEFAULT_GLOBS = (
    "manuscript.md",
    "manuscript/*.md",
    "abstract.md",
    "abstract/*.md",
    "cover_letter.md",
    "*cover_letter*.md",
    "prospero/*.md",
    "supplementary/*.md",
    "supplementary/**/*.md",
    "INDEX.md",
    "submission/**/manuscript*.md",
    "submission/**/abstract*.md",
)


# --------------------------------------------------------------------------
# Data classes
# --------------------------------------------------------------------------


@dataclass
class Hit:
    file: str
    line: int
    value: int
    context: str

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass
class Drift:
    category: str
    values: list[int]
    locations: list[Hit]
    severity: str = "MAJOR"

    def as_dict(self) -> dict:
        return {
            "category": self.category,
            "values": sorted(self.values),
            "locations": [h.as_dict() for h in self.locations],
            "severity": self.severity,
        }


@dataclass
class Report:
    submission_safe: bool
    drift_count: int
    drifts: list[Drift]
    categories_scanned: list[str]
    files_scanned: list[str]
    lock_violations: list[dict] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "submission_safe": self.submission_safe,
            "drift_count": self.drift_count,
            "drifts": [d.as_dict() for d in self.drifts],
            "categories_scanned": self.categories_scanned,
            "files_scanned": self.files_scanned,
            "lock_violations": self.lock_violations,
        }


# --------------------------------------------------------------------------
# Core
# --------------------------------------------------------------------------


def _to_int(raw: str) -> int:
    return int(raw.replace(",", ""))


def scan_file(path: Path) -> list[tuple[str, Hit]]:
    """Return (category, Hit) tuples for every matched N claim in path."""
    out: list[tuple[str, Hit]] = []
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return out
    for lineno, line in enumerate(text.splitlines(), start=1):
        for category, pat in PATTERNS:
            for m in pat.finditer(line):
                # Patterns with alternation may capture into group 1 or 2;
                # take whichever group fired.
                raw = next((g for g in m.groups() if g is not None), None)
                if raw is None:
                    continue
                try:
                    value = _to_int(raw)
                except ValueError:
                    continue
                # Skip implausibly small mentions like "2 patients" inside an
                # example table heading. Threshold is intentionally generous —
                # this gate cares about full-cohort drift, not in-text examples.
                if value < 5:
                    continue
                context = line.strip()
                if len(context) > 200:
                    context = context[:200] + "..."
                out.append((category, Hit(str(path), lineno, value, context)))
    return out


def collect_files(root: Path, extra_files: Iterable[Path] = ()) -> list[Path]:
    seen: set[Path] = set()
    files: list[Path] = []
    for pattern in DEFAULT_GLOBS:
        for hit in sorted(root.glob(pattern)):
            if hit.is_file() and hit.suffix.lower() in {".md", ".tex", ".txt"}:
                rp = hit.resolve()
                if rp not in seen:
                    seen.add(rp)
                    files.append(hit)
    for f in extra_files:
        rp = f.resolve()
        if rp not in seen and f.is_file():
            seen.add(rp)
            files.append(f)
    return files


def detect_drifts(hits_by_cat: dict[str, list[Hit]]) -> list[Drift]:
    """For each category, group hits by value. >1 distinct value = DRIFT."""
    drifts: list[Drift] = []
    for category, hits in hits_by_cat.items():
        # group by value
        by_value: dict[int, list[Hit]] = {}
        for h in hits:
            by_value.setdefault(h.value, []).append(h)
        if len(by_value) <= 1:
            continue
        # collapse for report
        all_hits = [h for hs in by_value.values() for h in hs]
        drifts.append(
            Drift(
                category=category,
                values=list(by_value.keys()),
                locations=all_hits,
                severity="MAJOR",
            )
        )
    return drifts


def check_pool_lock(
    lock_path: Path,
    hits_by_cat: dict[str, list[Hit]],
) -> list[dict]:
    """If a pool-lock yaml is supplied, assert each locked count matches."""
    try:
        import yaml  # type: ignore
    except ImportError:
        return [
            {
                "violation": "pyyaml-missing",
                "detail": "Install PyYAML to enable --pool-lock checks.",
            }
        ]
    try:
        lock = yaml.safe_load(lock_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        return [{"violation": "lock-read-error", "detail": str(exc)}]
    if not isinstance(lock, dict):
        return [{"violation": "lock-format", "detail": "lock root must be mapping"}]

    violations: list[dict] = []
    # Map lock keys to scan categories.
    pairs = [
        ("include_count", "included"),
        ("exclude_count", "excluded"),
        ("final_pool_n", "studies_total"),
    ]
    for lock_key, scan_cat in pairs:
        if lock_key not in lock:
            continue
        try:
            expected = int(lock[lock_key])
        except (TypeError, ValueError):
            violations.append(
                {
                    "violation": "lock-non-integer",
                    "key": lock_key,
                    "raw": lock[lock_key],
                }
            )
            continue
        hits = hits_by_cat.get(scan_cat, [])
        for h in hits:
            if h.value != expected:
                violations.append(
                    {
                        "violation": "pool-lock-mismatch",
                        "lock_key": lock_key,
                        "expected": expected,
                        "actual": h.value,
                        "file": h.file,
                        "line": h.line,
                        "context": h.context,
                    }
                )
    return violations


def build_report(
    files: list[Path],
    pool_lock: Path | None = None,
) -> Report:
    hits_by_cat: dict[str, list[Hit]] = {}
    for path in files:
        for cat, hit in scan_file(path):
            hits_by_cat.setdefault(cat, []).append(hit)

    drifts = detect_drifts(hits_by_cat)
    lock_violations: list[dict] = []
    if pool_lock is not None:
        lock_violations = check_pool_lock(pool_lock, hits_by_cat)

    submission_safe = not drifts and not lock_violations
    return Report(
        submission_safe=submission_safe,
        drift_count=len(drifts),
        drifts=drifts,
        categories_scanned=sorted(hits_by_cat.keys()),
        files_scanned=[str(p) for p in files],
        lock_violations=lock_violations,
    )


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Phase 5 cross-document N consistency gate. Scans manuscript, "
            "abstract, PROSPERO record, cover letter, and supplementary "
            "materials for cohort-size disagreement."
        )
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="Project root. When supplied, scans default glob set.",
    )
    parser.add_argument(
        "--files",
        type=Path,
        nargs="*",
        default=[],
        help="Explicit file list (in addition to --root glob results).",
    )
    parser.add_argument(
        "--pool-lock",
        type=Path,
        default=None,
        help=(
            "Path to FINAL_POOL_LOCK.yaml. When supplied, asserts every "
            "locked count matches in scanned documents."
        ),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Write JSON report to this path (in addition to stdout summary).",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress per-drift stdout summary; rely on --out / exit code.",
    )
    args = parser.parse_args(argv)

    if args.root is None and not args.files:
        parser.error("must supply --root or --files")

    files: list[Path] = []
    if args.root is not None:
        if not args.root.is_dir():
            parser.error(f"--root not a directory: {args.root}")
        files.extend(collect_files(args.root, args.files))
    else:
        files.extend(p for p in args.files if p.is_file())

    if not files:
        parser.error("no readable files matched")

    report = build_report(files, pool_lock=args.pool_lock)

    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report.as_dict(), indent=2), encoding="utf-8")

    if not args.quiet:
        if report.submission_safe:
            print(
                f"PASS: scanned {len(files)} files, "
                f"{len(report.categories_scanned)} categories, no drift."
            )
        else:
            print(
                f"FAIL: {report.drift_count} drift(s), "
                f"{len(report.lock_violations)} lock violation(s)."
            )
            for d in report.drifts:
                print(f"  - {d.category}: values={sorted(d.values)}")
                for h in d.locations:
                    print(f"      {h.file}:{h.line}  N={h.value}  {h.context[:80]}")
            for v in report.lock_violations:
                print(f"  - LOCK {v}")

    return 0 if report.submission_safe else 1


if __name__ == "__main__":
    sys.exit(main())
