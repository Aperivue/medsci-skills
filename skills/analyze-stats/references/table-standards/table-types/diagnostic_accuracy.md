# Table: Diagnostic Accuracy Results

## Reporting Guidelines
- **STARD**: Sensitivity, Specificity, PPV, NPV with 95% CIs
- **TRIPOD-AI / CLAIM**: For AI model performance

## Standard Structure

```
Table 2. Diagnostic Performance of [Model/Test] for [Condition]

                     Sensitivity       Specificity       PPV              NPV              AUC
                     (95% CI)          (95% CI)          (95% CI)         (95% CI)         (95% CI)

Model A              0.92 (0.87-0.96)  0.85 (0.79-0.90)  0.78 (0.71-0.84) 0.95 (0.91-0.97) 0.94 (0.91-0.97)
Model B              0.88 (0.82-0.93)  0.90 (0.85-0.94)  0.83 (0.76-0.88) 0.93 (0.89-0.96) 0.93 (0.89-0.96)
P value              .12               .08               .21              .34              .45

95% CIs were calculated using the Wilson score method. AUC comparison
by DeLong test.
```

## Rules
- **Always include 95% CIs** for all metrics (STARD requirement)
- **CI method**: Specify in footnote (Wilson score, Clopper-Pearson, DeLong)
- **Threshold**: State the decision threshold used (e.g., "at Youden optimal threshold")
- **Per-class results**: For multi-class, show per-class + macro/micro average
- **Comparison P values**: DeLong test for AUC, McNemar for sensitivity/specificity
- **Decimal places**: 2-3 for proportions (0.92), 2-3 for AUC (0.94)
- **Reader studies**: Include per-reader AND pooled results

## Key Footnote Content
- CI calculation method
- Comparison test used (DeLong, McNemar, bootstrap)
- Threshold selection method
- Whether results are per-patient or per-lesion
