# Exemplar anatomy — meta-analysis forest plot

A worked **anatomy model** for a publication-grade pairwise meta-analysis forest plot,
complementing the `critic_rubrics/data_plot.md` §C *forest* checklist (this shows the full
composition; the rubric scores a draft against it). Synthetic — describes *what each element
must show* and the errors to avoid; not an image to copy. Pairs with `analyze-stats`
`templates/forest_plot.py` / `meta_analysis.R`.

## Elements (top to bottom)
- **Per-study row**: study label (author year), the effect estimate as a **square sized by
  weight**, and its **95% CI** as a horizontal line; the numeric estimate (95% CI) in a right
  column. Weight (%) shown numerically, not only by square size.
- **Pooled diamond**: the random-effects summary, its width = the summary 95% CI. State the
  **model** (e.g., DerSimonian–Laird or REML random-effects) in the caption.
- **Prediction interval**: show it (a bar through the diamond) whenever k is sufficient — it
  conveys where a *new study's true (study-specific) effect* would likely fall, which the
  summary CI (a confidence interval for the pooled mean) does not. Its absence is the single
  most common forest-plot omission.
- **Heterogeneity line**: report **I², τ² (or τ), and Cochran's Q with its p** beneath the
  diamond — τ² is the actual between-study variance and must not be left implicit.
- **Reference line** at the null (OR/RR/HR = 1, or 0 for mean differences); a log scale for
  ratio measures so CIs are symmetric.
- **Axis**: framed to include all CIs without wasted whitespace; label the effect measure and
  which direction favours which arm.

## Discipline (what the figure must not do)
- **Do not pool when pooling is not defensible**: when heterogeneity is extreme *and
  unexplained* (a high I² with a large τ² and no subgroup/meta-regression that accounts for it),
  or k is very small, a single summary can be clinically and statistically misleading — then
  present studies without a summary diamond, or restrict to a justified subgroup, rather than
  showing a precise diamond that implies an agreement the studies do not have. (I² is a guide,
  not an automatic cut-off — judge it with τ² and whether the heterogeneity is explained.)
- **Subgroups**: plot each subgroup with its own diamond and a **test for subgroup differences**;
  do not narrate subgroup effects that are not shown as plotted strata.
- **Small-study effects**: a funnel plot + Egger's test belong with the forest **only when
  k ≥ 10**; below that, say tests are underpowered rather than over-interpreting asymmetry.
- **Certainty**: where GRADE is used, a certainty column (or caption note) keeps a tight CI from
  being read as strong evidence when risk of bias/imprecision is high.

## Common omission
- A **prediction interval** and an **explicit τ²**, plus an honest **no-pool / restrict
  decision under extreme heterogeneity** — the elements forest plots most often skip, and the
  ones that turn a precise-looking diamond into an over-statement of agreement. Cross-reference
  `critic_rubrics/data_plot.md` §C (forest) and the SR/MA reporting items via
  `/check-reporting` (PRISMA).
