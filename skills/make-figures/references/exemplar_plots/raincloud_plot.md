# Exemplar anatomy — raincloud plot for continuous-outcome comparisons

A worked **anatomy model** for a publication-grade raincloud plot comparing a continuous
outcome across groups: the distribution, individual observations, and a compact summary remain
visible together. Synthetic — describes *what each element must show*; not an image to copy.
Pairs the plot with the continuous-outcome comparison estimated in `/analyze-stats`.

## Elements
- **Outcome and cohort**: name the continuous endpoint, its unit and assessment timepoint; state
  the analysis population and exclusions so each plotted denominator is interpretable.
- **Group axis**: show every pre-specified group in a stated order; label arms or categories
  directly, and keep the order and colours consistent across panels.
- **Density half**: show a half-violin for each group's observed distribution on the outcome
  scale, oriented consistently beside the raw points; use a common density scale and smoothing
  rule across groups.
- **Density interpretation**: make clear that width encodes estimated density, not the number of
  participants; do not scale each group independently in a way that suggests incomparable counts.
- **Individual observations**: plot each participant as a point, jittered only along the group
  axis to reduce overlap; use transparency or a beeswarm arrangement without hiding points.
- **Summary box**: overlay the median and interquartile range; state any whisker convention if
  whiskers are drawn, and do not imply they are the full range unless they are.
- **Sample sizes**: print the number of participants in each group; for paired data, give the
  number of complete pairs as well as any group-specific denominators.
- **Comparison estimate**: state the pre-specified between-group contrast, its effect measure,
  and confidence interval; identify the reference group and direction of benefit where relevant.
- **Design-aware inference**: use a paired or repeated-measures contrast for matched observations,
  and an independent-group method only when observations are independent.
- **Uncertainty**: label the confidence level and interval method for the contrast; if group-level
  estimates are annotated too, distinguish their intervals from the contrast interval.
- **Axis**: label the outcome and unit, use the same numeric scale for all groups and facets, and
  show a zero or clinical reference only when meaningful to the endpoint.
- **Legend and caption**: define colour/group encodings, any transformation, the summary shown,
  the estimator and interval method, multiplicity handling for multiple contrasts, and the
  participant denominator at each timepoint.

## Discipline (what the figure must not do)
- Do not treat violin width as sample size or as observed values; it is a smoothed density estimate.
- Do not let smoothing invent modes or tails: disclose the density method, use a common bandwidth
  rule, and avoid a violin when the sample is too small to support a stable density.
- Do not omit raw points or sample sizes; a smooth shape alone conceals discreteness, outliers,
  clustering, and how much information supports each group.
- Do not present whiskers as confidence intervals; the box summarizes the sample distribution,
  while uncertainty in a group contrast belongs to its explicitly labelled interval.
- Do not connect unrelated participants; for paired observations, show within-person links and
  estimate the paired contrast rather than treating measurements as independent.
- Do not suppress clinically important outliers or silently truncate the axis; if a broken or
  zoomed scale is essential, mark it clearly and retain the full-range context.
- Do not substitute marginal group intervals or a p-value for the effect estimate and its interval;
  for many contrasts, state the multiplicity approach and avoid highlighting only favourable pairs.

## Common omission
- The **contrast with its confidence interval and the group denominators**: distributions can look
  separated while leaving the size, uncertainty, and amount of data behind the comparison unclear.
  Cross-reference `critic_rubrics/data_plot.md` §C and `/analyze-stats`.
