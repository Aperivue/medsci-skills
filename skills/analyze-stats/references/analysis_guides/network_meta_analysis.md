# Network Meta-Analysis (NMA) Analysis Guide

Comparing three or more interventions at once by combining **direct** (head-to-head) and
**indirect** evidence across a network, usually with a treatment **ranking**. The pooling is
standard meta-analysis; what fails review is the **transitivity assumption, consistency between
direct and indirect evidence, network geometry, ranking interpretation, and network-level
certainty**. This is the analysis-side companion to review probes **NM1–NM8** in
`network_meta_analysis.md`; for the pairwise machinery (search, screening, the random-effects
model, study-count thresholds) use the SR/MA workflow.

---

## When to Use

- Synthesis of ≥3 interventions with a connected evidence network (direct + indirect), or a
  **component NMA** decomposing multicomponent interventions.
- NOT for: a two-treatment pairwise meta-analysis (standard random-effects MA); a DTA meta-analysis
  (bivariate/HSROC).

## Transitivity (assess before pooling)

- An NMA is valid only if **effect modifiers are distributed similarly across the comparisons**
  (transitivity). **Assess and report it**: compare the distribution of plausible effect modifiers
  (baseline severity, age, dose, follow-up, year) across comparisons (box plots / a table), and/or
  network meta-regression. Transitivity is a clinical/epidemiological judgment — no test replaces it.

## Consistency / incoherence (the statistical footprint)

- Test **globally** (design-by-treatment interaction model) AND **locally** (node-splitting /
  loop-specific / back-calculation). A **star network (no closed loops)** cannot be checked — say so;
  the result then rests entirely on transitivity.
- Investigate the **source** of any inconsistency (often a single trial/loop), don't just report a
  global p value.

```r
library(netmeta)              # frequentist
nm <- netmeta(TE, seTE, treat1, treat2, studlab, data = d, sm = "OR", common = FALSE)
netsplit(nm)                  # local incoherence (direct vs indirect per comparison)
decomp.design(nm)             # global design-by-treatment / Q decomposition
netheat(nm)                   # net heat plot for inconsistency hotspots
netrank(nm, small.values = "bad")   # P-scores (frequentist ranking)
funnel(nm, order = ...)       # comparison-adjusted funnel plot
# Bayesian alternative: BUGSnet / gemtc / multinma (node-split, SUCRA, model fit via DIC)
```

## Network geometry, heterogeneity, ranking

- Present a **network plot** (node size ∝ sample size / #studies; edge thickness ∝ #trials) so
  thin (single-trial) edges and dominant nodes are visible; sparse/poorly-connected networks give
  fragile estimates.
- Report **between-study heterogeneity** (global τ²) and examine the usual **common-heterogeneity**
  assumption; high heterogeneity undermines pooling and transitivity.
- **Ranking (SUCRA / P-score / rankograms) is not a test of superiority** and is unstable when
  estimates are imprecise. Report ranking **with** the effect estimates (a **league table**), their
  intervals, and certainty — never "X is best" from SUCRA alone.

## Certainty (CINeMA / GRADE-NMA)

- Rate certainty **per network estimate** (within-study bias, reporting bias, indirectness,
  imprecision, heterogeneity, incoherence) via **CINeMA** or GRADE-NMA; **downgrade indirect-only**
  comparisons. Scale conclusions to certainty — a low-certainty estimate cannot support "superior."

## Component NMA

- A **component NMA** assumes **additivity** of component effects (often no component interaction) —
  state and, where possible, check it (an interaction/full-interaction model). Define the reference
  and the estimand (relative effects via a league table) explicitly.

## Reporting (PRISMA-NMA)

Report against **PRISMA-NMA**: the network plot, the transitivity assessment, the consistency
evaluation (global + local), the ranking with its caveats, comparison-adjusted publication-bias
assessment, and estimate-level certainty. Risk of bias uses **RoB-NMA**; pairwise items via the SR/MA
workflow. Review-side probes: NM1–NM8 in `network_meta_analysis.md`.
