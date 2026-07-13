#!/usr/bin/env python3
"""Radiomics / classical-ML pipeline-rigor gate (radiomics-ml).

Radiomics + tree-ensemble studies (features -> random forest / XGBoost -> clinical
outcome) are the most common solo-doable clinical-ML workflow, and the most commonly
over-optimistic: hundreds-to-thousands of features on tens of patients, hyperparameters
tuned on the same folds performance is reported from, features selected on the whole
dataset, unstable features never filtered, and discrimination reported without
calibration (Lambin 2017; Park & Kim radiomics-quality; CLEAR; TRIPOD+AI; PROBAST-AI).

This gate reads a declarative **pipeline manifest** (JSON — the artifact this skill
emits, or one the researcher writes) and decides each rigor requirement by rule. It
complements `self-review/check_cv_leakage` (which greps a finished manuscript's prose):
this one audits the pipeline spec at build time.

CHECKS (verdicts):
  1. NO_NESTED_CV          (Major)  hyperparameters are tuned and performance reported on
                                    the same CV (flat k-fold) or with no validation at all;
                                    nested CV or a held-out test set is required.
  2. HIGH_DIM_LOW_EVENTS   (Major)  at least as many features as events (p >= events) with no
                                    dimensionality reduction / regularisation — the classic
                                    radiomics overfitting trap.
  3. SELECTION_OUTSIDE_CV  (Major)  feature selection is fit outside the CV fold (on the whole
                                    dataset), leaking the held-out folds into selection.
  4. NO_FEATURE_STABILITY  (Minor)  no test-retest / ICC feature-stability filtering; radiomics
                                    features are notoriously unstable across acquisition.
  5. NO_CALIBRATION        (Minor)  a clinical prediction model reported by discrimination only
                                    (no calibration slope/intercept or flexible curve).
  6. NO_EXTERNAL_VALIDATION(Minor)  single cohort, no external / temporal validation for a
                                    clinical claim.

MANIFEST (JSON)
  {
    "task": "classification",
    "n_features": 1200,
    "n_samples": 140,
    "n_events": 40,                       // minority-class count (for events-per-feature)
    "cv_scheme": "nested",                // nested / single_split / held_out_test / flat / loocv / none
    "feature_selection_stage": "inside_cv", // inside_cv / outside_cv / none
    "dimensionality_reduction": true,     // LASSO / PCA / regularisation applied
    "feature_stability": "icc",           // icc / test_retest / none
    "calibration_reported": true,
    "external_validation": "temporal",    // external / temporal / none
    "model": "xgboost"
  }

INPUTS
  --manifest  radiomics/classical-ML pipeline manifest JSON (required).

OUTPUT
  A reconciliation table (stdout) and, with --out, a JSON artifact:
    {manifest, model, n_features, n_samples, n_events, cv_scheme, claims[...], summary}
  NO_NESTED_CV / HIGH_DIM_LOW_EVENTS / SELECTION_OUTSIDE_CV are Major.

Stdlib-only (json / argparse / pathlib). Exit codes: 0 clean (or report-only),
1 Major claim(s) found (with --strict), 2 input/usage error.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

VALID_CV = {"nested", "nested_cv", "single_split", "held_out_test", "holdout_test",
            "held-out", "train_test_holdout"}
NONE_VALUES = {"", "none", "no", "na", "n/a", "false", "0"}


def _norm(s) -> str:
    return str(s).strip().lower() if s is not None else ""


def check(m: dict) -> list[dict]:
    claims: list[dict] = []
    n_features = m.get("n_features")
    n_events = m.get("n_events")
    n_samples = m.get("n_samples")
    cv = _norm(m.get("cv_scheme"))
    sel = _norm(m.get("feature_selection_stage"))
    dimred = m.get("dimensionality_reduction")
    stability = _norm(m.get("feature_stability"))
    calib = m.get("calibration_reported")
    extval = _norm(m.get("external_validation"))

    # 1. No nested CV / no held-out validation.
    if cv not in VALID_CV:
        detail = ("no validation scheme (`none`)" if cv in NONE_VALUES
                  else f"flat CV ('{cv or 'missing'}') tunes and reports on the same folds")
        claims.append({
            "verdict": "NO_NESTED_CV", "severity": "Major",
            "detail": (f"{detail}; use nested cross-validation or a held-out test set so tuning "
                       f"does not inflate the reported performance"),
            "where": "cv_scheme",
        })

    # 2. High dimensionality vs events, no reduction.
    denom = n_events if isinstance(n_events, (int, float)) else n_samples
    if isinstance(n_features, (int, float)) and isinstance(denom, (int, float)) and denom > 0:
        if n_features >= denom and dimred is not True:
            unit = "events" if isinstance(n_events, (int, float)) else "samples"
            claims.append({
                "verdict": "HIGH_DIM_LOW_EVENTS", "severity": "Major",
                "detail": (f"{n_features} features vs {int(denom)} {unit} (p >= {unit}) with no "
                           f"dimensionality reduction / regularisation; radiomics overfits badly "
                           f"in this regime — apply LASSO / PCA / a stability+redundancy filter"),
                "where": "n_features",
            })

    # 3. Feature selection outside the CV fold.
    if sel in {"outside_cv", "outside", "whole_dataset", "before_cv", "pre_cv", "global"}:
        claims.append({
            "verdict": "SELECTION_OUTSIDE_CV", "severity": "Major",
            "detail": ("feature selection is fit outside the CV fold (on the whole dataset), so the "
                       "held-out folds leak into selection; nest selection inside each training fold"),
            "where": "feature_selection_stage",
        })

    # 4. No feature-stability filtering.
    if stability in NONE_VALUES:
        claims.append({
            "verdict": "NO_FEATURE_STABILITY", "severity": "Minor",
            "detail": ("no test-retest / ICC feature-stability filtering; radiomics features are "
                       "unstable across acquisition and segmentation — filter to reproducible features"),
            "where": "feature_stability",
        })

    # 5. No calibration.
    if calib is not True:
        claims.append({
            "verdict": "NO_CALIBRATION", "severity": "Minor",
            "detail": ("a clinical prediction model is reported without calibration (slope/intercept "
                       "or a flexible calibration curve), only discrimination"),
            "where": "calibration_reported",
        })

    # 6. No external / temporal validation.
    if extval in NONE_VALUES:
        claims.append({
            "verdict": "NO_EXTERNAL_VALIDATION", "severity": "Minor",
            "detail": ("single-cohort development with no external / temporal validation; a clinical "
                       "claim needs validation beyond the development sample"),
            "where": "external_validation",
        })

    return claims


def analyze(manifest_path: str) -> dict:
    p = Path(manifest_path)
    if not p.is_file():
        sys.stderr.write(f"ERROR: manifest not found: {manifest_path}\n")
        sys.exit(2)
    try:
        m = json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, ValueError) as e:
        sys.stderr.write(f"ERROR: manifest is not valid JSON: {e}\n")
        sys.exit(2)
    if not isinstance(m, dict):
        sys.stderr.write("ERROR: manifest JSON must be an object\n")
        sys.exit(2)

    claims = check(m)
    n_major = sum(1 for c in claims if c["severity"] == "Major")
    return {
        "manifest": str(p),
        "model": m.get("model"),
        "n_features": m.get("n_features"),
        "n_samples": m.get("n_samples"),
        "n_events": m.get("n_events"),
        "cv_scheme": m.get("cv_scheme"),
        "claims": claims,
        "summary": {
            "n_claims": len(claims),
            "n_major": n_major,
            "n_flag": len(claims) - n_major,
            "verdict": "MAJOR_CANDIDATE" if n_major else "OK",
        },
    }


def render(result: dict) -> str:
    lines = ["| Check | Severity | Detail |", "|---|---|---|"]
    for c in result["claims"]:
        lines.append(f"| {c['verdict']} | {c['severity']} | {c['detail']} |")
    if len(lines) == 2:
        lines.append("| (none) | — | radiomics/ML pipeline meets the rigor bar |")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="Radiomics / classical-ML pipeline-rigor gate.")
    ap.add_argument("--manifest", required=True, help="radiomics/classical-ML pipeline manifest JSON")
    ap.add_argument("--out", help="write JSON artifact to this path")
    ap.add_argument("--strict", action="store_true", help="exit 1 if any Major claim exists")
    ap.add_argument("--quiet", action="store_true", help="suppress stdout table")
    args = ap.parse_args()

    result = analyze(args.manifest)

    if not args.quiet:
        print("=" * 41)
        print(" Radiomics / Classical-ML Gate (radiomics-ml)")
        print("=" * 41)
        print(f"  model={result['model']}  n_features={result['n_features']}  "
              f"n_samples={result['n_samples']}  n_events={result['n_events']}  "
              f"cv_scheme={result['cv_scheme']}")
        print(render(result))
        print()
        s = result["summary"]
        if s["n_major"]:
            print(f"MAJOR candidate: {s['n_major']} radiomics/ML rigor issue(s).")
        elif s["n_flag"]:
            print(f"MINOR flag: {s['n_flag']} radiomics/ML rigor issue(s) (see table).")
        else:
            print("OK: radiomics/ML pipeline meets the rigor bar.")

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps({"detector": "check_radiomics_ml", **result}, indent=2), encoding="utf-8")
        if not args.quiet:
            print(f"\nwrote {args.out}")

    return 1 if (args.strict and result["summary"]["n_major"]) else 0


if __name__ == "__main__":
    sys.exit(main())
