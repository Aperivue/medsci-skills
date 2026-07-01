#!/usr/bin/env python3
"""Orphan figure / table gate — every numbered float must be cited in the body
(self-review Phase 2.5d cross-reference).

A figure or table that has a legend/caption but is never cited in the running text
is an "orphan": a reviewer or production editor flags it, and a journal may refuse
the float. This gate cross-checks each declared "Figure N." / "Table N." caption
against at least one in-text "Figure N" / "Table N" citation elsewhere in the body.

Verdict:
  FIGURE_ORPHAN (Minor)  a figure with a caption "Figure N." has no in-text
                         "Figure N" / "Fig. N" citation anywhere outside its caption.
  TABLE_ORPHAN  (Minor)  the same for a "Table N." caption.

Deterministic and caption-anchored: a line beginning "Figure N." / "Table N." (with
optional **bold**) DECLARES float N; any "Figure N" / "Table N" mention on a
DIFFERENT line CITES it. A float declared but never cited elsewhere is the orphan.
This needs no section-boundary heuristic — the caption line itself is the anchor, so
a caption that happens to reference another float still counts as citing that other
float.

Exit codes: 0 clean/report-only, 1 with --strict when any Major (none — Minor only),
2 usage. Stdlib-only.

Usage:
    python3 check_figure_citation.py --manuscript manuscript.md \
        [--out qc/figure_citation.json] [--strict] [--quiet]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# A caption/legend line: (optional **) Figure|Table N (.|:) ...
CAPTION_RE = re.compile(r"^\s*\*{0,2}\s*(?P<kind>Figure|Fig\.?|Table)\s+(?P<num>\d+)\s*[.:]", re.I)
# Any in-text mention: Figure N / Fig N / Fig. N / Table N (+ "Figures 1 and 2" heads)
MENTION_RE = re.compile(r"\b(?P<kind>Figures?|Figs?\.?|Tables?)\s+(?P<num>\d+)\b", re.I)


def _kind(raw: str) -> str:
    return "Table" if raw.lower().startswith("tab") else "Figure"


def check(text: str) -> list[dict]:
    lines = text.splitlines()
    declared: dict[tuple[str, int], int] = {}   # (kind, num) -> caption line index
    for i, line in enumerate(lines):
        m = CAPTION_RE.match(line)
        if m:
            declared.setdefault((_kind(m.group("kind")), int(m.group("num"))), i)

    cited: set[tuple[str, int]] = set()
    for i, line in enumerate(lines):
        for m in MENTION_RE.finditer(line):
            key = (_kind(m.group("kind")), int(m.group("num")))
            # a mention on any line other than this float's own caption line = a citation
            if declared.get(key) != i:
                cited.add(key)

    claims = []
    for (kind, num), cap_line in sorted(declared.items(), key=lambda kv: (kv[0][0], kv[0][1])):
        if (kind, num) in cited:
            continue
        claims.append({
            "verdict": "TABLE_ORPHAN" if kind == "Table" else "FIGURE_ORPHAN",
            "severity": "Minor",
            "detail": (f"{kind} {num} has a caption (line {cap_line + 1}) but is never cited "
                       f"in the body; add an in-text '{kind} {num}' citation or remove the float"),
            "where": lines[cap_line].strip()[:120],
        })
    return claims


def analyze(manuscript: str) -> dict:
    p = Path(manuscript)
    if not p.is_file():
        sys.stderr.write(f"ERROR: manuscript not found: {manuscript}\n")
        sys.exit(2)
    claims = check(p.read_text(encoding="utf-8"))
    return {
        "manuscript": str(p),
        "claims": claims,
        "summary": {
            "n_claims": len(claims),
            "n_major": 0,
            "n_flag": len(claims),
            "verdict": "REVIEW" if claims else "OK",
        },
    }


def render(result: dict) -> str:
    lines = ["| Check | Severity | Detail |", "|---|---|---|"]
    for c in result["claims"]:
        lines.append(f"| {c['verdict']} | {c['severity']} | {c['detail']} |")
    if len(lines) == 2:
        lines.append("| (none) | — | every captioned figure/table is cited in the body |")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Orphan figure/table gate — captioned floats must be cited (Phase 2.5d).")
    ap.add_argument("--manuscript", required=True, help="manuscript markdown/text")
    ap.add_argument("--out", help="write JSON artifact to this path")
    ap.add_argument("--strict", action="store_true",
                    help="exit 1 if any Major (none — this gate is Minor-only)")
    ap.add_argument("--quiet", action="store_true", help="suppress stdout table")
    args = ap.parse_args()

    result = analyze(args.manuscript)

    if not args.quiet:
        print("=" * 44)
        print(" Orphan figure / table citation (§2.5d)")
        print("=" * 44)
        print(render(result))
        print()
        n = result["summary"]["n_flag"]
        print(f"{'REVIEW: ' + str(n) + ' orphan float(s).' if n else 'OK: every captioned float is cited in the body.'}")

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(result, indent=2), encoding="utf-8")
        if not args.quiet:
            print(f"\nwrote {args.out}")

    return 1 if (args.strict and result["summary"]["n_major"]) else 0


if __name__ == "__main__":
    sys.exit(main())
