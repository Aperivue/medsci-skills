# metrics_manifest.json — declared metrics (model-assessment, Part B)

`check_metric_reporting.py --manifest metrics_manifest.json` reads the reported metrics as
structured fields instead of searching the results prose. A keyword search with a short negation
window misreads "we did not compute the Hausdorff distance or HD95", "FROC was not performed", a
"saliency map" as mAP, or the Medical Segmentation Decathlon ("MSD") as a surface distance; a
declared list does not. The gate checks **what is declared, not the reported numbers** — keep the
manifest in step with the Results.

Start from `templates/metrics_manifest.json`. Values are compared case-insensitively, with `-` and
spaces read as `_`; common synonyms are folded (`jaccard`→`iou`, `dsc`→`dice`, `hd`→`hausdorff`,
`auc`/`roc_auc`→`auroc`, `average_precision`/`pr_auc`→`auprc`, `mean_average_precision`→`map`,
`recall`→`sensitivity`, `precision`→`ppv`, `one_vs_one`→`pairwise`). Every value must be on the
field's allow-list, `none`, or `other:<description>` (a Minor `UNLISTED_METHOD`). Any other value, a
wrong type, a non-finite number, or an unknown key exits 2 and names the field. A field left out
counts as not reported.

| Field | Type | Allowed values | Used by |
|---|---|---|---|
| `task` | string | `segmentation`, `classification`, `detection`, `interactive`, `generative` | which checks run; exit 2 if missing and no `--task` |
| `metrics` | list | overlap `dice`, `iou`; boundary `hd95`, `hausdorff`, `nsd`, `surface_distance`; `pixel_accuracy`; `accuracy`, `auroc`, `auprc`, `sensitivity`, `specificity`, `ppv`, `npv`, `f1`; calibration `brier`, `calibration_slope`, `calibration_intercept`, `ece`; detection `froc`, `map`; interactive `noc`; similarity `mse`, `rmse`, `mae`, `psnr`, `ssim`, `snr`, `cnr`; `likert_visual_score` | every task (see below); an `other:` metric is recorded but satisfies no check |
| `ci_reported` | bool | | `CI_MISSING` (Minor) unless `true` |
| `classification.n_classes` | int ≥ 2 | | `MULTICLASS_NO_AVERAGING` when > 2 |
| `classification.averaging` | list | `one_vs_rest`, `macro`, `micro`, `pairwise`, `obuchowski` | `MULTICLASS_NO_AVERAGING` (Minor) |
| `detection.match_criterion` | string | `iou_threshold`, `centroid_threshold`, `mask_threshold` | `DETECTION_METRIC_MISSING` (Major) when absent |
| `detection.threshold` | number ≥ 0 | | recorded, not gated |
| `interactive.interaction_axis` | list | `dice_vs_interactions`, `interactions_to_threshold` | `INTERACTIVE_NO_INTERACTION_COUNT` (Major) |
| `interactive.initial_vs_converged` | bool | | `INTERACTIVE_NO_CONVERGENCE` (Minor) unless `true` |
| `interactive.per_case_time` | bool | | `INTERACTIVE_NO_TIME` (Minor) unless `true` |
| `generative.downstream_task` | list | `segmentation`, `detection`, `classification`, `quantitative_measurement` | `GENERATIVE_NO_DOWNSTREAM` (Major) |
| `notes` | any | free text, not read | — |

Checks by task (verdicts and severities as in prose mode):
- **segmentation / interactive** — `pixel_accuracy` declared → `PIXEL_ACCURACY_SEG` (Major);
  `dice` or `iou` without a boundary metric → `NO_BOUNDARY_METRIC` (Major).
- **interactive** — also the three interactive fields above.
- **classification** — `accuracy` without `auroc` and without both `sensitivity` and `specificity` →
  `ACCURACY_ONLY` (Major); `auroc` without `auprc` → `AUPRC_MISSING` (Minor); `n_classes` > 2 with
  `accuracy` or `auroc` and no averaging → `MULTICLASS_NO_AVERAGING` (Minor).
- **detection** — neither `froc` nor `map` → `DETECTION_METRIC_MISSING` (Major); one of them with no
  match criterion → the same verdict.
- **generative** — a similarity metric without a downstream task → `GENERATIVE_NO_DOWNSTREAM`
  (Major); no similarity metric → `GENERATIVE_NO_SIMILARITY` (Minor).

Every allow-listed value is named in `metric_guide.md` or `metric_selection_grounding.md`. An
`other:` value in a scheme field (averaging, match criterion, interaction axis, downstream task)
counts as covering that field; read each one by eye.
