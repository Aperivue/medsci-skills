#!/usr/bin/env python3
"""Rounded-component vs stated-difference arithmetic gate (self-review Phase 2.5a).

When a manuscript displays two metric values at a given precision and also states
their difference, the stated difference must equal the subtraction of the DISPLAYED
components at that same precision. A paper that reports "AUC 0.70 vs 0.73" (a shown
gap of 0.03) while stating the between-arm difference as "0.02" is self-consistent
only at full unrounded precision — at the displayed two decimals it reads as a
contradiction, and a reviewer flags it. (The usual cause: the delta is computed on
unrounded values, e.g. 0.726 − 0.703 = 0.023 → 0.02, while the components are shown
rounded to 0.70 / 0.73.)

Verdict:
  ROUNDED_DELTA_MISMATCH (Minor)  a stated difference does not equal the subtraction
                                  of its two displayed component values AT THE SAME
                                  precision. Fix: either report both components and
                                  the delta at a consistent precision, or add a
                                  footnote that the delta is computed on unrounded
                                  values.

Conservative by construction: fires only when (a) two component values joined by a
comparator (vs / versus / and / to / , ) appear in the same sentence as (b) an
explicitly LABELLED difference (Δ / difference / delta), and (c) all three are at the
SAME decimal precision. A higher-precision component pair (0.703 vs 0.726) with a
2-dp delta is the legitimate unrounded-delta case and is NOT flagged.

Exit codes: 0 clean/report-only, 1 with --strict when any Major (none here — Minor
only, so --strict never fails on this gate alone), 2 usage. Stdlib-only.

Usage:
    python3 check_rounded_delta.py --manuscript manuscript.md \
        [--out qc/rounded_delta.json] [--strict] [--quiet]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from decimal import Decimal
from pathlib import Path

# Two component values joined by a comparator (the "0.70 vs 0.73" construction).
COMP_PAIR = re.compile(
    r"(?P<a>\d?\.\d+|\d+\.\d+)\s*(?:vs\.?|versus|and|to|,|–|—|-)\s*(?P<b>\d?\.\d+|\d+\.\d+)",
    re.I)
# An explicitly labelled difference value.
DELTA = re.compile(
    r"(?:Δ\s*(?:AUC|AUROC|C[-\s]?index|accuracy)?|"
    r"(?:absolute\s+|between[-\s]\w+\s+|net\s+)?difference|delta|"
    r"differ(?:ed|s)?\s+by)"
    r"\s*(?:of|was|were|is|=|:|,|by)?\s*(?:only\s+|about\s+|approximately\s+)?"
    r"\(?(?P<d>\d?\.\d+|\d+\.\d+)",
    re.I)


def _prec(tok: str) -> int:
    return len(tok.split(".", 1)[1]) if "." in tok else 0


# How far back from a labelled difference to look for its two component values.
# Wide enough to bridge a "0.70 and 0.73; the difference was 0.02" clause boundary,
# narrow enough not to grab an unrelated pair from a previous sentence.
_LOOKBACK = 170


def check(text: str) -> list[dict]:
    claims: list[dict] = []
    seen: set[str] = set()
    for dm in DELTA.finditer(text):
        d_tok = dm.group("d")
        p = _prec(d_tok)
        if p == 0:
            continue
        window = text[max(0, dm.start() - _LOOKBACK):dm.start()]
        # bind the component pair to the delta's OWN sentence: drop anything up to the
        # last sentence terminator so a pair from a previous clause is not matched.
        cut = max(window.rfind(". "), window.rfind(".\n"), window.rfind("\n\n"))
        if cut != -1:
            window = window[cut + 1:]
        for cm in COMP_PAIR.finditer(window):
            a_tok, b_tok = cm.group("a"), cm.group("b")
            # the delta value itself is not a component of the pair
            if d_tok in (a_tok, b_tok):
                continue
            # all three must share the displayed precision (else it is the
            # legitimate unrounded-delta case, not a display contradiction)
            if _prec(a_tok) != p or _prec(b_tok) != p:
                continue
            a, b, d = Decimal(a_tok), Decimal(b_tok), Decimal(d_tok)
            shown = abs(a - b)
            q = Decimal(1).scaleb(-p)  # 10**-p
            if shown.quantize(q) == d.quantize(q):
                continue
            key = f"{a_tok}|{b_tok}|{d_tok}"
            if key in seen:
                continue
            seen.add(key)
            claims.append({
                "verdict": "ROUNDED_DELTA_MISMATCH",
                "severity": "Minor",
                "detail": (f"displayed components {a_tok} and {b_tok} differ by "
                           f"{shown.quantize(q)} at the shown precision, but the stated "
                           f"difference is {d_tok}; report components and delta at one "
                           f"precision or footnote that the delta is on unrounded values"),
                "where": text[max(0, dm.start() - _LOOKBACK):dm.end() + 4].replace("\n", " ").strip()[:170],
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
        lines.append("| (none) | — | stated differences match displayed components |")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Rounded-component vs stated-difference arithmetic gate (Phase 2.5a).")
    ap.add_argument("--manuscript", required=True, help="manuscript markdown/text")
    ap.add_argument("--out", help="write JSON artifact to this path")
    ap.add_argument("--strict", action="store_true",
                    help="exit 1 if any Major (none — this gate is Minor-only)")
    ap.add_argument("--quiet", action="store_true", help="suppress stdout table")
    args = ap.parse_args()

    result = analyze(args.manuscript)

    if not args.quiet:
        print("=" * 44)
        print(" Rounded-component vs stated difference (§2.5a)")
        print("=" * 44)
        print(render(result))
        print()
        n = result["summary"]["n_flag"]
        print(f"{'REVIEW: ' + str(n) + ' rounded-delta mismatch(es).' if n else 'OK: stated differences match displayed components.'}")

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps({"detector": "check_rounded_delta", **result}, indent=2), encoding="utf-8")
        if not args.quiet:
            print(f"\nwrote {args.out}")

    return 1 if (args.strict and result["summary"]["n_major"]) else 0


if __name__ == "__main__":
    sys.exit(main())
