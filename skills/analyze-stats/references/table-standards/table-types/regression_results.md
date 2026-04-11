# Table: Regression Results

## Reporting Guidelines
- **STROBE**: Observational studies — OR, HR, RR with 95% CI
- **TRIPOD**: Prediction models — coefficients or OR with CI

## Standard Structure

```
Table 3. Multivariable Logistic Regression for [Outcome]

Variable              Univariable              Multivariable
                      OR (95% CI)    P Value   OR (95% CI)      P Value

Age, per 10 y         1.22 (1.08-1.38) .002   1.18 (1.03-1.35)  .02
Sex, male vs female   1.45 (0.98-2.14) .06    1.38 (0.91-2.09)  .13
BMI, per 5 kg/m²      1.31 (1.12-1.53) <.001  1.25 (1.06-1.47)  .008
Stage III vs I-II     2.87 (1.92-4.29) <.001  2.54 (1.65-3.91)  <.001

OR = odds ratio, CI = confidence interval, BMI = body mass index.
```

## Rules
- **Reference category**: Always state (e.g., "male vs female", "Stage III vs I-II")
- **Clinically meaningful units**: "per 10 years" not "per 1 year" for continuous
- **Effect measure**: Match study design — OR (logistic), HR (Cox), RR (log-binomial), β (linear)
- **Always show both univariable AND multivariable** (or justify omission)
- **Model fit statistics**: AIC, C-statistic, or Hosmer-Lemeshow in footnote or separate row
- **Variable selection method**: State in footnote (e.g., "Variables with P < .10 in univariable entered multivariable")
- **Collinearity**: Note if VIF checked, in footnote

## gtsummary Code
```r
# Univariable
uv <- tbl_uvregression(
  data, y = outcome, method = glm,
  method.args = list(family = binomial),
  exponentiate = TRUE
)

# Multivariable
mv <- glm(outcome ~ age + sex + bmi + stage, data = data, family = binomial)
mv_tbl <- tbl_regression(mv, exponentiate = TRUE) %>%
  add_global_p() %>%
  bold_p(t = 0.05)

# Merge
tbl_merge(list(uv, mv_tbl),
          tab_spanner = c("Univariable", "Multivariable"))
```
