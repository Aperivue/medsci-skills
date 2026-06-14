# Exemplar anatomy — calibration plot (risk-prediction model)

A worked **anatomy model** for a calibration figure — the probability counterpart to the ROC/PR
discrimination plot. Complements the `critic_rubrics/data_plot.md` §C / §G calibration checks
(this composes; the rubric scores). Synthetic — describes *what each element must show* and the
errors to avoid; not an image to copy. Pairs with `analyze-stats` `templates/dca_plot.R` and the
TRIPOD+AI / `exemplar_plots/roc_pr.md` discrimination side.

## Elements
- **Predicted probability (x) vs observed frequency (y)**, both 0–1, with the **45° ideal line**.
- A **smooth/flexible calibration curve** (loess or restricted cubic spline) rather than only a
  handful of binned points — binning into deciles hides shape and is sensitive to the cut-points.
- **Calibration slope and intercept** reported in the panel: slope < 1 signals overfitting
  (extreme predictions too extreme); the **intercept is calibration-in-the-large** (mean predicted
  vs mean observed risk), and intercept ≠ 0 signals systematic over/under-prediction.
- A **distribution of predicted risks** (rug/histogram under the axis), so the reader sees where
  the data actually live — calibration in a region with no patients is uninformative.
- **On the validation/external set**, not the development set; with a CI band on the curve.

## Discipline (what the figure must not do)
- **Do not present discrimination (AUROC) as evidence of calibration** — a model can rank well yet
  be systematically miscalibrated; both are required when a probability drives a decision.
- **Do not rely on the Hosmer–Lemeshow test alone** — it is low-powered, depends on arbitrary
  grouping, and a non-significant p is not evidence of good calibration; show the curve + slope/
  intercept.
- **Do not extrapolate** the curve into probability ranges with no observations (see the rug).
- If recalibration was applied, say so and show calibration **after** it on held-out data.
- Where a threshold/decision is proposed, pair calibration with a **decision-curve (net-benefit)**
  analysis.

## Common omission
- The **slope/intercept**, the **predicted-risk distribution**, and **calibration on the external
  set** — the elements calibration figures most often drop, and the ones that decide whether the
  probabilities can be trusted at the bedside. Cross-reference `critic_rubrics/data_plot.md` §C/§G,
  the `peer-review/references/exemplar_reviews/calibration_missing.md` finding, and `analyze-stats`
  `templates/dca_plot.R`.
