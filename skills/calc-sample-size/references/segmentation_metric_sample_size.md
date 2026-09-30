# Segmentation-metric sample size (Dice / HD95 / NSD precision)

For a **segmentation** validation, the sizing question is not "how many events" but **how many
cases to estimate the segmentation metric precisely enough to be conclusive** — and, for a
comparison, precisely enough to separate the models. The diagnostic-accuracy calc (Test 1) and the
Riley prediction-model calc (Tests 12–13) do not apply: the outcome is a per-case **overlap /
boundary** score (Dice, HD95, NSD), bounded and often skewed, not a proportion or a risk. This is
the **design-time** case count for a segmentation study — including the external cohort a genuine
generalization claim needs (see `design-study/references/combine_models_ablation_design.md` and
`venue_accept_recipe.md`).

## Why a proportion/events calculation is the wrong tool

Per-case **Dice is bounded [0,1] and heteroscedastic**: near-ceiling and low-variance for large,
easy organs, but low and high-variance for **small or hard structures**. Precision therefore depends
on the **SD of per-case Dice**, which you must take from a **pilot or literature** — not from a
formula that assumes a proportion. **HD95 / NSD** are even more skewed (a few outlier cases dominate),
so their precision is worse at the same n.

## Precision sizing (estimate a mean metric within ±δ)

To estimate the mean metric with a two-sided 95% CI half-width **δ**:

    n ≈ ( 1.96 · SD / δ )²

where **SD** is the pilot/literature SD of the **per-case** metric.

**Check**: SD 0.10, δ 0.02 → 96.04 → **97** cases (z); with the t quantile
`presize::prec_mean(mean = 0.85, sd = 0.10, conf.width = 0.04)` returns 98.47 → 99.

```python
import math
from scipy.stats import norm

# Worked example = the Check inputs; replace with the pilot SD of the worst structure
sd_metric = 0.10
half_width = 0.02
n_prec = math.ceil((norm.ppf(0.975) * sd_metric / half_width)**2)
print(f"{n_prec} cases")
```

This is a **precision** calculation: it makes the CI a given width, it does not power a comparison.
Because Dice is bounded and non-normal, **report the CI by bootstrapping the per-case values
(BCa)**, not a naïve normal CI — the formula sizes the study, the bootstrap reports it. For near-ceiling Dice consider a variance-
stabilizing view or report the full distribution, since a symmetric ±δ misleads at the ceiling.

## Comparison sizing (model A vs B, or internal vs external, or an ablation contrast)

A model comparison on the **same cases** is **paired**: size on the **SD of the per-case
*difference*** (usually much smaller than the marginal SD, because easy cases are easy for both) or,
for an "as good as" claim, a **non-inferiority margin** on Dice. This is the calculation behind the
ablation contrasts in `combine_models_ablation_design.md` (un-adapted base, best single component,
direct-train-vs-transfer). Size each contrast with the **power** formula for a paired difference,
n = ((z_{1−α/2} + z_{1−β})·SD_Δ/Δ)² (non-inferiority: (z_{1−α} + z_{1−β}) and Δ + M), in
`multi_model_comparison_sample_size.md` § Metric-specific paired sizing. Do not reuse the precision
formula above with δ = the expected difference: a CI sized to just exclude zero at the expected Δ
does so only about half the time (50% power).

## Size on the worst structure, and size the external cohort

- **Per-structure, not the average.** Small/hard structures dominate the variance; size on the
  **worst structure you must report**, or the study is under-powered exactly where it matters.
- **The external cohort needs its own n.** The #1 acceptance lever is a *precise* external estimate
  with an honest drop; a 30-case external set gives a wide Dice CI. Size it to the precision the
  generalization claim requires.

## Required parameters + compute

- Pilot/literature **SD of the per-case metric** (per structure), the target **precision δ** or the
  **NI margin**, the metric itself. A t-interval on mean per-case Dice is closed-form, but the metric
  is **bounded and skewed near the ceiling**, so its nominal coverage is not the real one → **bootstrap
  per-case values** (BCa, resampling whole patients rather than structures); use the pilot for SD.
  Report N, the per-structure SD source, and δ / margin.

## Cross-links

Metric **selection** (Dice + a boundary/agreement metric, per-structure) → `/model-assessment`;
validation design + the split-leakage gate → `/model-assessment`; the comparator/ablation the size
serves → `design-study/references/combine_models_ablation_design.md`; presenting the across-cohort
result → `make-figures` `exemplar_plots/external_validation_comparison.md`.
