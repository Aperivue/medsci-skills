# Exemplar anatomy — Dose-response curve (restricted cubic spline)

A worked **anatomy model** for an adjusted exposure–outcome association drawn with a restricted
cubic spline (RCS): the ratio-scale effect compares each exposure value with a named reference.
Synthetic — describes what each element must show; not an image to copy. Pairs `analyze-stats`
`references/analysis_guides/survey_weighted.md` (RCS section) and `peer-review`
`references/domain-probes/observational_confounding.md` (probe O12).

## Elements
- **X-axis = exposure**, labelled with units and any transformation; restrict the display to the
  supported exposure range and state the displayed limits in the caption.
- **Y-axis = adjusted ratio-scale effect**, naming OR, RR, or HR and the outcome, on a log scale
  with ticks labelled as ratios and a horizontal **null line at 1**.
- **Fitted curve and confidence band**, with the confidence level and pointwise versus simultaneous
  coverage stated; distinguish multiple curves by line style as well as colour.
- **Knot number and locations in the caption**, including boundary knots, typically pre-specified
  at fixed percentiles of the exposure distribution. An illustrative convention is four knots at
  the 5th, 35th, 65th, and 95th percentiles; it is one convention, not a required choice. Give the
  corresponding exposure values and optionally mark knot positions on the axis, distinct from a rug.
- **Reference value named and marked**, with units and the reason for choosing it; the curve is
  pinned at ratio 1 with a zero-width CI there because the contrast is the reference with itself.
  Each contrast's CI comes from the covariance of the spline coefficients. Changing the reference
  shifts the curve and moves the pinch point; it does not change the fitted exposure relationship.
- **Exposure distribution below the curve**, as a rug or aligned histogram, with the analysis
  sample size stated. Sparse tail observations explain why the CI band often flares; distance from
  the reference also affects contrast uncertainty. Trim or explicitly mark extreme, poorly supported
  tails and state the display rule; distinguish display trimming from exclusions in model fitting.
- **Caption names the model and adjustment set**, listing covariates and stating how predictions
  handle them (held at specified values or standardized over a stated population).
- **Overall-association and non-linearity tests in the caption**, each with its p-value and method:
  overall tests all exposure spline terms jointly; non-linearity tests the non-linear terms against
  the linear model, retaining the same adjustment set and analysis sample. Use a likelihood-ratio
  test (LRT) or Wald test appropriate to the model; pre-specify the non-linearity test.
- **Survey-design caveat where relevant**: name weights, strata, clusters, and variance method;
  bands and tests must use the design, not just weighted point estimates. Use a design-appropriate
  Wald test or other justified design-based test, not an ordinary likelihood LRT for a quasi-model.
  State whether knot percentiles and the distribution display are weighted; follow
  `analyze-stats` `references/analysis_guides/survey_weighted.md` for implementation.

## Discipline (what the figure must not do)
- **Do not read off data-mined thresholds or "inflection points" as clinical cutoffs**; follow
  `peer-review` `observational_confounding.md` probe O12 for breakpoint uncertainty and stability.
- **Do not claim a J-, U-, or L-shape from appearance alone**: require the pre-specified
  non-linearity test plus curve and uncertainty support; significance does not establish a specific
  shape or locate a threshold. Do not over-interpret wiggles or tune knots to obtain significance.
- **Do not extrapolate beyond the data**; linear RCS tails are a model constraint, not evidence that
  the association continues beyond observed support. Do not hide wide CIs through axis clipping.
- **Do not interpret the reference's zero-width CI as perfect knowledge of risk**, or an adjusted
  observational association as a causal dose effect. Do not choose the reference to dramatize risk.

## Common omission
- The **named reference**, **knot specification**, and **exposure distribution** — without them,
  the CI pinch and flare invite false certainty and tail-shape claims. Score with
  `critic_rubrics/data_plot.md`; compare ratio-axis discipline in `funnel_plot.md` and sparse-tail
  discipline in `km_curve.md` and `cumulative_incidence.md`, without borrowing their estimands.
