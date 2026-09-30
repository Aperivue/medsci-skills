# Table: Model Performance Comparison

## Reporting Guidelines
- **TRIPOD-AI**: AI model development/validation
- **CLAIM**: AI in medical imaging

## Standard Structure

```
Table 3. Comparison of Model Performance on Test Set

Model          AUROC (95% CI)       Sensitivity (95% CI)  Specificity (95% CI)  P vs Baseline

Baseline CNN   0.87 (0.83-0.91)    0.82 (0.75-0.88)     0.85 (0.79-0.90)     —
Proposed Model 0.93 (0.90-0.96)    0.90 (0.84-0.94)     0.89 (0.84-0.93)     .003
Reader A       0.88 (0.84-0.92)    0.85 (0.78-0.90)     0.86 (0.80-0.91)     .52
Reader B       0.86 (0.81-0.90)    0.83 (0.76-0.89)     0.84 (0.78-0.89)     .71

AUROC compared by DeLong test. Sensitivity/specificity at the prespecified
threshold of [value] (fixed before the test data were analysed). 95% CIs by
Wilson score interval (one row per patient).
```

## Rules
- **Baseline/reference model**: Always include (first row, P = — or "Ref")
- **Reader comparison**: Include human readers when available
- **Same test set**: All models evaluated on identical held-out data
- **Threshold**: Specify how the threshold was chosen and on which data. A cut-off optimised on
  the evaluation data (e.g. Youden on the test set) makes Se/Sp optimistic — about 0.12 in
  Se + Sp at n = 60, AUC 0.75 in simulation (Leeflang et al. 2008,
  doi:10.1373/clinchem.2007.096032) — and two models compared at their own data-optimised
  cut-offs are not compared at a common operating point. Prespecify it, or derive it on
  training / cross-validation data and label a test-set Youden cut-off as exploratory
- **Bootstrap CIs**: State number of iterations if used (e.g., "1000 bootstrap replicates")
- **Multiple test sets**: Separate sections or sub-tables for internal vs external validation
- **Calibration**: Include Brier score or calibration slope if relevant

## AI-Specific Additions (CLAIM)
- Software version / model architecture in footnote or methods
- Training set size in footnote
- Hardware used (if inference time reported)
- Whether results are per-image or per-patient
