<!-- AUTO-GENERATED from skills/model-assessment/SKILL.md by scripts/gen_skill_docs.py. Do not edit by hand. -->

# model-assessment

> Use when validating or evaluating a trained medical-imaging model. Audits split leakage and validation design, computes task-correct held-out metrics (Dice + HD95, AUROC + AUPRC, FROC, calibration), and covers uncertainty/OOD and Grad-CAM explainability, each with a gate.

**Invoke:** `/model-assessment`

## When to use

`model-assessment` activates on requests such as: model validation, validate AI model, imaging model validation, data leakage, split leakage, train test split, patient-level split, internal validation, external validation, validation design, leakage audit, segmentation model validation, classification model validation, detection model validation, nnU-Net validation, deep learning validation, CLAIM 2024, generalizability, held-out test set, model evaluation, held-out metrics, test set metrics, Dice, HD95, NSD, surface distance, Metrics Reloaded, AUROC, AUPRC, bootstrap CI, calibration, ECE, reliability diagram, subgroup analysis, slice metrics, mAP, FROC, segmentation metrics, detection metrics, evaluate predictions, interactive segmentation, promptable segmentation, SAM2, MedSAM2, nnInteractive, number of clicks, NoC, interactions-to-threshold, click budget, generative metrics, image synthesis, SSIM, PSNR, SNR, CNR, downstream task, multiclass classification, Obuchowski index, Harrell's C, time-dependent ROC, uncertainty, uncertainty quantification, UQ, epistemic, aleatoric, MC-dropout, monte carlo dropout, deep ensemble, conformal prediction, split conformal, prediction interval, coverage, calibration under shift, out-of-distribution, OOD detection, distribution shift, Mahalanobis, energy score, ODIN, selective prediction, abstention, reject option, deployment safety, DECIDE-AI, predictive uncertainty, explainability, interpretability, saliency, saliency map, grad-cam, gradcam, grad-cam++, attention map, attention rollout, integrated gradients, captum, pytorch-grad-cam, heatmap, class activation map, CAM, feature attribution, sanity check, Adebayo, model randomization, localization metric, pointing game, IoU with ground truth, XAI, explainable AI, model looks at, faithfulness.

## Quality Card

**Purpose** — Catch the structural validity failures of an engineer-built imaging model's evaluation — patient-level leakage, tuning on the test set, an internal split sold as external validation, a single-run or task-incorrect headline metric — and, where the claim reaches deployment or interpretability, the point predictions, unmeasured coverage, unvalidated OOD guard, or unsanity-checked saliency map that would otherwise reach a clinical manuscript.

**Safety boundaries**

- Numbers come only from code executed on the supplied predictions or from the researcher's executed UQ/XAI code; never hand-typed, and never from running a model on real patient data.
- Every gate verdict is reproduced by a stdlib script (set arithmetic on patient IDs, rules on the metrics report or a manifest), never asserted from prose; the skill never alters predictions, splits, maps or coverage.
- Integrates MONAI / nnU-Net / MAPIE / captum / pytorch-grad-cam / OOD scorers by reference; it does not reimplement or replace them.

**Known limitations**

- The split-leakage gate sees only the split table it is given; leakage in upstream preprocessing is imaging-data's gate.
- The metric gate checks the reported metric choice; comparative inference (DeLong / NRI / IDI / decision curves / MRMC) is analyze-stats, and metric correctness depends on a correctly defined analysis unit.
- The uncertainty and explainability gates audit the declared manifests, not the executed code; a mislabelled field (unvalidated coverage recorded as validated, an unrun sanity check recorded as run) can hide a real gap.
- Clean audits are necessary, not sufficient: they audit the evaluation, not the model's clinical safety; prospective deployment monitoring (DECIDE-AI) still governs a clinical claim.

**Validation**

- `python3 scripts/check_split_leakage.py --splits <split_assignment.csv> --strict`
- `python3 scripts/check_metric_reporting.py --report <results.md> --task segmentation|classification|detection|interactive|generative --strict`
- `python3 scripts/check_metric_reporting.py --manifest metrics_manifest.json --strict  # preferred: declared metrics (templates/metrics_manifest.json)`
- `python3 scripts/check_uncertainty_reporting.py --manifest <uncertainty_manifest.json> --strict`
- `python3 scripts/check_explainability_report.py --manifest <explainability_report.json> --strict`
- `bash scripts/check_split_leakage_challenge/verify.sh  # deterministic, network-free`
- `bash scripts/metric_reporting_challenge/verify.sh  # deterministic, network-free`
- `bash scripts/check_uncertainty_reporting_challenge/verify.sh  # deterministic, network-free`
- `bash scripts/check_explainability_report_challenge/verify.sh  # deterministic, network-free`

**Evidence** — `ci_validator`

## Bundled resources

**References** (`skills/model-assessment/references/`):

- `explainability_guide.md`
- `metric_guide.md`
- `metric_selection_grounding.md`
- `metrics_manifest_schema.md`
- `uncertainty_guide.md`
- `validation_design.md`

**Scripts** (`skills/model-assessment/scripts/`):

- `check_explainability_report.py`
- `check_explainability_report_challenge/` (6 files)
- `check_metric_reporting.py`
- `check_split_leakage.py`
- `check_split_leakage_challenge/` (7 files)
- `check_uncertainty_reporting.py`
- `check_uncertainty_reporting_challenge/` (6 files)
- `metric_reporting_challenge/` (17 files)

**Templates** (`skills/model-assessment/templates/`):

- `metrics_manifest.json`

## Source

Canonical definition: [`skills/model-assessment/SKILL.md`](../../skills/model-assessment/SKILL.md)

---

*Part of [MedSci Skills](../../README.md) — Claude Code skills for the medical research lifecycle. This page is generated from the skill's `SKILL.md`; edit that file and re-run `scripts/gen_skill_docs.py`.*
