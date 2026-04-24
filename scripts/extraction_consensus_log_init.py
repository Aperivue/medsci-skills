#!/usr/bin/env python3
"""Initialize extraction_consensus_log.md template (DI-1).

Creates a standalone consensus log with the column set specified in
`skills/meta-analysis/references/data_integrity_checklist.md` DI-1.
Comparative extraction results belong in this log as formal rows, not as
inline R-script comments.

Usage:
    python3 scripts/extraction_consensus_log_init.py \\
        [--output 2_Data/extraction_consensus_log.md] \\
        [--project-root <path>] [--force]

Exit codes: 0 success, 2 bad args, 3 output exists without --force.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import sys
from pathlib import Path

COLUMNS = [
    "study_id",
    "arm",
    "numerator",
    "denominator",
    "source_page",
    "source_type",
    "extractor_initials",
    "second_reviewer_initials",
    "timestamp",
    "notes",
]

SOURCE_TYPES = "text | table | figure | KM-reconstruction"

TEMPLATE = """# Extraction Consensus Log

**Purpose**: DI-1 compliance — comparative / arm-specific extraction results recorded as formal rows (not inline R-script comments).

**Created**: {today}

## Column definitions

| Column | Meaning |
|---|---|
| `study_id` | First-author year or internal SR ID |
| `arm` | Treatment / comparator / subgroup label |
| `numerator` | Events (for proportions) or mean (for continuous) |
| `denominator` | Sample size or SD (for continuous) |
| `source_page` | Source paper page + table/figure ID |
| `source_type` | One of: {source_types} |
| `extractor_initials` | Primary extractor |
| `second_reviewer_initials` | Independent second reviewer |
| `timestamp` | ISO-8601 (YYYY-MM-DD) of consensus |
| `notes` | Methodology flag, denominator correction rationale, KM reconstruction link |

## Rows

| {header} |
|{sep}|
| | | | | | | | | | |

## Audit checklist (DI-1..DI-5)

- [ ] Every 2x2 / comparative extraction has an independent second-reviewer row (DI-2)
- [ ] KM-reconstructed rows link to `3_Extraction/km_reconstruction/{{study_id}}/` (DI-3)
- [ ] Denominator corrections cite source page + rationale + this log row (DI-4)
- [ ] Methodology flag (per-protocol / ITT / ITD) matches SR framework (DI-5)
"""


def main() -> int:
    ap = argparse.ArgumentParser(description="Initialize extraction consensus log")
    ap.add_argument(
        "--output",
        default="2_Data/extraction_consensus_log.md",
        help="Output path (default: 2_Data/extraction_consensus_log.md)",
    )
    ap.add_argument("--project-root", default=".", help="Project root (default: cwd)")
    ap.add_argument("--force", action="store_true", help="Overwrite if exists")
    args = ap.parse_args()

    out = (Path(args.project_root) / args.output).resolve()
    if out.exists() and not args.force:
        print(f"ERROR: {out} exists. Pass --force to overwrite.", file=sys.stderr)
        return 3

    out.parent.mkdir(parents=True, exist_ok=True)
    header = " | ".join(f"`{c}`" for c in COLUMNS)
    sep = "|".join(["---"] * len(COLUMNS))
    content = TEMPLATE.format(
        today=_dt.date.today().isoformat(),
        source_types=SOURCE_TYPES,
        header=header,
        sep=sep,
    )
    out.write_text(content)
    print(f"Created: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
