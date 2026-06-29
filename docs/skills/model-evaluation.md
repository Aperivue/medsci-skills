<!-- AUTO-GENERATED from skills/model-evaluation/SKILL.md by scripts/gen_skill_docs.py. Do not edit by hand. -->

# model-evaluation

> Compute and report task-correct held-out metrics for a trained medical-imaging model — segmentation (Dice plus a boundary metric such as HD95 or NSD, per structure), classification (AUROC plus AUPRC and sensitivity/specificity with bootstrap CIs at the deployment prevalence), or detection (FROC or mAP with a stated IoU criterion) — plus calibration and subgroup slices. Emits a per-case results table that analyze-stats turns into publication tables, and gates the metric choice against Metrics Reloaded and CLAIM 2024 (no pixel accuracy for segmentation, no bare accuracy under imbalance). Numbers come only from executed code, never hand-typed.

**Invoke:** `/model-evaluation` · **Tools:** Read, Write, Edit, Bash, Grep, Glob · **Model:** inherit

## When to use

`model-evaluation` activates on requests such as: model evaluation, held-out metrics, test set metrics, Dice, HD95, NSD, surface distance, Metrics Reloaded, AUROC, AUPRC, bootstrap CI, calibration, ECE, reliability diagram, subgroup analysis, slice metrics, mAP, FROC, segmentation metrics, detection metrics, evaluate predictions.

## Quality Card

**Purpose** — Make a medical-imaging model's held-out evaluation task-correct and honest — the right metric for the task and prevalence, with uncertainty, calibration, and subgroup performance — and emit a per-case table the publication statistics (analyze-stats) build on.

**Safety boundaries**

- Numbers come only from executed code on the supplied predictions; never hand-typed.
- The metric choice is gated by a stdlib script against Metrics Reloaded / CLAIM 2024; a pixel-accuracy or bare-accuracy headline is flagged, not emitted silently.

**Known limitations**

- It produces the per-case metrics; the comparative inference (DeLong / NRI / IDI / decision curves / MRMC) is analyze-stats.
- Metric correctness depends on a correctly defined analysis unit and a clean held-out split (use model-validation first).

**Validation**

- `python3 scripts/check_metric_reporting.py --report <results.md> --task segmentation|classification|detection --strict`
- `bash scripts/metric_reporting_challenge/verify.sh  # deterministic, network-free`

**Evidence** — `ci_validator`

## Bundled resources

**References** (`skills/model-evaluation/references/`):

- `metric_guide.md`
- `metric_selection_grounding.md`

**Scripts** (`skills/model-evaluation/scripts/`):

- `check_metric_reporting.py`
- `metric_reporting_challenge/` (8 files)

## Source

Canonical definition: [`skills/model-evaluation/SKILL.md`](../../skills/model-evaluation/SKILL.md)

---

*Part of [MedSci Skills](../../README.md) — Claude Code skills for the medical research lifecycle. This page is generated from the skill's `SKILL.md`; edit that file and re-run `scripts/gen_skill_docs.py`.*
