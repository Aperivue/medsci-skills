#!/usr/bin/env python3
"""
scope_drift_check.py — Phase 6 intra-manuscript scope drift detection.

Detects two related failure modes:

1. **Numeric anchor in Limitations only**: an AUC / OR / HR / RR /
   sensitivity / specificity value appears in the Limitations or Discussion
   section but is absent from Methods + Results. This is a strong indicator
   that a late-revision sensitivity analysis was introduced without
   propagating to the primary report, leaving the manuscript's stated scope
   inconsistent with its prose-level claims.

2. **PROSPERO ↔ Methods synthesis-method drift**: the PROSPERO record
   commits to a synthesis method (e.g., Freeman-Tukey transformation,
   random-effects DerSimonian-Laird, bivariate, HSROC, Bayesian) but the
   Methods section silently uses a different one — or vice versa. This
   is a documented "silent protocol deviation" pattern that reviewers
   flag as fabrication-grade if accompanied by a "no amendment lodged"
   PROSPERO note.

Why this gate exists
====================
Cross-project precedents (anonymized):
- Project (DTA-MA example, reporting-quality SR variant): a leave-pair-out
  sensitivity envelope appeared in Limitations with five AUC values and
  four CIs. The primary pool AUC `0.869` was not reported in Methods or
  Results.
- Project (intervention-MA example): PROSPERO committed to Freeman-Tukey
  pooled-proportion; Methods said descriptive-only Python with no R; the
  manuscript line "no amendment lodged" turned the silent change into a
  documented violation.

P0 active-fix pattern when caught.

Usage
=====

    python scope_drift_check.py \\
        --manuscript manuscript.md \\
        --prospero prospero/prospero_v2.md \\
        --out qc/scope_drift.json

    python scope_drift_check.py \\
        --manuscript manuscript.md \\
        --out qc/scope_drift.json

Output (qc/scope_drift.json):

    {
      "submission_safe": false,
      "limitations_only_anchors": [
        {"anchor": "0.869", "kind": "AUC",
         "found_in": ["Limitations:31"], "missing_from": ["Methods", "Results"]}
      ],
      "synthesis_method_drift": [
        {"method": "Freeman-Tukey", "prospero": true, "methods": false}
      ]
    }

Exit codes:
    0 — no drift
    1 — drift detected
    2 — invocation error

Read-only script. No file modification.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path


# Section detection — case-insensitive header match. We deliberately accept
# common variants seen in radiology / MA manuscripts: bolded all-caps
# (`## **METHODS**`), Title Case (`## Methods`), and Markdown subsections.
SECTION_HEADERS: dict[str, re.Pattern[str]] = {
    "Methods": re.compile(
        r"^#{1,3}\s*\*{0,2}(?:METHODS?|Method[s]?|Materials and Methods)\*{0,2}\s*$",
        re.IGNORECASE | re.MULTILINE,
    ),
    "Results": re.compile(
        r"^#{1,3}\s*\*{0,2}(?:RESULTS?|Result[s]?|Findings)\*{0,2}\s*$",
        re.IGNORECASE | re.MULTILINE,
    ),
    "Discussion": re.compile(
        r"^#{1,3}\s*\*{0,2}(?:DISCUSSION|Discussion)\*{0,2}\s*$",
        re.IGNORECASE | re.MULTILINE,
    ),
    "Limitations": re.compile(
        r"^#{1,3}\s*\*{0,2}(?:LIMITATIONS?|Limitations?|Study Limitations)\*{0,2}\s*$",
        re.IGNORECASE | re.MULTILINE,
    ),
    "Conclusion": re.compile(
        r"^#{1,3}\s*\*{0,2}(?:CONCLUSIONS?|Conclusion[s]?)\*{0,2}\s*$",
        re.IGNORECASE | re.MULTILINE,
    ),
}


# Numeric anchor patterns. We bias toward conservative matchers: false
# positives (e.g. "0.50%" from a table) are easier to triage than false
# negatives (a missed AUC). Each entry yields a canonical "anchor" string.
ANCHOR_PATTERNS = [
    # AUC: 0.600-0.999 (typical study range, excludes test-set 0.5 floor)
    ("AUC", re.compile(r"\b(0\.[6-9]\d{2})\b")),
    # OR / HR / RR / aOR / aHR with explicit label
    (
        "RiskRatio",
        re.compile(
            r"\b(?:aOR|aHR|OR|HR|RR)\s*[=:]\s*(\d+\.\d+)\b",
            re.IGNORECASE,
        ),
    ),
    # Sensitivity / specificity with explicit label
    (
        "SnSp",
        re.compile(
            r"\b(?:Sn|Sp|sens(?:itivity)?|spec(?:ificity)?)\s*[=:]\s*"
            r"(\d+(?:\.\d+)?%?)\b",
            re.IGNORECASE,
        ),
    ),
]


# Synthesis method keywords (case-insensitive substring search). When the
# PROSPERO record names a method that does NOT appear in Methods (or
# vice-versa), emit a drift.
SYNTHESIS_METHODS = [
    "Freeman-Tukey",
    "Mantel-Haenszel",
    "DerSimonian-Laird",
    "REML",
    "bivariate",
    "HSROC",
    "Bayesian",
    "random-effects",
    "fixed-effect",
    "fixed-effects",
    "Egger",
    "I²",
    "Wilson",
    "Clopper-Pearson",
]


@dataclass
class LimitsOnlyAnchor:
    anchor: str
    kind: str
    found_in: list[str]
    missing_from: list[str]


@dataclass
class SynthesisDrift:
    method: str
    prospero: bool
    methods: bool


@dataclass
class Report:
    submission_safe: bool
    limitations_only_anchors: list[LimitsOnlyAnchor] = field(default_factory=list)
    synthesis_method_drift: list[SynthesisDrift] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "submission_safe": self.submission_safe,
            "limitations_only_anchors": [asdict(a) for a in self.limitations_only_anchors],
            "synthesis_method_drift": [asdict(s) for s in self.synthesis_method_drift],
        }


def split_sections(text: str) -> dict[str, str]:
    """Return mapping of section name → body text. Sections without a header
    return empty string. Body extends from the matched header to the next
    matched header in the document."""
    # Compute (name, start, end_of_header_line) per match across the doc.
    hits: list[tuple[str, int, int]] = []
    for name, pat in SECTION_HEADERS.items():
        for m in pat.finditer(text):
            hits.append((name, m.start(), m.end()))
    hits.sort(key=lambda t: t[1])

    out: dict[str, str] = {name: "" for name in SECTION_HEADERS}
    for i, (name, start, hdr_end) in enumerate(hits):
        body_start = hdr_end
        body_end = hits[i + 1][1] if i + 1 < len(hits) else len(text)
        out[name] = (out[name] + "\n" + text[body_start:body_end]).strip()
    return out


def find_anchors(text: str) -> list[tuple[str, str]]:
    """Return (anchor_string, kind) tuples found in text."""
    out: list[tuple[str, str]] = []
    for kind, pat in ANCHOR_PATTERNS:
        for m in pat.finditer(text):
            anchor = m.group(1)
            out.append((anchor, kind))
    return out


def line_numbers(text: str, needle: str) -> list[int]:
    """Return 1-based line numbers in text containing the literal needle."""
    out: list[int] = []
    for i, line in enumerate(text.splitlines(), start=1):
        if needle in line:
            out.append(i)
    return out


def detect_limits_only(text: str) -> list[LimitsOnlyAnchor]:
    sections = split_sections(text)
    limits = sections.get("Limitations", "")
    discussion = sections.get("Discussion", "")
    methods = sections.get("Methods", "")
    results = sections.get("Results", "")

    # Anchors that appear in Limitations OR Discussion but NOT in Methods or
    # Results. We include Discussion because in many manuscripts the
    # Limitations subsection is folded into Discussion without an explicit
    # `## Limitations` header.
    out: list[LimitsOnlyAnchor] = []
    seen: set[tuple[str, str]] = set()
    for region_name, region_text in (("Limitations", limits), ("Discussion", discussion)):
        for anchor, kind in find_anchors(region_text):
            if (anchor, kind) in seen:
                continue
            in_methods = anchor in methods
            in_results = anchor in results
            if not in_methods and not in_results:
                lineno = line_numbers(text, anchor)
                found_label = f"{region_name}:{lineno[0]}" if lineno else region_name
                out.append(
                    LimitsOnlyAnchor(
                        anchor=anchor,
                        kind=kind,
                        found_in=[found_label],
                        missing_from=["Methods", "Results"],
                    )
                )
                seen.add((anchor, kind))
    return out


def detect_synthesis_drift(
    manuscript_text: str,
    prospero_text: str | None,
) -> list[SynthesisDrift]:
    if prospero_text is None:
        return []
    sections = split_sections(manuscript_text)
    methods_text = sections.get("Methods", "")
    out: list[SynthesisDrift] = []
    for method in SYNTHESIS_METHODS:
        # case-insensitive presence
        in_prospero = method.lower() in prospero_text.lower()
        in_methods = method.lower() in methods_text.lower()
        if in_prospero != in_methods:
            out.append(
                SynthesisDrift(
                    method=method,
                    prospero=in_prospero,
                    methods=in_methods,
                )
            )
    return out


def build_report(
    manuscript_path: Path,
    prospero_path: Path | None,
) -> Report:
    text = manuscript_path.read_text(encoding="utf-8")
    prospero_text: str | None = None
    if prospero_path is not None and prospero_path.is_file():
        prospero_text = prospero_path.read_text(encoding="utf-8")

    limits_only = detect_limits_only(text)
    synth_drift = detect_synthesis_drift(text, prospero_text)
    submission_safe = not limits_only and not synth_drift
    return Report(
        submission_safe=submission_safe,
        limitations_only_anchors=limits_only,
        synthesis_method_drift=synth_drift,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Phase 6 intra-manuscript scope drift detection. Flags numeric "
            "anchors that appear only in Limitations/Discussion (not Methods/"
            "Results) and PROSPERO↔Methods synthesis-method disagreement."
        )
    )
    parser.add_argument(
        "--manuscript",
        type=Path,
        required=True,
        help="Path to manuscript.md (markdown).",
    )
    parser.add_argument(
        "--prospero",
        type=Path,
        default=None,
        help=(
            "Path to PROSPERO record markdown. When supplied, also performs "
            "synthesis-method cross-check vs Methods."
        ),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Write JSON report to this path.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress stdout summary.",
    )
    args = parser.parse_args(argv)

    if not args.manuscript.is_file():
        parser.error(f"--manuscript not a file: {args.manuscript}")
    if args.prospero is not None and not args.prospero.is_file():
        parser.error(f"--prospero not a file: {args.prospero}")

    report = build_report(args.manuscript, args.prospero)

    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report.as_dict(), indent=2), encoding="utf-8")

    if not args.quiet:
        if report.submission_safe:
            print("PASS: no scope drift detected.")
        else:
            print(
                f"FAIL: {len(report.limitations_only_anchors)} limits-only anchor(s), "
                f"{len(report.synthesis_method_drift)} synthesis drift(s)."
            )
            for a in report.limitations_only_anchors:
                print(f"  - SCOPE_DRIFT {a.kind} {a.anchor!r} found in {a.found_in}, "
                      f"missing from {a.missing_from}")
            for s in report.synthesis_method_drift:
                print(f"  - PROSPERO_DRIFT {s.method} prospero={s.prospero} methods={s.methods}")

    return 0 if report.submission_safe else 1


if __name__ == "__main__":
    sys.exit(main())
