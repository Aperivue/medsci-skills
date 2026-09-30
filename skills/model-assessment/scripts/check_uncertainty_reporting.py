#!/usr/bin/env python3
"""Uncertainty / OOD / selective-prediction reporting-rigor gate (uncertainty-imaging).

A medical-imaging model framed for deployment must say more than a point prediction: it
needs calibrated uncertainty, an out-of-distribution (OOD) guard validated on a held-out
OOD set, and — if it abstains — a pre-specified operating point. The common failures are
reporting point predictions under a deployment claim, quoting conformal intervals whose
empirical coverage was never checked, and claiming OOD detection with no held-out OOD
data (Gal 2016 MC-dropout; Lakshminarayanan 2017 deep ensembles; Angelopoulos & Bates
conformal; Ovadia 2019 calibration-under-shift; DECIDE-AI deployment monitoring).

This gate reads a declarative **uncertainty manifest** (JSON — the artifact this skill
emits, or one the researcher writes) and decides each requirement by rule. It complements
`model-evaluation`'s calibration/subgroup metrics: this one audits the uncertainty spec at
design/report time, so a deployment-framed claim carries the uncertainty machinery a
reviewer expects.

CHECKS (verdicts):
  1. POINT_PREDICTION_NO_UNCERTAINTY (Major)  a deployment-framed claim reports point
                                    predictions only (uncertainty_method `none`); no
                                    MC-dropout / deep ensemble / conformal / Bayesian UQ.
  2. CONFORMAL_NO_COVERAGE_VALIDATION (Major)  conformal (or split-conformal) intervals are
                                    reported without empirical coverage validated on a
                                    held-out calibration/test set — the coverage guarantee
                                    is only asymptotic/assumption-bound until measured.
  3. OOD_NO_HELDOUT_SET      (Major)  an OOD-detection claim with no held-out OOD test set
                                    (only in-distribution data) — the detector's operating
                                    point and AUROC are unmeasured.
  4. ENSEMBLE_NOT_INDEPENDENT (Minor)  a deep-ensemble UQ claim whose members are not
                                    independent (shared seed/init, or < 2 members) — this
                                    underestimates epistemic uncertainty.
  5. MCDROPOUT_DISABLED_AT_INFERENCE (Minor)  MC-dropout UQ but dropout is not active at
                                    inference; with dropout off every forward pass is
                                    identical and the "uncertainty" is a point prediction.
  6. SELECTIVE_NO_TARGET     (Minor)  selective prediction / abstention is offered without a
                                    pre-specified coverage or risk target (the operating
                                    point is chosen post hoc).
  7. NO_CALIBRATION_UNDER_SHIFT (Minor)  uncertainty is evaluated in-distribution only, with
                                    no distribution-shift stress — deployment uncertainty
                                    degrades under shift (Ovadia 2019).

MANIFEST (JSON)
  {
    "task": "classification",
    "deployment_claim": true,             // is a deployment / clinical-use claim made?
    "uncertainty_method": "conformal",    // conformal / mc_dropout / deep_ensemble / bayesian / none
    "coverage_target": 0.90,              // nominal coverage (conformal / selective); null if n/a
    "coverage_validated": true,           // empirical coverage measured on held-out cal/test
    "ensemble_members": 5,                // deep_ensemble member count
    "ensemble_independent": true,         // members trained with distinct seeds / inits
    "mc_dropout_active_at_inference": true,  // dropout kept ON at inference for MC sampling
    "ood_method": "mahalanobis",          // energy / mahalanobis / odin / msp / none
    "ood_heldout_set": "external-ood-cohort",  // held-out OOD test set (null / none if absent)
    "selective_prediction": true,         // model may abstain
    "selective_target": 0.95,             // pre-specified coverage/risk target (null if none)
    "calibration_under_shift": true       // uncertainty evaluated under distribution shift
  }

INPUTS
  --manifest  uncertainty manifest JSON (required).

OUTPUT
  A reconciliation table (stdout) and, with --out, a JSON artifact:
    {manifest, task, uncertainty_method, ood_method, deployment_claim, claims[...], summary}
  POINT_PREDICTION_NO_UNCERTAINTY / CONFORMAL_NO_COVERAGE_VALIDATION / OOD_NO_HELDOUT_SET are Major.

Stdlib-only (json / argparse / pathlib). Exit codes: 0 clean (or report-only),
1 Major claim(s) found (with --strict), 2 input/usage error.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

NONE_VALUES = {"", "none", "no", "na", "n/a", "false", "0", "null"}
CONFORMAL = {"conformal", "split_conformal", "split-conformal", "cqr", "raps", "aps"}
MC_DROPOUT = {"mc_dropout", "mcdropout", "mc-dropout", "monte_carlo_dropout"}
DEEP_ENSEMBLE = {"deep_ensemble", "deep-ensemble", "ensemble", "deep_ensembles"}


def _norm(s) -> str:
    return str(s).strip().lower() if s is not None else ""


def _is_none(v) -> bool:
    """True for an absent / disabled field (None, or a none-like scalar)."""
    return v is None or _norm(v) in NONE_VALUES


def check(m: dict) -> list[dict]:
    claims: list[dict] = []
    deployment = m.get("deployment_claim")
    method = _norm(m.get("uncertainty_method"))
    coverage_validated = m.get("coverage_validated")
    ensemble_members = m.get("ensemble_members")
    ensemble_independent = m.get("ensemble_independent")
    mc_active = m.get("mc_dropout_active_at_inference")
    ood = _norm(m.get("ood_method"))
    ood_set = m.get("ood_heldout_set")
    selective = m.get("selective_prediction")
    selective_target = m.get("selective_target")
    calib_shift = m.get("calibration_under_shift")

    method_none = method in NONE_VALUES

    # 1. Deployment claim with point predictions only.
    if deployment is True and method_none:
        claims.append({
            "verdict": "POINT_PREDICTION_NO_UNCERTAINTY", "severity": "Major",
            "detail": ("a deployment / clinical-use claim reports point predictions only "
                       "(no uncertainty method); add MC-dropout, a deep ensemble, conformal "
                       "prediction, or a Bayesian estimate so each prediction carries uncertainty"),
            "where": "uncertainty_method",
        })

    # 2. Conformal intervals without empirical coverage validation.
    if method in CONFORMAL and coverage_validated is not True:
        claims.append({
            "verdict": "CONFORMAL_NO_COVERAGE_VALIDATION", "severity": "Major",
            "detail": ("conformal intervals are reported without empirical coverage validated on a "
                       "held-out calibration/test set; measure achieved coverage against the nominal "
                       "target (exchangeability can fail on clinical data — verify, do not assume)"),
            "where": "coverage_validated",
        })

    # 3. OOD claim with no held-out OOD test set.
    if ood not in NONE_VALUES and _is_none(ood_set):
        claims.append({
            "verdict": "OOD_NO_HELDOUT_SET", "severity": "Major",
            "detail": (f"an OOD-detection claim ('{ood}') with no held-out OOD test set; its operating "
                       f"point and detection AUROC are unmeasured — evaluate on data known to be "
                       f"out-of-distribution (different scanner / site / pathology)"),
            "where": "ood_heldout_set",
        })

    # 4. Deep ensemble whose members are not independent.
    if method in DEEP_ENSEMBLE:
        n = ensemble_members if isinstance(ensemble_members, (int, float)) else None
        if ensemble_independent is not True or (n is not None and n < 2):
            claims.append({
                "verdict": "ENSEMBLE_NOT_INDEPENDENT", "severity": "Minor",
                "detail": ("a deep-ensemble uncertainty claim whose members are not independent "
                           "(shared seed/init, or fewer than 2 members); train each member from a "
                           "distinct seed/initialisation or the ensemble underestimates uncertainty"),
                "where": "ensemble_independent",
            })

    # 5. MC-dropout with dropout disabled at inference.
    if method in MC_DROPOUT and mc_active is not True:
        claims.append({
            "verdict": "MCDROPOUT_DISABLED_AT_INFERENCE", "severity": "Minor",
            "detail": ("MC-dropout uncertainty but dropout is not active at inference; with dropout "
                       "off every stochastic pass is identical and the estimate collapses to a point "
                       "prediction — keep dropout layers in train mode during sampling"),
            "where": "mc_dropout_active_at_inference",
        })

    # 6. Selective prediction without a pre-specified operating point.
    if selective is True and _is_none(selective_target):
        claims.append({
            "verdict": "SELECTIVE_NO_TARGET", "severity": "Minor",
            "detail": ("selective prediction / abstention is offered without a pre-specified coverage "
                       "or risk target; fixing the operating point post hoc inflates the reported "
                       "accuracy-at-coverage — pre-specify the target coverage / risk"),
            "where": "selective_target",
        })

    # 7. No calibration-under-shift stress.
    if not method_none and calib_shift is not True:
        claims.append({
            "verdict": "NO_CALIBRATION_UNDER_SHIFT", "severity": "Minor",
            "detail": ("uncertainty is evaluated in-distribution only, with no distribution-shift "
                       "stress; deployment uncertainty degrades under shift (scanner / site / case-mix) "
                       "— report calibration on shifted or external data"),
            "where": "calibration_under_shift",
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
        "task": m.get("task"),
        "deployment_claim": m.get("deployment_claim"),
        "uncertainty_method": m.get("uncertainty_method"),
        "ood_method": m.get("ood_method"),
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
        lines.append("| (none) | — | uncertainty / OOD reporting meets the deployment bar |")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="Uncertainty / OOD / selective-prediction reporting-rigor gate.")
    ap.add_argument("--manifest", required=True, help="uncertainty manifest JSON")
    ap.add_argument("--out", help="write JSON artifact to this path")
    ap.add_argument("--strict", action="store_true", help="exit 1 if any Major claim exists")
    ap.add_argument("--quiet", action="store_true", help="suppress stdout table")
    args = ap.parse_args()

    result = analyze(args.manifest)

    if not args.quiet:
        print("=" * 41)
        print(" Uncertainty / OOD Reporting Gate (uncertainty-imaging)")
        print("=" * 41)
        print(f"  task={result['task']}  deployment_claim={result['deployment_claim']}  "
              f"uncertainty_method={result['uncertainty_method']}  ood_method={result['ood_method']}")
        print(render(result))
        print()
        s = result["summary"]
        if s["n_major"]:
            print(f"MAJOR candidate: {s['n_major']} uncertainty/OOD reporting issue(s).")
        elif s["n_flag"]:
            print(f"MINOR flag: {s['n_flag']} uncertainty/OOD reporting issue(s) (see table).")
        else:
            print("OK: uncertainty / OOD reporting meets the deployment bar.")

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps({"detector": "check_uncertainty_reporting", **result}, indent=2), encoding="utf-8")
        if not args.quiet:
            print(f"\nwrote {args.out}")

    return 1 if (args.strict and result["summary"]["n_major"]) else 0


if __name__ == "__main__":
    sys.exit(main())
