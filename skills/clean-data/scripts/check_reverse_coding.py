#!/usr/bin/env python3
"""Reverse-coded-item detector for multi-item scale reliability (clean-data Stage 2).

A multi-item scale (Likert Trust/Satisfaction/Burden, etc.) mixes positively- and
negatively-worded items. A negatively-worded ("reverse") item must be recoded
`(min+max) - x` before the scale total or Cronbach's alpha is computed. When that
recoding is skipped, the reverse item correlates negatively with the rest of the
scale and Cronbach's alpha collapses — often turning *negative*. A negative alpha
is almost never a real measurement phenomenon: it is a reverse-coding bug. Authors
who instead defend it as "multidimensional structure" lose a review round (the
motivating incident: a Trust scale shipped at alpha = -0.57 until one item was
recoded, after which alpha = 0.58).

This script flags reverse-code suspects *before* alpha is reported, so they are
recoded at cleaning time rather than mis-explained at revision time.

INPUTS
  --data        CSV with one row per respondent.
  --items       scale item columns (repeatable / space-separated). >= 2 required.
  --min         lowest point of the response scale (default 1).
  --max         highest point of the response scale (default: inferred per item
                from the observed maximum across all items).
  --threshold   item-rest correlation at or below which an item is a reverse-code
                suspect (default 0.0 — i.e. a negative item-rest correlation).

OUTPUT  (per scale)
  - alpha_raw            Cronbach's alpha on the items AS-GIVEN (un-recoded)
  - per item: item_rest_r (corrected item-total correlation)
  - suspects             items with item_rest_r <= threshold
  - verdict:
      REVERSE_CODING_LIKELY   alpha_raw < 0           (recode then re-run)
      REVERSE_CODING_SUSPECT  suspects present, alpha_raw >= 0
      OK                      no suspects, alpha_raw >= 0
  Exit 1 (with --strict) if verdict != OK.

Stdlib-only (csv / json / argparse / math / statistics). Exit codes: 0 clean
(or report-only), 1 reverse-coding flagged (with --strict), 2 input/usage error.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path

NULLISH = {"", "na", "n/a", "nan", "null", "none", ".", "missing"}


def _to_float(raw: str):
    if raw is None:
        return None
    s = raw.strip()
    if s.lower() in NULLISH:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _pearson(xs: list[float], ys: list[float]):
    """Pearson r over paired complete observations. None if undefined."""
    n = len(xs)
    if n < 2:
        return None
    mx = sum(xs) / n
    my = sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx <= 0 or syy <= 0:        # a constant column has no correlation
        return None
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    return sxy / math.sqrt(sxx * syy)


def _variance(vals: list[float]):
    n = len(vals)
    if n < 2:
        return 0.0
    m = sum(vals) / n
    return sum((v - m) ** 2 for v in vals) / (n - 1)


def cronbach_alpha(rows: list[list[float]]):
    """rows = list of complete item vectors (one per respondent). None if undefined."""
    if not rows:
        return None
    k = len(rows[0])
    if k < 2:
        return None
    item_vars = [_variance([r[j] for r in rows]) for j in range(k)]
    totals = [sum(r) for r in rows]
    total_var = _variance(totals)
    if total_var <= 0:
        return None
    return (k / (k - 1.0)) * (1.0 - sum(item_vars) / total_var)


def analyze(data_path: Path, items: list[str], scale_min: float,
            scale_max, threshold: float) -> dict:
    with data_path.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        header = reader.fieldnames or []
        missing = [c for c in items if c not in header]
        if missing:
            raise SystemExit(f"USAGE-ERR: item columns not in CSV: {missing}")
        raw_rows = list(reader)

    # Listwise-complete matrix (drop any respondent missing >=1 item) — matches
    # the default complete-case alpha so the flag mirrors the reported alpha.
    complete: list[list[float]] = []
    n_total = len(raw_rows)
    for row in raw_rows:
        vec = [_to_float(row.get(c)) for c in items]
        if all(v is not None for v in vec):
            complete.append(vec)  # type: ignore[arg-type]

    n_used = len(complete)
    alpha_raw = cronbach_alpha(complete) if n_used >= 2 else None

    # Per-item corrected item-total (item-rest) correlation.
    per_item = []
    suspects = []
    k = len(items)
    for j, name in enumerate(items):
        item_rest_r = None
        if n_used >= 2 and k >= 2:
            xs = [r[j] for r in complete]
            rest = [sum(r[t] for t in range(k) if t != j) for r in complete]
            item_rest_r = _pearson(xs, rest)
        flagged = item_rest_r is not None and item_rest_r <= threshold
        if flagged:
            suspects.append(name)
        per_item.append({
            "item": name,
            "item_rest_r": None if item_rest_r is None else round(item_rest_r, 3),
            "reverse_suspect": bool(flagged),
        })

    if alpha_raw is not None and alpha_raw < 0:
        verdict = "REVERSE_CODING_LIKELY"
    elif suspects:
        verdict = "REVERSE_CODING_SUSPECT"
    else:
        verdict = "OK"

    return {
        "items": items,
        "n_total": n_total,
        "n_complete": n_used,
        "scale_min": scale_min,
        "scale_max": scale_max,  # echoed only; flag is correlation-based
        "threshold": threshold,
        "alpha_raw": None if alpha_raw is None else round(alpha_raw, 3),
        "per_item": per_item,
        "suspects": suspects,
        "verdict": verdict,
        "recode_hint": (
            None if verdict == "OK"
            else "Recode suspect items as (min+max)-x, then recompute alpha "
                 "(see ~/.claude/rules/survey-scale-reliability.md)."
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Reverse-coded-item / negative-alpha detector.")
    ap.add_argument("--data", required=True)
    ap.add_argument("--items", nargs="+", required=True)
    ap.add_argument("--min", type=float, default=1.0, dest="scale_min")
    ap.add_argument("--max", type=float, default=None, dest="scale_max")
    ap.add_argument("--threshold", type=float, default=0.0)
    ap.add_argument("--out", default=None, help="write JSON report to this path")
    ap.add_argument("--strict", action="store_true",
                    help="exit 1 if any reverse-coding is flagged")
    args = ap.parse_args()

    if len(args.items) < 2:
        print("USAGE-ERR: need >= 2 scale items", file=sys.stderr)
        return 2

    data_path = Path(args.data)
    if not data_path.is_file():
        print(f"USAGE-ERR: data file not found: {data_path}", file=sys.stderr)
        return 2

    report = analyze(data_path, args.items, args.scale_min, args.scale_max, args.threshold)

    if args.out:
        Path(args.out).write_text(json.dumps(report, indent=2), encoding="utf-8")

    a = report["alpha_raw"]
    print(f"Scale items: {', '.join(report['items'])}  (n={report['n_complete']} complete)")
    print(f"Cronbach's alpha (as-given): {a}")
    for it in report["per_item"]:
        mark = "  <-- reverse-code suspect" if it["reverse_suspect"] else ""
        print(f"  item-rest r  {it['item']:<16} {it['item_rest_r']}{mark}")
    print(f"VERDICT: {report['verdict']}")
    if report["recode_hint"]:
        print(f"  {report['recode_hint']}")

    if args.strict and report["verdict"] != "OK":
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
