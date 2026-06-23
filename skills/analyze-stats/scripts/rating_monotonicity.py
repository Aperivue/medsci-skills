#!/usr/bin/env python3
"""Confidence-weighted rating → AUC monotonicity probe (reusable template).

NOT an auto-discovered detector — it needs the score *encoding* as input, so it is
a template/helper you point at your own score definition, not a manuscript scanner.

When an observer / reader study collapses a (binary-call × confidence) rating into a
single score used as the ROC/AUC predictor, that score MUST be strictly monotonic in
"evidence for the positive label" across the full ladder:

    negative-call, highest confidence   = strongest evidence AGAINST positive = LOWEST
    …
    negative-call, lowest confidence
    positive-call, lowest confidence
    …
    positive-call, highest confidence    = strongest evidence FOR positive = HIGHEST

A *folded* score — the classic bug `cws = confidence if positive_call else (K+1) − confidence`
— makes negative/high-confidence collide with positive/low-confidence and is NOT
monotonic; it understates discrimination and can flip a gradient to equivalence. Prose
review cannot see this; re-checking the encoding does.

Input JSON (`--encoding score_def.json`):
    {
      "confidence_levels": [1, 2, 3, 4, 5],
      "scores": {
        "positive": {"1": 6, "2": 7, "3": 8, "4": 9, "5": 10},
        "negative": {"1": 5, "2": 4, "3": 3, "4": 2, "5": 1}
      }
    }
`scores[call][confidence]` is the numeric value fed to the ROC/AUC routine for that cell.

Exit codes: 0 monotonic, 1 a collision/inversion (folded or mis-encoded), 2 usage.
Stdlib-only (json / argparse / sys). Run `--demo` for the 10-combination unit test.
"""

from __future__ import annotations

import argparse
import json
import sys


def evidence_order(levels: list) -> list[tuple[str, object]]:
    """Cells ordered from strongest-against-positive to strongest-for-positive."""
    asc = sorted(levels, key=lambda x: float(x))
    # negative call: highest confidence first (strongest against) → lowest
    neg = [("negative", c) for c in reversed(asc)]
    # positive call: lowest confidence first → highest (strongest for)
    pos = [("positive", c) for c in asc]
    return neg + pos


def check_encoding(spec: dict) -> dict:
    levels = spec["confidence_levels"]
    scores = spec["scores"]
    order = evidence_order(levels)
    seq = []
    for call, conf in order:
        # JSON object keys are strings; tolerate int/str confidence keys.
        cell = scores[call]
        val = cell.get(str(conf), cell.get(conf))
        if val is None:
            return {"ok": False, "problems": [f"missing score for {call}/conf {conf}"],
                    "sequence": seq}
        seq.append({"call": call, "confidence": conf, "score": val})
    problems = []
    for a, b in zip(seq, seq[1:]):
        if b["score"] == a["score"]:
            problems.append(
                f"collision: {a['call']}/{a['confidence']} and {b['call']}/{b['confidence']} "
                f"share score {a['score']} (a folded/mirrored encoding maps opposite evidence "
                f"to the same value)")
        elif b["score"] < a["score"]:
            problems.append(
                f"inversion: {a['call']}/{a['confidence']} (={a['score']}) ranks above "
                f"{b['call']}/{b['confidence']} (={b['score']}) but carries weaker evidence "
                f"for the positive label")
    return {"ok": not problems, "problems": problems,
            "sequence": [(s["call"], s["confidence"], s["score"]) for s in seq]}


def _demo() -> int:
    """The 10-combination (K=5) unit test: a correct directional encoding passes,
    the folded encoding fails on collisions."""
    levels = [1, 2, 3, 4, 5]
    correct = {"confidence_levels": levels,
               "scores": {"positive": {str(c): 5 + c for c in levels},
                          "negative": {str(c): 6 - c for c in levels}}}
    folded = {"confidence_levels": levels,
              "scores": {"positive": {str(c): c for c in levels},
                         "negative": {str(c): 6 - c for c in levels}}}
    rc = check_encoding(correct)
    rf = check_encoding(folded)
    ok = rc["ok"] and not rf["ok"]
    print(f"correct directional encoding: monotonic={rc['ok']} (expected True)")
    print(f"folded encoding:              monotonic={rf['ok']} (expected False)")
    if rf["problems"]:
        print(f"  folded problems[0]: {rf['problems'][0]}")
    print("DEMO PASS" if ok else "DEMO FAIL")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="Confidence-weighted rating→AUC monotonicity probe.")
    ap.add_argument("--encoding", help="JSON score-definition file (see module docstring)")
    ap.add_argument("--demo", action="store_true", help="run the 10-combination unit test")
    args = ap.parse_args()

    if args.demo:
        return _demo()
    if not args.encoding:
        sys.stderr.write("ERROR: --encoding FILE or --demo is required\n")
        return 2
    try:
        spec = json.loads(open(args.encoding, encoding="utf-8").read())
    except (OSError, ValueError) as e:
        sys.stderr.write(f"ERROR: cannot read encoding: {e}\n")
        return 2

    res = check_encoding(spec)
    if res["ok"]:
        print("OK: the (call × confidence) → score encoding is strictly monotonic.")
        return 0
    print("NON-MONOTONIC encoding (folded or mis-ordered) — this mis-estimates the AUC:")
    for p in res["problems"]:
        print(f"  - {p}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
