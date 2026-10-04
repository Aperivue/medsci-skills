# Challenge card — task-correct metric reporting (model-assessment)

## Problem
The metric must match the task and the prevalence. The recurrent failures are a
**segmentation** result reported as **pixel accuracy** or **Dice alone** (overlap is
shape-insensitive and penalises the same boundary error far more on small structures;
pixel accuracy is meaningless on an imbalanced mask), a
**classification** result reported as **bare accuracy** on a balanced set (prevalence-
dependent, hides minority-class failure), and a **detection** result with no FROC/mAP or
no stated IoU criterion. These pass a prose read but are caught by Metrics Reloaded
(Maier-Hein & Reinke et al., *Nat Methods* 2024) and CLAIM 2024.

## What the gate does
`scripts/check_metric_reporting.py` is a conservative presence linter: given a results
section and the task, it flags when the reported metric set is wrong for the task
(`NO_BOUNDARY_METRIC`, `PIXEL_ACCURACY_SEG`, `ACCURACY_ONLY`, `AUPRC_MISSING`,
`DETECTION_METRIC_MISSING`) or carries no uncertainty (`CI_MISSING`). It checks which
metrics are named, not their values — it never recomputes a number.

## Fixture (synthetic only — no real results)
- `fixture/seg_bad.md` — Dice + pixel accuracy, no boundary metric, no CI.
- `fixture/seg_good.md` — Dice + HD95 per structure, with 95% CIs.
- `fixture/clf_bad.md` — accuracy on a balanced set, no AUROC.
- `fixture/clf_good.md` — AUROC + AUPRC + sensitivity/specificity with CIs.

## Expected (`verify.sh`, network-free)
- `seg_bad` flags `NO_BOUNDARY_METRIC` + `PIXEL_ACCURACY_SEG`; `seg_good` passes.
- `clf_bad` flags `ACCURACY_ONLY`; `clf_good` passes.

## Manifest mode
`fixture/manifest_*.json` declare the same mismatches as `metrics_manifest.json` fields
(`--manifest`): Dice + pixel accuracy without a boundary metric, FROC without a match criterion,
accuracy + sensitivity without specificity or AUROC. Each is flagged; `manifest_seg_good.json`
passes; an off-list metric exits 2. A declared list is not misread by negation ("FROC was not
performed") or by word sense ("saliency map", the Decathlon "MSD").
A declaration with no headline metric (classification with none of accuracy / AUROC / AUPRC /
sensitivity / specificity / PPV / NPV; segmentation with neither Dice nor IoU) is flagged
`CLASSIFICATION_METRIC_MISSING` / `SEGMENTATION_METRIC_MISSING` (Major) instead of passing; Minor
when only an `other:` metric is declared, since it may be the headline metric under another name.
