# Exemplar anatomy — model-comparison leaderboard (across models, one cohort)

A worked **anatomy model** for the figure that carries a fair **model-vs-model** comparison: several
architectures / families ranked **on the same test cohort**. It is the mirror of
`external_validation_comparison.md` — that one is **one model across cohorts**; this one is **many
models on one cohort** — and it is the visual proof that the comparison was fair rather than a "we
beat everyone" table. Pairs `design-study/references/multi_model_comparison_design.md`,
`calc-sample-size/references/multi_model_comparison_sample_size.md`, and the `analyze-stats`
`table-standards/table-types/model_comparison.md`. Synthetic — describes *what each element must
show* and the errors to avoid; not an image to copy, no real citations.

## Elements
- The **metric per model** as a **forest / dumbbell**, one row per model, with the **strong,
  fairly-tuned reference baseline** as the labelled reference row — so each model is read as a
  **difference from the baseline**, not as an isolated number.
- **A CI on every model's estimate** — a **bootstrap (BCa) CI on per-case values** for Dice (bounded
  and skewed near ceiling, so resample whole patients rather than trust a t-interval), a **DeLong CI**
  for AUC (DeLong gives the AUC's standard error and the correlated-AUC contrast — it is not a
  confidence band around the ROC curve). The CI width is what turns a stack of point estimates into a
  comparison a reviewer can judge.
- **The paired Δ vs the reference** annotated per model (Δ + its **CI / significance**), because the
  models were run on the **same cases** — the paired difference, not two marginal numbers placed
  side by side, is the comparison.
- **Ranking honesty**: where models are near-tied, add a **rank-stability strip** (seed-to-seed spread)
  or a **critical-difference** view so models the test does not separate read as **unranked** rather
  than ordered — and are not captioned as a demonstrated tie.
- **Faceting by structure / subgroup / class** where the endpoint demands it (per-organ Dice, per-class
  AUC), so a model that wins on average but loses on the hard structure is visible.
- **Matched-budget disclosure in the caption** — same data, patient-level split, preprocessing, and
  **HPO / training budget** across all models, and the number of seeds. The figure's credibility rests
  on this line; without it a leaderboard is unfalsifiable.

## Discipline (what the figure must not do)
- **Do not bold / highlight your own row as the winner unless the paired Δ vs the runner-up excludes
  zero** — and read that Δ, not the overlap of the two marginal CIs, which can overlap while the paired
  difference is real; where the Δ does not clear zero, encode **not separated** instead of a winner.
- **Do not plot one point per model with no CI or seed spread** — a single-run leaderboard ranks by
  *skill + luck*; a bare ranked list is a leaderboard of luck.
- **Do not put models trained on different data / split / budget in the same ranking** without saying
  so — an unfair comparison drawn as a clean leaderboard is the core failure this figure exists to
  prevent.
- **Do not show only the metric / facet where you win** — lead with the **pre-specified primary
  metric**; hiding the facets where the proposed model loses overstates the result.
- **Do not rank by point estimate alone** — order by estimate but let the CIs / critical difference
  govern what counts as a real gap.

## Common omission
- The **paired-Δ CI**, the **seed / rank-stability encoding**, and the **matched-budget caption** — the
  three elements a leaderboard most often drops, and the ones that separate a fair comparison from a
  marketing chart. The case count behind a *separable* comparison is a design-time decision
  (`calc-sample-size/references/multi_model_comparison_sample_size.md`). Cross-reference
  `external_validation_comparison.md` (across-cohort sibling), `forest_plot.md` (layout kin),
  `critic_rubrics/data_plot.md`, and `/model-validation` (fair comparison, tuning-on-test).
