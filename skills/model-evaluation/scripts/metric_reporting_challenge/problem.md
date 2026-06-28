# Challenge card — task-correct metric reporting (model-evaluation)

## Problem
The metric must match the task and the prevalence. The recurrent failures are a
**segmentation** result reported as **pixel accuracy** or **Dice alone** (overlap is
shape- and size-insensitive; pixel accuracy is meaningless on an imbalanced mask), a
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
