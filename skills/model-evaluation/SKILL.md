---
name: model-evaluation
description: >
  Compute and report task-correct held-out metrics for a trained medical-imaging model — segmentation
  (Dice plus a boundary metric such as HD95 or NSD, per structure), classification (AUROC plus AUPRC and
  sensitivity/specificity with bootstrap CIs at the deployment prevalence), or detection (FROC or mAP with
  a stated IoU criterion) — plus calibration and subgroup slices. Emits a per-case results table that
  analyze-stats turns into publication tables, and gates the metric choice against Metrics Reloaded and
  CLAIM 2024 (no pixel accuracy for segmentation, no bare accuracy under imbalance). Numbers come only
  from executed code, never hand-typed.
triggers: model evaluation, held-out metrics, test set metrics, Dice, HD95, NSD, surface distance, Metrics Reloaded, AUROC, AUPRC, bootstrap CI, calibration, ECE, reliability diagram, subgroup analysis, slice metrics, mAP, FROC, segmentation metrics, detection metrics, evaluate predictions
tools: Read, Write, Edit, Bash, Grep, Glob
model: inherit
---

# Model-Evaluation Skill

## Purpose

This skill makes a medical-imaging model's **held-out evaluation task-correct and honest**: the right
metric for the task and the prevalence, with uncertainty, calibration, and subgroup performance. It
emits a **per-case metric table** that the publication statistics build on, and gates the metric choice
against Metrics Reloaded (Maier-Hein & Reinke et al., *Nat Methods* 2024) and CLAIM 2024.

It sits between `/model-validation` (which audits the split / design) and `/analyze-stats` (which owns
the comparative inference). It computes the imaging-specific per-case metrics (surface distances, FROC,
ECE of a softmax head); `/analyze-stats` owns DeLong / NRI / IDI / decision curves / MRMC. Like
`/analyze-stats`, it **generates and executes** code on your predictions — numbers are never hand-typed.

## When to use
- You have held-out predictions + ground truth and need task-correct metrics with CIs, calibration, and
  subgroup slices, plus a per-case table for the manuscript statistics.

## When NOT to use
- Auditing the validation design / leakage → `/model-validation`.
- DeLong / NRI / IDI / decision curves / MRMC reader study → `/analyze-stats`.
- Building / training the model → `/model-scaffold`; LLM / MLLM → `/mllm-eval`.
- Figure rendering → `/make-figures`.

## Workflow

### Phase 1 — Fix the analysis unit and the task
State the task (segmentation / classification / detection) and the **analysis unit** the metric must
respect (per-patient vs per-lesion vs per-image). A per-lesion metric must not be reported as
per-patient.

### Phase 2 — Compute task-correct metrics
Generate evaluation code that computes, on the held-out predictions:
- **segmentation**: Dice/IoU **and** a boundary metric (HD95 / NSD), **per structure** not only a global
  mean, with bootstrap 95% CIs.
- **classification**: **AUROC and AUPRC** with bootstrap CIs, sensitivity/specificity, and PPV/NPV **at
  the deployment prevalence** (not a balanced set).
- **detection**: **FROC / mAP** with the **IoU match criterion stated**.
Add **calibration** (reliability diagram / ECE) and **subgroup** slices (the Model Card Factors).
See `${CLAUDE_SKILL_DIR}/references/metric_guide.md`. Emit a **per-case CSV** for `/analyze-stats`.

### Phase 3 — Gate the metric choice (deterministic)
```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/check_metric_reporting.py \
  --report results.md --task segmentation|classification|detection --strict
```
`PIXEL_ACCURACY_SEG` / `NO_BOUNDARY_METRIC` / `ACCURACY_ONLY` / `DETECTION_METRIC_MISSING` must be zero.

### Phase 4 — Hand off
The per-case table → `/analyze-stats` (DeLong / NRI / IDI / decision curves, publication tables);
figures → `/make-figures`; the numbers + subgroup performance → `/model-card`; Methods/Results →
`/write-paper`; compliance → `/check-reporting`.

## Anti-Hallucination

- **Never fabricate a metric value.** Every number comes from executed code on the supplied predictions;
  if predictions or ground truth are missing, say so and stop — do not invent a result.
- **Never report pixel/voxel accuracy for segmentation or bare accuracy under imbalance** — the gate
  flags these; report Dice + a boundary metric, or AUROC + AUPRC with CIs.
- **Never report a per-lesion metric as if it were per-patient** — respect the analysis unit.
- If a metric definition or its CI method is uncertain, flag `[VERIFY]` and ask.

## Deterministic gate
`scripts/check_metric_reporting.py` — flags a task-metric mismatch / missing uncertainty (stdlib,
network-free). Reproducible challenge: `bash ${CLAUDE_SKILL_DIR}/scripts/metric_reporting_challenge/verify.sh`.

## Reference Files

Load on demand (keep SKILL.md short):
- `${CLAUDE_SKILL_DIR}/references/metric_guide.md` — operational checklist: the task-correct metric
  per task (segmentation Dice + HD95/NSD per structure; classification AUROC + AUPRC + sens/spec at
  deployment prevalence; detection FROC/mAP with a stated IoU), plus calibration, subgroup slices,
  run-variance, and the per-case CSV hand-off.
- `${CLAUDE_SKILL_DIR}/references/metric_selection_grounding.md` — the standards grounding behind
  those choices: the Metrics Reloaded task-fingerprint principle, why each metric pairing is
  required, calibration vs discrimination, disaggregated reporting, and the CLAIM 2024
  reporting-fit map (`/check-reporting` owns the item audit).

## Boundaries

```
model-validation (design) -> model-evaluation (this skill: per-case task-correct metrics + CIs)
  -> analyze-stats (DeLong / NRI / IDI / decision curves, publication tables) -> make-figures
  -> model-card (numbers + subgroup) -> write-paper + check-reporting
```
