# metrics_manifest.json — declared metrics (model-assessment, Part B)

`check_metric_reporting.py --manifest metrics_manifest.json` reads the reported metrics as
structured fields instead of searching the results prose. A keyword search with a short negation
window misreads "we did not compute the Hausdorff distance or HD95", "FROC was not performed", a
"saliency map" as mAP, or the Medical Segmentation Decathlon ("MSD") as a surface distance; a
declared list does not. The gate checks **what is declared, not the reported numbers** — keep the
manifest in step with the Results.

Start from `templates/metrics_manifest.json`. Values are compared case-insensitively, with `-` and
spaces read as `_`; common synonyms are folded (`jaccard`→`iou`, `dsc`→`dice`, `hd`→`hausdorff`,
`auc`/`roc_auc`→`auroc`, `pr_auc`→`auprc`, `mean_average_precision`→`map`, `recall`→`sensitivity`,
`precision`→`ppv`, `one_vs_one`→`pairwise`, `assd`/`masd`→`surface_distance`, `surface_dice`→`nsd`,
`sensitivity_per_false_positive`→`froc`). "Average precision" is not folded: it is AUPRC for a
classifier but the detection AP, so write `auprc` or `map`. Every value must be on the
field's allow-list, `none`, or `other:<description>` (a Minor `UNLISTED_METHOD`). Any other value, a
wrong type, a non-finite number anywhere in the file, or an unknown key exits 2 and names the
field. A field left out counts as not reported. Only the sub-object of the declared `task` is used;
the others are validated but not read.

| Field | Type | Allowed values | Used by |
|---|---|---|---|
| `task` | string | `segmentation`, `classification`, `detection`, `interactive`, `generative` | which checks run; exit 2 if missing and no `--task` |
| `metrics` | list | overlap `dice`, `iou`; boundary `hd95`, `hausdorff`, `nsd`, `surface_distance`; `pixel_accuracy`; `accuracy`, `auroc`, `auprc`, `sensitivity`, `specificity`, `ppv`, `npv`; calibration `brier`, `calibration_slope`, `calibration_intercept`, `ece`; detection `froc`, `map`; interactive `noc`; similarity `mse`, `rmse`, `mae`, `psnr`, `ssim`, `snr`, `cnr`; `likert_visual_score` | the checks below; `ppv`, `npv`, `brier`, `calibration_*`, `ece` and `likert_visual_score` are recorded, not gated; an `other:` metric is recorded but satisfies no check |
| `ci_reported` | bool | | `CI_MISSING` (Minor) unless `true` |
| `classification.n_classes` | int ≥ 2 | | `MULTICLASS_NO_AVERAGING` when > 2 |
| `classification.averaging` | list | `one_vs_rest`, `macro`, `micro`, `pairwise`, `obuchowski` | `MULTICLASS_NO_AVERAGING` (Minor) |
| `detection.match_criterion` | string | `iou_threshold`, `centroid_threshold`, `mask_threshold` | `DETECTION_METRIC_MISSING` (Major) when absent |
| `detection.threshold` | number ≥ 0 | | recorded, not gated |
| `interactive.interaction_axis` | list | `dice_vs_interactions`, `interactions_to_threshold` | `INTERACTIVE_NO_INTERACTION_COUNT` (Major) unless this or the metric `noc` is declared |
| `interactive.initial_vs_converged` | bool | | `INTERACTIVE_NO_CONVERGENCE` (Minor) unless `true` |
| `interactive.per_case_time` | bool | | `INTERACTIVE_NO_TIME` (Minor) unless `true` |
| `generative.downstream_task` | list | `segmentation`, `detection`, `classification`, `quantitative_measurement` | `GENERATIVE_NO_DOWNSTREAM` (Major) |
| `notes` | any | free text, not read | — |

Checks by task (verdicts and severities as in prose mode, plus the two headline-metric verdicts,
which run in manifest mode only because a declared list makes the absence certain):
- **segmentation / interactive** — neither `dice` nor `iou` declared → `SEGMENTATION_METRIC_MISSING`
  (Major); `pixel_accuracy` declared → `PIXEL_ACCURACY_SEG` (Major);
  `dice` or `iou` without a boundary metric → `NO_BOUNDARY_METRIC` (Major).
- **interactive** — also the three interactive fields above (the metric `noc` counts as an interaction axis).
- **classification** — none of `accuracy`, `auroc`, `auprc`, `sensitivity`, `specificity`, `ppv`,
  `npv` declared → `CLASSIFICATION_METRIC_MISSING` (Major; calibration metrics alone do not count);
  `accuracy` without `auroc` and without both `sensitivity` and `specificity` →
  `ACCURACY_ONLY` (Major); `auroc` without `auprc` → `AUPRC_MISSING` (Minor); `n_classes` > 2 with
  `accuracy` or `auroc` and no averaging → `MULTICLASS_NO_AVERAGING` (Minor).
- **detection** — neither `froc` nor `map` → `DETECTION_METRIC_MISSING` (Major); one of them with no
  match criterion → the same verdict.
- **generative** — a similarity metric without a downstream task → `GENERATIVE_NO_DOWNSTREAM`
  (Major); no similarity metric → `GENERATIVE_NO_SIMILARITY` (Minor).

Both headline-metric verdicts drop to Minor when an `other:` metric is declared, since it may be
the headline metric under a name the list does not carry.

The final line states only what was checked, marked as declared: `OK (as declared): no
metric-reporting issue found by the <task> checks.` when nothing fired, `No Major issue (as
declared): N Minor (see table).` when only Minors did. The `--out` JSON carries `"basis":
"declared"` (prose-mode JSON has no `basis` key).

Not on the list (write `other:` and check by eye): boundary IoU / boundary F1, NRMSE, a weighted
average. Every allow-listed value is named in `metric_guide.md` or `metric_selection_grounding.md`. An
`other:` value in a scheme field (averaging, match criterion, interaction axis, downstream task)
counts as covering that field; read each one by eye.
