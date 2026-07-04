---
name: uncertainty-imaging
description: >
  Design or audit the uncertainty-quantification, out-of-distribution (OOD) detection, and
  selective-prediction layer of a medical-imaging model framed for deployment — so a clinical-use claim
  carries calibrated per-case uncertainty (MC-dropout / deep ensemble / conformal / Bayesian), an OOD
  guard validated on a held-out OOD set, an abstention rule at a pre-specified operating point, and
  uncertainty checked under distribution shift. Emits an uncertainty manifest and a deterministic gate
  that flags a deployment claim built on point predictions, conformal intervals with unmeasured coverage,
  and an OOD claim with no held-out OOD data. Integrates MAPIE / captum / pretrained OOD scorers; it does
  not reimplement them and never runs a model on real patient data.
triggers: uncertainty, uncertainty quantification, UQ, epistemic, aleatoric, MC-dropout, monte carlo dropout, deep ensemble, conformal prediction, split conformal, prediction interval, coverage, calibration under shift, out-of-distribution, OOD detection, distribution shift, Mahalanobis, energy score, ODIN, selective prediction, abstention, reject option, deployment safety, DECIDE-AI, predictive uncertainty
tools: Read, Write, Edit, Bash, Grep, Glob
model: inherit
---

# Uncertainty-Imaging Skill

## Purpose

A medical-imaging model framed for **deployment** must say more than "class 1, 0.87". It needs a
**calibrated uncertainty** on each case, an **out-of-distribution (OOD) guard** validated on data known
to be out-of-distribution, and — if it abstains — a **pre-specified operating point**. The failures are
predictable and reviewer-visible: a clinical-use claim built on point predictions, conformal intervals
quoted without ever measuring their coverage, an "OOD detector" evaluated only on in-distribution data,
a deep ensemble whose members share a seed, and uncertainty validated only in-distribution when
deployment sees scanner/site/case-mix shift. This skill designs that layer and audits an existing one
(Gal 2016; Lakshminarayanan 2017; Angelopoulos & Bates; Ovadia 2019; DECIDE-AI).

It is the deployment-safety companion in the model-engineering lane: `/model-evaluation` computes the
held-out metrics and calibration, and **uncertainty-imaging** covers the uncertainty / OOD / abstention
machinery a deployment claim rests on. It **integrates** MAPIE (conformal), captum, and pretrained OOD
scorers; it does not reimplement them and never runs a model on real patient data.

## When to use
- Your model is framed for clinical use / deployment and a reviewer will ask "what does it do when it is
  unsure, or off-distribution?"
- You report conformal / MC-dropout / ensemble uncertainty and want the coverage, independence, and
  shift checks right before submission.
- You want to audit an existing uncertainty/OOD section for the failure modes below.

## When NOT to use
- Held-out discrimination / calibration metrics of the point predictor → `/model-evaluation` then
  `/analyze-stats`.
- Training-repo scaffolding / the split → `/model-scaffold` (+ `/model-validation`).
- Interpretability / saliency of a trained network → `/explainability`.
- Classical-ML calibration of a tabular model → `/radiomics-ml` + `/analyze-stats`.
- Reimplementing MAPIE / an OOD library → out of scope (this skill wires and audits them).

## The failure modes (what the gate enforces)
1. **Point predictions under a deployment claim.** A clinical-use claim with no uncertainty method at
   all — add MC-dropout, a deep ensemble, conformal prediction, or a Bayesian estimate.
2. **Conformal without coverage validation.** Conformal's guarantee holds under exchangeability, which
   can fail on clinical data — measure achieved coverage on a held-out calibration/test set.
3. **OOD claim with no held-out OOD set.** An OOD detector's operating point and AUROC are unmeasured
   until you evaluate on data known to be out-of-distribution (different scanner / site / pathology).
4. **Non-independent ensemble.** A deep ensemble whose members share a seed/init (or has < 2 members)
   underestimates epistemic uncertainty.
5. **MC-dropout with dropout off at inference.** Dropout must stay active during sampling; off, every
   pass is identical and the estimate collapses to a point prediction.
6. **Selective prediction without a target.** Abstention chosen post hoc inflates accuracy-at-coverage;
   pre-specify the coverage / risk operating point.
7. **No calibration under shift.** Uncertainty evaluated in-distribution only; deployment uncertainty
   degrades under shift, so report it on shifted / external data.

## Workflow

### Phase 1 — Choose the uncertainty method (integrate, don't reimplement)
- **Conformal prediction** (MAPIE) — distribution-free prediction sets/intervals at a nominal coverage;
  the strongest default when a calibration set is available. Validate empirical coverage.
- **Deep ensembles** (Lakshminarayanan 2017) — train K independent members (distinct seeds/inits); the
  best-quality epistemic uncertainty, at K× cost.
- **MC-dropout** (Gal 2016) — keep dropout active at inference and sample T passes; cheap, weaker.
- **Bayesian / Laplace** — a last-layer Laplace approximation is a light option.
See `references/uncertainty_guide.md`.

### Phase 2 — Add the OOD guard and the abstention rule
- **OOD detection** — an energy score, Mahalanobis distance on features, ODIN, or max-softmax; **evaluate
  on a held-out OOD set** (different scanner/site/pathology) and report detection AUROC + the operating
  point.
- **Selective prediction** — abstain below a confidence/uncertainty threshold set to a **pre-specified**
  target coverage or risk; report the risk–coverage curve.

### Phase 3 — Stress it under shift
Report calibration / coverage on **shifted or external** data, not in-distribution only (Ovadia 2019).

### Phase 4 — Emit the uncertainty manifest
```json
{
  "task": "classification",
  "deployment_claim": true,
  "uncertainty_method": "conformal",
  "coverage_target": 0.90,
  "coverage_validated": true,
  "ood_method": "mahalanobis",
  "ood_heldout_set": "external-ood-cohort",
  "selective_prediction": true,
  "selective_target": 0.95,
  "calibration_under_shift": true
}
```

### Phase 5 — Gate the spec (deterministic)
```bash
python3 scripts/check_uncertainty_reporting.py --manifest uncertainty_manifest.json --strict
```
Verdicts: `POINT_PREDICTION_NO_UNCERTAINTY`, `CONFORMAL_NO_COVERAGE_VALIDATION`, `OOD_NO_HELDOUT_SET`
(Major); `ENSEMBLE_NOT_INDEPENDENT`, `MCDROPOUT_DISABLED_AT_INFERENCE`, `SELECTIVE_NO_TARGET`,
`NO_CALIBRATION_UNDER_SHIFT` (Minor). Audits the declared spec at design/report time; it complements
`/model-evaluation`'s executed calibration/subgroup metrics.

## Integration
- **`/model-evaluation`** — the point predictor's held-out metrics + calibration this layer sits on top of.
- **`/analyze-stats`** — calibration curve / risk–coverage plotting for the report.
- **`/check-reporting`** — TRIPOD+AI / DECIDE-AI deployment-monitoring items.
- **`/model-validation`** — the DECIDE-AI monitoring seam (the deployment-time counterpart of the split
  audit).

## Anti-Hallucination

- **Never fabricate coverage, OOD AUROC, or calibration numbers.** Every value in the manifest and every
  reported number comes from the researcher's executed code — never invented. This skill designs and
  audits the uncertainty spec; it does not run a model on real patient data.
- **Never report conformal coverage as guaranteed without measuring it.** Exchangeability can fail on
  clinical data (`CONFORMAL_NO_COVERAGE_VALIDATION`).
- **Never report an uncertainty/OOD audit "pass" without running `check_uncertainty_reporting.py`.** The
  verdict is reproduced deterministically, never asserted from prose.
- **Integrate, don't reimplement.** Reference MAPIE / captum / OOD scorers; do not write a new conformal
  or OOD library or claim results for one.

## Reproducible challenge
`scripts/check_uncertainty_reporting_challenge/` ships a synthetic weak/strong uncertainty-manifest pair
with a network-free `verify.sh` wired into the skill's validation commands.
