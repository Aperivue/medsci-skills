# Survey-Weighted Analysis Guide

Methods for analyzing complex survey data (KNHANES, NHANES, KCHS, and similar
nationally representative health surveys) that use stratified, multistage
probability sampling designs.

---

## When to Use

- Data from a national health survey with sampling weights (e.g., KNHANES, NHANES, KCHS)
- Goal: produce nationally representative prevalence, means, or associations
- Cross-national comparisons using parallel survey datasets
- NOT for: simple random samples, census data, or claims-based cohorts (NHIS, JMDC)

Claims-based databases (NHIS, JMDC) are NOT surveys -- they do not have sampling
weights or complex sampling design. Use standard regression for these.

---

## Key Concepts

### Complex Survey Design Elements

| Element | Description | Survey variable |
|---------|-------------|-----------------|
| **Stratification** | Groups the population into non-overlapping strata before sampling | `strata` |
| **Clustering (PSU)** | Primary sampling units within strata (e.g., districts, census blocks) | `cluster` / `PSU` |
| **Sampling weights** | Inverse probability of selection, adjusted for non-response and post-stratification | `weight` |

Ignoring these elements produces biased standard errors, incorrect p-values, and
non-representative point estimates.

### Dataset-Specific Design Variables

| Dataset | Strata variable | Cluster/PSU variable | Weight variable | Notes |
|---------|----------------|---------------------|-----------------|-------|
| **KNHANES** | `kstrata` | `psu` | `wt_itvex` (interview+exam) or `wt_ntr` (nutrition) | Years may be non-consecutive (PHQ-9 only in certain cycles) |
| **NHANES** | `SDMVSTRA` | `SDMVPSU` | `WTMECXYR` (exam) or `WTINTXYR` (interview) | 2-year cycles; combine cycles with adjusted weights |
| **KCHS** | varies by year | varies by year | `wt` | Annual community survey; single-stage cluster design |

### Weight Selection Rules

- **Interview-only variables**: use interview weight
- **Exam/lab variables**: use exam weight (smaller denominator)
- **Nutrition variables (KNHANES)**: use nutrition weight
- **Multi-cycle NHANES**: divide weight by number of cycles combined (e.g., 4 cycles: weight/4)
- **Single-cycle analysis**: use the cycle-specific weight as-is

### Subpopulation (domain) analysis — never row-delete

A restricted analysis (adults only, one sex, a disease subgroup) must keep the **full design** and select the domain, **not** filter the data frame and refit. Row-deletion discards the strata/PSU structure of the dropped units and gives wrong standard errors and design degrees of freedom.

- R `survey`: `subset(design, age >= 18)` on the **design object** (or `svyby`), not `svydesign(data = df[df$age>=18, ])`.
- Stata: `svy, subpop(if age>=18):` — never `keep if age>=18` before `svy:`.
- Python `samplics` / R is preferred; statsmodels has no native domain estimator.

### Reporting & common errors (these invalidate the inference, flag at review)

- **Model-based SEs on weighted points.** Applying the weight but computing SEs without strata + PSU (or replicate weights) understates uncertainty. Always declare `strata` + `id`/`cluster`.
- **Weighted total ≠ sample size.** Report the **unweighted n** as the analytic sample; the weighted figure is a *population* estimate, not "n".
- **Design effect / effective n.** Report DEFF or the effective sample size where precision is load-bearing; a large DEFF means far fewer independent observations than rows.
- **Unweighted vs weighted divergence.** If they differ materially, that signals weight-dependent selection — discuss it, do not hide it.
- **Data-driven thresholds.** A restricted-cubic-spline "non-linear/saturation" claim needs a pre-specified non-linearity test (LRT/Wald vs the linear model), and any "inflection point / threshold" from a recursive breakpoint search must carry a **confidence interval** and a stability check — a searched cutoff is exploratory, not a validated target (review-side probe O12 in `observational_confounding.md`).

---

## Step-by-Step Workflow

### Step 1: Declare Survey Design

Always declare the design before any analysis. This ensures correct variance estimation.

**Python (statsmodels)**:
```python
# statsmodels does not have a native survey design object.
# Use linearmodels or manual weight application.
# For publication-quality survey analysis, R is strongly recommended.
```

**R (survey package)**:
```r
library(survey)

# KNHANES
design_kr <- svydesign(
  id = ~psu,
  strata = ~kstrata,
  weights = ~wt_itvex,
  data = df_kr,
  nest = TRUE
)

# NHANES (2-year cycle)
design_us <- svydesign(
  id = ~SDMVPSU,
  strata = ~SDMVSTRA,
  weights = ~WTMECXYR,
  data = df_us,
  nest = TRUE
)
```

**SAS**:
```sas
/* KNHANES */
PROC SURVEYLOGISTIC DATA=kr;
  STRATA kstrata;
  CLUSTER psu;
  WEIGHT wt_itvex;
  MODEL outcome(event='1') = exposure covariates;
RUN;

/* NHANES */
PROC SURVEYLOGISTIC DATA=us;
  STRATA SDMVSTRA;
  CLUSTER SDMVPSU;
  WEIGHT WTMECXYR;
  MODEL outcome(event='1') = exposure covariates;
RUN;
```

### Step 2: Weighted Descriptive Statistics

**R**:
```r
# Weighted means
svymean(~continuous_var, design, na.rm = TRUE)

# Weighted proportions
svymean(~factor(categorical_var), design, na.rm = TRUE)

# Weighted Table 1 by group
library(tableone)
svyCreateTableOne(
  vars = c("age", "sex", "bmi", "income"),
  strata = "exposure_group",
  data = design,
  test = TRUE
)
```

**SAS**:
```sas
PROC SURVEYMEANS DATA=dataset;
  STRATA strata_var;
  CLUSTER cluster_var;
  WEIGHT weight_var;
  VAR continuous_var1 continuous_var2;
RUN;

PROC SURVEYFREQ DATA=dataset;
  STRATA strata_var;
  CLUSTER cluster_var;
  WEIGHT weight_var;
  TABLES group * categorical_var / CHISQ;
RUN;
```

### Step 3: Weighted Regression — Sequential Model Building

The standard cross-national analysis pattern uses sequential model building:

| Model | Covariates | Purpose |
|-------|-----------|---------|
| Model 1 | Age, sex | Minimal adjustment |
| Model 2 | Model 1 + income, education, smoking, alcohol, BMI, comorbidities | Full adjustment |

**R (survey-weighted logistic regression)**:
```r
# Model 1: age + sex
model1 <- svyglm(
  outcome ~ exposure + age + sex,
  design = design,
  family = quasibinomial()
)

# Model 2: full adjustment
model2 <- svyglm(
  outcome ~ exposure + age + sex + income + education +
            smoking + alcohol + bmi + cvd_history,
  design = design,
  family = quasibinomial()
)

# Extract weighted OR (wOR) with 95% CI
extract_wor <- function(model, var) {
  coef_val <- coef(model)[var]
  se_val <- summary(model)$coefficients[var, "Std. Error"]
  or <- exp(coef_val)
  ci_lo <- exp(coef_val - 1.96 * se_val)
  ci_hi <- exp(coef_val + 1.96 * se_val)
  p_val <- summary(model)$coefficients[var, "Pr(>|t|)"]
  data.frame(wOR = or, CI_lower = ci_lo, CI_upper = ci_hi, P = p_val)
}
```

**SAS (PROC SURVEYLOGISTIC)**:
```sas
/* Model 2: full adjustment */
PROC SURVEYLOGISTIC DATA=dataset;
  STRATA strata_var;
  CLUSTER cluster_var;
  WEIGHT weight_var;
  CLASS sex(ref='Male') income(ref='High') smoking(ref='Never') / PARAM=REF;
  MODEL outcome(event='1') = exposure age sex income education smoking alcohol bmi;
  ODDSRATIO exposure / CL=WALD;
RUN;
```

### Step 4: Subgroup / Stratified Analyses

```r
# Stratified by sex
svyglm(
  outcome ~ exposure + age + income + education + smoking + alcohol + bmi,
  design = subset(design, sex == "Male"),
  family = quasibinomial()
)
# Repeat for Female
# Note: exclude the stratification variable from covariates
```

Reporting pattern: "Weighted odds ratios are adjusted for all covariates except
for the stratification variable."

### Step 5: Advanced Analyses (Optional)

**Restricted cubic spline (dose-response)**:
```r
library(rms)
design_rms <- svydesign(id = ~psu, strata = ~kstrata,
                         weights = ~wt_itvex, data = df)
model_rcs <- svyglm(
  outcome ~ rcs(continuous_exposure, 3) + age + sex + covariates,
  design = design_rms,
  family = quasibinomial()
)
```

**Weighted quantile sum (WQS) regression**:
```r
library(gWQS)
# WQS for composite exposure (e.g., LE8 components)
result_wqs <- gwqs(
  outcome ~ wqs + age + sex + covariates,
  mix_name = c("comp1", "comp2", "comp3", "comp4"),
  data = df,
  q = 4,           # quartiles
  b = 500,         # bootstrap iterations
  seed = 42,
  family = "binomial",
  weights = df$weight_var
)
```

---

## Weighted SMD (Standardized Mean Difference)

For balance assessment in weighted analyses:

```r
library(survey)
library(tableone)

# SMD in survey design
tab <- svyCreateTableOne(
  vars = covariates,
  strata = "treatment",
  data = design,
  smd = TRUE
)
print(tab, smd = TRUE)
```

**Manual calculation (Python)**:
```python
def weighted_smd(x, treatment, weights, is_binary=False):
    """Calculate weighted standardized mean difference."""
    t_mask = treatment == 1
    c_mask = treatment == 0
    
    w1, w0 = weights[t_mask], weights[c_mask]
    x1, x0 = x[t_mask], x[c_mask]
    
    wm1 = np.average(x1, weights=w1)
    wm0 = np.average(x0, weights=w0)
    
    if is_binary:
        denom = np.sqrt((wm1 * (1 - wm1) + wm0 * (1 - wm0)) / 2)
    else:
        wv1 = np.average((x1 - wm1) ** 2, weights=w1)
        wv0 = np.average((x0 - wm0) ** 2, weights=w0)
        denom = np.sqrt((wv1 + wv0) / 2)
    
    return (wm1 - wm0) / denom if denom > 0 else 0.0
```

---

## Cross-National Analysis Pattern

When comparing two countries using parallel surveys:

1. **Never pool** raw data across countries into a single regression
2. Analyze each country **independently** with country-specific survey design
3. Present results **side-by-side** in the same table
4. Compare effect magnitudes narratively (not via interaction terms)

### Standard Output Table Format

| Variable | Korea (KNHANES) | | US (NHANES) | |
|----------|------|------|------|------|
| | Model 1 wOR (95% CI) | Model 2 wOR (95% CI) | Model 1 wOR (95% CI) | Model 2 wOR (95% CI) |
| Exposure | 1.42 (1.21-1.67) | 1.35 (1.14-1.59) | 1.28 (1.10-1.49) | 1.22 (1.04-1.43) |

---

## Reporting Templates

**Methods**:
"To account for the complex survey designs and ensure nationally representative
estimates, appropriate stratification, clustering, and sampling weights were
applied. Weighted logistic regression models were used to estimate weighted odds
ratios (wORs) and 95% confidence intervals (CIs). Model 1 adjusted for age and
sex, while Model 2 further included [covariates]. All analyses were performed
using SAS version 9.4 (SAS Institute Inc.) [and R version X.X.X (R Foundation
for Statistical Computing)]. A two-sided P value of less than 0.05 was
considered statistically significant."

**Results**:
"In the weighted analysis of [N] participants from [DATASET], [EXPOSURE] was
significantly associated with [OUTCOME] (wOR [X.XX]; 95% CI [X.XX-X.XX]) after
adjusting for [covariates] (Model 2)."

---

## Common Reviewer Flags

1. Survey weights not applied (unweighted analysis of survey data)
2. Strata/cluster variables not specified (incorrect SE estimation)
3. Wrong weight variable used (interview weight for lab variables)
4. Multi-cycle NHANES weights not adjusted (divided by number of cycles)
5. Data pooled across countries instead of analyzed separately
6. Weighted proportions not reported (using raw counts instead)
7. Subgroup analysis includes the stratification variable as covariate
8. Missing data handling not stated (complete case vs imputation)

---

## Python vs R Recommendation

| Task | Recommended | Reason |
|------|-------------|--------|
| Survey-weighted regression | **R (survey)** | Native support, correct variance estimation |
| Survey-weighted Table 1 | **R (tableone)** | `svyCreateTableOne()` handles design |
| WQS regression | **R (gWQS)** | Only available in R |
| Dose-response (RCS) | **R (rms + survey)** | Integrated with survey design |
| Quick descriptives | Python (statsmodels) | Adequate for simple weighted means |

For publication-quality survey analysis, **R is strongly recommended** over Python.
Python's statsmodels supports basic weighted regression but lacks full survey
design support (no strata/cluster specification for variance estimation).

---

## R Packages

- `survey` -- core survey design and analysis
- `tableone` -- survey-weighted baseline tables with SMD
- `rms` -- restricted cubic splines with survey design
- `gWQS` -- weighted quantile sum regression
- `srvyr` -- tidyverse-compatible survey analysis wrapper

## SAS Procedures

- `PROC SURVEYMEANS` -- weighted means and proportions
- `PROC SURVEYFREQ` -- weighted frequency tables and chi-square
- `PROC SURVEYLOGISTIC` -- weighted logistic regression (wOR)
- `PROC SURVEYREG` -- weighted linear regression
- `PROC SURVEYPHREG` -- weighted Cox proportional hazards
