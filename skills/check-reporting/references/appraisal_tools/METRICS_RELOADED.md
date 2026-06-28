# Metrics Reloaded — metric-selection appraisal reference

An **appraisal / selection** reference (deliberately **not** a counted reporting checklist —
the same treatment as `METRICS.md`). It summarises the metric-selection guidance of
**Metrics Reloaded** (Maier-Hein, Reinke et al., "Metrics reloaded: recommendations for
image analysis validation," *Nature Methods* 2024, CC BY) and its **pitfalls** companion
(Reinke et al., *Nature Methods* 2024), for choosing the right validation metric for an
image-analysis task. Consumed by `/model-evaluation` (`check_metric_reporting.py`),
`/model-validation` (MD6), and the `model_development` probe.

> Verify wording against the papers before quoting them as a formal instrument; the points
> below are the load-bearing recommendations, phrased for medical imaging.

## Pick the metric from the problem, not habit
Metrics Reloaded frames metric choice by the **problem category** (image-level
classification, semantic segmentation, instance segmentation, object detection) and the
**domain interest** (is boundary accuracy important? are small structures clinically
critical? is the data imbalanced?). The metric should reflect what a clinical error costs.

## Common pitfalls it warns against
- **Segmentation**: Dice/IoU alone is overlap-only and **insensitive to boundary error** and
  unstable on **small structures**; pair it with a **boundary metric** (HD95 / NSD) and report
  **per structure**. Define behaviour for **empty references** (Dice 0/0 is undefined).
- **Classification under imbalance**: **accuracy is misleading**; use threshold-independent
  discrimination (**AUROC**) plus **AUPRC** (minority class), and prevalence-dependent **PPV/NPV
  at the deployment base rate** — not a balanced set.
- **Object detection**: report **FROC / mAP with the IoU match criterion stated**; an unstated
  match threshold makes the metric undefined.
- **Aggregation**: a single global mean hides per-case/per-structure failure; report the
  distribution and handle missing values explicitly.

## Use in the lane
- `/model-evaluation` computes the recommended metric set with CIs and gates the report with
  `check_metric_reporting.py`.
- `/model-validation` MD6 and the `model_development` probe flag a metric-vs-task mismatch.
- Reporting compliance of the manuscript stays with CLAIM 2024 / TRIPOD+AI in `/check-reporting`.
