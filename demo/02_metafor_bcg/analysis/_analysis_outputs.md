# Analysis Outputs — Demo 2: BCG Vaccine Meta-Analysis
Generated: 2026-04-14
Study type: Meta-analysis (intervention, 13 RCTs)
Effect measure: Risk Ratio (log-transformed)
Model: Random-effects (REML)

## Key Results
- Pooled RR: 0.489 (95% CI: 0.344-0.696)
- I²: 92.2%, tau²: 0.3132
- Meta-regression R² (latitude): 75.6%
- Egger's test p = 0.189
- Trim-and-fill: 1 imputed, adjusted RR = 0.518

## Tables
- `tables/study_results.csv` — Per-study RR with 95% CI and weights
- `tables/summary_table.csv` — Pooled estimates (overall, subgroup, trim-and-fill)
- `tables/metaregression_table.csv` — Meta-regression coefficients
- `tables/leave_one_out.csv` — Leave-one-out sensitivity analysis

## Figures
- `figures/forest_plot.{pdf,png}` — Forest plot (13 studies, REML)
- `figures/funnel_plot.{pdf,png}` — Funnel plot
- `figures/funnel_trimfill.{pdf,png}` — Funnel plot with trim-and-fill
- `figures/bubble_plot.{pdf,png}` — Meta-regression bubble plot (latitude)

## Data
- `data/bcg_raw.csv` — Original dataset (metafor::dat.bcg)

