# Analysis outputs — Demo 5

Two scripts, both reading only the per-case artifacts in `../results/`. Nothing is typed in by
hand, and neither script touches the imaging data: by this stage the study is a table of one row
per case, which is what makes the analysis reproducible on a laptop.

| Script | Emits |
|---|---|
| `make_tables.py` | `tables/table1_cohort_characteristics.csv`, `tables/table2_performance.csv`, `tables/table3_subgroups.csv`, `tables/table4_normalisation_evidence.csv`, `tables/key_scalars.csv` |
| `make_figs.py` | `../figures/fig1_dice_by_arm.*`, `../figures/fig3_normalisation_evidence.*`, `../figures/fig4_subgroups_external_ct.*` (see `figures/_figure_manifest.md`) |

## The tables

**Table 1 — cohort characteristics.** What each arm contains and how the images differ: case count,
target-free count, spleen volume (median, IQR, range) and slice thickness (median, IQR, range, and
how many cases are 5 mm or thicker). This is where the external cohort's heterogeneity becomes
visible — 219 of 300 external CT cases are 5 mm or thicker, against a training set spanning
1.5–8 mm within one institution.

**Table 2 — performance.** The headline: evaluated and scored counts, target-free cases, empty
predictions, false positives on a target-free case, Dice (median with bootstrap 95 % CI, plus mean
and minimum) and HD95, and Δ-Dice against the internal arm. Mean and minimum sit beside the median
deliberately: the external CT mean of 0.7116 against a median of 0.8932 is the tail that a median
alone would hide, and Figure 1 draws it.

**Table 3 — pre-specified subgroups.** Both axes, identical cut-points across arms, fixed before any
case was scored. A per-arm tertile would have made the arms non-comparable, which is why the
cut-points are constants in the script rather than quantiles of the data.

**Table 4 — normalisation evidence.** What the *trained* plan's normaliser does to each external
arm: the scheme it carries, its clip window and z-score parameters, and then the three measured
columns — how many cases contain any negative voxel, what share of each volume is flattened at the
clip ceiling, and how many intensity levels survive. This is the table behind the study's finding.

## Cross-check that matters

`make_tables.py` and `pipeline/aggregate_results.py` compute the headline medians and intervals
**independently** — different code paths, same inputs, same fixed bootstrap (10,000 resamples, seed
20260725). They agree to the last reported digit on all three arms (0.9595 / 0.8932 / 0.0152 and
their intervals). That agreement is a real check, not a formality: a bootstrap that silently
reseeds, or a denominator that silently includes the target-free cases, would show up here as a
disagreement rather than as a plausible number nobody questions.

## What is not here

No statistical test between arms. The three rungs differ in cohort, scanner population and modality
all at once, so a p-value comparing them would be answering a question the design cannot pose. The
comparison the design *does* support is the Δ from internal with each arm's own interval, which is
what Table 2 and Figure 2 report. Likewise the subgroup rows are estimates with intervals, not a
tested interaction — a difference in significance across strata is not a tested interaction, and the
manuscript says so rather than implying one.
