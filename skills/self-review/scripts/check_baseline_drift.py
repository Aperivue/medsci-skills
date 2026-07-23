#!/usr/bin/env python3
"""Baseline-drift gate (self-review) -- anchor the refine loop to the human-approved version.

Self-review is run in a loop (review -> revise -> review). The danger is not any single
pass but the *anchor*: each pass takes the previous **AI output** as its baseline, so a
small framing bias introduced in one pass becomes the starting point for the next and
compounds -- claims strengthen, scope inflates, caveats accrete -- while every individual
pass looks locally reasonable. Nothing measures how far the manuscript has drifted from
the last version a human actually approved.

This gate compares the current manuscript against a **baseline** -- the last
human-approved / circulated version (the frozen v_N of manuscript-versioning), NOT the
last AI output -- and reports lexical framing drift. It is advisory: framing is a
judgment call the author owns, so every finding is Minor and the gate never blocks
(--strict is accepted for CLI parity but exits 0). Comparing to the AI's own previous
draft would defeat the purpose; the baseline must be a human anchor.

  STRENGTH_INFLATION            certainty/assertion markers rose while hedges fell vs the
                               baseline -- the same result stated more strongly than a
                               human signed off on.
  SIGNIFICANCE_INFLATION_DRIFT significance-inflation tokens (novel / pivotal /
                               unprecedented / paradigm-shifting ...) rose vs the baseline.
  SCOPE_INFLATION_DRIFT        generalization phrases the baseline did not contain ("in
                               clinical practice", "broadly applicable", "can be used to")
                               appeared -- the estimand's reach widened without new data.
  HEDGE_ACCRETION              hedge / caveat density rose vs the baseline -- the additive,
                               over-hardening side of drift (the cumulative form of what
                               the ceiling pass catches within one pass).

Conservative by construction: a probe fires only when a density delta exceeds an explicit
threshold, so ordinary revision does not trip it. With no --baseline (the crossfire path
passes only --manuscript) there is nothing to anchor against and the gate emits zero
findings.

INPUTS
  --manuscript  current manuscript markdown/text (required).
  --baseline    the last human-approved version (optional; without it the gate is a no-op).
  thresholds    --strength-delta (2.0), --sig-delta (2), --scope-delta (1),
                --hedge-delta (8.0). Densities are per 1,000 words; --sig/--scope are
                absolute counts (those tokens are rare). A probe fires when the delta
                exceeds its threshold.

OUTPUT
  A drift table (stdout) and, with --out, a JSON artifact:
    {detector, manuscript, baseline, claims[{verdict, severity, detail, where}], summary}
  Every claim is severity "Minor". Exit code is always 0 for the findings themselves
  (advisory); --strict is accepted for CLI parity but never blocks. Exit 2 on a missing
  manuscript.

Stdlib-only (json / re / argparse / pathlib). Exit codes: 0 clean or advisory findings,
2 input/usage error.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

DETECTOR = "check_baseline_drift"

# --------------------------------------------------------------------------- #
# Lexicons -- fixed, word-boundary matched. Kept small and unambiguous to hold the
# false-positive rate down on a widely-used skill.
# --------------------------------------------------------------------------- #
ASSERTION = [
    "demonstrates", "demonstrate", "proves", "prove", "proven", "establishes",
    "establish", "confirms", "confirm", "definitively", "conclusively",
    "unequivocally", "undoubtedly", "clearly shows", "guarantees", "ensures",
    "highly accurate", "highly effective",
]
HEDGE = [
    "may", "might", "could", "suggests", "suggest", "appears", "appear", "seems",
    "seem", "potentially", "possibly", "perhaps", "tends to", "is likely",
    "are likely", "we speculate", "cannot exclude",
]
SIGNIFICANCE = [
    "novel", "pivotal", "unprecedented", "paradigm", "paradigm-shifting",
    "groundbreaking", "revolutionary", "cutting-edge", "state-of-the-art",
    "remarkable", "landmark", "first-ever", "first to demonstrate",
]
SCOPE = [
    "in clinical practice", "in routine practice", "in the general population",
    "broadly applicable", "widely applicable", "can be used to", "should be used",
    "generalizable to", "translate directly", "ready for deployment",
    "ready for clinical use", "in real-world",
]


def _count(text: str, terms: list[str]) -> int:
    n = 0
    for t in terms:
        pat = r"(?<![A-Za-z0-9-])" + re.escape(t) + r"(?![A-Za-z0-9-])"
        n += len(re.findall(pat, text))
    return n


def _present(text: str, terms: list[str]) -> set[str]:
    found = set()
    for t in terms:
        pat = r"(?<![A-Za-z0-9-])" + re.escape(t) + r"(?![A-Za-z0-9-])"
        if re.search(pat, text):
            found.add(t)
    return found


def _words(text: str) -> int:
    return max(1, len(re.findall(r"[A-Za-z0-9']+", text)))


def _profile(text: str) -> dict:
    low = text.lower()
    w = _words(text)
    return {
        "words": w,
        "assertion": _count(low, ASSERTION),
        "hedge": _count(low, HEDGE),
        "sig": _count(low, SIGNIFICANCE),
        "scope_terms": _present(low, SCOPE),
        "sig_terms": _present(low, SIGNIFICANCE),
    }


def _per1k(n: int, words: int) -> float:
    return round(n * 1000.0 / words, 2)


def analyze(current: str, baseline: str | None, thr: dict) -> dict:
    claims: list[dict] = []
    if baseline is None:
        return {"claims": claims, "summary": {"n_claims": 0, "verdict": "OK"}}

    cur = _profile(current)
    base = _profile(baseline)

    # STRENGTH_INFLATION: assertions up AND hedges down (per 1k)
    d_assert = _per1k(cur["assertion"], cur["words"]) - _per1k(base["assertion"], base["words"])
    d_hedge = _per1k(cur["hedge"], cur["words"]) - _per1k(base["hedge"], base["words"])
    if d_assert >= thr["strength"] and d_hedge < 0:
        claims.append({
            "verdict": "STRENGTH_INFLATION",
            "severity": "Minor",
            "detail": (
                f"certainty markers {_per1k(base['assertion'], base['words'])}->"
                f"{_per1k(cur['assertion'], cur['words'])}/1k while hedges "
                f"{_per1k(base['hedge'], base['words'])}->{_per1k(cur['hedge'], cur['words'])}/1k "
                "vs baseline -- the result is stated more strongly than the approved version"
            ),
            "where": "whole document",
        })

    # SIGNIFICANCE_INFLATION_DRIFT: absolute significance-token count up
    d_sig = cur["sig"] - base["sig"]
    if d_sig >= thr["sig"]:
        added = sorted(cur["sig_terms"] - base["sig_terms"])
        detail = f"significance-inflation tokens {base['sig']}->{cur['sig']} vs baseline"
        if added:
            detail += " (added: " + ", ".join(added) + ")"
        claims.append({"verdict": "SIGNIFICANCE_INFLATION_DRIFT", "severity": "Minor", "detail": detail, "where": "whole document"})

    # SCOPE_INFLATION_DRIFT: new generalization phrases absent from baseline
    added_scope = sorted(cur["scope_terms"] - base["scope_terms"])
    if len(added_scope) >= thr["scope"]:
        claims.append({
            "verdict": "SCOPE_INFLATION_DRIFT",
            "severity": "Minor",
            "detail": "generalization phrase(s) not in baseline: " + ", ".join(f'"{p}"' for p in added_scope),
            "where": "whole document",
        })

    # HEDGE_ACCRETION: hedge density up (the additive/over-hardening drift)
    if d_hedge >= thr["hedge"]:
        claims.append({
            "verdict": "HEDGE_ACCRETION",
            "severity": "Minor",
            "detail": (
                f"hedge/caveat density {_per1k(base['hedge'], base['words'])}->"
                f"{_per1k(cur['hedge'], cur['words'])}/1k vs baseline -- cumulative over-hardening"
            ),
            "where": "whole document",
        })

    verdict = "DRIFT_FLAGS" if claims else "OK"
    return {"claims": claims, "summary": {"n_claims": len(claims), "verdict": verdict}}


def render(result: dict, manuscript: str, baseline: str | None) -> str:
    lines = ["Baseline-drift scan"]
    lines.append(f"  manuscript: {manuscript}")
    lines.append(f"  baseline:   {baseline if baseline else '(none -- no-op)'}")
    claims = result["claims"]
    if not claims:
        lines.append("  OK: no framing drift beyond threshold." if baseline else "  OK: no baseline supplied; nothing to anchor against.")
        return "\n".join(lines)
    lines.append(f"  DRIFT FOUND: {len(claims)} finding(s) (advisory / Minor)")
    for c in claims:
        lines.append(f"    [{c['verdict']}] {c['detail']}")
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Report lexical framing drift of a manuscript vs its last human-approved baseline.")
    ap.add_argument("--manuscript", required=True, help="current manuscript markdown/text")
    ap.add_argument("--baseline", help="last human-approved version (optional; no-op without it)")
    ap.add_argument("--out", help="optional JSON artifact path")
    ap.add_argument("--quiet", action="store_true", help="suppress the stdout summary")
    ap.add_argument("--strict", action="store_true", help="accepted for CLI parity; never blocks (advisory)")
    ap.add_argument("--strength-delta", type=float, default=2.0, help="min assertion-density rise per 1k (default 2.0)")
    ap.add_argument("--sig-delta", type=int, default=2, help="min significance-token count rise (default 2)")
    ap.add_argument("--scope-delta", type=int, default=1, help="min new scope phrases (default 1)")
    ap.add_argument("--hedge-delta", type=float, default=8.0, help="min hedge-density rise per 1k (default 8.0)")
    args = ap.parse_args(argv)

    mpath = Path(args.manuscript)
    if not mpath.is_file():
        print(f"error: manuscript not found: {args.manuscript}", file=sys.stderr)
        return 2
    current = mpath.read_text(encoding="utf-8", errors="replace")

    baseline_text = None
    if args.baseline:
        bpath = Path(args.baseline)
        if not bpath.is_file():
            print(f"error: baseline not found: {args.baseline}", file=sys.stderr)
            return 2
        baseline_text = bpath.read_text(encoding="utf-8", errors="replace")

    thr = {
        "strength": args.strength_delta,
        "sig": args.sig_delta,
        "scope": args.scope_delta,
        "hedge": args.hedge_delta,
    }
    result = analyze(current, baseline_text, thr)
    out = {
        "detector": DETECTOR,
        "manuscript": str(args.manuscript),
        "baseline": str(args.baseline) if args.baseline else None,
        **result,
    }
    if args.out:
        Path(args.out).write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    if not args.quiet:
        print(render(result, str(args.manuscript), str(args.baseline) if args.baseline else None))
    return 0


if __name__ == "__main__":
    sys.exit(main())
