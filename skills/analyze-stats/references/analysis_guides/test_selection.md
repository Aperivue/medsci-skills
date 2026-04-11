# Statistical Test Selection Guide

Decision tree for selecting the appropriate statistical test based on data structure.
Reference: Petrie & Sabin flowchart, Kirkwood Summary Guide.

---

## Step 1: Outcome Variable Type

| Outcome type | Next step |
|---|---|
| Continuous (measurement, score) | Step 2A |
| Binary / Categorical | Step 2B |
| Time-to-event (survival) | → Survival analysis type |
| Agreement / Reliability | → Inter-rater Agreement type |
| Diagnostic accuracy (Se/Sp/AUC) | → Diagnostic Accuracy type |

---

## Step 2A: Continuous Outcome

| Groups | Pairing | Normal? | Test | analyze-stats type |
|--------|---------|---------|------|--------------------|
| 1 | - | Yes | One-sample t-test | Group Comparison |
| 1 | - | No | Wilcoxon signed-rank (one-sample) | Group Comparison |
| 2 | Independent | Yes | Independent t-test | Group Comparison |
| 2 | Independent | No | Mann-Whitney U | Group Comparison |
| 2 | Paired | Yes | Paired t-test | Group Comparison |
| 2 | Paired | No | Wilcoxon signed-rank | Group Comparison |
| 3+ | Independent | Yes | One-way ANOVA + post-hoc | Group Comparison |
| 3+ | Independent | No | Kruskal-Wallis + post-hoc | Group Comparison |
| 3+ | Repeated | Yes | RM ANOVA | **Repeated Measures** |
| 3+ | Repeated | No | Friedman test | **Repeated Measures** |
| - | Correlation | Yes | Pearson r | Correlation |
| - | Correlation | No | Spearman rho | Correlation |
| - | Regression | - | Multiple linear regression | **Linear Regression** |

---

## Step 2B: Categorical Outcome

| Groups | Pairing | Condition | Test | analyze-stats type |
|--------|---------|-----------|------|--------------------|
| 1 | - | - | Binomial / z-test for proportion | Group Comparison |
| 2 | Independent | Expected >= 5 | Chi-squared | Group Comparison |
| 2 | Independent | Expected < 5 | Fisher's exact | Group Comparison |
| 2 | Paired | - | McNemar's test | Group Comparison |
| 2+ | Independent | Ordered | Chi-squared trend | Group Comparison |
| 3+ | Independent | - | Chi-squared | Group Comparison |
| 3+ | Paired | - | Cochran's Q | Group Comparison |
| - | Regression | Binary outcome | Logistic regression | **Logistic Regression** |

---

## Step 3: Confounder Control

| Situation | Method | analyze-stats type |
|-----------|--------|--------------------|
| Continuous outcome + multivariable | Multiple linear regression | **Linear Regression** |
| Binary outcome + multivariable | Logistic regression | **Logistic Regression** |
| Survival outcome + multivariable | Cox proportional hazards | Survival |
| Observational study + treatment comparison | Propensity score | **Propensity Score** |
| Repeated measures + missing data | LMM / GEE | **Repeated Measures** |

---

## Normality Assessment

| Method | When | Criterion |
|--------|------|-----------|
| Shapiro-Wilk | n < 50 | p >= 0.05 → normal |
| Kolmogorov-Smirnov | n >= 50 | p >= 0.05 → normal |
| Q-Q plot | Always (visual) | Points on diagonal |
| Skewness/Kurtosis | Supplementary | |skew| < 2, |kurt| < 7 |

Practical rule: n > 30 → t-test is generally robust (CLT), unless extreme skew or outliers.

---

## Common Reviewer Flags

- Using independent test on paired data
- Using chi-squared when expected cell count < 5 (should use Fisher's exact)
- Not reporting assumption check results
- Missing multiple comparison correction for 3+ groups
- Not specifying the test selection rationale in Methods
