---
name: model-assessment
description: Use when validating or evaluating a trained medical-imaging model. Audits split leakage and validation design, computes task-correct held-out metrics (Dice + HD95, AUROC + AUPRC, FROC, calibration), and covers uncertainty/OOD and Grad-CAM explainability, each with a gate.
metadata:
  triggers: "model validation, validate AI model, imaging model validation, data leakage, split leakage, train test split, patient-level split, internal validation, external validation, validation design, leakage audit, segmentation model validation, classification model validation, detection model validation, nnU-Net validation, deep learning validation, CLAIM 2024, generalizability, held-out test set, model evaluation, held-out metrics, test set metrics, Dice, HD95, NSD, surface distance, Metrics Reloaded, AUROC, AUPRC, bootstrap CI, calibration, ECE, reliability diagram, subgroup analysis, slice metrics, mAP, FROC, segmentation metrics, detection metrics, evaluate predictions, interactive segmentation, promptable segmentation, SAM2, MedSAM2, nnInteractive, number of clicks, NoC, interactions-to-threshold, click budget, generative metrics, image synthesis, SSIM, PSNR, SNR, CNR, downstream task, multiclass classification, Obuchowski index, Harrell's C, time-dependent ROC, uncertainty, uncertainty quantification, UQ, epistemic, aleatoric, MC-dropout, monte carlo dropout, deep ensemble, conformal prediction, split conformal, prediction interval, coverage, calibration under shift, out-of-distribution, OOD detection, distribution shift, Mahalanobis, energy score, ODIN, selective prediction, abstention, reject option, deployment safety, DECIDE-AI, predictive uncertainty, explainability, interpretability, saliency, saliency map, grad-cam, gradcam, grad-cam++, attention map, attention rollout, integrated gradients, captum, pytorch-grad-cam, heatmap, class activation map, CAM, feature attribution, sanity check, Adebayo, model randomization, localization metric, pointing game, IoU with ground truth, XAI, explainable AI, model looks at, faithfulness"
---

# Model-Assessment Skill

Assess a trained medical-imaging model (in-house, vendor or open-weights; segmentation,
classification or detection) in the order the evidence is built: **Part A** designs and audits the
validation study, **Part B** computes task-correct held-out metrics, **Part C** adds the
uncertainty / OOD / abstention layer a deployment claim needs, and **Part D** makes an
explainability analysis survive review. Run the parts the request needs (a Grad-CAM question starts
at Part D), but no metric headline is reported before the Part A split gate is green. Each part ends
in a stdlib gate whose verdict is reproduced from a file — never report a pass without running it.

Numbers come only from code executed on the supplied predictions, split table, or the researcher's
executed UQ/XAI code; if predictions or ground truth are missing, say so and stop. Integrate
MONAI / nnU-Net, MAPIE, captum, pytorch-grad-cam and pretrained OOD scorers by reference — never
reimplement them, never build or train the model, never run a model on real patient data.

Elsewhere: building/training → `/model-scaffold`; choosing or vetting the model →
`/model-selection`; data-stage preprocessing leakage → `/imaging-data`; paired model comparison /
added value over a baseline / decision curves / MRMC / ICC / calibration tables → `/analyze-stats`
(added value: `incremental_value.md`); AI-vs-expert reader rubric
and IRR → `/design-ai-benchmarking`; LLM/MLLM → `/mllm-eval`; general validity → `/design-study`;
classical-ML tabular calibration → `/radiomics-ml`; item-by-item reporting audit →
`/check-reporting`; a finished manuscript → `/self-review` or `/peer-review` (the MD0–MD11
`model_development.md` probe).

## Part A — Validation design

The rationale behind Phases 2–7 — the full leakage taxonomy, the internal-vs-external ladder,
comparator design, run variance, test-set sizing, the reporting map — is in
`${CLAUDE_SKILL_DIR}/references/validation_design.md` (load on demand). Verify citations via
`/search-lit` (confirmed DOI/PMID), else mark `[UNVERIFIED - NEEDS MANUAL CHECK]`; flag an uncertain
CLAIM 2024 / TRIPOD+AI / Metrics Reloaded item `[VERIFY]` and ask.

### Phase 1 — Task, intended-use horizon, analysis unit
State the task, the **intended-use horizon** (screening, triage, pre-procedure, post-hoc), the
**single headline metric** the conclusion leans on, and the **analysis unit** (per-patient /
per-lesion / per-image). Everything downstream is read against this; a per-lesion metric is never
reported as per-patient.

### Phase 2 — Leakage audit (run first)
Produce the emitted split-assignment table (`patient_id,split`) and run:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/check_split_leakage.py \
  --splits <split_assignment.csv> --out qc/split_leakage.json --strict
```

`PATIENT_OVERLAP` (a patient in ≥ 2 partitions) and `MISSING_SEED` (an unreproducible split) are
Major, `SINGLE_PARTITION` Minor — proven by set arithmetic. A design with patient overlap is never
approved. Then walk the leakage the table cannot show (Kapoor & Narayanan, *Patterns* 2023):
preprocessing fit before the split (normalisation, resampling, foundation-model embeddings, ComBat
harmonisation over the whole cohort — `/imaging-data` gates the declared pipeline), site / scanner /
burned-in-label shortcuts, and temporal leakage (a random split where future and past coexist).
The decisive question: *could any value used in training have been computed only with knowledge of
a test case?*

### Phase 3 — Validation tier
Classify honestly: apparent → internal random split → cross-validation → temporal → geographic /
external (different site, scanner, vendor) → multi-site external. Cross-validation and bootstrap are
development-time optimism corrections, **not** external validation. Flag a generalisability or
deployment claim that outruns the design, and "external validation" where the single external set
was used for tuning. Confirm the test set was touched **once** — no architecture search,
hyperparameter sweep, early stopping, or threshold choice read it.

### Phase 4 — Comparator
Clinical-only baseline, incremental value over an existing score, or reader comparison (hand the
rubric / inter-rater design to `/design-ai-benchmarking`).

### Phase 5 — Test-set sizing
Count **events per class** in the test set, not the cohort total: a sparse positive set gives a CI
spanning much of the usable range, and calibration needs roughly ≥ 100 events. Hand formal sizing to
`/calc-sample-size`.

### Phase 6 — Prospective evaluation and deployment-monitoring horizon
Retrospective external validation shows accuracy *transfers*, not that the model is safe and useful
in the workflow. For a clinical-use claim design the higher tier explicitly — silent / shadow
deployment → prospective comparative or impact study / RCT on a clinical endpoint →
post-deployment monitoring with recalibration-or-withdrawal triggers and subgroup audit
(`references/validation_design.md` §2b). Scope the claim to the tier reached: a retrospective
external study never claims deployment readiness or outcome benefit.

### Phase 7 — Reporting-guideline fit
Map via `/check-reporting`: **CLAIM 2024** (diagnostic imaging AI), **TRIPOD+AI** (prediction model),
**STARD-AI** (diagnostic accuracy), **PROBAST+AI** (risk of bias), and for a prospective/live
evaluation **DECIDE-AI** or **CONSORT-AI / SPIRIT-AI**.

## Part B — Held-out metrics

### Phase 8 — Compute task-correct metrics
Generate and **execute** evaluation code on the held-out predictions (Metrics Reloaded —
Maier-Hein & Reinke et al., *Nat Methods* 2024):
- **segmentation** — Dice/IoU **and** a boundary metric (HD95 / NSD), **per structure**, 95% CIs by
  **patient-level** bootstrap (resample patients, not pixels or slices);
- **classification** — **AUROC and AUPRC** with patient-level bootstrap CIs, sensitivity/specificity,
  and PPV/NPV **at the deployment prevalence**, never bare accuracy on a balanced set. Report AUPRC
  with the test-set prevalence, which is its no-skill value: AUPRC moves with prevalence, so a value
  from an enriched or case-control test set does not carry over to deployment or across datasets. For
  **multiclass**, state the aggregation (one-vs-rest / macro / micro / pairwise / Obuchowski);
- **detection** — **FROC / mAP** with the **IoU match criterion stated**. Lesions and false positives
  cluster within patients, so CIs come from a **patient-level bootstrap** (resample patients, carrying
  all their lesions and false positives), not a Wilson/binomial interval over lesions, which is too
  narrow; compare two detectors' FROC curves with **JAFROC** (RJafroc), not per-lesion tests;
- **interactive / promptable segmentation** (SAM2 / MedSAM2 / nnInteractive) — the segmentation
  metrics **plus** Dice-vs-interactions / number-of-clicks (NoC) to a target threshold,
  initial-vs-converged (or peak) Dice, and per-case interaction/inference time. With two arms
  (simulated prompting + human operator), record **protocol fidelity** — identical prompt types,
  stopping rule, target threshold, seeds — because arm-to-arm comparability is what lets the human arm
  validate the simulated one (human-arm design: `/design-study`);
- **generative / synthesis** — full-reference (MSE/RMSE/PSNR/SSIM) or no-reference (SNR/CNR, visual
  scores) quality **plus a downstream-task evaluation**: image quality is not clinical utility
  (Park et al., *Radiol Med* 2024);
- **time-to-event** discrimination (Harrell's C, time-dependent ROC) → `/analyze-stats`.

Report the headline as the **point estimate with a patient-level bootstrap 95% CI** over the test
cases: that is the uncertainty of the test-set estimate. Seed-to-seed SD across training runs is a
different quantity (training-run variability, usually smaller) — report it separately, over ≥ 5
runs, for a training-recipe or model-comparison claim, and never present it as the CI. A frozen
vendor or open-weights model has no training runs to vary; its uncertainty is the test-set CI. Add
**calibration** — for a binary risk or diagnostic output, calibration-in-the-large (intercept), the
calibration slope and a flexible (loess) calibration curve, plus the Brier score; ECE only as a
supplementary top-label summary for multi-class confidence, with its binning stated — and
**subgroup** slices (the Model Card Factors). Emit `results.md` (metrics report) and a **per-case
CSV** for `/analyze-stats`. Load
`${CLAUDE_SKILL_DIR}/references/metric_guide.md` for the per-task checklist and
`${CLAUDE_SKILL_DIR}/references/metric_selection_grounding.md` for why each pairing is required and
the CLAIM 2024 fit map.

### Phase 9 — Gate the metric choice
```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/check_metric_reporting.py \
  --report results.md --task segmentation|classification|detection|interactive|generative \
  --out qc/metric_reporting.json --strict
```
`PIXEL_ACCURACY_SEG` / `NO_BOUNDARY_METRIC` / `ACCURACY_ONLY` / `DETECTION_METRIC_MISSING` must be zero.

## Part C — Uncertainty, OOD and selective prediction (deployment claims)

A deployment-framed model must say what it does when unsure or off-distribution. Read
`${CLAUDE_SKILL_DIR}/references/uncertainty_guide.md` for method choice and the manifest schema.

### Phase 10 — Choose the uncertainty method, OOD guard and abstention rule
- **Conformal** (MAPIE) — prediction sets/intervals at nominal coverage; the strongest default with a
  calibration set. Its coverage guarantee is finite-sample but needs exchangeability, which can fail
  on clinical data, so **measure** achieved coverage on a test split disjoint from the calibration
  split and report it with its binomial CI — never report it as guaranteed.
- **Deep ensemble** — K ≥ 2 independent members (distinct seeds/inits); shared seeds underestimate
  epistemic uncertainty.
- **MC-dropout** — dropout **active at inference**, T passes; off, every pass is identical and the
  estimate collapses to a point prediction.
- **Bayesian / last-layer Laplace** — a light option.
- **OOD guard** — energy score, feature Mahalanobis, ODIN or max-softmax, **evaluated on a held-out OOD
  set** (different scanner/site/pathology) with detection AUROC and the operating point.
- **Selective prediction** — abstain at a **pre-specified** coverage/risk target; report the
  risk–coverage curve. A post-hoc threshold inflates accuracy-at-coverage.
- **Under shift** — report calibration/coverage on shifted or external data, not in-distribution only
  (Ovadia 2019).

### Phase 11 — Emit and gate the uncertainty manifest
Write `uncertainty_manifest.json`:
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
```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/check_uncertainty_reporting.py --manifest uncertainty_manifest.json \
  --out qc/uncertainty_reporting.json --strict
```
Verdicts: `POINT_PREDICTION_NO_UNCERTAINTY`, `CONFORMAL_NO_COVERAGE_VALIDATION`, `OOD_NO_HELDOUT_SET`
(Major); `ENSEMBLE_NOT_INDEPENDENT`, `MCDROPOUT_DISABLED_AT_INFERENCE`, `SELECTIVE_NO_TARGET`,
`NO_CALIBRATION_UNDER_SHIFT` (Minor). It audits the declared spec; it complements, not replaces,
Phase 8's executed calibration. Report TRIPOD+AI / DECIDE-AI deployment-monitoring fit via `/check-reporting`.

## Part D — Explainability

A saliency / Grad-CAM map is the most over-interpreted artifact in imaging AI: Adebayo et al.
(*NeurIPS* 2018) showed many methods produce convincing maps independent of the model's weights and
labels. Read `${CLAUDE_SKILL_DIR}/references/explainability_guide.md` for method by architecture,
sanity checks, localisation metrics and framing.

### Phase 12 — Produce, sanity-check and quantify the maps
Choose the method for the architecture — Grad-CAM / Grad-CAM++ for CNNs, attention rollout for ViTs,
integrated gradients / SHAP for attribution — wired through captum or pytorch-grad-cam. Run the
Adebayo **model-parameter** and **data (label) randomisation** tests; a faithful map degrades when
they are randomised, and both axes are the minimum bar. If the map is claimed to localise the finding,
compute IoU / pointing game / Dice against ground-truth masks **over the cohort** — not eyeballed,
cherry-picked cases. Frame a map as **attribution** ("where signal is attributed"), never as proof the
model is correct or of causation.

### Phase 13 — Emit and gate the explainability report
Write `explainability_report.json`:
```json
{
  "method": "grad-cam++",
  "n_examples": 200,
  "cohort_level": true,
  "localization_metric": "iou",
  "localization_value": 0.63,
  "sanity_checks": ["model_randomization", "data_randomization"],
  "interpretation": "localization"
}
```
`interpretation`: `attribution` / `localization` / `faithfulness` — never `validation` / `causal`.
```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/check_explainability_report.py --manifest explainability_report.json \
  --out qc/explainability_report.json --strict
```
Verdicts: `SALIENCY_AS_VALIDATION`, `NO_SANITY_CHECK`, `NO_LOCALIZATION_METRIC` (Major);
`INSUFFICIENT_SANITY`, `CHERRY_PICKED_EXAMPLES`, `MISSING_METHOD` (Minor).

## Outputs and hand-off

- Part A: validation-design decision notes (leakage, tier, comparator, metric, sizing handoff, reporting
  fit) and `qc/split_leakage.json`.
- Part B: `results.md`, the per-case CSV, and `qc/metric_reporting.json`.
- Part C: `uncertainty_manifest.json` + `qc/uncertainty_reporting.json`.
- Part D: `explainability_report.json` + `qc/explainability_report.json`.

The per-case table → `/analyze-stats` (paired ΔAUC of frozen models on the same test patients —
DeLong or bootstrap; added value over a baseline per `incremental_value.md`; decision curves;
publication tables);
figures → `/make-figures`; numbers and subgroup performance → `/model-card`; Methods/Results →
`/write-paper`; compliance → `/check-reporting`; sizing → `/calc-sample-size`; the reviewer-side audit
of the draft → `/self-review`, whose `ai_overclaiming` / `image_synthesis` probes also check saliency
claims. Gate regression (`${CLAUDE_SKILL_DIR}/`): `scripts/check_split_leakage_challenge/verify.sh`,
`scripts/metric_reporting_challenge/verify.sh`, `scripts/check_uncertainty_reporting_challenge/verify.sh`,
`scripts/check_explainability_report_challenge/verify.sh`, and `tests/test_*.sh`.
