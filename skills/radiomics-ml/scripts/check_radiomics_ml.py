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
  2. HIGH_DIM_LOW_EVENTS   (Major)  at least as many candidate features as events (p >= events,
                                    events = the minority-class count) — the classic radiomics
                                    overfitting trap. Declaring dimensionality reduction /
                                    regularisation does NOT clear it: `n_features` already counts the
                                    candidates left after outcome-blind reduction, and LASSO /
                                    penalisation does not rescue a small sample. A floor for the
                                    worst case, not a sample-size criterion: size the study with
                                    pmsampsize (calc-sample-size Test 12).
     HIGH_DIM_NOT_ASSESSED (Minor)  the check above could not be run to a clearance because
                                    n_features, n_samples or n_events is not declared (it still
                                    fires as Major when the declared counts already prove p >= the
                                    bound). Not Major: the defect is unknown, not certain.
  3. SELECTION_OUTSIDE_CV  (Major)  feature selection is fit outside the CV fold (on the whole
                                    dataset), leaking the held-out folds into selection — or the
                                    stage is missing / unrecognised, so in-fold selection is unproven.
  4. NO_FEATURE_STABILITY  (Minor)  no test-retest / ICC feature-stability filtering (missing, none,
                                    or a value that is not a recognised stability filter); radiomics
                                    features are notoriously unstable across acquisition.
  5. NO_CALIBRATION        (Minor)  a clinical prediction model reported by discrimination only
                                    (no calibration slope/intercept or flexible curve).
  6. NO_EXTERNAL_VALIDATION(Minor)  single cohort, no external / temporal / geographic validation for
                                    a clinical claim (internal resampling such as bootstrap or a
                                    random split is not external validation).

MANIFEST (JSON)
  {
    "task": "classification",
    "n_features": 40,                     // candidate features reaching outcome-driven selection,
                                          // after outcome-blind reduction (integer >= 1)
    "n_samples": 140,                     // integer >= n_events
    "n_events": 40,                       // events (integer >= 0); the minority count
                                          // min(n_events, n_samples - n_events) is used
    "cv_scheme": "nested",                // nested / single_split / held_out_test / flat / loocv / none
                                          // single_split / held_out_test: tuned on the training split
                                          // only, test touched once; tuned on the test split = flat
    "feature_selection_stage": "inside_cv", // inside_cv / outside_cv / none (no outcome-driven
                                          // selection); missing or unrecognised = not proven in-fold
    "dimensionality_reduction": true,     // informational; does not clear HIGH_DIM_LOW_EVENTS
    "feature_stability": "icc",           // icc / test_retest / none
    "calibration_reported": true,
    "external_validation": "temporal",    // external / temporal / geographic / none
    "model": "xgboost"
  }

INPUTS
  --manifest  radiomics/classical-ML pipeline manifest JSON (required).

OUTPUT
  A reconciliation table (stdout) and, with --out, a JSON artifact:
    {manifest, basis: "declared", model, n_features, n_samples, n_events, cv_scheme, claims[...],
     summary}
  NO_NESTED_CV / HIGH_DIM_LOW_EVENTS / SELECTION_OUTSIDE_CV are Major. The OK line reads
  "OK (as declared)": the gate checks the manifest, not the pipeline that ran.

Categorical values are matched case-insensitively, with `-` and spaces read as `_`.

Stdlib-only (json / argparse / pathlib). Exit codes: 0 clean (or report-only),
1 Major claim(s) found (with --strict), 2 input/usage error (including a count field that is
not a non-negative integer, n_features < 1, or n_events > n_samples).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

VALID_CV = {"nested", "nested_cv", "single_split", "held_out_test", "holdout_test",
            "held-out", "train_test_holdout"}
NONE_VALUES = {"", "none", "no", "na", "n/a", "false", "0"}
# feature_selection_stage: positive allow-lists; anything else (incl. missing) is unproven.
SEL_INSIDE = {"inside_cv", "inside", "inside_fold", "in_fold", "in_cv", "within_cv",
              "within_fold", "nested"}
SEL_NO_SELECTION = {"none", "no", "na", "n/a", "no_selection", "not_applicable"}
SEL_OUTSIDE = {"outside_cv", "outside", "outside_fold", "whole_dataset", "full_dataset",
               "all_data", "before_cv", "pre_cv", "prior_to_cv", "global"}
STABILITY_OK = {"icc", "test_retest", "retest", "icc_test_retest"}
EXTERNAL_OK = {"external", "temporal", "geographic", "external_temporal", "temporal_external",
               "external_and_temporal", "external_geographic"}
COUNT_FIELDS = ("n_features", "n_samples", "n_events")


def _norm(s) -> str:
    return str(s).strip().lower() if s is not None else ""


def _key(s) -> str:
    """Normalise a categorical value: lower case, `-` and whitespace read as `_`."""
    return "_".join(_norm(s).replace("-", " ").split())


def _is_count(v) -> bool:
    if isinstance(v, bool):
        return False
    if isinstance(v, int):
        return v >= 0
    return isinstance(v, float) and v.is_integer() and v >= 0


def validate(m: dict) -> list[str]:
    """Input errors in the count fields (reported with exit 2, never silently skipped)."""
    errors = []
    for f in COUNT_FIELDS:
        if m.get(f) is not None and not _is_count(m[f]):
            errors.append(f"`{f}` must be a non-negative integer, got {m[f]!r}")
    if errors:
        return errors
    nf, ns, ne = m.get("n_features"), m.get("n_samples"), m.get("n_events")
    if nf is not None and nf < 1:
        errors.append(f"`n_features` must be at least 1, got {nf!r}")
    if ns is not None and ne is not None and ne > ns:
        errors.append(f"`n_events` ({ne!r}) exceeds `n_samples` ({ns!r})")
    return errors


def check(m: dict) -> list[dict]:
    claims: list[dict] = []
    n_features = m.get("n_features")
    n_events = m.get("n_events")
    n_samples = m.get("n_samples")
    cv = _norm(m.get("cv_scheme"))
    sel_raw = m.get("feature_selection_stage")
    sel = _key(sel_raw)
    dimred = m.get("dimensionality_reduction")
    stability = _key(m.get("feature_stability"))
    calib = m.get("calibration_reported")
    extval = _key(m.get("external_validation"))

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

    # 2. High dimensionality vs events. Declared dimensionality reduction / regularisation does
    #    not clear it: n_features counts the candidates left after outcome-blind reduction.
    unit = None
    denom = None
    if _is_count(n_events):
        denom, unit = n_events, "events"
        if _is_count(n_samples) and n_samples >= n_events:
            denom = min(n_events, n_samples - n_events)
    elif n_events is None and _is_count(n_samples):
        denom, unit = n_samples, "samples"
    if _is_count(n_features) and denom is not None and n_features >= denom:
        if dimred is True:
            why = ("declared dimensionality reduction / regularisation does not clear this — "
                   "`n_features` must count the candidates left after outcome-blind reduction, "
                   "and LASSO / penalisation fit with the outcome does not shrink that count")
        else:
            why = "with no dimensionality reduction / regularisation"
        claims.append({
            "verdict": "HIGH_DIM_LOW_EVENTS", "severity": "Major",
            "detail": (f"{n_features} features vs {int(denom)} {unit} (p >= {unit}) {why}; "
                       f"radiomics overfits badly "
                       f"in this regime — reduce the candidates without the outcome "
                       f"(stability, redundancy, clinical prior), then size the study with "
                       f"pmsampsize (/calc-sample-size Test 12); p < events is a floor, not a "
                       f"sample-size criterion, and penalisation does not rescue a small sample"),
            "where": "n_features",
        })
    elif any(m.get(f) is None for f in COUNT_FIELDS):
        # A missing count is not a clearance: without all three the minority-class bound is
        # unknown (n_samples alone is an upper bound on events; n_events alone may be the majority).
        missing = ", ".join(f"`{f}`" for f in COUNT_FIELDS if m.get(f) is None)
        claims.append({
            "verdict": "HIGH_DIM_NOT_ASSESSED", "severity": "Minor",
            "detail": (f"{missing} not declared, so features vs events (the minority-class count) "
                       f"is not assessed; declare n_features, n_samples and n_events"),
            "where": "n_features / n_samples / n_events",
        })

    # 3. Feature selection outside the CV fold (or not shown to be inside it).
    if sel in SEL_OUTSIDE:
        claims.append({
            "verdict": "SELECTION_OUTSIDE_CV", "severity": "Major",
            "detail": ("feature selection is fit outside the CV fold (on the whole dataset), so the "
                       "held-out folds leak into selection; nest selection inside each training fold"),
            "where": "feature_selection_stage",
        })
    elif sel not in SEL_INSIDE and sel not in SEL_NO_SELECTION:
        shown = "missing" if sel == "" else f"an unrecognised value ('{sel_raw}')"
        claims.append({
            "verdict": "SELECTION_OUTSIDE_CV", "severity": "Major",
            "detail": (f"feature_selection_stage is {shown}, so selection inside the CV fold is not "
                       f"shown; declare inside_cv (selection nested in each training fold), "
                       f"outside_cv, or none (no outcome-driven selection)"),
            "where": "feature_selection_stage",
        })

    # 4. No feature-stability filtering (positive allow-list).
    if stability not in STABILITY_OK and not stability.startswith("icc"):
        detail = ("no test-retest / ICC feature-stability filtering; radiomics features are "
                  "unstable across acquisition and segmentation — filter to reproducible features")
        if stability not in NONE_VALUES:
            detail = (f"feature_stability '{m.get('feature_stability')}' is not a recognised "
                      f"stability filter (icc / test_retest); " + detail)
        claims.append({
            "verdict": "NO_FEATURE_STABILITY", "severity": "Minor",
            "detail": detail,
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

    # 6. No external / temporal validation (positive allow-list).
    if extval not in EXTERNAL_OK:
        detail = ("single-cohort development with no external / temporal validation; a clinical "
                  "claim needs validation beyond the development sample")
        if extval not in NONE_VALUES:
            detail = (f"external_validation '{m.get('external_validation')}' is not external / "
                      f"temporal / geographic validation (internal resampling or a random split of "
                      f"the development cohort does not count); " + detail)
        claims.append({
            "verdict": "NO_EXTERNAL_VALIDATION", "severity": "Minor",
            "detail": detail,
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
    errors = validate(m)
    if errors:
        for e in errors:
            sys.stderr.write(f"ERROR: {e}\n")
        sys.exit(2)

    claims = check(m)
    n_major = sum(1 for c in claims if c["severity"] == "Major")
    return {
        "manifest": str(p),
        "basis": "declared",
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
            print("OK (as declared): radiomics/ML pipeline meets the rigor bar.")

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps({"detector": "check_radiomics_ml", **result}, indent=2), encoding="utf-8")
        if not args.quiet:
            print(f"\nwrote {args.out}")

    return 1 if (args.strict and result["summary"]["n_major"]) else 0


if __name__ == "__main__":
    sys.exit(main())
