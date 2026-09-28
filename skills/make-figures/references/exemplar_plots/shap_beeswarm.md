# Exemplar anatomy — SHAP summary (beeswarm) feature-attribution plot

A worked **anatomy model** for the SHAP beeswarm — the default feature-attribution figure of a
medical prediction-model paper, answering "which features moved this model's prediction, and in
which direction". It complements `critic_rubrics/data_plot.md` §G, whose five Medical-AI items
cover discrimination, calibration, subgroup performance, colour and clinical utility but stop
short of attribution. Where `model_comparison_leaderboard.md` reads *across models on one cohort*,
this figure reads *across features on one model*. Synthetic — describes *what each element must
show* and the errors to avoid; not an image to copy, no real citations.

## Elements
- **Y-axis = features, ordered by mean |SHAP value|** — state the ordering in the caption, because
  the ordering *is* the claim. **X-axis = the SHAP value** for the **output being explained** (the
  predicted probability or log-odds, and **for which class** on a classifier), with a **vertical
  line at 0** separating features that push the prediction up from those that push it down.
- **Colour = the feature's own value**, low → high, on a sequential scale, with the **clipping
  range stated in the caption** (a 5th–95th percentile cap is the usual choice) — otherwise one
  outlier value owns the legend and the remaining cases read as a single shade.
- **Every explained instance plotted.** The load-bearing content is the **spread** per feature, not
  its centre: a bar chart of mean |SHAP| is a different and much weaker figure, because it cannot
  show a feature that is small on average but decisive for a subgroup.
- **Direction consistency readable off the plot.** A feature whose high values sit on one side only
  is directionally consistent; a feature whose colours **split across both sides of 0** is
  interaction- or context-dependent and must not be described as monotonic.
- **Caption states the explainer and its assumptions** — explainer type (exact tree vs kernel /
  sampling), the **background or reference distribution** the expected value is taken against, and
  the **number of instances explained** — plus that attribution is **model-conditional**: it
  describes *this fitted model*, not the data and not the pathophysiology.
- **Presented alongside, not instead of, the other two model views** — discrimination
  (`roc_pr.md`) and calibration (`calibration_plot.md`). Attribution is a third view and substitutes
  for neither.

## Discipline (what the figure must not do)
- **Do not read SHAP values as causal effects, or as a variable-importance ranking that licenses
  clinical action.** SHAP attributes the *model's* output, and where predictors are **correlated
  the credit is split arbitrarily among them** — so the ranking is a statement about this model's
  sensitivity, not a stable claim about the predictors. Same discipline as
  `model_comparison_leaderboard.md`'s ranking-honesty rule.
- **Do not present a bare global ordering with no uncertainty** — bootstrap the explained set and
  show whether the ordering is stable, or state plainly that no interval is available. An
  unadorned beeswarm invites reading small differences in mean |SHAP| as meaningful.
- **Do not let the beeswarm answer a question it cannot.** It explains one model on one output: it
  cannot show *why the model beat a comparator* (`model_comparison_leaderboard.md`), *why a
  subgroup was disadvantaged* (`external_validation_comparison.md`), or *why performance dropped
  externally* (`external_validation_comparison.md` again) — those are the across-model and
  across-cohort axes.
- **Do not treat a large |SHAP| value as a large effect on the patient's risk** — the SHAP scale and
  the outcome scale are different units; keep them in separate panels with separate axes.
- **Do not colour by a feature with missing or imputed values without saying so** — the unattributed
  missingness bucket is silently read as "the model simply ignores missing data".

## Common omission
- The **stated mean-|SHAP| ordering**, the **zero line with the explained class named**, the
  **per-feature spread rather than a mean**, and the **explainer + background + n in the caption** —
  what this figure most often drops, and what turns a decorative cloud into evidence. A bare,
  unannotated beeswarm is among the most over-read figures in a medical-AI paper, because it looks
  quantitative and carries no statement of what was explained. Cross-reference
  `critic_rubrics/data_plot.md` §G, `analyze-stats`
  `references/table-standards/table-types/model_comparison.md`, and the fair-comparison conditions in
  `design-study` `references/multi_model_comparison_design.md`.
