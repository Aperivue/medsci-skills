# Between-model comparison sample size (is model A really better than B, C, …)

For a study whose claim is that **one model outperforms others** — several architectures / families
compared head-to-head on the same task — the sizing question is not single-model precision (Test 15
for Dice, Test 1 for AUC) but **how many cases separate the models**. A study powered only to
estimate each model's metric can still be too small to tell whether the ranking is real. This is the
**size** counterpart to the fair-comparison **design** in
`design-study/references/multi_model_comparison_design.md`; decide it before data collection.

## Why single-model precision under-sizes a comparison

Sizing each arm to a tight marginal CI does **not** guarantee the *difference* is distinguishable
from zero — two models can each have a narrow CI and still overlap. The comparison is powered by the
**difference**, and its precision depends on the **SD of the per-case difference**, which the
marginal SDs do not give you.

## Pair the design — it shrinks the required n

Run **all models on the same cases** (a paired / within-case design). Then size on the **SD of the
per-case difference**, which is usually **much smaller** than either marginal SD because easy cases
are easy for every model and hard cases are hard for every model (the between-model differences are
correlated away). A paired comparison needs far fewer cases than two independent arms for the same
power — and it is also the only design that supports the paired statistics below.

## Metric-specific paired sizing

- **Classification / detection — paired ΔAUC:** use the **DeLong** (1988) variance of the *difference*
  of two correlated AUCs (or Obuchowski for the MRMC / clustered case); size so the **ΔAUC CI excludes
  zero** (superiority) or lies within the **non-inferiority margin**. Sizing on each AUC's marginal CI
  is the wrong tool — the covariance between the two ROC curves is exactly what a paired calc uses.
- **Segmentation — paired ΔDice / ΔHD95 / ΔNSD:** size on the SD of the **per-case metric difference**
  and report the delta CI by **bootstrapping the paired per-case differences (BCa)** — there is no
  closed-form Dice CI. This extends the A-vs-B section of `segmentation_metric_sample_size.md` beyond
  a single contrast; **size on the worst structure** you must report.
- Take the **per-case-difference SD from a pilot** (or a prior head-to-head), never from a marginal-SD
  formula that assumes independence.

## More than two models — multiplicity across contrasts

Comparing **k models** creates up to k(k−1)/2 pairwise contrasts. Decide the estimand **before** the
data:

- **Primary-contrast design (preferred):** pre-specify **one** primary comparison — the proposed model
  vs the **strong, fairly-tuned reference baseline** (e.g., nnU-Net) — sized at full α; everything else
  is secondary / exploratory and labelled so. This avoids sizing for a multiplicity you do not need.
- **All-pairs confirmatory:** if every pairwise claim is confirmatory, a **family-wise correction**
  (Bonferroni / Tukey-analog) lowers the per-contrast α, which **inflates the required n per contrast** —
  budget for it. Running k(k−1)/2 unplanned tests and headlining the one that clears p < 0.05 is the
  rejected pattern (`analyze-stats` `analysis_guides/multiplicity.md`).

## Ranking stability — the trap a difference calc still misses

A **single-run** leaderboard ranks models by *true skill + run-to-run noise* (random seed, data order,
augmentation draw). Near-tied models can swap rank between seeds, so "our model ranked first" from one
run is not evidence. Two additions:

- **Report run-to-run variance:** train each model over **multiple seeds** and report the metric's
  seed SD; for the paired difference of repeated cross-validation runs use the **Nadeau–Bengio
  corrected-resampled variance** (a naïve paired t over overlapping CV folds is anticonservative).
- **Comparing many models (over datasets/structures):** the **Demšar (2006)** framework — Friedman
  test + Nemenyi **critical-difference** — tells you which rank gaps are real; models within the
  critical difference are **statistically tied**, not ranked. Size / seed so the top rank is stable,
  or report the tie honestly.

## Required parameters

The **per-case-difference SD** of the primary metric (pilot / prior head-to-head; per structure for
segmentation), the **metric** and its paired-CI method (DeLong for AUC, bootstrap for Dice), the target
**δ or NI margin on the delta**, the **number of models + which single contrast is primary**, and (for
a ranking claim) the **seed-to-seed SD**. Report N, the difference-SD source, the primary contrast, and
the multiplicity handling.

## Cross-links

The fair-comparison design the size serves → `design-study/references/multi_model_comparison_design.md`;
the single-metric precision + one A-vs-B Dice contrast → `segmentation_metric_sample_size.md`;
reader-in-the-loop (AI-vs-reader) sizing → `mrmc_reader_study_sample_size.md` (Test 14); presenting the
result → `make-figures` `exemplar_plots/model_comparison_leaderboard.md` + `analyze-stats`
`table-standards/table-types/model_comparison.md`; the multiplicity discipline →
`analyze-stats` `analysis_guides/multiplicity.md`.
