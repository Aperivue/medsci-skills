# Exemplar anatomy — external-validation performance across cohorts

A worked **anatomy model** for the figure that carries the **#1 acceptance lever** of a clinical
DL validation study: performance **across cohorts** — internal vs one or more external sets, or by
**site / scanner / vendor / sequence** — shown with its **honest drop**. It is the visual proof of
generalization, and the figure a reviewer scans first. Pairs
`design-study/references/venue_accept_recipe.md` (external validation = top lever),
`combine_models_ablation_design.md`, and `analyze-stats` `table-standards/table-types/model_comparison.md`.
Synthetic — describes *what each element must show* and the errors to avoid; not an image to copy,
no real citations.

## Elements
- The **metric by cohort** (Dice / AUC / HD95) as a **forest or dumbbell** (one row per cohort), with
  **internal as the labelled reference** and each external cohort below it — so the **drop** is read
  at a glance, not buried in a table.
- **Per-cohort N and a CI on each estimate** — for Dice, a **bootstrap (BCa) CI on per-case values**
  (a t-interval is closed-form but the metric is bounded and bunches near the ceiling, so resample
  whole patients instead); the CI width makes a small external cohort's uncertainty honest.
- The **Δ from internal** annotated per external cohort (the generalization gap), and, if the design
  is non-inferiority, the **margin**.
- **Faceting by structure / subgroup / sequence** where the endpoint demands it, so a per-organ or
  per-sequence weakness is visible rather than averaged away.
- **The failure mode marked** — the cohort / structure / sequence where the model broke (e.g., a
  contrast-sequence collapse, a small-structure floor) shown, not dropped.

## Discipline (what the figure must not do)
- **Do not show only the internal result** — a validation figure without the external axis is not a
  validation figure.
- **Do not plot an external number ≈ internal without its N and CI** — a suspiciously **flat**
  external result is the visual signature of leakage / tuning-on-test; the CI and N are what make a
  flat result credible or expose it.
- **Do not pool cohorts into one bar** — report **per-cohort**; pooling hides which site/vendor
  drove the drop.
- **Do not omit the failed subgroups / structures / sequences** — hiding the decline overstates
  generalization and invites the reviewer's first probe (an honest negative is an acceptance asset).
- **Do not use a naïve normal CI for Dice** — bounded, skewed per-case scores need a bootstrap CI.

## Common omission
- The **per-cohort N + CI**, the **Δ-from-internal** annotation, and the **failed subgroups** — the
  elements this figure most often drops, and the ones that turn "it generalizes" into a claim a
  reviewer can check. The case count behind a precise external estimate is a design-time decision
  (`calc-sample-size` `references/segmentation_metric_sample_size.md`). Cross-reference
  `forest_plot.md` (layout kin), `critic_rubrics/data_plot.md`, and `/model-validation` (internal vs
  external, tuning-on-test).
