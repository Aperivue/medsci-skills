#!/usr/bin/env python3
"""Complete / quasi-complete separation: the logistic model that "runs" and is meaningless.

A predictor that perfectly (or almost perfectly) predicts the outcome breaks maximum
likelihood: the estimate diverges, and no finite MLE exists. The failure is silent. `glm`
does not error — it returns, with an odds ratio of 0.00 (or an enormous one), a p value of
0.99, and an AUC. That AUC gets written into a table.

This happens routinely in diagnostic imaging, because the good signs are the pathognomonic
ones. A sign with 100% specificity and 100% PPV — T2-FLAIR mismatch for IDH status, the
string sign, a halo sign — has an empty cell against the outcome by construction. Enter it
as a covariate in an incremental-value model and the model is numerically undefined while
looking entirely healthy.

So this runs on the DATA, before any model is fitted. It is a cross-tabulation, not an
inference: a zero cell is arithmetic, and arithmetic can be checked in advance.

Verdicts:
  COMPLETE_SEPARATION (major)  an empty predictor x outcome cell — the MLE does not exist
  QUASI_SEPARATION (major)     a cell below the sparsity floor — the estimate is unstable
                               and its CI is not trustworthy even when the model converges

Both name the two remedies, because the choice between them is a study-design decision and
not a numerical one:

  1. Firth's penalised likelihood (`logistf` in R, `Logit(...).fit_regularized` in
     statsmodels) — keeps one model, gives finite estimates.
  2. A two-stage rule: classify the sign-positive cases directly, and model only the
     sign-negative remainder. When the sign is pathognomonic this is usually also the
     clinically meaningful design, because a sign-positive patient is already diagnosed and
     the interesting question is what to do with everyone else.

Usage:
    check_separation.py --data cohort.csv --outcome idh_mutant \\
        [--predictor t2flair_mismatch --predictor sex] [--auto] \\
        [--sparse-floor 5] [--out qc/separation.json] [--strict]

With --auto, every column other than the outcome is screened (categorical columns up to
--max-levels, plus continuous columns for perfect separation). Stdlib only.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

MISSING = {"", "na", "n/a", "nan", "null", "none", "."}

REMEDY = (
    "Remedies (this is a design choice, not a numerical one): (1) Firth's penalised "
    "likelihood (`logistf` in R) keeps a single model and yields finite estimates; "
    "(2) a two-stage rule — classify the sign-positive cases directly and model only the "
    "sign-negative remainder. When the predictor is pathognomonic, (2) is usually also the "
    "clinically meaningful design: a sign-positive patient is already diagnosed."
)


def is_missing(v: str) -> bool:
    return v.strip().lower() in MISSING


def numeric(v: str) -> float | None:
    try:
        return float(v)
    except ValueError:
        return None


def load(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8-sig", errors="replace") as fh:
        r = csv.DictReader(fh)
        rows = [row for row in r]
        return (r.fieldnames or []), rows


def check_categorical(pred: str, pairs: list[tuple[str, str]], floor: int) -> list[dict]:
    """Cross-tabulate a categorical predictor against the outcome and read the cells."""
    table: dict[str, Counter] = defaultdict(Counter)
    outcomes = sorted({o for _, o in pairs})
    for p, o in pairs:
        table[p][o] += 1

    findings: list[dict] = []
    for level in sorted(table):
        for out in outcomes:
            n = table[level][out]
            if n == 0:
                findings.append(
                    {
                        "verdict": "COMPLETE_SEPARATION",
                        "severity": "major",
                        "predictor": pred,
                        "cell": {"level": level, "outcome": out, "n": 0},
                        "table": {lv: dict(c) for lv, c in table.items()},
                        "detail": (
                            f"`{pred}` = {level!r} has ZERO cases with outcome = {out!r}. The "
                            f"predictor separates the outcome perfectly at this level, so the "
                            f"logistic MLE does not exist: the model will still run and report an "
                            f"odds ratio near 0 (or enormous) with p ~ 1, and any AUC it produces "
                            f"is a numerical artifact. {REMEDY}"
                        ),
                    }
                )
            elif n < floor:
                findings.append(
                    {
                        "verdict": "QUASI_SEPARATION",
                        "severity": "major",
                        "predictor": pred,
                        "cell": {"level": level, "outcome": out, "n": n},
                        "table": {lv: dict(c) for lv, c in table.items()},
                        "detail": (
                            f"`{pred}` = {level!r} has only {n} case(s) with outcome = {out!r} "
                            f"(below the sparsity floor of {floor}). The estimate for this level is "
                            f"unstable and its confidence interval is not trustworthy even when the "
                            f"model converges. {REMEDY}"
                        ),
                    }
                )
    return findings


def check_continuous(pred: str, pairs: list[tuple[float, str]]) -> list[dict]:
    """A continuous predictor whose ranges do not overlap across the outcome separates it
    perfectly — the same failure, reached from the other direction."""
    by_out: dict[str, list[float]] = defaultdict(list)
    for v, o in pairs:
        by_out[o].append(v)
    if len(by_out) != 2:
        return []
    (a, va), (b, vb) = sorted(by_out.items())
    if max(va) < min(vb) or max(vb) < min(va):
        return [
            {
                "verdict": "COMPLETE_SEPARATION",
                "severity": "major",
                "predictor": pred,
                "cell": {
                    f"{a}_range": [min(va), max(va)],
                    f"{b}_range": [min(vb), max(vb)],
                },
                "detail": (
                    f"`{pred}` separates the outcome perfectly: its range for {a!r} "
                    f"([{min(va)}, {max(va)}]) does not overlap its range for {b!r} "
                    f"([{min(vb)}, {max(vb)}]). A threshold classifies every case, so the logistic "
                    f"MLE diverges. {REMEDY}"
                ),
            }
        ]
    return []


def audit(data: Path, outcome: str, predictors: list[str], auto: bool,
          floor: int, max_levels: int) -> dict:
    fields, rows = load(data)
    if outcome not in fields:
        raise SystemExit(f"outcome column {outcome!r} not in {data.name} (columns: {', '.join(fields)})")

    out_vals = {r[outcome].strip() for r in rows if not is_missing(r[outcome])}
    if len(out_vals) != 2:
        raise SystemExit(
            f"outcome {outcome!r} has {len(out_vals)} distinct values ({sorted(out_vals)}); "
            "separation is defined for a binary outcome."
        )

    if auto:
        predictors = [c for c in fields if c != outcome]
    missing_cols = [p for p in predictors if p not in fields]
    if missing_cols:
        raise SystemExit(f"predictor column(s) not in {data.name}: {', '.join(missing_cols)}")

    findings: list[dict] = []
    screened: list[str] = []
    skipped: list[dict] = []

    for pred in predictors:
        pairs = [
            (r[pred].strip(), r[outcome].strip())
            for r in rows
            if not is_missing(r[pred]) and not is_missing(r[outcome])
        ]
        if not pairs:
            skipped.append({"predictor": pred, "reason": "no complete cases"})
            continue

        levels = {p for p, _ in pairs}
        nums = [numeric(p) for p, _ in pairs]
        all_numeric = all(n is not None for n in nums)

        if len(levels) <= max_levels and not (all_numeric and len(levels) > max_levels):
            findings.extend(check_categorical(pred, pairs, floor))
            screened.append(pred)
        elif all_numeric:
            findings.extend(check_continuous(pred, [(n, o) for n, (_, o) in zip(nums, pairs)]))  # type: ignore[arg-type]
            screened.append(pred)
        else:
            skipped.append(
                {"predictor": pred, "reason": f"{len(levels)} levels, not numeric — an identifier?"}
            )

    return {
        "detector": "check_separation",
        "data": str(data),
        "outcome": outcome,
        "outcome_levels": sorted(out_vals),
        "screened": screened,
        "skipped": skipped,
        "sparse_floor": floor,
        "findings": findings,
        "summary": {
            "COMPLETE_SEPARATION": sum(1 for f in findings if f["verdict"] == "COMPLETE_SEPARATION"),
            "QUASI_SEPARATION": sum(1 for f in findings if f["verdict"] == "QUASI_SEPARATION"),
        },
        "model_safe": not findings,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", required=True, type=Path, help="CSV, one row per analysis unit")
    ap.add_argument("--outcome", required=True, help="binary outcome column")
    ap.add_argument("--predictor", action="append", default=[], dest="predictors",
                    help="predictor entering the model (repeatable)")
    ap.add_argument("--auto", action="store_true", help="screen every column except the outcome")
    ap.add_argument("--sparse-floor", type=int, default=5,
                    help="a non-zero cell below this is quasi-separation (default 5)")
    ap.add_argument("--max-levels", type=int, default=10,
                    help="a column with more distinct values than this is treated as continuous")
    ap.add_argument("--out", type=Path, help="write the JSON audit record here")
    ap.add_argument("--strict", action="store_true", help="exit 1 if any separation is found")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()

    if not a.data.is_file():
        raise SystemExit(f"not found: {a.data}")
    if not a.predictors and not a.auto:
        raise SystemExit("give at least one --predictor, or --auto to screen every column")

    rep = audit(a.data, a.outcome, a.predictors, a.auto, a.sparse_floor, a.max_levels)

    if a.out:
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_text(json.dumps(rep, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if not a.quiet:
        print(f"{a.data.name}: outcome {a.outcome!r}, {len(rep['screened'])} predictor(s) screened")
        for s in rep["skipped"]:
            print(f"  skipped {s['predictor']}: {s['reason']}")
        for f in rep["findings"]:
            print(f"  [{f['severity'].upper()}] {f['verdict']} — {f['detail']}")
        if not rep["findings"]:
            print("  OK — no empty or sparse predictor x outcome cell; the MLE is well defined")

    return 1 if (a.strict and rep["findings"]) else 0


if __name__ == "__main__":
    sys.exit(main())
