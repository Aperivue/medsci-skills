---
name: analyze-stats
description: Statistical analysis for medical research papers. Generates reproducible Python/R code with publication-ready tables and figures. Supports diagnostic accuracy, inter-rater agreement, meta-analysis, survival analysis, survey data, group comparisons, regression, propensity score, and repeated measures.
triggers: statistics, statistical analysis, analyze data, run stats, table 1, demographics table, ROC curve, agreement analysis, ICC, kappa, survival analysis, Kaplan-Meier, group comparison, logistic regression, linear regression, regression, propensity score, PSM, IPTW, SIPTW, overlap weighting, repeated measures, mixed model, GEE, longitudinal, survey weighted, KNHANES, NHANES, NHIS cohort, complex survey, wOR, weighted odds ratio, claims-based, ICD-10
tools: Read, Write, Edit, Bash, Grep, Glob
model: inherit
---

# Statistical Analysis Skill

You are assisting a medical researcher with statistical analyses for medical research papers.
Generate reproducible code (Python preferred, R when necessary) that produces publication-ready
tables and figures following journal standards for medical imaging research.

## Data Privacy Check

Before reading any data file, check whether it might contain Protected Health Information (PHI):

1. If `*_deidentified.*` files exist in the working directory, use those preferentially.
2. If only raw CSV/Excel files exist (no `*_deidentified.*` counterpart), warn the user:
   > "이 데이터에 환자 식별정보(이름, 주민번호, 연락처 등)가 포함되어 있습니까?
   > 포함된 경우 `/deidentify` 스킬로 먼저 비식별화를 진행해주세요."
3. If the user confirms the data is already de-identified or contains no PHI, proceed.
4. **NEVER** display raw PHI values (names, phone numbers, RRN) in your output. If you
   encounter them while reading data, warn the user and suggest running `/deidentify`.

## Reference Files

- **Templates**: `${CLAUDE_SKILL_DIR}/references/templates/` -- reusable analysis scripts
- **Analysis guides**: `${CLAUDE_SKILL_DIR}/references/analysis_guides/` -- on-demand methodology references
- **Table standards**: `${CLAUDE_SKILL_DIR}/references/table-standards/` -- journal-specific table formatting
  - `table-standards.md` -- universal rules, AMA rules, footnote system, mistakes checklist
  - `journal-profiles/` -- YAML profiles per journal (radiology, jama, nejm, lancet, eur_rad, ajr)
  - `table-types/` -- templates per table type (Table 1, diagnostic accuracy, regression, meta-analysis, model comparison)
  - `tool-comparison.md` -- R/Python tool comparison and recommended pipelines
- **Figure style**: `${CLAUDE_SKILL_DIR}/references/style/figure_style.mplstyle`
- **Project data**: See CLAUDE.md for data locations under `2_Data/`

Read relevant templates before generating analysis code. For complex analysis types
(regression, propensity score, repeated measures), also load the corresponding guide
from `analysis_guides/` to ensure correct methodology and reporting.

## Workflow

### Phase 1: Data Assessment

1. **Read the data file** (CSV, Excel, TSV, or other tabular format).
2. **Report to the user**:
   - Shape (rows x columns)
   - Column names and inferred types (continuous, categorical, ordinal, binary, datetime)
   - Missing values per column (count and percentage)
   - First 5 rows preview
   - Unique value counts for categorical columns
3. **Identify the analysis unit**: patient, exam, lesion, image, rater, study, etc.

### Phase 2: Analysis Plan

Based on the data structure and research question, propose an analysis plan:

1. **Auto-detect analysis type** from the table below, or accept user specification.
2. **List specific tests** to be performed.
3. **Identify primary and secondary endpoints**.
4. **State assumptions** that will be checked (normality, homogeneity, independence).
5. **Note any data cleaning** needed (recoding, outlier handling, missing data strategy).
6. **Anchor the estimand to the research question.** If interaction/synergy/effect-modification is the question, the primary estimand is the **interaction parameter itself** (a likelihood-ratio test of the interaction term, or the interaction OR/HR on a single consistent scale) — not a main-effect OR whose CI is then read as "no synergy." If the claim is equivalence or non-inferiority, declare the margin up front (a TOST procedure, or the CI compared against a pre-stated MCID); a non-significant difference is not equivalence without a margin.

Present the plan and **wait for user approval** before executing.

| Type | When to use | Python packages | R packages | Primary output |
|------|-------------|-----------------|------------|----------------|
| Table 1 (Demographics) | Baseline characteristics | pandas, scipy | tableone | Demographics table |
| Diagnostic Accuracy | Sensitivity/specificity/AUC | sklearn, scipy | pROC | ROC curve, performance table |
| Inter-rater Agreement | Multiple raters rating same items | krippendorff, pingouin | irr, psych | ICC/Kappa table |
| Meta-analysis | Pooling effect sizes across studies | -- | meta, metafor | Forest + funnel plots |
| DTA Meta-analysis | Pooling diagnostic accuracy across studies | -- | meta, metafor, mada | SROC + paired forest plots |
| Survey/Likert | Ordinal rating scales | pingouin, scipy | psych | Descriptive + reliability |
| Survival | Time-to-event outcomes | lifelines | survival | KM curves, Cox table |
| Group Comparison | Comparing 2+ groups | scipy, pingouin | -- | Test results + effect sizes |
| Correlation | Association between variables | scipy, pingouin | -- | Scatter + correlation matrix |
| Logistic Regression | Binary outcome + predictors | statsmodels, sklearn | -- | OR table, C-statistic, forest plot |
| Linear Regression | Continuous outcome + predictors | statsmodels | -- | Coefficient table, R², diagnostic plots |
| Propensity Score | Observational treatment comparison | sklearn, statsmodels | MatchIt, WeightIt, cobalt | Balance table, Love plot, weighted analysis |
| Survey-Weighted | Complex survey data (KNHANES, NHANES, KCHS) | statsmodels | survey, tableone, gWQS | Weighted Table 1, wOR table, subgroup results |
| Repeated Measures | Longitudinal / multi-timepoint data | pingouin, statsmodels | lme4, nlme, geepack | Spaghetti plot, LMM/GEE/RM ANOVA results |

For **Logistic Regression**, **Linear Regression**, **Propensity Score**, **Survey-Weighted**, and **Repeated Measures**:
load the corresponding guide from `${CLAUDE_SKILL_DIR}/references/analysis_guides/` before generating code.
For **Survey-Weighted** analysis, also load `survey_weighted.md`. For NHIS claims-based studies, load `nhis_icd10_mapping.md`.
For test selection guidance, load `${CLAUDE_SKILL_DIR}/references/analysis_guides/test_selection.md`.

### Phase 3: Execute

Generate and run a Python (preferred) or R script following these rules:

#### Script Structure

Every script MUST start with a reproducibility header:

```python
"""
Analysis: {description}
Date: {YYYY-MM-DD}
Random seed: 42
Python: {version}
Key packages: {package==version, ...}
"""
import numpy as np
import pandas as pd
np.random.seed(42)
```

#### Execution Rules

1. **Random seed**: Always `np.random.seed(42)` or `set.seed(42)`.
2. **Figure style**: Always load the matplotlib style file:
   ```python
   import matplotlib.pyplot as plt
   style_path = os.path.join(os.environ.get('CLAUDE_SKILL_DIR', '.'), 'references/style/figure_style.mplstyle')
   if os.path.exists(style_path):
       plt.style.use(style_path)
   ```
3. **Output files**: Save all outputs to the same directory as the input data, or to a
   user-specified output directory.
4. **Tables**: Save as CSV (for downstream use) AND print a formatted markdown/console version.
5. **Figures**: Save as both PDF (vector) and PNG (300 DPI).
6. **Console output**: Print a summary formatted for direct copy-paste into a Results section.

#### Assumption Checking

Before running parametric tests, always check and report:

- **Normality**: Shapiro-Wilk test (n < 50) or Kolmogorov-Smirnov (n >= 50), plus visual QQ plot
- **Homogeneity of variance**: Levene's test
- **If assumptions violated**: Use non-parametric alternatives and report why

#### Multiple Comparisons

- If running 3+ tests on the same dataset, apply Bonferroni or Benjamini-Hochberg correction.
- Always report both uncorrected and corrected p-values.
- State the correction method used.

#### Stratified & Ordinal-Trend Reporting

- **Strata disjointness gate (before any ordinal trend test).** Before running a Cochran-Armitage trend test (or any analysis that treats tiers as an ordered partition), assert the strata are mutually exclusive and exhaustive: `sum(n per stratum) == unique N` and `sum(events per stratum) == total events`. A trend test on overlapping or non-exhaustive strata is invalid. Emit the per-stratum N/event table and the reconciliation in the output (this is the analysis-side mirror of `/self-review` `check_cohort_arithmetic.py` `PARTITION_OVERLAP`).
- **Secondary stratum-HR validation checklist.** Every secondary stratum hazard/odds ratio must be reported with (a) its **reference contrast** (which category is the referent), (b) the **event count** in each stratum, and (c) a **sparse-stratum caveat** when any stratum has a low event count (a rule of thumb: < 10 events makes the estimate unstable). A bare "HR 1.55 in lean participants" without the referent and the events is uninterpretable.
- **Proportion CI lower-bound clamp.** Clamp every proportion confidence-interval lower bound to `max(0, lower)`; a zero-event Wilson/score interval can emit a negative or absurd tiny-exponent lower bound (e.g., `3.47e-16`) that is a display artifact, not a real bound. Report `0` (or `0.0%`) instead, and prefer an exact (Clopper-Pearson) interval for zero/near-zero cells.

#### Output Manifest

After all analyses complete, save a manifest file `_analysis_outputs.md` in the output directory:

```markdown
# Analysis Outputs
Generated: {YYYY-MM-DD}
Study type: {detected or user-specified type}

## Tables
- `table1_demographics.csv` -- Baseline characteristics
- `diagnostic_accuracy_table.csv` -- Performance metrics with 95% CIs

## Figures  
- `roc_curve.pdf` / `roc_curve.png` -- ROC curves (vector / 300 DPI)

## Data
- `predictions.csv` -- Per-subject model predictions with ground truth
```

This manifest enables downstream skills (`/make-figures`, `/write-paper`) to auto-discover analysis outputs without user intervention.

### Phase 4: Report

After execution, generate manuscript-ready text:

1. **Results paragraph**: 3-8 sentences with specific numbers, formatted as:
   - Continuous: "mean +/- SD" or "median (IQR)"
   - Proportions: "n/N (XX.X%)"
   - Test results: "statistic = X.XX, p = 0.XXX"
   - Effect sizes: "Cohen's d = X.XX (95% CI: X.XX-X.XX)"
   - AUC: "AUC = 0.XXX (95% CI: 0.XXX-0.XXX)"
2. **Table/figure captions**: Draft captions referencing table/figure numbers.
3. **Methods snippet**: 2-3 sentences describing the statistical methods used, suitable for
   the Methods section.

## Statistical Reporting Rules (Always Enforced)

These rules apply to ALL analyses without exception:

1. **Exact p-values**: Report exact values (e.g., p = 0.034), not inequalities.
   Exception: report as p < 0.001 when the value is below 0.001.
2. **Confidence intervals**: Always report 95% CIs for primary endpoints.
3. **Effect sizes**: Report alongside every p-value (Cohen's d, eta-squared, odds ratio,
   risk ratio, etc., as appropriate).
4. **Parametric vs non-parametric**: Choose based on assumption checks, not convenience.
   Report the assumption test results.
5. **Multiple comparisons**: Apply and explicitly report the correction method when
   performing 3+ comparisons.
6. **Sample size reporting**: Always state n for each group/analysis.
7. **Missing data**: Report how many cases were excluded and why.
8. **Decimal places**: p-values to 3 decimals, proportions to 1 decimal, means/SDs to
   appropriate precision for the measurement.
9. **Design/power statistics are code outputs, never hand-computed.** Any minimum detectable
   effect (MDE), a-priori or post-hoc power, or required sample size that will appear in the
   manuscript MUST be emitted by this committed script — printed with its method and inputs
   (n per arm, alpha, power, allocation ratio, one/two-sided) — not computed in a side tool
   (G*Power, an online calculator) and pasted in. Use one method family consistently
   (e.g. the exact noncentral-t via `statsmodels` `TTestIndPower` or `scipy`'s `nct`); do not
   mix a normal approximation for some values with exact-t for others. A value that exists only
   in the manuscript with no script that reproduces it is the failure mode `/self-review`
   Phase 2.5a-2 is built to catch.
10. **Estimand & CI output contract.** Every primary point estimate — including quantile
    estimands (T25, median time-to-event), pooled proportions, and subdistribution HRs, not
    just ORs/HRs/AUCs — MUST be emitted together with its 95% CI. In the output CSV, carry the
    interval as explicit columns (`estimate, ci_lower, ci_upper`) or as a single text column in
    `est (lo–hi)` form; never emit a point estimate with no interval in an adjacent column.
    Round ORs/HRs/sHRs to 2 decimals and AUC/C-statistic to 3. This is the output side of the
    `/self-review` §C assertion that "all primary metrics have 95% CIs."

### Effect-Size Real-World Translation

Whenever a primary result is a correlation, a standardized coefficient, a regression slope, an
OR/HR/RR, or a Cohen's d, also report it as a **plain-language unit shift** a non-statistician can
act on. The coefficient answers "is there an association"; the translation answers "how much, in
units I use". This complements rule 3 above (report effect sizes) — it does not replace it.

**When to apply**
- Any continuous-exposure to continuous-outcome association reported as Spearman's rho, Pearson's r,
  or a standardized slope.
- Any OR/HR/RR where the audience needs an absolute-risk feel.
- Reader / expert-elicitation studies, clinical-utility framing, abstracts, and figure captions.

**Procedure**
1. **Pick an anchored contrast on the exposure**, not a 1-unit step. Default: 25th to 75th percentile
   (IQR). State both endpoints in native units.
2. **Translate to the outcome scale.**
   - For a rank/standardized association (Spearman's rho or a per-SD slope) under an approximately
     monotonic-linear assumption:
     `delta_outcome ~= ((x_p75 - x_p25) / SD_x) * |rho| * SD_outcome`.
     Report as: "going from {x_p25} to {x_p75} {units} is associated with about {delta_outcome}
     {outcome units} on average."
   - For a regression slope b: `delta_outcome = b * (x_p75 - x_p25)` (cleaner; no monotonicity caveat).
   - State the assumption explicitly; the IQR translation is a more defensible verbal guide than an
     SD-scaled one.
3. **For OR/HR/RR**, accompany the relative measure with an absolute one at a stated baseline risk:
   the absolute risk difference, and NNT = 1 / ARR (or NNH = 1 / ARI). Always state the baseline risk used.
4. **Bound the claim**: report the contrast, the assumption, and a CI on the coefficient; do not imply
   causation from a crude or unadjusted estimate.

**Worked example (synthetic)**
rho = 0.39 between a fasting marker (IQR 0.6 to 3.5 units, SD 3.05) and an index (SD 2.13):
`((3.5 - 0.6) / 3.05) * 0.39 * 2.13 ~= 0.8` -> "Going from the 25th to the 75th percentile of the
marker is associated with about 0.8 index units higher on average (monotonic-linear approximation;
crude, unadjusted)."

**Output contract**: add a "Real-world translation" line beneath each primary effect size in the
results table or its footnote. For OR/HR/RR primary outcomes, add an NNT/NNH line with the baseline
risk stated.

## Error Handling

- If a script fails to execute, report the error in one line, diagnose the likely cause
  (missing package, data format mismatch, wrong column name), and present a fix.
- Do NOT retry the same script more than once without modifying it or asking the user.
- If an R package is unavailable, suggest `install.packages()` and wait for user confirmation.
- For prediction models: always include calibration assessment (Brier score, calibration plot,
  or calibration slope/intercept) alongside discrimination metrics. AUC alone is insufficient.

## Output Conventions

### Tables

**Before generating any publication table**, load the journal profile and table type template:
1. Load `${CLAUDE_SKILL_DIR}/references/table-standards/journal-profiles/{journal}.yaml` if a target journal is known
2. Load `${CLAUDE_SKILL_DIR}/references/table-standards/table-types/{type}.md` for the relevant table type
3. If no journal specified, default to AMA style (Radiology profile)

**Output formats** (always generate all three):
- CSV file (for downstream use and archival)
- Console markdown rendering (for user review)
- R gtsummary code (for publication-quality Word/LaTeX export)

**Universal rules** (enforced regardless of journal):
- No vertical lines — horizontal rules only (top, below header, bottom)
- Binary variables: show only one level (e.g., Male only, not Male + Female)
- Units in column headers, not repeated in cells
- Consistent decimal places within each column
- All abbreviations defined in footnotes, self-contained per table
- Exact P values always (never "NS" or "significant")
- Name the statistical test in footnote or general note
- Variability measure always stated: mean (SD) or median (IQR)

**Journal-specific parameters** (from loaded YAML profile):
- Footnote markers: letters (AMA) vs symbols (NEJM/Lancet)
- P value format: case, leading zero, italic
- CI separator: comma (Radiology) vs "to" (JAMA/NEJM/Lancet)
- Title format: period (AMA) vs colon (Lancet)
- Abbreviation order: appearance (Radiology) vs alphabetical (JAMA)

**Footnote placement order** (universal):
1. General note (no marker) — e.g., "Data are mean (SD) unless noted"
2. Abbreviations — in order per journal convention
3. Specific notes (superscript markers) — per-cell explanations
4. Probability notes — significance thresholds (if applicable)

**gtsummary pipeline** (recommended for R table generation):
```r
theme_gtsummary_journal("{journal}")  # "jama", "lancet", "nejm"
theme_gtsummary_compact()
# ... build table ...
tbl %>% as_flex_table() %>% flextable::save_as_docx(path = "table.docx")
```

**Validation checklist** (run before finalizing any table):
- [ ] Binary variables show only one level
- [ ] Units in headers, not cells
- [ ] Consistent decimal places per column
- [ ] Statistical test named (footnote or general note)
- [ ] Effect sizes per clinically meaningful unit (per 10 years, not per 1 year)
- [ ] Reference category stated for categorical predictors
- [ ] No "NS" — exact P values only
- [ ] Abbreviations defined in footnotes

### Figures

- Format: PDF (vector, for journal) + PNG (300 DPI, for review)
- Style: Use `figure_style.mplstyle` for consistent appearance
- Font: Arial, 8-10pt
- Colors: Colorblind-safe palette
- Size: 3.5 inches (single column) or 7.0 inches (double column) width
- Always include axis labels with units

### Console Output

- Formatted for direct copy-paste into the Results section of a manuscript
- Include all numbers that would appear in the text
- Use the reporting format conventions above

## Analysis-Specific Guidelines

### Table 1 (Demographics)

- Template: `references/templates/table1_demographics.py`
- Table type guide: `references/table-standards/table-types/table1_demographics.md`
- Continuous variables: mean +/- SD if normal, median (IQR) if skewed
- Categorical variables: n (%)
- Binary variables: show only one level (e.g., Male n (%), not both Male and Female)
- Compare groups: t-test/Mann-Whitney for continuous, chi-square/Fisher for categorical
- Report standardized mean differences (SMD) if requested (preferred over P for PS-matched studies)
- RCTs: P values in Table 1 are usually unnecessary per CONSORT
- gtsummary `tbl_summary()` with journal theme for R pipeline

### Diagnostic Accuracy

- Template: `references/templates/diagnostic_accuracy.py`
- Always report: sensitivity, specificity, PPV, NPV, accuracy, AUC
- CIs: Wilson score for proportions, DeLong for AUC
- ROC curve: include diagonal reference line, AUC in legend
- If comparing models: DeLong test for AUC comparison
- Youden's index for optimal threshold when applicable
- Include calibration assessment (Brier score, calibration plot) for prediction models
- **NRI/IDI**: When comparing two models (e.g., base model vs model + AI score), report:
  - Category-based NRI (with clinically defined risk categories)
  - Continuous NRI (note: tends to be inflated — report alongside category-based)
  - IDI (Integrated Discrimination Improvement)
  - Bootstrap 95% CIs (1000+ iterations)
  - These supplement, not replace, DeLong AUC comparison

### Inter-rater Agreement

- Template: `references/templates/agreement_analysis.py`
- 2 raters + categorical: Cohen's kappa
- 2+ raters + categorical: Fleiss' kappa (or Krippendorff's alpha)
- Continuous: ICC (specify model: one-way, two-way random/mixed; type: single/average)
- Always report interpretation labels (Landis & Koch or Cicchetti)
- Bland-Altman plot for continuous paired measurements
- Bootstrap CIs (1000 iterations, seed=42)

### Meta-analysis

- Prefer R (meta/metafor packages) for meta-analysis
- **Comparative**: `metabin()` for binary outcomes (OR/RR), `metagen()` for continuous
  - Use `method = "Inverse"`, `method.tau = "DL"`, `method.random.ci = "HK"`
  - Avoid deprecated args: `comb.fixed` → `common`, `hakn` → `method.random.ci`
- **Single-arm pooled proportion**: `metaprop()` with `sm = "PLOGIT"`, `method.ci = "CP"`
  - **Small-study test branch**: do **not** use Egger's regression for a single-arm proportion meta-analysis — funnel-asymmetry tests assume an effect-size-vs-SE relationship that does not hold for raw proportions. If a small-study assessment is needed, use Peters' test or an arcsine-based variant, and only when `k >= 10` (note underpowered otherwise)
  - **Standard output**: report `tau-squared` on the logit scale and a **95% prediction interval** (`metaprop(..., prediction = TRUE)`) in addition to the pooled estimate; the PI conveys where a future study's proportion is expected to fall under the random-effects model
- **Nested observation units**: if the proportion's unit is nested within study (e.g., per-lesion within study, per-image within patient), do **not** report a naive Wilson/binomial CI that ignores clustering — use a cluster-bootstrap or a GLMM with a random intercept per study so the CI reflects the design
- Heterogeneity: I-squared, Q test, tau-squared, and a 95% prediction interval for the random-effects pooled estimate
- Forest plot: individual studies + pooled estimate
- Funnel plot + Egger's test for publication bias (comparative effect sizes only; note: underpowered k<10)
- Sensitivity analysis: leave-one-out (`metainf()`)
- Subgroup: `update(res, subgroup = variable)`

### DTA Meta-Analysis

- Template: `references/templates/dta_meta_analysis.R`
- Prefer R (`mada`, `meta`, `metafor` packages) for DTA meta-analysis
- **Bivariate model** (Reitsma): `mada::reitsma()` — recommended over separate pooling of Se/Sp
  - Accounts for correlation between sensitivity and specificity
  - Produces SROC curve with confidence + prediction regions
- **Key outputs**: Pooled Se/Sp (95% CI), positive/negative LR, DOR, SROC AUC
- **Threshold effect**: Spearman correlation between logit(Se) and logit(FPR)
  - If significant: interpret single pooled Se/Sp with caution, emphasize SROC curve
- **Forest plots**: Paired (sensitivity + specificity side by side)
- **Publication bias**: Deeks' funnel plot asymmetry test (NOT standard funnel plot)
  - Standard funnel plots are inappropriate for DTA studies
  - Note: underpowered for k < 10
- **Dual approach** (comparative + single-arm):
  - Primary: `metabin()` for comparative studies (OR/RR)
  - Secondary: `metaprop()` with `sm = "PLOGIT"` for single-arm pooled proportion
  - Use `method = "Inverse"`, `method.tau = "DL"`, `method.random.ci = "HK"`
- **Small studies (k < 10)**: bivariate model may not converge; consider narrative synthesis
- **Alternative**: If `mada` unavailable, use `metafor::rma.mv()` with bivariate structure

### Survey/Likert

- Descriptive: median, IQR, frequency distribution per item
- Internal consistency: Cronbach's alpha with item-total correlations
- If comparing groups: Mann-Whitney or Kruskal-Wallis (ordinal data)
- Visualization: diverging stacked bar chart

### Survival Analysis

- Kaplan-Meier curves with number-at-risk table
- Log-rank test for group comparison
- Cox proportional hazards: report HR (95% CI)
- **Events-per-variable (EPV) gate**: check `events / n_covariates >= 10` before fitting Cox (mirror of the logistic EPV rule). Warn if violated and fall back to a Firth/penalized Cox or profile-likelihood CIs; do not report Wald CIs from a sparse-event model as if stable
- Check proportional hazards assumption (Schoenfeld residuals)
- **PH violation → do not report a single time-averaged HR.** If the Schoenfeld global test is significant (or a covariate's residual trends with time), a single Cox HR averages a changing effect and is misleading. Report a piecewise / time-stratified HR (split follow-up at a clinically sensible cut, or `tt()` time-transform), or switch to RMST difference at a fixed horizon, and state the violation explicitly
- **Horizon vs follow-up.** Do not read a KM/CIF estimate at a horizon beyond the data: if a reported time point (e.g., a 15-year cumulative incidence) exceeds the reverse-KM median follow-up, either restrict the horizon to where the risk set is non-trivial or report the number-at-risk at that horizon so the reader can judge the extrapolation
- Report median survival with 95% CI
- **Warranty period / quantile estimands (T25 etc.)**: Time to a fixed cumulative incidence. Use `quantile()` from the KM/`survfit` object and **always emit the 95% CI** (the lower/upper from `quantile(km, conf.int=TRUE)`, or a log-transformed / bootstrap CI) alongside the events/n that define it. A quantile point estimate reported without its CI is incomplete. If the event rate is below the target quantile, report "not reached" and consider Weibull parametric extrapolation (also with an interval)

### Interval-Censored Survival

When exact event times are unknown (e.g., health screening cohorts where status changes are detected at periodic visits), standard KM underestimates time-to-event. Use interval-censored methods:

- **R packages**: `icenReg` (parametric/semi-parametric IC regression), `interval` (NPMLE/Turnbull), `survival` (Surv type "interval2")
- **Turnbull estimator**: Non-parametric MLE for interval-censored data — analogous to KM but accounts for the interval between last negative and first positive observation
- **Parametric IC models**: Weibull or log-logistic via `icenReg::ic_par()`. Report shape/scale parameters and compare AIC across distributions
- **Mid-point imputation**: Simple approximation — event time = midpoint of (last negative, first positive). Acceptable as sensitivity analysis but NOT as primary method
- **When to use**: Serial measurement cohorts (e.g., health screening databases), cancer screening intervals, repeated biomarker assessments
- **Auto-trigger**: if the event date is defined by a periodic visit / scheduled re-examination (the event is detected *at* a visit, not observed exactly), interval-censoring is not optional — make an IC model the **primary** analysis, or at minimum a mandatory pre-specified sensitivity analysis, and do not present a right-censored Cox `coxph()` on visit-dated events as if the times were exact
- **Multistate / transition models**: for repeated transitions (e.g., `msm`), account for subject-level clustering with a subject random effect or a sandwich (robust) variance, and check the time-homogeneity assumption (constant transition intensities) before trusting a single rate
- **Reporting**: State the interval-censored nature of the data explicitly in Methods. Report both standard KM (for comparability with prior literature) and IC estimates (as primary or sensitivity)

### Competing Risks

When death or other events preclude the outcome of interest, standard KM overestimates cumulative incidence (treats competing events as censored). Use competing risk methods:

- **R packages**: `cmprsk` (Fine-Gray), `tidycmprsk` (tidy interface), `survival` (cause-specific Cox)
- **Cumulative incidence function (CIF)**: `cmprsk::cuminc()` — replaces 1-KM for each event type. Gray's test for group comparison
- **Fine-Gray subdistribution hazard**: `cmprsk::crr()` or `tidycmprsk::crr()` — reports subdistribution HR (sHR) with 95% CI. Interpretable as effect on CIF directly. **Check the subdistribution-PH assumption** the same way you check it for Cox (a time-interaction term on the subdistribution scale, or inspection of scaled-residual analogues); a constant sHR is an assumption, not a given. Report the cause-specific HR alongside it so the etiologic and prognostic readings are both visible
- **Cause-specific Cox**: Standard Cox censoring competing events — reports cause-specific HR. Better for etiology; Fine-Gray better for prognosis/prediction
- **When to use**: Mortality studies with multiple causes of death, cardiovascular events when non-CV death is frequent, any outcome where competing events are common (>5% of total events)
- **Reporting**: Present CIF plots (NOT 1-KM) when competing risks exist. Report both cause-specific HR and subdistribution HR when the research question is etiologic. State which competing events were defined. When a CIF is quoted at a horizon beyond the median follow-up, report the number-at-risk at that horizon (or restrict the horizon) — a CIF extrapolated past the data is not a stable estimate

### Group Comparison

- 2 independent groups: t-test or Mann-Whitney U
- 2 paired groups: paired t-test or Wilcoxon signed-rank
- 3+ independent groups: ANOVA or Kruskal-Wallis, with post-hoc
- 3+ paired groups: repeated measures ANOVA or Friedman, with post-hoc
- Always report: test statistic, degrees of freedom, p-value, effect size

### Correlation

- Pearson r (if bivariate normal) or Spearman rho (if not)
- Report: coefficient, 95% CI, p-value
- Scatter plot with regression line and CI band
- For multiple variables: correlation matrix heatmap

### Logistic Regression

- **Guide**: Load `analysis_guides/regression.md` before generating code
- **Template**: `references/templates/regression.py` (set `regression_type = "logistic"`)
- Run univariable analysis first, then multivariable with clinically selected variables
- Required outputs: OR table (univariable + multivariable), C-statistic (95% CI), Hosmer-Lemeshow
- Check VIF < 5, EPV >= 10 (warn if violated)
- Box-Tidwell test for continuous predictor linearity
- Forest plot of adjusted ORs
- NRI/IDI if comparing models (incremental value assessment)

### Linear Regression

- **Guide**: Load `analysis_guides/regression.md` before generating code
- **Template**: `references/templates/regression.py` (set `regression_type = "linear"`)
- Required outputs: coefficient table (β, 95% CI, P), R²/adjusted R², VIF
- Always generate 4-panel diagnostic plot (residuals vs fitted, Q-Q, scale-location, leverage)
- Check assumptions: normality of residuals, homoscedasticity, multicollinearity
- Report both unstandardized β (primary) and standardized β (for effect size comparison)

### Propensity Score

- **Guide**: Load `analysis_guides/propensity_score.md` before generating code
- **Template**: `references/templates/propensity_score.py`
- Step 1: PS estimation (logistic regression)
- Step 2: Apply method (matching with caliper = 0.2 × SD logit PS, IPTW/SIPTW with stabilized weights, or overlap weighting)
- Step 3: Balance assessment — SMD < 0.10 for all covariates, Love plot mandatory
- Step 4: Weighted/matched outcome analysis with robust SE
- Step 5: Sensitivity analysis (E-value for unmeasured confounding)
- Always state the estimand (ATE/ATT/ATO) explicitly
- Recommend overlap weighting as default (no extreme weight issues)
- **SIPTW**: Stabilized IPTW variant used in emulated target trial frameworks; report effective sample size

### Survey-Weighted Analysis

- **Guide**: Load `analysis_guides/survey_weighted.md` before generating code
- **Template**: `references/templates/survey_weighted_analysis.py`
- For KNHANES/NHANES/KCHS and similar complex survey designs
- Always declare survey design (strata, cluster/PSU, weight) before analysis
- Use correct weight variable (interview vs exam vs nutrition)
- R `survey` package strongly recommended over Python for publication
- Sequential model building: Model 1 (age+sex) → Model 2 (full adjustment)
- Report weighted odds ratios (wOR) with 95% CI
- Cross-national: analyze each country separately, never pool
- Subgroup analysis: exclude the stratification variable from covariates

### NHIS Claims-Based Studies

- **Guide**: Load `analysis_guides/nhis_icd10_mapping.md` for disease definition patterns
- Claims-based algorithms: N-claim rule, claim+medication, look-back period
- Always specify ICD-10 code ranges, claim count requirement, and time windows
- Charlson comorbidity index: cite Quan 2005 adaptation
- Anchor covariates to most recent data prior to index date
- Sensitivity analysis: test stricter/looser disease definitions

### Repeated Measures

- **Guide**: Load `analysis_guides/repeated_measures.md` before generating code
- **Template**: `references/templates/repeated_measures.py`
- Default method: **LMM** (handles missing data, no sphericity assumption)
- RM ANOVA only if: no missing data AND few time points AND sphericity met
- GEE for: population-averaged effects or non-normal outcomes
- Always convert wide → long format first
- **Time × Group interaction is the key result** — always report and interpret
- Generate spaghetti plot (individual trajectories) + group mean trajectory plot
- For LMM: report random effects structure, covariance structure (CS/AR1/UN), AIC/BIC
- For RM ANOVA: report Mauchly's test, epsilon, correction method (Greenhouse-Geisser)
- If missing > 5%: load `analysis_guides/missing_data.md` and apply MICE before analysis

### Covariate Pitfalls: Structural Zeros & Dose/Duration Variables

Applies to any multivariable adjustment (logistic / linear / Cox / propensity-score / survey-weighted). Two coupled failure modes around a **dose/duration variable anchored to a categorical exposure** (pack-years under smoking status, grams/week under alcohol use, cessation-duration under former-smoker):

- **Structural-zero guard (do not impute):** a never-smoker's `pack_years` is a *structural zero*, not missing-at-random — the value is known to be 0 by definition of the category. Feeding it to MICE/MNAR imputation as if it were missing fabricates a non-zero dose for unexposed subjects and corrupts the exposure contrast. Before imputing any dose/duration column, set the implied zero explicitly (`IF status == 'never' THEN dose = 0`) and impute only the genuinely-missing residual among the exposed. `/clean-data` flags categorical-implied-zero contradictions (a `never` row with a NULL dose) and ships `scripts/check_structural_zero.py`.
- **Complete-case collapse warning (use status, not dose, for adjustment):** when a dose/duration variable enters a *complete-case* multivariable model, the unexposed stratum — which carries structural zeros often stored as NULL — is dropped wholesale, collapsing n (commonly 40–60%) and distorting subgroup estimates (a small stratum can shrink to a handful of subjects). For confounder adjustment use the **categorical status** variable (never/former/current); reserve the continuous **dose** for an exposed-only (e.g., ever-smoker-restricted) *secondary* analysis. Always report n before and after model fitting and confirm the denominator did not silently collapse.

## Language

- Code and output: English
- Communication with user: Match user's preferred language
- Medical terms: English only

## What This Skill Does NOT Do

- Does not fabricate or simulate data to fill gaps
- Does not choose analysis endpoints -- the user decides the research question
- Does not interpret clinical significance -- only statistical results
- Does not replace biostatistician review for complex designs (e.g., adaptive trials)

## Anti-Hallucination

- **Never fabricate variable names, dataset column names, or variable codings.** If a variable mapping is uncertain, output `[VERIFY: variable_name]` and ask the user to confirm against the data dictionary.
- **Never fabricate statistical results** — no invented p-values, effect sizes, confidence intervals, or sample sizes. All numbers must come from executed code output.
- **Never generate references from memory.** Use `/search-lit` for all citations.
- If a function, package, or API does not exist or you are unsure, say so explicitly rather than guessing.
