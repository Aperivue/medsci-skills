# Figure manifest — Demo 5

Five figures. Every value plotted is read at build time from `../../results/`; none is typed into a
figure script. Figures live in `../../figures/`; the generators live here and in `../../pipeline/`.

| # | File | Generator | Reads | What it shows |
|---|---|---|---|---|
| 1 | `fig1_dice_by_arm.{png,pdf}` | `analysis/make_figs.py::fig1` | `results/per_case_*.csv` | Per-case Dice for all three rungs, box + jittered points. The internal arm is tight and high; the external CT arm has a long tail to zero that its median 0.8932 conceals; the MRI arm sits at the floor with a few cases up to 0.91. |
| 2 | `across_cohorts_dice.png` | `pipeline/aggregate_results.py::_make_figure` | `results/per_case_*.csv` | Across-cohort median Dice with bootstrap 95% CI, internal as the dashed reference. The honest drop read at a glance. Owns the bootstrap, so it is not duplicated in `make_figs.py`. |
| 3 | `fig3_normalisation_evidence.{png,pdf}` | `analysis/make_figs.py::fig3` | `results/normalizer_evidence_rung{2,3}_*.json` | **The mechanism.** (a) per-case minimum intensity: every CT case has a Hounsfield air floor near −1000, no MRI case has one. (b) the share of each volume flattened at the trained plan's clip ceiling, median 2.7 % on CT against 23.2 % on MRI. |
| 4 | `fig4_subgroups_external_ct.{png,pdf}` | `analysis/make_figs.py::fig4` | `analysis/tables/table3_subgroups.csv` | The pre-specified subgroups on the external CT arm, both axes with identical cut-points. Enlarged spleens (>250 mL) score 0.7694 against 0.9114 for normal volumes. |
| 5 | `fig5_case_flow.{svg,pdf,png,600.png}` | `skills/make-figures/scripts/generate_flow_diagram.R` via `figures/case_flow.yaml` | `qc/dataset_profile_msd.json`, `qc/amos22_dataset_profile_spleen.json`, `qc/split_leakage.json`, `results/per_case_*.csv` | STARD-style case accounting for both source datasets: what was excluded and why, the seed-42 split, the three rungs, and the three target-free cases that are reported rather than scored. |

## Conventions

Navy `#1B2A4E` / coral `#B83E3A`, per the repository's figure convention. Exclusion boxes are
`shape: box` with `\l` left-aligned bullets; the three rung nodes carry the `highlight` (thicker
border) that marks an analytic endpoint. Rasterised figures are 300 dpi with a vector PDF beside
them; the flow diagram additionally emits a 600 dpi line-art copy for journals that require it.

## Reproduce

```bash
cd analysis && python3 make_tables.py && python3 make_figs.py     # figs 1, 3, 4 (+ all tables)
cd .. && python3 pipeline/aggregate_results.py --results-dir results \
    --out results/summary_across_cohorts.md --figure figures/across_cohorts_dice.png   # fig 2
Rscript ../../skills/make-figures/scripts/generate_flow_diagram.R \
    --type stard --config figures/case_flow.yaml --out figures/fig5_case_flow          # fig 5
```

Figures 1–4 are deterministic apart from point jitter, which is seeded (`default_rng(20260725)`)
and never a reported quantity. Figure 5 is deterministic given Graphviz.
