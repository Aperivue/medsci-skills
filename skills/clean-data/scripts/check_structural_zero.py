#!/usr/bin/env python3
"""Categorical-implied-zero (structural-zero) detector for clean-data Stage 2.

A dose/duration variable anchored to a categorical exposure has a known zero at
the reference level: a never-smoker's pack-years is 0 *by definition*, not
missing. When that implied zero is instead stored as NULL/blank, two downstream
failures follow — a complete-case model silently drops the whole unexposed
stratum, or MICE imputes a non-zero dose for people who have no exposure — both
of which corrupt the exposure contrast. This script finds those contradiction
rows so they are fixed at cleaning time (set 0 at the reference level; impute
only the residual missingness among the exposed).

INPUTS
  --data            CSV with one row per subject.
  --category-col    categorical exposure column (e.g. smoking_status).
  --reference-level value of the category that implies a zero dose (e.g. never).
  --dose-col        dose/duration column that should be 0 at the reference level
                    (e.g. pack_years). Repeatable for several dose columns.

OUTPUT
  Per (reference-level, dose) pair: counts of
    - implied_zero_missing : category == reference AND dose is NULL/blank   (FIX)
    - implied_zero_nonzero : category == reference AND dose > 0  (mislabeled — review)
    - implied_zero_ok      : category == reference AND dose == 0
  Exit 1 (with --strict) if any implied_zero_missing rows exist.

Stdlib-only (csv / json / argparse). Exit codes: 0 clean (or report-only),
1 contradiction rows found (with --strict), 2 input/usage error.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

NULLISH = {"", "na", "n/a", "nan", "null", "none", ".", "missing"}


def _is_null(v: str) -> bool:
    return v.strip().lower() in NULLISH


def _to_float(v: str):
    try:
        return float(v.strip())
    except (ValueError, AttributeError):
        return None


def _norm(s: str) -> str:
    return s.strip().lower()


def analyze(data: str, category_col: str, reference: str, dose_cols: list[str]) -> dict:
    p = Path(data)
    if not p.is_file():
        sys.stderr.write(f"ERROR: data file not found: {data}\n")
        sys.exit(2)
    with p.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            sys.stderr.write("ERROR: empty CSV\n")
            sys.exit(2)
        fields = {_norm(c): c for c in reader.fieldnames}
        cat_key = fields.get(_norm(category_col))
        if cat_key is None:
            sys.stderr.write(f"ERROR: category column '{category_col}' not in {reader.fieldnames}\n")
            sys.exit(2)
        dose_keys = {}
        for d in dose_cols:
            k = fields.get(_norm(d))
            if k is None:
                sys.stderr.write(f"ERROR: dose column '{d}' not in {reader.fieldnames}\n")
                sys.exit(2)
            dose_keys[d] = k
        rows = list(reader)

    ref = _norm(reference)
    results = []
    total_missing = 0
    for d, dkey in dose_keys.items():
        miss = nonzero = ok = ref_n = 0
        for r in rows:
            if _norm(r.get(cat_key, "")) != ref:
                continue
            ref_n += 1
            raw = r.get(dkey, "")
            if _is_null(raw):
                miss += 1
            else:
                val = _to_float(raw)
                if val is None:
                    continue            # non-numeric, not our concern here
                if val > 0:
                    nonzero += 1
                else:
                    ok += 1
        total_missing += miss
        results.append({
            "dose_col": d,
            "reference_level": reference,
            "reference_n": ref_n,
            "implied_zero_missing": miss,
            "implied_zero_nonzero": nonzero,
            "implied_zero_ok": ok,
            "verdict": "FIX_STRUCTURAL_ZERO" if miss else ("REVIEW_MISLABEL" if nonzero else "OK"),
        })

    return {
        "data": str(p),
        "category_col": category_col,
        "n_rows": len(rows),
        "results": results,
        "total_implied_zero_missing": total_missing,
        "suggested_fix": (
            f"Set dose = 0 where {category_col} == '{reference}' (structural zero), "
            "then impute only the residual missingness among the exposed."
        ) if total_missing else None,
    }


def render(result: dict) -> str:
    lines = [
        "| Dose col | ref n | implied-zero MISSING | nonzero (mislabel) | zero (ok) | Verdict |",
        "|---|---|---|---|---|---|",
    ]
    for r in result["results"]:
        mark = {"FIX_STRUCTURAL_ZERO": "✗ Fix", "REVIEW_MISLABEL": "△ Review", "OK": "✓"}[r["verdict"]]
        lines.append(
            f"| {r['dose_col']} | {r['reference_n']} | {r['implied_zero_missing']} | "
            f"{r['implied_zero_nonzero']} | {r['implied_zero_ok']} | {mark} |"
        )
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="Categorical-implied-zero (structural-zero) detector.")
    ap.add_argument("--data", required=True, help="subject-level CSV")
    ap.add_argument("--category-col", required=True, help="categorical exposure column")
    ap.add_argument("--reference-level", required=True, help="category value implying a zero dose")
    ap.add_argument("--dose-col", required=True, action="append",
                    help="dose/duration column (repeatable)")
    ap.add_argument("--out", help="write JSON artifact to this path")
    ap.add_argument("--strict", action="store_true", help="exit 1 if any implied-zero-missing rows")
    args = ap.parse_args()

    result = analyze(args.data, args.category_col, args.reference_level, args.dose_col)

    print("=" * 41)
    print(" Categorical-Implied-Zero (structural zero)")
    print("=" * 41)
    print(f"category: {args.category_col} == '{args.reference_level}'")
    print(render(result))
    print()
    if result["total_implied_zero_missing"]:
        print(f"FIX: {result['total_implied_zero_missing']} reference-level row(s) store the implied "
              f"zero as missing.")
        print(result["suggested_fix"])
    else:
        print("OK: no categorical-implied-zero stored as missing.")

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(f"\nwrote {args.out}")

    return 1 if (args.strict and result["total_implied_zero_missing"]) else 0


if __name__ == "__main__":
    sys.exit(main())
