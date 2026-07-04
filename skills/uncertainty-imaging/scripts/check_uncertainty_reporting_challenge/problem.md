# Challenge card — uncertainty-imaging (uncertainty / OOD reporting rigor)

## Problem
A medical-imaging model framed for deployment must carry more than a point prediction: a
calibrated uncertainty on each case, an out-of-distribution guard validated on held-out
OOD data, and — if it abstains — a pre-specified operating point. The over-optimistic
failures are predictable: a clinical-use claim built on point predictions, conformal
intervals quoted without ever measuring their coverage, and an "OOD detector" evaluated
only on in-distribution data. Reviewers of a deployment-framed AI paper (DECIDE-AI,
TRIPOD+AI) ask for exactly these.

## What the gate does
`scripts/check_uncertainty_reporting.py` reads a declarative **uncertainty manifest**
(JSON) and decides each requirement by rule:
- `POINT_PREDICTION_NO_UNCERTAINTY` (Major) — a deployment claim with no uncertainty method.
- `CONFORMAL_NO_COVERAGE_VALIDATION` (Major) — conformal intervals with unmeasured coverage.
- `OOD_NO_HELDOUT_SET` (Major) — an OOD claim with no held-out OOD test set.
- `ENSEMBLE_NOT_INDEPENDENT` / `MCDROPOUT_DISABLED_AT_INFERENCE` / `SELECTIVE_NO_TARGET` /
  `NO_CALIBRATION_UNDER_SHIFT` (Minor) — method-specific correctness + robustness flags.

It **integrates** MAPIE / captum / the pretrained-detector ecosystem by reference; it does
not reimplement them and never runs a model on real patient data. The gate audits the
declared spec — a mislabelled field can hide a real problem, so it complements, not
replaces, `model-evaluation`'s executed calibration/subgroup metrics.

## Fixture (synthetic only — no real images, no PII)
- `fixture/uncertainty_weak.json` — a deployment claim with point predictions, an OOD claim
  with no held-out OOD set, and selective prediction with no target.
- `fixture/uncertainty_strong.json` — conformal with validated coverage, OOD on a held-out
  cohort, selective prediction at a pre-specified target, calibration under shift.

## Expected (`verify.sh`, network-free)
1. The weak manifest fires `POINT_PREDICTION_NO_UNCERTAINTY` + `OOD_NO_HELDOUT_SET` (Major)
   + `SELECTIVE_NO_TARGET` (Minor); stdout matches `expected/weak.txt`; exit 1 under `--strict`.
2. The strong manifest fires nothing; stdout matches `expected/strong.txt`; exit 0.

This is the deployment-uncertainty bar decided deterministically: a point-prediction
clinical claim flagged, a calibrated + OOD-guarded + abstaining model cleared.
