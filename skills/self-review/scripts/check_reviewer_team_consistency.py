#!/usr/bin/env python3
"""
check_reviewer_team_consistency.py — fabrication-grade self-review check.

Detects manuscripts that simultaneously claim dual independent reviewers
(in Methods + PROSPERO) and confess to single-reviewer execution (in
Discussion §Limitations). Either claim alone is fine; the conjunction is
a fabrication-grade red flag.

Why this check exists
=====================
Cross-project precedent (anonymized): a reporting-quality SR-of-AI-tools
manuscript had:
- Methods: "Two reviewers independently screened titles and abstracts ..."
- PROSPERO record: "Two independent reviewers will perform full-text
  screening and data extraction."
- Discussion §Limitations: "Single primary reviewer; a 20% sample by an
  additional reviewer is deferred to before submission."

The conjunction admits in Limitations what Methods denies in narrative
form. Reviewers and editors who notice this read it as fabrication-grade
(the manuscript misrepresents what was actually done) and reject.

Detection strategy
==================
Section-aware grep for two regex families:
- DUAL claim: "(independently|dual|two reviewers|both reviewers|two
  independent)" within Methods OR a PROSPERO record file.
- SINGLE confession: "(single primary reviewer|one additional reviewer|
  20% sample|sample of records|deferred to before submission|due to
  resource constraints|by the first reviewer alone)" within Limitations
  OR Discussion.

Both present → MAJOR self-review red flag.

Usage
=====

    python check_reviewer_team_consistency.py \\
        --manuscript manuscript.md \\
        --prospero prospero/record.md \\
        --out _audit_self/reviewer_team_consistency.md

Output
======
Markdown report at `--out` summarizing matches. Also a JSON sidecar at
`--out` + ".json".

Exit codes
==========
  0  no conflict
  1  MAJOR red flag detected (both DUAL and SINGLE patterns present)
  2  invocation error
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path


DUAL_PATTERNS = [
    (
        re.compile(r"\btwo\s+(?:independent\s+)?reviewers?\b", re.IGNORECASE),
        "two reviewers",
    ),
    (re.compile(r"\bdual\s+(?:independent\s+)?(?:reviewers?|extractors?)\b", re.IGNORECASE),
     "dual reviewers"),
    (re.compile(r"\bindependent(?:ly)?\s+screened\b", re.IGNORECASE), "independently screened"),
    (
        re.compile(r"\bboth\s+reviewers?\s+(?:independently|extracted|screened)\b", re.IGNORECASE),
        "both reviewers",
    ),
    (
        re.compile(r"\bindependent(?:ly)?\s+(?:extracted|coded|assessed)\b", re.IGNORECASE),
        "independent extraction",
    ),
    (
        re.compile(r"\bindependent\s+reviewers?\b", re.IGNORECASE),
        "independent reviewers",
    ),
]

SINGLE_PATTERNS = [
    (re.compile(r"\bsingle\s+primary\s+reviewer\b", re.IGNORECASE), "single primary reviewer"),
    (
        re.compile(r"\bone\s+additional\s+reviewer\b", re.IGNORECASE),
        "one additional reviewer",
    ),
    (
        re.compile(r"\b20\s*%?\s+sample\b", re.IGNORECASE),
        "20% sample",
    ),
    (
        re.compile(r"\bsample\s+of\s+records\b", re.IGNORECASE),
        "sample of records",
    ),
    (
        re.compile(r"\bdeferred\s+to\s+before\s+submission\b", re.IGNORECASE),
        "deferred to before submission",
    ),
    (
        re.compile(r"\bdue\s+to\s+resource\s+constraints\b", re.IGNORECASE),
        "due to resource constraints",
    ),
    (
        re.compile(r"\b(?:by|with)\s+(?:the\s+)?first\s+reviewer\s+(?:alone|only)\b", re.IGNORECASE),
        "first reviewer alone",
    ),
]


SECTION_HEADERS = {
    "Methods": re.compile(
        r"^#{1,3}\s*\*{0,2}(?:METHODS?|Method[s]?|Materials and Methods)\*{0,2}\s*$",
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
}


@dataclass
class Hit:
    pattern_label: str
    line: int
    context: str


@dataclass
class Report:
    submission_safe: bool
    dual_hits: list[dict] = field(default_factory=list)
    single_hits: list[dict] = field(default_factory=list)


def split_sections(text: str) -> dict[str, str]:
    out: dict[str, str] = {name: "" for name in SECTION_HEADERS}
    headers: list[tuple[str, int, int]] = []
    for name, pat in SECTION_HEADERS.items():
        for m in pat.finditer(text):
            headers.append((name, m.start(), m.end()))
    headers.sort(key=lambda t: t[1])
    for i, (name, _, hdr_end) in enumerate(headers):
        end = headers[i + 1][1] if i + 1 < len(headers) else len(text)
        out[name] = (out[name] + "\n" + text[hdr_end:end]).strip()
    return out


def scan_text(text: str, patterns: list[tuple[re.Pattern[str], str]]) -> list[Hit]:
    hits: list[Hit] = []
    lines = text.splitlines()
    for lineno, line in enumerate(lines, start=1):
        for pat, label in patterns:
            if pat.search(line):
                ctx = line.strip()
                if len(ctx) > 200:
                    ctx = ctx[:200] + "..."
                hits.append(Hit(pattern_label=label, line=lineno, context=ctx))
    return hits


def hit_to_dict(h: Hit, source: str) -> dict:
    return {
        "source": source,
        "pattern": h.pattern_label,
        "line": h.line,
        "context": h.context,
    }


def build_report(manuscript: str, prospero: str | None) -> Report:
    sections = split_sections(manuscript)

    dual_hits: list[dict] = []
    single_hits: list[dict] = []

    # Methods → DUAL evidence.
    for h in scan_text(sections.get("Methods", ""), DUAL_PATTERNS):
        dual_hits.append(hit_to_dict(h, "manuscript:Methods"))

    # PROSPERO → DUAL evidence.
    if prospero is not None:
        for h in scan_text(prospero, DUAL_PATTERNS):
            dual_hits.append(hit_to_dict(h, "prospero"))

    # Discussion & Limitations → SINGLE evidence.
    for region in ("Limitations", "Discussion"):
        for h in scan_text(sections.get(region, ""), SINGLE_PATTERNS):
            single_hits.append(hit_to_dict(h, f"manuscript:{region}"))

    submission_safe = not (dual_hits and single_hits)
    return Report(
        submission_safe=submission_safe,
        dual_hits=dual_hits,
        single_hits=single_hits,
    )


def render_markdown(report: Report) -> str:
    lines = ["# Reviewer-team consistency audit", ""]
    if report.submission_safe:
        lines.append(
            "Status: **PASS** — no conjunction of DUAL claim + SINGLE confession."
        )
        lines.append("")
        if report.dual_hits:
            lines.append(f"DUAL claims found ({len(report.dual_hits)}, OK alone):")
            for h in report.dual_hits:
                lines.append(f"- `{h['source']}` line {h['line']}: `{h['pattern']}` — {h['context']}")
        if report.single_hits:
            lines.append("")
            lines.append(f"SINGLE confessions found ({len(report.single_hits)}, OK alone):")
            for h in report.single_hits:
                lines.append(f"- `{h['source']}` line {h['line']}: `{h['pattern']}` — {h['context']}")
    else:
        lines.append("Status: **MAJOR red flag** — DUAL claim and SINGLE confession both present.")
        lines.append("")
        lines.append("Reviewers will read this as fabrication-grade. Fix one of:")
        lines.append("1. Methods / PROSPERO honestly states single-reviewer execution.")
        lines.append("2. The Limitations admission is rewritten if dual review was actually done.")
        lines.append("")
        lines.append("## DUAL claims (Methods / PROSPERO)")
        for h in report.dual_hits:
            lines.append(f"- `{h['source']}` line {h['line']}: `{h['pattern']}`")
            lines.append(f"  > {h['context']}")
        lines.append("")
        lines.append("## SINGLE confessions (Discussion / Limitations)")
        for h in report.single_hits:
            lines.append(f"- `{h['source']}` line {h['line']}: `{h['pattern']}`")
            lines.append(f"  > {h['context']}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Reviewer-team consistency check (fabrication-grade self-review)."
    )
    parser.add_argument("--manuscript", type=Path, required=True)
    parser.add_argument("--prospero", type=Path, default=None)
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("_audit_self/reviewer_team_consistency.md"),
    )
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)

    if not args.manuscript.is_file():
        print(f"ERROR: manuscript not found: {args.manuscript}", file=sys.stderr)
        return 2
    prospero_text: str | None = None
    if args.prospero is not None:
        if not args.prospero.is_file():
            print(f"ERROR: prospero not found: {args.prospero}", file=sys.stderr)
            return 2
        prospero_text = args.prospero.read_text(encoding="utf-8")

    text = args.manuscript.read_text(encoding="utf-8")
    report = build_report(text, prospero_text)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(render_markdown(report), encoding="utf-8")
    json_out = args.out.with_suffix(args.out.suffix + ".json")
    json_out.write_text(
        json.dumps(
            {
                "submission_safe": report.submission_safe,
                "dual_hits": report.dual_hits,
                "single_hits": report.single_hits,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    if not args.quiet:
        if report.submission_safe:
            print(
                f"PASS: no conjunction. DUAL={len(report.dual_hits)} "
                f"SINGLE={len(report.single_hits)}"
            )
        else:
            print(
                f"FAIL: MAJOR red flag. DUAL={len(report.dual_hits)} "
                f"SINGLE={len(report.single_hits)}"
            )
            print(f"See {args.out}")

    return 0 if report.submission_safe else 1


if __name__ == "__main__":
    sys.exit(main())
