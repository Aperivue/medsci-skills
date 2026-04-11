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
- **Continuous variables**: Mean (SD) if normal; Median (IQR) if skewed. State which in footnote
- **Categorical variables**: n (%)
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
