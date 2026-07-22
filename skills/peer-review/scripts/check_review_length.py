#!/usr/bin/env python3
"""Measure a review draft's Comments-to-the-Authors block, per comment.

The peer-review skill already specifies the budget: a three-tier word target, a
per-Major line budget, a 545-word peer-comment baseline, a ratio-over-2.0 trim
flag and a 1400-word hard cap. All of it was prose, and the instruction was
literally "measure with awk + wc". Prose does not bind. On one live review the
author section was measured nine times by hand (922 / 882 / 861 / 827 / 796 /
776 / 720 / 716 / 635) and overshot the chosen tier three times, because `wc -w`
on raw markdown counts `**Major`, list numbers and table pipes, so every
measurement needed a bespoke strip-and-count one-liner. None of them reported
where the words actually were. The sibling rule about request types shipped as
prose, failed the same way, and was given a script; the budgets beside it were
never generalised.

The aggregate count says "trim". The per-item table says *which comment* to
trim, which is the part that changes what you write.

Tier targets (skills/peer-review/SKILL.md, Phase 3):
    1  <=700 w   R1 revisions, minor-revision recommendations, reporting-only
    2  700-1000  default; typical first round with 1-2 design-level concerns
    3  1000-1400 fatal-flaw hierarchy, cross-domain, task-formulation critique
Hard cap 1400. Baseline 545 w = median of 21 real reviewer blocks across 13
decision letters; ratio > 2.0 flags a trim candidate.

The per-Major budget is stated in the skill as lines (5-8 for tiers 1-2, 8-12
for tier 3). Converted here at ~17 words/line to 140 and 220 words; override
with --major-budget if your line width differs.

Verdicts:
  AUTHOR_BLOCK_NOT_FOUND (major)  no Comments-to-the-Authors heading; refuses to
                                  measure the whole file and call that a pass
  HARD_CAP (major)                author section over 1400 words
  TIER_EXCEEDED (major)           over the declared --tier ceiling
  MAJOR_OVERLONG (minor)          one Major comment over the per-tier budget
  RATIO_HIGH (minor)              over 2.0x the 545-word peer baseline

Usage:
    check_review_length.py --review draft.md [--tier 2] [--out qc/len.json] [--strict]

Exit 0 unless --strict and a major fires. Stdlib only.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

AUTHOR_HEAD = re.compile(r"^#{1,6}\s*.*comments?\s+to\s+the\s+authors?\b", re.I)
ANY_HEAD = re.compile(r"^#{1,6}\s+")
BOLD_LABEL = re.compile(r"^\*\*(.+?)\*\*:?\s*$")
ITEM_START = re.compile(r"^\s*(\d{1,2})[).]\s+")

TIERS = {1: (0, 700), 2: (700, 1000), 3: (1000, 1400)}
HARD_CAP = 1400
BASELINE = 545          # median reviewer block, n=21
MAJOR_BUDGET = {1: 140, 2: 140, 3: 220}


def strip_markdown(line: str) -> str:
    """Drop markup that is structure, not prose. Table rows and fences go whole."""
    line = re.sub(r"^\s*[-*+]\s+", "", line)
    line = ITEM_START.sub("", line)
    line = re.sub(r"\*\*|__|`", "", line)
    line = re.sub(r"(?<!\w)\*(?!\s)(.+?)(?<!\s)\*(?!\w)", r"\1", line)
    line = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", line)
    return line


def count_words(lines: list[str]) -> int:
    n = 0
    fence = False
    for raw in lines:
        s = raw.strip()
        if s.startswith("```"):
            fence = not fence
            continue
        if fence or not s or ANY_HEAD.match(s) or s.startswith("|") or set(s) <= set("-=*_ "):
            continue
        for tok in strip_markdown(s).split():
            if any(c.isalnum() for c in tok):
                n += 1
    return n


def author_block(text: str) -> list[str] | None:
    """Lines of the Comments-to-the-Authors section, or None if absent."""
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if AUTHOR_HEAD.match(line):
            start = i + 1
            break
    if start is None:
        return None
    end = len(lines)
    for j in range(start, len(lines)):
        if ANY_HEAD.match(lines[j]):
            end = j
            break
    return lines[start:end]


def itemize(block: list[str]) -> list[dict]:
    """Split the block into labelled comments: each bold label opens a section,
    and a leading `N)` inside a section opens a comment within it."""
    items: list[dict] = []
    section = "general comments"
    cur = {"label": section, "lines": []}

    def flush() -> None:
        if cur["lines"] and count_words(cur["lines"]):
            items.append({"label": cur["label"], "words": count_words(cur["lines"])})

    for line in block:
        m = BOLD_LABEL.match(line.strip())
        if m:
            flush()
            section = re.sub(r"\s+", " ", m.group(1)).strip().lower()
            cur = {"label": section, "lines": []}
            continue
        n = ITEM_START.match(line)
        if n and cur["lines"]:
            flush()
            cur = {"label": f"{section} {n.group(1)}", "lines": [line]}
            continue
        if n:
            cur["label"] = f"{section} {n.group(1)}"
        cur["lines"].append(line)
    flush()
    return items


def audit(path: Path, tier: int | None, major_budget: int | None) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace")
    block = author_block(text)
    findings: list[dict] = []

    if block is None:
        return {
            "detector": "check_review_length",
            "review": str(path),
            "words": None,
            "items": [],
            "findings": [{
                "verdict": "AUTHOR_BLOCK_NOT_FOUND", "severity": "major",
                "detail": ("No 'Comments to the Authors' heading found, so there is nothing to "
                           "measure. Measuring the whole file instead would report a number that "
                           "includes the scorecard and the editor's block, and a gate that "
                           "measures the wrong thing is worse than no gate."),
            }],
            "summary": {"major": 1, "minor": 0},
        }

    total = count_words(block)
    items = itemize(block)
    effective_tier = tier or next((t for t, (lo, hi) in TIERS.items() if lo < total <= hi), 3)
    budget = major_budget or MAJOR_BUDGET[effective_tier]
    ratio = round(total / BASELINE, 2)

    if total > HARD_CAP:
        findings.append({
            "verdict": "HARD_CAP", "severity": "major",
            "detail": f"{total} words exceeds the {HARD_CAP}-word hard cap.",
        })
    elif tier and total > TIERS[tier][1]:
        findings.append({
            "verdict": "TIER_EXCEEDED", "severity": "major",
            "detail": (f"{total} words against a declared tier {tier} ceiling of "
                       f"{TIERS[tier][1]}. Either cut, or declare the higher tier and justify it."),
        })

    over = [i for i in items
            if re.match(r"^major", i["label"]) and i["label"] != "major comments"
            and i["words"] > budget]
    if over:
        findings.append({
            "verdict": "MAJOR_OVERLONG", "severity": "minor",
            "evidence": [f"{i['label']}: {i['words']} w" for i in over],
            "detail": (f"Over the ~{budget}-word per-Major budget for tier {effective_tier}. "
                       "A long Major is usually two comments, or one comment carrying its own "
                       "argument twice."),
        })

    if ratio > 2.0:
        findings.append({
            "verdict": "RATIO_HIGH", "severity": "minor",
            "detail": (f"{ratio}x the {BASELINE}-word peer baseline. Reviews above 2x read as "
                       "Reviewer 2 regardless of how good the findings are."),
        })

    return {
        "detector": "check_review_length",
        "review": str(path),
        "words": total,
        "tier_declared": tier,
        "tier_effective": effective_tier,
        "ratio_vs_baseline": ratio,
        "major_budget": budget,
        "items": items,
        "findings": findings,
        "summary": {"major": sum(1 for f in findings if f["severity"] == "major"),
                    "minor": sum(1 for f in findings if f["severity"] == "minor")},
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--review", required=True, type=Path)
    ap.add_argument("--tier", type=int, choices=(1, 2, 3),
                    help="declared tier; without it the tier is inferred and never 'exceeded'")
    ap.add_argument("--major-budget", type=int, help="words per Major comment (default 140/220)")
    ap.add_argument("--out", type=Path)
    ap.add_argument("--strict", action="store_true", help="exit 1 if a major verdict fires")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()

    if not a.review.is_file():
        raise SystemExit(f"not found: {a.review}")

    rep = audit(a.review, a.tier, a.major_budget)

    if a.out:
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_text(json.dumps(rep, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if not a.quiet:
        if rep["words"] is None:
            print(f"{a.review.name}: author block not found")
        else:
            declared = f"declared {rep['tier_declared']}" if rep["tier_declared"] else "inferred"
            print(f"{a.review.name}: {rep['words']} w | tier {rep['tier_effective']} ({declared}) "
                  f"| {rep['ratio_vs_baseline']}x baseline")
            for i in rep["items"]:
                print(f"    {i['words']:5d}  {i['label']}")
        for f in rep["findings"]:
            print(f"  [{f['severity'].upper()}] {f['verdict']}: {f['detail']}")
            for e in f.get("evidence", []):
                print(f"           - {e}")
        if not rep["findings"]:
            print("  OK - within tier, per-Major budget and baseline ratio")

    return 1 if (a.strict and rep["summary"]["major"]) else 0


if __name__ == "__main__":
    sys.exit(main())
