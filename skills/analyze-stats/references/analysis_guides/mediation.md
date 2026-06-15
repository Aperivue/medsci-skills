# Mediation Analysis Guide

Decomposing an exposure–outcome association into a path **through** a mediator (indirect
effect) and a path **not through** it (direct effect). The estimate is easy; the
*identification* is hard — that is where mediation analyses fail review.

---

## When to Use

- A pre-specified hypothesis that exposure X affects outcome Y **partly via** mediator M
- M is measured, plausibly on the causal path, and (ideally) measured **after X and before Y**
- NOT for: a single-timepoint design used to assert a causal X→M→Y chain (see the design caveat
  below — that is the most common reason mediation papers are rejected); not a substitute for a
  longitudinal or experimental test of the mechanism

---

## Identification comes first (this, not the bootstrap, is the issue)

A bootstrapped indirect-effect CI quantifies the **sampling variability** of the a×b product. It
says nothing about whether the indirect effect is **identified**. Causal mediation requires, beyond
no exposure–outcome and no exposure–mediator confounding:

- **No unmeasured mediator–outcome confounding (sequential ignorability).** This must hold *even in
  a trial that randomizes X*, because M is not randomized. In observational data it essentially
  never holds unmodelled — so a **sensitivity analysis is mandatory**, not optional.
- **No mediator–outcome confounder affected by the exposure** (an exposure-induced M–Y confounder
  breaks the standard product/difference method; use a method that allows it, e.g. an interventional
  or G-computation estimator).
- **Correct temporal order.** X precedes M precedes Y. A **cross-sectional** design measures all
  three together and cannot establish this — report the indirect effect as *consistent with*
  mediation, state plainly that the design cannot order X/M/Y, and reserve the causal claim for a
  two-wave / longitudinal design (review probe O13 in `observational_confounding.md`).

## Method

- **Estimator**: bootstrapped product-of-coefficients (a×b) is standard for continuous M and Y
  (R `mediation`, `CMAverse`, or Hayes PROCESS; Python `pingouin`/`statsmodels`). For a binary
  outcome use the **counterfactual / natural-effects** decomposition (e.g. `CMAverse`,
  `regmedint`), not the naive product on the odds-ratio scale (non-collapsibility distorts it).
- **Bootstrap** the indirect effect (≥ 2000, ideally 5000 resamples) and report the **bias-corrected
  percentile CI** — not the Sobel test (Sobel assumes normality of a×b and is underpowered).
- **Exposure–mediator interaction**: with the counterfactual approach, report the natural direct and
  indirect effects allowing X×M interaction rather than assuming it away.

## Reporting (AGReMA)

Report against **AGReMA** (A Guideline for Reporting Mediation Analyses). Minimum:

- The full mediation model (every path), the estimator, and the confounder set for **each** of the
  X→Y, X→M, and M→Y relationships (they differ — name them separately).
- Total, direct, and indirect effects, each with a bootstrap CI.
- **Proportion mediated only with uncertainty, and only when the total effect is well-estimated.**
  Proportion mediated = indirect / total is **unstable when the total effect is small or near-null**
  — it can exceed 100% or flip sign. Do not headline a proportion-mediated when the total-effect CI
  is wide or crosses the null.
- The **sensitivity analysis** for unmeasured mediator–outcome confounding: an **E-value for the
  indirect effect** (or a ρ-/correlation-based mediation sensitivity, e.g. `mediation::medsens`),
  stating how strong unmeasured M–Y confounding would have to be to null the indirect effect.
- The temporal structure of X, M, Y (and, if cross-sectional, the explicit caveat).

## Common failures (flag at review)

- Causal "X affects Y through M" from cross-sectional data with no temporal caveat → reframe to
  association-level + add the sensitivity analysis (O13).
- A significant bootstrap CI treated as evidence of identification.
- No sensitivity analysis for unmeasured M–Y confounding.
- Proportion-mediated quoted as a stable figure when the total effect is small.
- Binary-outcome mediation via the naive OR product instead of a counterfactual decomposition.

## Anti-Hallucination

- Never fabricate path coefficients, indirect effects, or bootstrap CIs — all from executed code.
- Do not assert a causal direction the design cannot support; state the identification assumptions.
- Generate references via `/search-lit` (AGReMA, VanderWeele).
