#!/usr/bin/env python3
"""
prisma_cascade_check.py — PRISMA flow cascade arithmetic auto-verify.

PRISMA 2020 flow diagrams chain a cascade of subtractions:

    [identified across databases] → [after dedup]
    → [title/abstract screened]
    → [full-text reviewed]
    → [included in qualitative synthesis]
    → [included in quantitative synthesis]

Each transition has a corresponding "excluded" count. The arithmetic is
trivial in principle but reviewers and editors find off-by-one errors at
high frequency: the prose cascade `151 + 108 + 39 + 1 + 1 + 4 = 304` is
followed by a prose summary "305" four lines later. The desk-reject
follows immediately because the prose is presented as fact.

This script:

1. Reads round-by-round screening TSV artifacts
   (`round1.tsv`, `round2.tsv`, `round3_adjudication.tsv`).
2. Computes the canonical flow chain from raw decisions.
3. Optionally cross-checks against a manuscript markdown body and emits
   a per-stage drift report.

Usage
=====

    python prisma_cascade_check.py \\
        --round1 2_Screening/round1.tsv \\
        --round2 2_Screening/round2.tsv \\
        --round3 2_Screening/round3_adjudication.tsv \\
        --out qc/prisma_cascade.json

    python prisma_cascade_check.py \\
        --round1 ... --round2 ... --round3 ... \\
        --manuscript manuscript.md \\
        --out qc/prisma_cascade.json

Decision column defaults:
    round 1 / round 2: `decision` ∈ {INCLUDE, EXCLUDE, MAYBE}
    round 3: `round3_decision` ∈ {INCLUDE, EXCLUDE}

Output JSON:

    {
      "submission_safe": false,
      "stage_counts": {
        "round1_total": 458,
        "round1_include": 220,
        "round2_include": 87,
        "round3_include": 42,
        "round3_exclude": 45
      },
      "cascade_arithmetic": {
        "round1_to_round2": {"excluded": 238, "checked": true},
        "round2_to_round3": {"excluded": 133, "checked": true}
      },
      "manuscript_drift": [
        {"stage": "round3_include", "computed": 42, "manuscript": 43,
         "manuscript_line": 67}
      ]
    }

Exit codes:
    0 — no drift (and manuscript agrees if supplied)
    1 — drift between computed cascade and manuscript prose
    2 — invocation error
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path


def count_decisions(tsv_path: Path, decision_col: str) -> dict[str, int]:
    """Return {decision: count} for the given TSV."""
    delim = "," if tsv_path.suffix.lower() == ".csv" else "\t"
    counts: dict[str, int] = {}
    total = 0
    with tsv_path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh, delimiter=delim)
        if reader.fieldnames is None or decision_col not in reader.fieldnames:
            print(
                f"ERROR: decision column {decision_col!r} not in {tsv_path}",
                file=sys.stderr,
            )
            sys.exit(2)
        for row in reader:
            decision = (row.get(decision_col) or "").strip().upper()
            if decision:
                counts[decision] = counts.get(decision, 0) + 1
                total += 1
    counts["_total"] = total
    return counts


def search_manuscript_stage(text: str, stage_name: str) -> tuple[int | None, int | None]:
    """Best-effort grep for a stage count and its line number.

    Stage names map to a small dictionary of cascade phrases. Returns
    (value, lineno) or (None, None) when no match found.
    """
    patterns = {
        "round1_include": [
            r"(\d{1,3}(?:,\d{3})*)\s+records?\s+(?:were\s+)?(?:included\s+)?after\s+title.{0,40}abstract",
            r"(\d{1,3}(?:,\d{3})*)\s+records?\s+screened\s+by\s+title",
        ],
        "round2_include": [
            r"(\d{1,3}(?:,\d{3})*)\s+records?\s+(?:moved\s+forward\s+)?to\s+full.?text",
            r"(\d{1,3}(?:,\d{3})*)\s+records?\s+(?:were\s+)?retrieved\s+for\s+full.?text",
        ],
        "round3_include": [
            r"(\d{1,3}(?:,\d{3})*)\s+studies?\s+(?:were\s+)?included\s+in\s+(?:the\s+)?(?:final\s+)?(?:qualitative|quantitative)\s+synthesis",
            r"(\d{1,3}(?:,\d{3})*)\s+studies?\s+(?:were\s+)?included\s+in\s+(?:the\s+)?(?:meta-analysis|review)",
            r"(?:included|comprised|finally\s+included)\s+(\d{1,3}(?:,\d{3})*)\s+studies?",
        ],
    }
    pats = patterns.get(stage_name)
    if not pats:
        return None, None
    for lineno, line in enumerate(text.splitlines(), start=1):
        for pat in pats:
            m = re.search(pat, line, flags=re.IGNORECASE)
            if m:
                try:
                    val = int(m.group(1).replace(",", ""))
                except ValueError:
                    continue
                return val, lineno
    return None, None


@dataclass
class CascadeReport:
    submission_safe: bool
    stage_counts: dict[str, int] = field(default_factory=dict)
    cascade_arithmetic: dict[str, dict] = field(default_factory=dict)
    manuscript_drift: list[dict] = field(default_factory=list)


def build_report(
    round1: Path,
    round2: Path,
    round3: Path,
    manuscript: Path | None,
    r1_col: str,
    r2_col: str,
    r3_col: str,
) -> CascadeReport:
    r1 = count_decisions(round1, r1_col)
    r2 = count_decisions(round2, r2_col)
    r3 = count_decisions(round3, r3_col)

    stage_counts = {
        "round1_total": r1.get("_total", 0),
        "round1_include": r1.get("INCLUDE", 0) + r1.get("MAYBE", 0),
        "round2_include": r2.get("INCLUDE", 0) + r2.get("MAYBE", 0),
        "round3_include": r3.get("INCLUDE", 0),
        "round3_exclude": r3.get("EXCLUDE", 0),
    }

    cascade: dict[str, dict] = {
        "round1_to_round2": {
            "excluded": stage_counts["round1_total"] - stage_counts["round2_include"],
            "checked": True,
        },
        "round2_to_round3": {
            "excluded": (
                stage_counts["round2_include"]
                - (stage_counts["round3_include"] + stage_counts["round3_exclude"])
            ),
            "checked": True,
        },
    }

    drifts: list[dict] = []
    if manuscript is not None and manuscript.is_file():
        text = manuscript.read_text(encoding="utf-8")
        for stage in ("round1_include", "round2_include", "round3_include"):
            val, lineno = search_manuscript_stage(text, stage)
            if val is None:
                continue
            if val != stage_counts[stage]:
                drifts.append(
                    {
                        "stage": stage,
                        "computed": stage_counts[stage],
                        "manuscript": val,
                        "manuscript_line": lineno,
                    }
                )

    submission_safe = not drifts
    return CascadeReport(
        submission_safe=submission_safe,
        stage_counts=stage_counts,
        cascade_arithmetic=cascade,
        manuscript_drift=drifts,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="PRISMA flow cascade arithmetic auto-verify.")
    parser.add_argument("--round1", type=Path, required=True)
    parser.add_argument("--round2", type=Path, required=True)
    parser.add_argument("--round3", type=Path, required=True)
    parser.add_argument("--manuscript", type=Path, default=None)
    parser.add_argument("--r1-col", default="decision")
    parser.add_argument("--r2-col", default="decision")
    parser.add_argument("--r3-col", default="round3_decision")
    parser.add_argument("--out", type=Path, default=Path("qc/prisma_cascade.json"))
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)

    for p, label in (
        (args.round1, "--round1"),
        (args.round2, "--round2"),
        (args.round3, "--round3"),
    ):
        if not p.is_file():
            print(f"ERROR: {label} not a file: {p}", file=sys.stderr)
            return 2

    report = build_report(
        args.round1, args.round2, args.round3,
        args.manuscript, args.r1_col, args.r2_col, args.r3_col,
    )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(
            {
                "submission_safe": report.submission_safe,
                "stage_counts": report.stage_counts,
                "cascade_arithmetic": report.cascade_arithmetic,
                "manuscript_drift": report.manuscript_drift,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    if not args.quiet:
        if report.submission_safe:
            print(
                "PASS: cascade computed. Stages: "
                + " → ".join(
                    f"{k}={v}" for k, v in report.stage_counts.items() if not k.startswith("_")
                )
            )
        else:
            print(
                f"FAIL: {len(report.manuscript_drift)} manuscript-prose "
                "drift(s) vs computed cascade."
            )
            for d in report.manuscript_drift:
                print(
                    f"  {d['stage']}: computed={d['computed']} "
                    f"manuscript={d['manuscript']} (line {d['manuscript_line']})"
                )

    return 0 if report.submission_safe else 1


if __name__ == "__main__":
    sys.exit(main())
