#!/usr/bin/env python3
"""Power-aware null-interpretation gate (self-review §C estimand contracts).

A headline negative claim ("no synergy", "no association", "not associated",
"showed no difference") is only interpretable next to a *precision* statement —
a minimum-detectable-effect, a power calculation, an equivalence margin / TOST,
or a confidence-interval-compatibility sentence. A primary NULL that asserts
"the null was not underpowered or fragile" while the interval (e.g. interaction
OR 1.04, 95% CI 0.75–1.44) does not exclude a modest effect, with no MDE/
equivalence reported, is a Major a prose pass misses but a panel/co-reviewer
catches.

Verdict:
  CONFIRM_NULL_NO_MDE (Major)  a negative/equivalence claim sits in the Title /
                               Abstract / Conclusion with no minimum-detectable-
                               effect, power, equivalence-margin/TOST, or CI-
                               compatibility token anywhere in those regions.

Conservative by construction: it fires only when a headline negative claim is
present AND no precision token appears anywhere in the title+abstract+conclusion
regions (a single MDE/power/equivalence/CI-compatibility sentence suppresses it).

Exit codes: 0 clean (or report-only), 1 with --strict when any Major exists, 2 usage.
Stdlib-only (json / re / argparse / pathlib).

Usage:
    python3 check_null_calibration.py --manuscript manuscript.md \
        [--out qc/null_calibration.json] [--strict] [--quiet]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# Headline negative / equivalence claims. Anchored to a NULL conclusion, not a
# mere mention of the word "no".
NEGATIVE_CLAIM = re.compile(
    r"\bno\s+(?:significant\s+)?(?:synerg|associat|interaction|difference|effect|relationship|correlation|impact)"
    r"|\bnot\s+(?:significantly\s+)?associat(?:ed)?"
    r"|\b(?:was|were|is|are)\s+not\s+associated"
    r"|\bshowed\s+no\b|\bfound\s+no\b|\bdid\s+not\s+(?:differ|increase|decrease|affect|predict|improve)"
    r"|\bno\s+evidence\s+(?:of|for|that)\b"
    r"|\bhad\s+no\s+(?:significant\s+)?(?:effect|association|impact)"
    r"|\bnull\b(?:\s+(?:finding|result|association|hypothesis))"
    r"|\b(?:were|was)\s+(?:statistically\s+)?equivalent\b|\bno\s+meaningful\b",
    re.IGNORECASE)

# Precision / MDE / equivalence / CI-compatibility tokens that make a null
# interpretable.
PRECISION_TOKEN = re.compile(
    r"minimum\s+detectable\s+effect|\bMDE\b|detectable\s+(?:effect|difference)"
    r"|power(?:ed)?\s+to\s+detect|statistical(?:ly)?\s+power|post[-\s]?hoc\s+power|a\s+priori\s+power"
    r"|equivalence\s+(?:margin|bound|test|range)|\bTOST\b|two\s+one[-\s]sided"
    r"|non[-\s]?inferiority\s+margin|smallest\s+effect\s+size\s+of\s+interest|\bSESOI\b"
    r"|(?:confidence\s+interval|CI)\s+(?:excludes?|is\s+compatible|includes?\s+values|rules?\s+out|cannot\s+exclude)"
    r"|compatible\s+with\s+(?:effects?|a\s+(?:clinically\s+)?(?:meaningful|modest|important))"
    r"|cannot\s+(?:exclude|rule\s+out)\s+a\b|may\s+be\s+underpowered|was\s+underpowered"
    r"|wide\s+confidence\s+interval|interval\s+(?:does\s+not\s+exclude|spans)|equivalence\s+was\s+(?:not\s+)?established",
    re.IGNORECASE)

REGION_HEADINGS = re.compile(
    r"^#{1,4}\s*\*{0,2}(?:ABSTRACT|Abstract|CONCLUSIONS?|Conclusions?|DISCUSSION|Discussion|"
    r"Interpretation|Clinical Implications?|Summary)\*{0,2}\s*$",
    re.IGNORECASE | re.MULTILINE)


def headline_region(text: str) -> str:
    """Title (first heading / first non-empty line) + Abstract + Conclusion/
    Discussion regions + any inline 'Conclusion:' clause. Fallback: whole text."""
    spans: list[str] = []
    # title = first markdown heading, else first non-empty line
    mt = re.search(r"^#{1,6}\s+(.+)$", text, re.MULTILINE)
    if mt:
        spans.append(mt.group(1))
    else:
        for line in text.splitlines():
            if line.strip():
                spans.append(line.strip())
                break
    all_headings = [m.start() for m in re.finditer(r"^#{1,4}\s", text, re.MULTILINE)]
    for m in REGION_HEADINGS.finditer(text):
        s = m.end()
        nxt = next((h for h in all_headings if h > s), len(text))
        spans.append(text[s:nxt])
    for m in re.finditer(r"(?:^|\n)\s*\*{0,2}(?:Conclusions?|Interpretation)\*{0,2}\s*[:.]\s*(.+?)(?:\n\n|$)",
                         text, re.IGNORECASE | re.DOTALL):
        spans.append(m.group(1))
    if not spans:
        spans.append(text)
    return "\n".join(spans)


def check(text: str) -> list[dict]:
    region = headline_region(text)
    nm = NEGATIVE_CLAIM.search(region)
    if not nm:
        return []
    if PRECISION_TOKEN.search(region):
        return []  # a precision/MDE/equivalence/CI-compatibility sentence is present
    return [{
        "verdict": "CONFIRM_NULL_NO_MDE",
        "severity": "Major",
        "detail": (f"a headline negative/equivalence claim ('{nm.group(0).strip()}') in the "
                   f"Title/Abstract/Conclusion is not accompanied by a minimum-detectable-"
                   f"effect, power, equivalence-margin/TOST, or CI-compatibility statement; a "
                   f"non-significant result is not evidence of no effect without one"),
        "where": region[max(0, nm.start() - 40):nm.end() + 60].replace("\n", " ").strip()[:160],
    }]


def analyze(manuscript: str) -> dict:
    p = Path(manuscript)
    if not p.is_file():
        sys.stderr.write(f"ERROR: manuscript not found: {manuscript}\n")
        sys.exit(2)
    claims = check(p.read_text(encoding="utf-8"))
    n_major = sum(1 for c in claims if c["severity"] == "Major")
    return {
        "manuscript": str(p),
        "claims": claims,
        "summary": {
            "n_claims": len(claims),
            "n_major": n_major,
            "n_flag": len(claims) - n_major,
            "verdict": "MAJOR_CANDIDATE" if n_major else "OK",
        },
    }


def render(result: dict) -> str:
    lines = ["| Check | Severity | Detail |", "|---|---|---|"]
    for c in result["claims"]:
        lines.append(f"| {c['verdict']} | {c['severity']} | {c['detail']} |")
    if len(lines) == 2:
        lines.append("| (none) | — | no headline null lacks a precision/MDE statement |")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="Power-aware null-interpretation gate (§C).")
    ap.add_argument("--manuscript", required=True, help="manuscript markdown/text")
    ap.add_argument("--out", help="write JSON artifact to this path")
    ap.add_argument("--strict", action="store_true", help="exit 1 if any Major claim exists")
    ap.add_argument("--quiet", action="store_true", help="suppress stdout table")
    args = ap.parse_args()

    result = analyze(args.manuscript)

    if not args.quiet:
        print("=" * 41)
        print(" Null Calibration (§C)")
        print("=" * 41)
        print(render(result))
        print()
        s = result["summary"]
        if s["n_major"]:
            print(f"MAJOR candidate: {s['n_major']} headline null without a precision/MDE statement.")
        else:
            print("OK: no headline null lacks a precision/MDE statement.")

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(result, indent=2), encoding="utf-8")
        if not args.quiet:
            print(f"\nwrote {args.out}")

    return 1 if (args.strict and result["summary"]["n_major"]) else 0


if __name__ == "__main__":
    sys.exit(main())
