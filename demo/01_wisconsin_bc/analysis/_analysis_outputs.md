# Analysis Outputs
Generated: 2026-04-14
Study type: Diagnostic accuracy

## Tables
- `tables/table1_demographics.csv` -- Baseline characteristics (age by diagnosis)
- `tables/diagnostic_accuracy.csv` -- Sensitivity, specificity, PPV, NPV, AUC (95% CI)
- `tables/predictions.csv` -- Per-subject predictions from all 3 models

## Figures
- `figures/roc_curve.pdf` / `figures/roc_curve.png` -- 3-model ROC comparison with 95% CIs
- `figures/confusion_matrices.pdf` / `figures/confusion_matrices.png` -- Side-by-side confusion matrices

## Summary
- N = 569 (train: 455, test: 114)
- Malignant: 212 (37.3%), Benign: 357 (62.7%)
- Best model: Random Forest (AUC = 0.994)
- All 3 models: AUC > 0.97
