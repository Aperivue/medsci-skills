# Observational Cohort Sample Size: Precision Branch

Use this reference when a cohort study is extraction-constrained or when the goal is precision rather than formal power.

## When To Use

- Retrospective hospital-based cohort with all eligible records included.
- National database cohort where the sample is fixed by release permissions.
- Sparse-event outcome where the real question is whether confidence intervals are narrow enough to support a claim.

## Core Checks

1. Primary estimand: risk difference, odds ratio, hazard ratio, incidence rate, or mean difference.
2. Event count: total events and events per modeled parameter.
3. Precision target: acceptable confidence interval half-width or maximum acceptable upper bound.
4. Model complexity: covariate count relative to events.
5. Fragility: subgroup and sensitivity analyses with smaller denominators.

## Rule-of-Thumb Gates

| Situation | Minimum check |
|---|---|
| Logistic or Cox model | Events per parameter and shrinkage/penalization consideration |
| Sparse binary outcome | Exact or profile-likelihood confidence intervals |
| Incidence rate | Poisson exact CI around event rate |
| Null association claim | Upper CI bound must exclude clinically meaningful effect |
| Subgroup analysis | Interaction test plus event count per subgroup |

## Manuscript Phrase

"The study size was determined by all eligible participants in the released cohort. We therefore evaluated statistical informativeness by the number of outcome events, events per modeled parameter, and the width of the 95% confidence intervals around the primary estimate rather than by a conventional a priori recruitment target."

## Minimal R Sketch

```r
events <- 130
parameters <- 8
epv <- events / parameters

rate <- 130 / 250000
poisson.test(130, T = 250000)$conf.int
```

## Reviewer-Safe Interpretation

- If events are sparse, do not write "no association" without discussing the upper confidence bound.
- If EPV is below 10, state that estimates are exploratory or use penalized/sparse models.
- If a subgroup has few events, report it descriptively even when the p-value looks attractive.

