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
  COMPLETE_SEPARATION (major)  an empty predictor x outcome cell, a continuous predictor
                               whose outcome ranges do not overlap, or a linear combination
                               of the predictors that classifies every case — the MLE does
                               not exist
  QUASI_SEPARATION (major)     a cell below the sparsity floor — the estimate is unstable
                               and its CI is not trustworthy even when the model converges;
                               or quasi-complete separation (outcome ranges that touch only
                               at a tied boundary value, or a linear combination of the
                               predictors that splits the outcome except for ties) — the
                               MLE does not exist

Each predictor is screened on its own first. A model with two or more predictors can be
separated JOINTLY while every predictor passes on its own (y = 1[x1 > x2]), so the screened
predictors are then checked together: the linear-programming test of Konis (2007), the one
behind R's `detectseparation` / `safeBinaryRegression`, on the complete cases with the
categorical predictors dummy-coded. The joint test needs scipy. Without it the report says
the joint check was not run, and the OK line does not claim that the MLE exists.

Both name the two remedies, because the choice between them is a study-design decision and
not a numerical one:

  1. Firth's penalised likelihood (`logistf` in R; statsmodels has no Firth fit —
     `Logit(...).fit_regularized` is an L1 (lasso) penalty, not Firth — so in Python use a
     dedicated Firth implementation or call `logistf`) — keeps one model, gives finite
     estimates.
  2. A two-stage rule: classify the sign-positive cases directly, and model only the
     sign-negative remainder. When the sign is pathognomonic this is usually also the
     clinically meaningful design, because a sign-positive patient is already diagnosed and
     the interesting question is what to do with everyone else.

Usage:
    check_separation.py --data cohort.csv --outcome idh_mutant \\
        [--predictor t2flair_mismatch --predictor sex] [--auto] \\
        [--sparse-floor 5] [--out qc/separation.json] [--strict]

With --auto, every column other than the outcome is screened (categorical columns up to
--max-levels, plus continuous columns for perfect separation). The per-predictor screen is
stdlib only; the joint check uses scipy when it is installed.
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
    (lo_out, lo), (hi_out, hi) = ((a, va), (b, vb)) if max(va) <= min(vb) else ((b, vb), (a, va))
    if max(lo) == min(hi):
        # The ranges touch only at a tied boundary value: a threshold there classifies every
        # case except the ties. That is quasi-complete separation — no finite MLE exists, and
        # glm "converges" to a huge slope with p ~ 1.
        return [
            {
                "verdict": "QUASI_SEPARATION",
                "severity": "major",
                "predictor": pred,
                "cell": {
                    f"{a}_range": [min(va), max(va)],
                    f"{b}_range": [min(vb), max(vb)],
                },
                "detail": (
                    f"`{pred}` separates the outcome quasi-completely: its range for {lo_out!r} "
                    f"([{min(lo)}, {max(lo)}]) and its range for {hi_out!r} "
                    f"([{min(hi)}, {max(hi)}]) overlap only at the tied boundary value "
                    f"{max(lo)}. A threshold there classifies every other case, so the logistic "
                    f"MLE does not exist: the model will still run and report a huge "
                    f"coefficient with p ~ 1. {REMEDY}"
                ),
            }
        ]
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


def check_joint(rows: list[dict[str, str]], outcome: str, out_levels: list[str],
                kinds: dict[str, str]) -> tuple[dict, dict | None]:
    """Joint (multivariable) separation: is there a linear combination of the screened
    predictors that splits the outcome, with at most ties on the boundary?

    The per-predictor screen cannot see this. y = 1[x1 > x2] passes it for x1 and for x2,
    yet glm(y ~ x1 + x2) has no finite MLE. This is the linear program of Konis (2007),
    the test behind R's `detectseparation` / `safeBinaryRegression`: with s_i = +/-1 for the
    outcome and z_i the design row (intercept, dummy-coded categorical predictors,
    standardised continuous ones), separation exists iff some direction d, |d_j| <= 1,
    has s_i * z_i.d >= 0 for every case and > 0 for at least one. A second program
    (maximise the smallest margin) tells complete from quasi-complete separation.

    Returns (joint_check record, finding or None)."""
    preds = list(kinds)
    cc = [r for r in rows
          if not is_missing(r[outcome]) and all(not is_missing(r[p]) for p in preds)]
    record: dict = {"status": "not_run", "predictors": preds, "n_complete": len(cc)}
    ys = {r[outcome].strip() for r in cc}
    if len(ys) != 2:
        record["reason"] = "the complete cases do not contain both outcome levels"
        return record, None
    try:
        import numpy as np
        from scipy.optimize import linprog
    except ImportError:
        record["reason"] = "scipy is not installed; joint separation was NOT checked"
        return record, None

    cols: list[list[float]] = [[1.0] * len(cc)]
    owner: list[str] = ["(intercept)"]
    for p in preds:
        vals = [r[p].strip() for r in cc]
        if kinds[p] == "categorical":
            for lv in sorted(set(vals))[1:]:
                cols.append([1.0 if v == lv else 0.0 for v in vals])
                owner.append(p)
        else:
            xs = [float(v) for v in vals]
            mu = sum(xs) / len(xs)
            sd = (sum((x - mu) ** 2 for x in xs) / len(xs)) ** 0.5
            if sd > 0:
                cols.append([(x - mu) / sd for x in xs])
                owner.append(p)
    s = np.array([1.0 if r[outcome].strip() == out_levels[1] else -1.0 for r in cc])
    A = np.array(cols).T * s[:, None]
    n, k = A.shape
    record["design_columns"] = k

    # Program 1: maximise sum_i s_i z_i.d subject to s_i z_i.d >= 0 and |d_j| <= 1.
    res = linprog(-A.sum(axis=0), A_ub=-A, b_ub=np.zeros(n), bounds=[(-1, 1)] * k,
                  method="highs")
    if res.status != 0:
        record["reason"] = f"linear program did not solve ({res.message})"
        return record, None
    d = res.x
    margins = A @ d
    tol = 1e-6
    if not (-res.fun > tol and margins.max() > tol and margins.min() > -tol):
        record["status"] = "clear"
        return record, None

    # Program 2: maximise t subject to s_i z_i.d >= t, |d_j| <= 1, 0 <= t <= 1.
    A2 = np.hstack([-A, np.ones((n, 1))])
    c2 = np.zeros(k + 1)
    c2[-1] = -1.0
    res2 = linprog(c2, A_ub=A2, b_ub=np.zeros(n), bounds=[(-1, 1)] * k + [(0, 1)],
                   method="highs")
    complete = res2.status == 0 and -res2.fun > tol

    involved = sorted({owner[j] for j in range(1, k) if abs(d[j]) > tol})
    n_tied = int((np.abs(margins) <= tol).sum())
    record["status"] = "separated"
    record["involved"] = involved
    verdict = "COMPLETE_SEPARATION" if complete else "QUASI_SEPARATION"
    how = ("classifies every case" if complete else
           f"classifies every case except {n_tied} tied on the boundary")
    finding = {
        "verdict": verdict,
        "severity": "major",
        "predictor": " + ".join(involved),
        "cell": {"joint": involved, "n_complete": n, "n_tied": 0 if complete else n_tied},
        "detail": (
            f"The predictors {', '.join(f'`{p}`' for p in involved)} separate the outcome "
            f"JOINTLY: a linear combination of them {how} (n = {n} complete cases; "
            f"categorical predictors dummy-coded; model = all screened predictors: "
            f"{', '.join(preds)}). No one predictor separates it on its own, but a logistic model "
            f"containing them has no finite MLE: it will still run and report huge "
            f"coefficients with p ~ 1. {REMEDY}"
        ),
    }
    return record, finding


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
    kinds: dict[str, str] = {}
    mle_absent = False

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
            found = check_categorical(pred, pairs, floor)
            kinds[pred] = "categorical"
            # an empty cell already means no finite MLE for any model containing pred
            mle_absent = mle_absent or any(f["cell"]["n"] == 0 for f in found)
        elif all_numeric:
            found = check_continuous(pred, [(n, o) for n, (_, o) in zip(nums, pairs)])  # type: ignore[arg-type]
            kinds[pred] = "continuous"
            mle_absent = mle_absent or bool(found)
        else:
            skipped.append(
                {"predictor": pred, "reason": f"{len(levels)} levels, not numeric — an identifier?"}
            )
            continue
        findings.extend(found)
        screened.append(pred)

    # Screening one predictor at a time is exact for a one-predictor model only.
    if len(screened) < 2:
        joint: dict = {"status": "not_needed", "predictors": screened,
                       "reason": "one predictor: the per-predictor screen is exact"}
    else:
        joint, jf = check_joint(rows, outcome, sorted(out_vals), kinds)
        # If one predictor on its own already has no finite MLE, the joint program finds that
        # same separation again; report it once.
        if jf is not None and not mle_absent:
            findings.append(jf)

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
        "joint_check": joint,
        # Safe only when nothing fired AND the joint check ran (or was not needed): an
        # unchecked multivariable model is not certified.
        "model_safe": not findings and joint["status"] in ("clear", "not_needed"),
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
        j = rep["joint_check"]
        if not rep["findings"]:
            if j["status"] == "clear":
                print(f"  OK — no empty or sparse predictor x outcome cell, and no joint separation "
                      f"across the {len(j['predictors'])} screened predictors (n = "
                      f"{j['n_complete']} complete cases); the logistic MLE exists")
            elif j["status"] == "not_needed":
                print("  OK — no empty or sparse predictor x outcome cell; the logistic MLE exists")
            else:
                print("  no empty or sparse predictor x outcome cell, predictor by predictor — but "
                      f"JOINT separation was NOT checked ({j.get('reason', 'not run')}), so the "
                      "multivariable model is not certified")

    return 1 if (a.strict and rep["findings"]) else 0


if __name__ == "__main__":
    sys.exit(main())
