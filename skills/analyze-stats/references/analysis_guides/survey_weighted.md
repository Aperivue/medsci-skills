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
| **NHANES** | `SDMVSTRA` | `SDMVPSU` | `WTMEC2YR` (exam) or `WTINT2YR` (interview); subsample weights such as `WTSAF2YR` (fasting); 2017–March 2020 pre-pandemic files: `WTMECPRP` / `WTINTPRP` / `WTSAFPRP` | 2-year cycles; combine cycles with the NCHS rules below |
| **KCHS** | varies by year | varies by year | `wt` | Annual community survey; single-stage cluster design |

### Weight Selection Rules

- **Use the weight of the smallest subsample that contains every variable in the analysis**
  (NCHS: "You must use the weight of the smallest subpopulation that includes all the variables
  you want to include in your analysis").
  - Interview-only variables: interview weight.
  - Exam variables: exam (MEC) weight.
  - **Subsample laboratory variables use their own subsample weight**, not the MEC weight:
    NHANES fasting glucose `LBXGLU` and fasting triglycerides `LBXTR` come with `WTSAF2YR`
    (`WTSAFPRP` in the pre-pandemic file); environmental/other subsamples likewise carry their own
    weight in the component file. Check each component's documentation. The standard
    biochemistry profile (`LBXSGL`, `LBXSTR`) is drawn regardless of fasting status and is not a
    fasting value.
  - Nutrition variables (KNHANES): nutrition weight.
- **Multi-cycle NHANES** (NCHS weighting tutorial):
  - 2001–2002 onward: divide each 2-year weight by the number of 2-year cycles combined
    (e.g. 2011–2018, four cycles: `WTMEC2YR / 4`).
  - **1999–2002**: the 2-year weights for 1999–2000 and 2001–2002 are not comparable; NCHS
    requires the 4-year weights (`WTMEC4YR`, `WTINT4YR`). Combined with later cycles, give
    1999–2002 the share 2/k: e.g. 1999–2006 is `2/4 * WTMEC4YR` for 1999–2002 and
    `1/4 * WTMEC2YR` for 2003–2006.
  - **2017–March 2020 pre-pandemic** covers 3.2 years, so weights are proportional to time, not
    divided by the number of files: combined with 2015–2016, `2/5.2 * WTMEC2YR` (2015–2016) and
    `3.2/5.2 * WTMECPRP` (2017–March 2020). The pre-pandemic weights are in `P_DEMO`, not
    `DEMO_J`.
- **Single-cycle analysis**: use the cycle-specific weight as-is.

### Subpopulation (domain) analysis — never row-delete

A restricted analysis (adults only, one sex, a disease subgroup) must keep the **full design** and select the domain, **not** filter the data frame and refit. Row-deletion discards the strata/PSU structure of the dropped units and gives wrong standard errors and design degrees of freedom.

- R `survey`: `subset(design, age >= 18)` on the **design object** (or `svyby`), not `svydesign(data = df[df$age>=18, ])`.
- Stata: `svy, subpop(if age>=18):` — never `keep if age>=18` before `svy:`.
- Python: `references/templates/survey_weighted_analysis.py` treats subgroups and complete cases
  as domains of the full design (it reproduces `svyglm` on `subset(design, …)`). statsmodels
  alone has no survey design object: `freq_weights`/`var_weights` give design-free SEs.

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

**Python**: use `references/templates/survey_weighted_analysis.py`. It computes Taylor-
linearization variance from weights + strata + PSUs (the `svyglm` estimator, t-based CIs on the
design df) and writes a matching `survey_analysis.R` for cross-checking. Do not use
`statsmodels` GLM with `freq_weights` for survey inference: it treats each respondent as *w*
people, so the "n" becomes the population total and the CI collapses (synthetic check,
30 strata x 6 PSUs: 1.24 (1.24–1.25) vs `svyglm` 1.24 (0.90–1.72)).

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

# NHANES (2-year cycle; exam variables. Use WTSAF2YR for fasting-subsample labs)
design_us <- svydesign(
  id = ~SDMVPSU,
  strata = ~SDMVSTRA,
  weights = ~WTMEC2YR,
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
  WEIGHT WTMEC2YR;
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

# Extract weighted OR (wOR) with 95% CI. confint() on an svyglm uses a t quantile on the
# design degrees of freedom -- the same reference distribution as the P value. A hand-built
# coef +/- 1.96*SE interval does not, and can disagree with the P value when the design
# df is small.
extract_wor <- function(model, var) {
  ci <- exp(confint(model))[var, ]
  data.frame(wOR = exp(coef(model)[var]), CI_lower = ci[1], CI_upper = ci[2],
             P = summary(model)$coefficients[var, "Pr(>|t|)"],
             design_df = model$df.residual)
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
                         weights = ~wt_itvex, data = df, nest = TRUE)
model_rcs <- svyglm(
  outcome ~ rcs(continuous_exposure, 3) + age + sex + covariates,
  design = design_rms,
  family = quasibinomial()
)
```

**Weighted quantile sum (WQS) regression — not design-based.** `gWQS::gwqs()` fits an ordinary
GLM: `weights =` enters the sampling weights as case weights, and strata and PSUs are ignored, so
its CIs and P values are **not** survey-valid inference (contrast "Model-based SEs on weighted
points" above). Use it only as an exploratory mixture analysis, label it as such, and keep the
design-based `svyglm` models as the inferential results.
```r
library(gWQS)   # exploratory only: no strata/PSU in the variance
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
4. **Test the between-country difference** — a cross-national paper's headline is the
   contrast, and "significant in Korea, not in the US" is the difference-in-significance
   fallacy (Gelman & Stern 2006, doi:10.1198/000313006X152649). The two samples are
   independent, so the ratio of wORs has a closed-form CI (Altman & Bland 2003,
   doi:10.1136/bmj.326.7382.219), using each country's **design-based** SE:

```r
# m_kr, m_us: svyglm fits from the two country designs; "exposure" = the coefficient name
b1 <- coef(m_kr)["exposure"]; s1 <- SE(m_kr)["exposure"]
b2 <- coef(m_us)["exposure"]; s2 <- SE(m_us)["exposure"]
d <- b1 - b2; se_d <- sqrt(s1^2 + s2^2)
ratio <- exp(d); ci <- exp(d + c(-1, 1) * qnorm(0.975) * se_d)
p_diff <- 2 * pnorm(-abs(d / se_d))
```

### Standard Output Table Format

| Variable | Korea (KNHANES) | | US (NHANES) | | Korea vs US |
|----------|------|------|------|------|------|
| | Model 1 wOR (95% CI) | Model 2 wOR (95% CI) | Model 1 wOR (95% CI) | Model 2 wOR (95% CI) | Ratio of Model 2 wORs (95% CI); P |
| Exposure | [X.XX (X.XX-X.XX)] | [X.XX (X.XX-X.XX)] | [X.XX (X.XX-X.XX)] | [X.XX (X.XX-X.XX)] | [X.XX (X.XX-X.XX)]; [P] |

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
"In the weighted analysis of [unweighted N] participants from [DATASET], the
Model 2 weighted odds ratio for [OUTCOME] comparing [EXPOSURE] with [REFERENCE] was
[X.XX] (95% CI [X.XX-X.XX]; P = [exact]), adjusted for [covariates]." Describe the
association in words only after reading the interval; do not write "significantly
associated" into a template.

---

## Common Reviewer Flags

1. Survey weights not applied (unweighted analysis of survey data)
2. Strata/cluster variables not specified (incorrect SE estimation)
3. Wrong weight variable used (interview weight for lab variables; MEC weight for a fasting- or
   other subsample variable)
4. Multi-cycle NHANES weights not combined by the NCHS rules (divide by the number of 2-year
   cycles from 2001–2002 on; 4-year weights for 1999–2002; 3.2/total years for 2017–March 2020)
5. Data pooled across countries instead of analyzed separately
6. Weighted proportions not reported (using raw counts instead)
7. Subgroup analysis includes the stratification variable as covariate
8. Missing data handling not stated (complete case vs imputation)

---

## Python vs R Recommendation

| Task | Recommended | Reason |
|------|-------------|--------|
| Survey-weighted logistic regression | R (survey) or `survey_weighted_analysis.py` | Both design-based (linearization); the Python template writes the matching R script |
| Survey-weighted Table 1 | **R (tableone)** | `svyCreateTableOne()` handles design |
| WQS regression | R (gWQS) | Exploratory only — not design-based |
| Dose-response (RCS) | **R (rms + survey)** | Integrated with survey design |
| Quick descriptives | Python (statsmodels) | Adequate for simple weighted means |

For designs or models beyond weighted logistic regression (replicate weights, Cox, Poisson,
calibration, svyby tables), use R `survey`. Plain statsmodels weighting is not survey
inference: it has no strata/PSU in the variance.

---

## R Packages

- `survey` -- core survey design and analysis
- `tableone` -- survey-weighted baseline tables with SMD
- `rms` -- restricted cubic splines with survey design
- `gWQS` -- weighted quantile sum regression (not design-based; exploratory)
- `srvyr` -- tidyverse-compatible survey analysis wrapper

## SAS Procedures

- `PROC SURVEYMEANS` -- weighted means and proportions
- `PROC SURVEYFREQ` -- weighted frequency tables and chi-square
- `PROC SURVEYLOGISTIC` -- weighted logistic regression (wOR)
- `PROC SURVEYREG` -- weighted linear regression
- `PROC SURVEYPHREG` -- weighted Cox proportional hazards
