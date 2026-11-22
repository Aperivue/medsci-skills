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
| 2 | Independent | Expected < 5 (rule of thumb) | Fisher's exact | Group Comparison |
| 2 | Paired | - | McNemar's test | Group Comparison |
| 2+ | Independent | Ordered | Chi-squared trend | Group Comparison |
| 3+ | Independent | Expected cell counts >= 5 (rule of thumb) | Chi-squared | Group Comparison |
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
- Rule of thumb, not a threshold: n > 30 per group → the t-test is often adequate (CLT); extreme
  skew or outliers can still undermine it.
- **Comparing the spread of two measurements made on the same units**: the independent-samples
  F-test and Levene's test assume two independent samples, so they do not apply to paired
  measurements, even when the location comparison was correctly made paired. With one pair per
  independent unit and approximately bivariate-normal data, the Pitman–Morgan test is the
  standard paired test of equal variances. When a unit contributes several pairs (lesions,
  repeated exams), see "Pseudoreplication comes first" in `agreement_reliability.md`. When pairs
  are independent but the distributional assumption is doubtful, the choice of a method that
  keeps the pairing is a question for a statistician.

---

## Common Reviewer Flags

- Using independent test on paired data (including an F-test or Levene's test on paired variances)
- Using the asymptotic chi-squared test on an independent table with small expected counts (the
  "expected < 5" convention is a rule of thumb; an exact test avoids the approximation)
- Not reporting assumption check results
- Missing multiplicity handling when several confirmatory contrasts are interpreted together (e.g.,
  pairwise contrasts among 3+ groups)
- Not specifying the test selection rationale in Methods
