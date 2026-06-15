#!/usr/bin/env python3
"""Parenthesis-span corruption gate (post em-dash-reduction safety scan).

Reducing em-dashes to satisfy a classical-style gate (`" — X — "` appositive →
`(X)`) is a common edit. When a bulk regex pairs two *unrelated* single em-dashes
across a sentence boundary, it wraps a whole sentence inside one parenthesis:

    "... E-value 2.79 — Sixth, the lean-MASLD subgroup was small — and ..."
  → "... E-value 2.79 (Sixth, the lean-MASLD subgroup was small) and ..."

The result is grammatically broken but **paren-balanced**, so a balance check
misses it; only a human re-read (or this scan) catches it. This gate flags any
outer `(...)` span whose content (after stripping nested parens) contains:

  PAREN_SPAN_ORDINAL  (Major) an ordinal limitation marker ("First," … "Tenth,") —
                      the exact corruption above; an ordinal sentence-opener does
                      not belong inside a parenthesis.
  PAREN_SPAN_SENTENCE (Major) a sentence boundary ("word. Capital") inside a LONG
                      span (> --min-sentence-span chars, default 120) — a wrapped
                      sentence. The length guard avoids false positives on short
                      legitimate parentheticals ("(Dr. Smith)", "(Fig. 2; cf. A)").

Run it after `--fix` / `/humanize` em-dash work (and standalone on any draft).

INPUT
  --manuscript  manuscript markdown/text (required).

OUTPUT
  stdout table and, with --out, a JSON artifact {manuscript, claims[], summary}.
  Both verdicts are Major. Exit 1 (with --strict) when any Major claim exists.

Stdlib-only (re / json / argparse / pathlib). Exit codes: 0 clean (or report-only),
1 Major claim(s) found (with --strict), 2 input/usage error.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ORDINAL_RE = re.compile(
    r"\b(First|Second|Third|Fourth|Fifth|Sixth|Seventh|Eighth|Ninth|Tenth)\s*,", re.IGNORECASE)
# A sentence boundary: a lowercase word, a period, whitespace, then a capitalized
# word. (Requiring lowercase-before-period skips most abbreviations like "Fig.".)
SENTENCE_BOUNDARY_RE = re.compile(r"[a-z]{2,}\.\s+[A-Z][a-z]")


def _strip_nested(s: str) -> str:
    """Remove inner (...) groups so only the outer span's own text is tested."""
    prev = None
    while prev != s:
        prev = s
        s = re.sub(r"\([^()]*\)", " ", s)
    return s


def _outer_spans(text: str):
    """Yield (content, start) for every top-level balanced (...) span."""
    depth = 0
    start = -1
    for i, ch in enumerate(text):
        if ch == "(":
            if depth == 0:
                start = i
            depth += 1
        elif ch == ")" and depth > 0:
            depth -= 1
            if depth == 0 and start >= 0:
                yield text[start + 1:i], start


def check(text: str, min_sentence_span: int) -> list[dict]:
    claims = []
    for content, pos in _outer_spans(text):
        inner = _strip_nested(content)
        om = ORDINAL_RE.search(inner)
        if om:
            claims.append({
                "verdict": "PAREN_SPAN_ORDINAL",
                "severity": "Major",
                "detail": (f"a parenthesis wraps an ordinal sentence-opener "
                           f"('{om.group(0).strip()}') — likely an em-dash→paren "
                           f"conversion that paired unrelated dashes across a sentence"),
                "where": content.strip()[:160],
            })
            continue
        if len(inner) > min_sentence_span and SENTENCE_BOUNDARY_RE.search(inner):
            sm = SENTENCE_BOUNDARY_RE.search(inner)
            claims.append({
                "verdict": "PAREN_SPAN_SENTENCE",
                "severity": "Major",
                "detail": (f"a long parenthesis ({len(inner)} chars) contains a sentence "
                           f"boundary ('{sm.group(0).strip()}') — a whole sentence appears "
                           f"wrapped in parentheses"),
                "where": content.strip()[:160],
            })
    return claims


def analyze(manuscript: str, min_sentence_span: int) -> dict:
    p = Path(manuscript)
    if not p.is_file():
        sys.stderr.write(f"ERROR: manuscript not found: {manuscript}\n")
        sys.exit(2)
    claims = check(p.read_text(encoding="utf-8"), min_sentence_span)
    n_major = sum(1 for c in claims if c["severity"] == "Major")
    return {
        "manuscript": str(p),
        "claims": claims,
        "summary": {
            "n_claims": len(claims),
            "n_major": n_major,
            "verdict": "MAJOR_CANDIDATE" if n_major else "OK",
        },
    }


def render(result: dict) -> str:
    lines = ["| Check | Severity | Detail |", "|---|---|---|"]
    for c in result["claims"]:
        lines.append(f"| {c['verdict']} | {c['severity']} | {c['detail']} |")
    if len(lines) == 2:
        lines.append("| (none) | — | no parenthesis-span corruption detected |")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="Parenthesis-span corruption gate (post em-dash reduction).")
    ap.add_argument("--manuscript", required=True, help="manuscript markdown/text")
    ap.add_argument("--min-sentence-span", type=int, default=120,
                    help="min span length (chars) for the sentence-boundary check (default 120)")
    ap.add_argument("--out", help="write JSON artifact to this path")
    ap.add_argument("--strict", action="store_true", help="exit 1 if any Major claim exists")
    ap.add_argument("--quiet", action="store_true", help="suppress stdout table")
    args = ap.parse_args()

    result = analyze(args.manuscript, args.min_sentence_span)
    if not args.quiet:
        print("=" * 41)
        print(" Parenthesis-Span Corruption")
        print("=" * 41)
        print(render(result))
        print()
        s = result["summary"]
        print(f"MAJOR candidate: {s['n_major']} wrapped-sentence span(s)." if s["n_major"]
              else "OK: no parenthesis-span corruption detected.")

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(result, indent=2), encoding="utf-8")
        if not args.quiet:
            print(f"\nwrote {args.out}")

    return 1 if (args.strict and result["summary"]["n_major"]) else 0


if __name__ == "__main__":
    sys.exit(main())
