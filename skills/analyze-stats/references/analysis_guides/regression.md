# Regression Analysis Guide

Covers both logistic regression (binary outcome) and multiple linear regression (continuous outcome).

---

## Logistic Regression

### When to Use
Binary outcome variable (0/1, event/no event) with one or more predictors.
Used for risk factor identification and prediction model building.

### Assumptions
1. Binary outcome
2. Linear relationship between continuous predictors and log-odds (Box-Tidwell test)
3. Independent observations (if repeated → GEE or mixed logistic)
4. No multicollinearity: VIF < 5
5. Sufficient sample: EPV >= 10 (minimum), >= 20 (recommended)

### Variable Selection
- **Clinical rationale first** — avoid purely data-driven stepwise selection
- Include: variables significant at P < 0.10 in univariable analysis + known confounders
- STROBE/TRIPOD guideline compliance required

### Model Assessment

**Calibration:**
- Hosmer-Lemeshow test: P > 0.05 = adequate fit (overpowered with large N)
- Calibration plot: predicted probability vs observed frequency

**Discrimination:**
- C-statistic (= AUC): 0.7-0.8 acceptable, 0.8-0.9 excellent, > 0.9 outstanding

**Multicollinearity:**
- VIF > 5 → remove or combine variables

### Required Outputs
1. OR table: univariable AND multivariable OR (95% CI), P-value per variable
2. C-statistic with 95% CI
3. Hosmer-Lemeshow test result
4. VIF table (supplementary)
5. Box-Tidwell results for continuous predictors (supplementary)

### OR Table Format
| Variable | Univariable OR (95% CI) | P | Multivariable OR (95% CI) | P |
|----------|------------------------|---|--------------------------|---|
| Age (per 10 yr) | 1.45 (1.12-1.88) | 0.005 | 1.32 (1.01-1.73) | 0.042 |

### Reporting Template
"Multivariable logistic regression was performed to identify independent predictors of [outcome]. Variables with P < 0.10 in univariable analysis and clinically relevant confounders were included. The model showed good discrimination (C-statistic = 0.82, 95% CI 0.78-0.86) and calibration (Hosmer-Lemeshow P = 0.45). [Variable] was independently associated with [outcome] (adjusted OR = 2.15, 95% CI 1.43-3.24; P < 0.001)."

### Pitfalls
- OR != RR: when event rate > 10%, OR overestimates RR
- EPV < 10 → overfitting risk. Consider penalized regression (LASSO/Ridge)
- Specify reference category for categorical variables
- Specify units for continuous variables (per 1 year vs per 10 years)
- Complete separation → use Firth's penalized likelihood

---

## Multiple Linear Regression

### When to Use
Continuous outcome variable with one or more predictors.
Used for identifying determinants and estimating adjusted effects.

### Assumptions (LINE + No Multicollinearity)
1. **L**inearity: residuals vs fitted plot
2. **I**ndependence: no repeated measures (if repeated → LMM/GEE)
3. **N**ormality of residuals: Q-Q plot, Shapiro-Wilk on residuals
4. **E**qual variance (homoscedasticity): residuals vs fitted, Scale-Location plot
5. No multicollinearity: VIF < 5
6. No influential outliers: Cook's distance < 4/n

### Assumption Violations → Alternatives
| Violation | Fix |
|-----------|-----|
| Non-linearity | Log transform, polynomial terms, GAM |
| Heteroscedasticity | Robust SE, WLS |
| Non-normal residuals | Transform outcome, bootstrap CI |
| Multicollinearity | Remove variable, combine, Ridge/LASSO |

### Model Evaluation
- R² (coefficient of determination): proportion of variance explained
- Adjusted R²: penalized for number of predictors — use for model comparison
- In medical research, R² = 0.2-0.4 can be meaningful (high biological variability)

### Diagnostic Plots (4-panel, always generate)
1. Residuals vs Fitted → linearity + homoscedasticity
2. Q-Q plot → residual normality
3. Scale-Location → homoscedasticity
4. Residuals vs Leverage → influential outliers (Cook's distance)

### Required Outputs
1. Coefficient table: β (95% CI), P-value per variable
2. R² and adjusted R²
3. VIF table
4. 4-panel diagnostic plot
5. Standardized coefficients (optional, for effect size comparison)

### Coefficient Table Format
| Variable | β (95% CI) | P |
|----------|-----------|---|
| Age (per year) | 0.45 (0.32 to 0.58) | < 0.001 |
| Model R² | 0.35 | |
| Adjusted R² | 0.33 | |

### Reporting Template
"Multiple linear regression was performed with [outcome] as the dependent variable. The model explained X% of the variance (adjusted R² = 0.XX). After adjusting for [covariates], [variable] was significantly associated with [outcome] (β = X.XX, 95% CI X.XX to X.XX; P = exact). Model assumptions were verified using diagnostic plots."

### Pitfalls
- Always report β units (per 1 year, per 10 kg/m², etc.)
- Standardized β useful for comparing effect sizes but unstandardized is standard in papers
- EPV for continuous outcome: N >= 10-20 per predictor
- Always present diagnostic plots (at minimum in supplementary)
