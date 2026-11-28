# Exemplar anatomy — Prognostic nomogram (risk-prediction model)

A worked **anatomy model** for a point-based multivariable prognostic or diagnostic nomogram
(logistic, Cox proportional-hazards, or competing-risks regression): each predictor maps
to a shared points scale, sums to Total Points, and translates to predicted probability or
survival/cumulative incidence at stated horizon(s). Synthetic — describes *what each element must
show* and the errors to avoid; not an image to copy, no real citations. Pairs `calibration_plot.md`,
`decision_curve.md`, `km_curve.md`, `cumulative_incidence.md`, and `peer-review`
`references/domain-probes/survival_prognostic.md` (probes S1, S3, S5–S8, T2, T4).

## Elements
- **Top Points axis** (commonly 0–100), calibrated so the predictor with the largest regression
  effect span reaches the top of the scale; tick density must allow reading values without guessing
  at final journal column width.
- **One horizontal axis per predictor**, in a stated order (clinical grouping or descending effect
  span), showing exact **units**, category labels, and reference levels. Non-linear effects (e.g.
  restricted cubic splines) must show non-uniform tick spacing explicitly, and interactions must be
  drawn as separate stratified axes rather than hidden in a footnote.
- **Total Points axis** aligned below all predictors, spanning the sum of possible predictor points
  (with the observed development-cohort range noted or marked so sparse/impossible extremes are
  transparent).
- **Linear predictor axis (optional)** when readers need to check log-odds or log-hazard arithmetic
  directly against the published regression table.
- **Outcome axis(es) at the bottom**, naming the exact **estimand and time horizon(s)** (e.g.
  predicted 30-day event probability, 3- and 5-year overall survival, or 5-year cause-specific
  cumulative incidence; probe S8) — never an unlabelled "Risk" or "Survival" axis.
- **Worked synthetic walkthrough in the caption** (or a single dashed-arrow example on the plot):
  one synthetic patient mapped from predictor ticks → points → Total Points → predicted risk,
  verifying that axes are internally aligned and legible at print size.
- **Caption states model provenance**: regression family (logistic, Cox, Fine–Gray, or combined
  cause-specific hazards), development N and event count, censoring or competing-risks method,
  shrinkage/penalization if applied, and a pointer to the paired validation calibration plot and
  decision curve.

## Discipline (what the figure must not do)
- **Do not treat a nomogram as evidence of model performance or clinical utility** — a nomogram
  only displays fitted regression weights; it proves neither discrimination, calibration, nor net
  benefit. Always pair with `calibration_plot.md` and `decision_curve.md` on validation data (probes S7, T2).
- **Do not include post-decision or leaky predictors** (e.g. pathology margin status or adjuvant
  therapy in a "preoperative" nomogram); follow `survival_prognostic.md` probe S1.
- **Do not ignore competing risks** for cause-specific recurrence or mortality endpoints: censoring
  competing death in a standard Cox nomogram overestimates absolute risk; derive a cumulative-incidence
  estimate that accounts for the competing event — via either a Fine–Gray subdistribution model or
  cause-specific hazard models combined into a cumulative incidence function — label the axis as
  cumulative incidence, and justify the estimand choice (probes S3, S8; `cumulative_incidence.md`).
- **Do not ship an unshrunk, small-event-count, or stepwise-selected fit without disclosing
  optimism**: extreme weights exaggerate predicted risks. State shrinkage/penalization and publish
  the full regression equation (coefficients + intercept or baseline survival / cumulative baseline
  hazard at each horizon) in the supplement so predictions are reproducible beyond ruler reading
  (probe T4).
- **Do not extrapolate outcome horizons beyond supported follow-up** (probes S5, S6) or let dense
  category ticks collide at print width.

## Common omission
- The **named endpoint/horizon**, **competing-risks or shrinkage disclosure**, and **paired
  calibration + full regression formula** — without them, a visually clean nomogram invites bedside
  use of an overfitted, miscalibrated, or horizon-mismatched score. Score layout and typography with
  `critic_rubrics/data_plot.md` §D/§E/§G; pair with `calibration_plot.md`, `decision_curve.md`,
  `cumulative_incidence.md`, and `peer-review` `references/domain-probes/survival_prognostic.md`.
