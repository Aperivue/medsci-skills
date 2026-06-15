# Table 1: Baseline Demographics / Characteristics

## Reporting Guidelines
- **RCT**: CONSORT (Table 1 should NOT include P values — randomization makes them irrelevant)
- **Cohort/Cross-sectional**: STROBE (P values optional, SMD preferred for propensity-matched)
- **Diagnostic**: STARD (patient demographics + index test characteristics)

## Standard Structure

```
Table 1. Baseline Characteristics of Patients

                          Group A (n=XXX)    Group B (n=XXX)    P Value
Age, y                    65.3 (12.1)        62.1 (11.8)        .04
Sex
  Male                    53 (52)            48 (47)            .41
  Female                  49 (48)            54 (53)
BMI, kg/m²               24.8 (3.2)         25.1 (3.5)         .52
...

Data are presented as mean (SD) for continuous variables and n (%)
for categorical variables.
```

## Rules
- **Binary variables**: Show only one level (e.g., Male only; Female is implied)
- **Continuous variables**: Mean (SD) if normal; Median (IQR) if skewed. State which in footnote. **Choose by skewness, not by a mean−median/SD heuristic** (see below)
- **Categorical variables**: n (%)

### Mean (SD) vs Median (IQR): choose by skewness, and couple the test

The selection criterion is **`|skewness| > 1`** (equivalently a Shapiro–Wilk rejection or a clear visual departure), **not** a `|mean − median| / SD > 0.5` rule. The mean−median/SD ratio fails exactly where it matters: a strongly right-skewed lab with a large SD (triglycerides, glucose, HbA1c, creatinine, often diastolic BP) can have skewness 2–4 yet `|mean − median|/SD ≈ 0.3`, so the heuristic wrongly keeps it as mean (SD). Use skewness so heavy-tailed labs are reported as median (IQR).

**Couple the statistic to the test** — a variable shown as median (IQR) must be compared with a **rank test (Wilcoxon / Mann–Whitney)**, and a variable shown as mean (SD) with a **t-test**. Reporting median (IQR) but a t-test p-value (or vice versa) is an internal inconsistency a reviewer will flag (and `/self-review` Phase 2.5a checks prose↔table statistic-type match).

```python
import numpy as np
from scipy.stats import skew, ttest_ind, mannwhitneyu

def summarize_continuous(x_by_group, full):
    """Return ('mean_sd'|'median_iqr', display, p) for one continuous variable.
    full = all non-missing values pooled; x_by_group = [groupA_vals, groupB_vals]."""
    if abs(skew(full, nan_policy="omit")) > 1:          # skewed -> median (IQR) + Wilcoxon
        stat, p = mannwhitneyu(*x_by_group, alternative="two-sided")
        return "median_iqr", f"{np.median(full):.1f} ({np.percentile(full,25):.1f}-{np.percentile(full,75):.1f})", p
    stat, p = ttest_ind(*x_by_group, equal_var=False)   # symmetric -> mean (SD) + t-test
    return "mean_sd", f"{np.mean(full):.1f} ({np.std(full,ddof=1):.1f})", p
```

In `gtsummary`, drive the same split: put skewed variables in `type = list(<var> ~ "continuous")` with `statistic = list(<skewed> ~ "{median} ({p25}-{p75})")` and `add_p(test = list(<skewed> ~ "wilcox.test", <symmetric> ~ "t.test"))`.
- **Column headers**: Include group size — "Group A (n=XXX)"
- **Units**: In row label — "Age, y" or "Age, years"
- **Missing data**: Report as "Missing" row or footnote stating N with complete data
- **P values in RCTs**: Omit (CONSORT recommendation) or include for observational studies
- **SMD**: Preferred over P values for propensity-matched studies

## gtsummary Code
```r
tbl_summary(
  data, by = group,
  type = list(age ~ "continuous2"),
  statistic = list(
    all_continuous() ~ c("{mean} ({sd})"),
    all_categorical() ~ "{n} ({p}%)"
  ),
  digits = list(all_continuous() ~ 1, all_categorical() ~ c(0, 1)),
  missing = "ifany",
  missing_text = "Missing"
) %>%
  add_p() %>%         # omit for RCTs
  add_overall() %>%
  bold_labels()
```
