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
| 2 | Independent | Yes | Welch t-test | Group Comparison |
| 2 | Independent | No | Mann-Whitney U | Group Comparison |
| 2 | Paired | Yes | Paired t-test | Group Comparison |
| 2 | Paired | No | Wilcoxon signed-rank | Group Comparison |
| 3+ | Independent | Yes | Welch ANOVA + post-hoc (Games-Howell) | Group Comparison |
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

Decide from the design, prior knowledge of the variable and its shape — not from a normality
test's P value.

| Method | Use |
|--------|-----|
| Q-Q plot / histogram | Always (visual) |
| Skewness | `|skew| > 1` → median (IQR) + rank test; otherwise mean (SD) + Welch (Table 1 rule, `table-types/table1_demographics.md`) |
| Shapiro-Wilk / Kolmogorov-Smirnov | Not a gate. They reject trivial departures at large n and miss real ones at small n; KS with an estimated mean/SD is miscalibrated (Lilliefors 1967, doi:10.1080/01621459.1967.10482916); choosing the test by a preliminary test distorts the type I error (Rochon, Gondan & Kieser 2012, doi:10.1186/1471-2288-12-81) |

- Two independent groups, mean-type summary: **Welch's t-test** by default (no equal-variance
  assumption; Delacre, Lakens & Leys 2017, doi:10.5334/irsp.82). 3+ groups: Welch ANOVA. Levene's
  test is not a gate, and Mann-Whitney is not a remedy for unequal variances.
- Practical rule: n > 30 per group → the t-test is generally robust (CLT), unless extreme skew or
  outliers.

---

## Common Reviewer Flags

- Using independent test on paired data
- Using chi-squared when expected cell count < 5 (should use Fisher's exact)
- Not reporting assumption check results
- Missing multiple comparison correction for 3+ groups
- Not specifying the test selection rationale in Methods
