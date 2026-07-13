#!/usr/bin/env python3
"""Inline-emphasis over-use gate — a typographic AI tell (self-review §J / humanize P25).

LLM-drafted prose over-uses inline italic emphasis: single-word italics
(*into*, *passive*, *same*), whole-clause italics (*a redesign of the relationship
itself*), and mid-paragraph signposting. A human copy-editor strips almost all of it.
This gate counts NON-allowlisted italic emphasis spans per 1,000 body words and flags
an over-dense manuscript.

Verdict:
  EMPHASIS_OVERUSE (Minor)  italic-emphasis density exceeds the threshold after an
                            allowlist of legitimate italics (statistical symbols,
                            Latin phrases, journal/species terms) is removed.
                            Escalation note added when a span is a whole clause
                            (a long italic phrase, the strongest tell).

Scope, by construction, to keep false positives low on a widely-used skill:
  * Only ITALIC (`*...*`) spans count. Bold (`**...**`) is NOT counted — a bold
    run-in lead-in ("**Study design.**") is a legitimate Nature/npj subheading style
    (manuscript-style-classical §1.2), so counting it would fight another rule.
  * Fenced code blocks and allowlisted italics are excluded.
  * Fires only when both the density AND the raw count clear a floor, so a short
    note with one stray italic never trips it.

Exit codes: 0 clean/report-only, 1 with --strict when any Major (none — Minor only),
2 usage. Stdlib-only.

Usage:
    python3 check_emphasis_density.py --manuscript manuscript.md \
        [--out qc/emphasis_density.json] [--per-1000 5.0] [--strict] [--quiet]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# An italic span: single * ... * that is not part of a ** ... ** bold span.
ITALIC_RE = re.compile(r"(?<!\*)\*(?!\*)([^*\n]{1,120}?)\*(?!\*)")
FENCE_RE = re.compile(r"```.*?```", re.S)
WORD_RE = re.compile(r"[A-Za-z0-9']+")

# Legitimate italics that must NOT count toward the tell.
LATIN = {
    "in vivo", "in vitro", "ex vivo", "in situ", "in silico", "de novo", "post hoc",
    "a priori", "a posteriori", "et al", "et al.", "vs", "vs.", "versus", "i.e.",
    "e.g.", "per se", "et cetera", "ad hoc", "in utero", "in toto", "c-index",
}
# Single statistical symbols routinely italicised (P, t, r, n, F, z, d, k, R, b).
STAT_SYMBOL = re.compile(r"^[A-Za-z](?:[\s=<>²]|$)|^[A-Za-z]\s*[<>=]")
# A stat clause: an italic that is just a symbol + operator + number (e.g. "P = .03").
STAT_CLAUSE = re.compile(r"^[A-Za-z]\s*[=<>]\s*[.\d]")


def _is_allowlisted(span: str) -> bool:
    s = span.strip()
    low = s.strip(".,;:").lower()
    if low in LATIN:
        return True
    if len(s) <= 2:                       # single letter / symbol (P, t, n, β)
        return True
    if STAT_SYMBOL.match(s) or STAT_CLAUSE.match(s):
        return True
    # a species / gene-like token: single capitalised italic word with no space
    if " " not in s and re.fullmatch(r"[A-Za-z][A-Za-z0-9\-]+", s) and s[:1].isupper():
        # allow only if it looks like a proper noun/gene, not a plain emphasised word
        return bool(re.search(r"[A-Z].*[a-z].*[A-Z]|[0-9]", s))  # e.g. BRCA1, TP53
    return False


def check(text: str, per_1000: float) -> list[dict]:
    body = FENCE_RE.sub(" ", text)
    n_words = len(WORD_RE.findall(body))
    if n_words == 0:
        return []
    spans = [m.group(1) for m in ITALIC_RE.finditer(body)]
    flagged = [s for s in spans if not _is_allowlisted(s)]
    n = len(flagged)
    density = n * 1000.0 / n_words
    if n < 5 or density <= per_1000:
        return []
    whole_clause = [s for s in flagged if len(WORD_RE.findall(s)) >= 6]
    detail = (f"{n} non-allowlisted italic emphasis spans in {n_words} body words "
              f"({density:.1f}/1000 > {per_1000:.1f} threshold) — an LLM typographic "
              f"tell; a human editor removes almost all inline emphasis")
    if whole_clause:
        detail += (f". {len(whole_clause)} are whole-clause italics (e.g. "
                   f"\"*{whole_clause[0][:48]}*\") — the strongest tell; rewrite without italics")
    return [{
        "verdict": "EMPHASIS_OVERUSE",
        "severity": "Minor",
        "detail": detail,
        "where": ", ".join(f"*{s[:24]}*" for s in flagged[:6]),
    }]


def analyze(manuscript: str, per_1000: float) -> dict:
    p = Path(manuscript)
    if not p.is_file():
        sys.stderr.write(f"ERROR: manuscript not found: {manuscript}\n")
        sys.exit(2)
    claims = check(p.read_text(encoding="utf-8"), per_1000)
    return {
        "manuscript": str(p),
        "claims": claims,
        "summary": {"n_claims": len(claims), "n_major": 0, "n_flag": len(claims),
                    "verdict": "REVIEW" if claims else "OK"},
    }


def render(result: dict) -> str:
    lines = ["| Check | Severity | Detail |", "|---|---|---|"]
    for c in result["claims"]:
        lines.append(f"| {c['verdict']} | {c['severity']} | {c['detail']} |")
    if len(lines) == 2:
        lines.append("| (none) | — | inline-emphasis density within human range |")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Inline-emphasis over-use gate — a typographic AI tell (§J / humanize P25).")
    ap.add_argument("--manuscript", required=True, help="manuscript markdown/text")
    ap.add_argument("--out", help="write JSON artifact to this path")
    ap.add_argument("--per-1000", type=float, default=5.0,
                    help="italic-emphasis spans per 1000 words that trips the flag (default 5)")
    ap.add_argument("--strict", action="store_true",
                    help="exit 1 if any Major (none — this gate is Minor-only)")
    ap.add_argument("--quiet", action="store_true", help="suppress stdout table")
    args = ap.parse_args()

    result = analyze(args.manuscript, args.per_1000)

    if not args.quiet:
        print("=" * 42)
        print(" Inline-emphasis over-use (§J / P25)")
        print("=" * 42)
        print(render(result))
        print()
        n = result["summary"]["n_flag"]
        print("REVIEW: emphasis over-use." if n else "OK: inline-emphasis density within human range.")

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps({"detector": "check_emphasis_density", **result}, indent=2), encoding="utf-8")
        if not args.quiet:
            print(f"\nwrote {args.out}")

    return 1 if (args.strict and result["summary"]["n_major"]) else 0


if __name__ == "__main__":
    sys.exit(main())
