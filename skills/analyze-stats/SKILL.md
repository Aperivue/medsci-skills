---
name: analyze-stats
description: Use when data needs statistical analysis. Runs reproducible Python/R code for Table 1, diagnostic accuracy, agreement, regression, survival, propensity score, survey-weighted and repeated-measures models, with publication tables. Sample size is /calc-sample-size; pooling studies is /meta-analysis.
model: inherit
metadata:
  triggers: "statistics, statistical analysis, analyze data, run stats, table 1, demographics table, ROC curve, agreement analysis, ICC, kappa, survival analysis, Kaplan-Meier, group comparison, logistic regression, linear regression, regression, propensity score, PSM, IPTW, SIPTW, overlap weighting, repeated measures, mixed model, GEE, longitudinal, survey weighted, KNHANES, NHANES, NHIS cohort, complex survey, wOR, weighted odds ratio, claims-based, ICD-10"
---

# Statistical Analysis Skill

Generate reproducible code (Python preferred, R when necessary) for medical research analyses,
run it, and produce publication-ready tables and figures from its output.

## Data Privacy Check

Before reading any data file, check whether it might contain Protected Health Information (PHI):

1. If `*_deidentified.*` files exist in the working directory, use those.
2. If only raw CSV/Excel files exist, ask the user whether the data contain patient identifiers
   (names, national ID / RRN, contact details); if so, have them de-identify it first with
   `/deidentify`.
3. Proceed once the user confirms the data are de-identified or contain no PHI.
4. **NEVER** display raw PHI values (names, phone numbers, RRN) in your output, because console
   output is copied into transcripts and drafts. If you encounter them, warn the user and suggest
   `/deidentify`.

## Reference Files

- `${CLAUDE_SKILL_DIR}/references/templates/` — reusable analysis scripts; read the matching one
  before generating code.
- `${CLAUDE_SKILL_DIR}/references/analysis_guides/` — methodology guides; the Phase 2 table says
  which to read.
- `${CLAUDE_SKILL_DIR}/references/table-standards/` — `table-standards.md` (universal and AMA
  rules, footnote order, gtsummary pipeline), `journal-profiles/` (YAML per journal: radiology,
  jama, nejm, lancet, european_radiology, ajr), `table-types/` (one template per table type),
  `tool-comparison.md` (R/Python table tools).
- `${CLAUDE_SKILL_DIR}/references/style/figure_style.mplstyle` — figure style.

## Workflow

### Phase 1: Data Assessment

1. **Read the data file** (CSV, Excel, TSV, or other tabular format).
2. **Report to the user**: shape (rows x columns); column names and inferred types (continuous,
   categorical, ordinal, binary, datetime); missing values per column (count and percentage);
   first 5 rows; unique value counts for categorical columns.
3. **Identify the analysis unit**: patient, exam, lesion, image, rater, study, etc.
4. If a variable name or coding is uncertain, write `[VERIFY: variable_name]` and ask the user to
   confirm it against the data dictionary; never guess a column name or coding.

### Phase 2: Analysis Plan

**Observational designs** (cohort, case-control, cross-sectional, registry, survey): before
planning, look for a `variable_operationalization.md` from `/define-variables` (or an equivalent
codebook-backed definition table). If none exists, warn the user and recommend running
`/define-variables` first, because exposure/outcome/covariate definitions and cutoffs invented
ad hoc from the data dictionary are a common reason reviewers reject observational work. This is
a warning, not a block: proceed on explicit user confirmation and record that the artifact was
not available.

Propose an analysis plan; the user decides the research question and endpoints. Mark any
clinical definition, cutoff, diagnostic criterion or guideline claim you could not confirm
`[VERIFY]`.

1. **Detect the analysis type** from the table in Analysis-Specific Guidelines, or accept the
   user's specification.
2. **List the specific tests** to be performed.
3. **Identify primary and secondary endpoints**.
4. **State the assumptions** that will be checked (normality, homogeneity, independence).
5. **Note data cleaning** needed (recoding, outlier handling, missing-data strategy).
6. **Anchor the estimand to the research question.**
   - Interaction, synergy or effect modification: the primary estimand is the **interaction
     parameter itself** (a likelihood-ratio test of the interaction term, or the interaction
     OR/HR on one stated scale) — not a main-effect OR whose CI is then read as "no synergy". A
     public-health or biological **synergy** claim is additive-scale: report **RERI**, **AP** or
     **S**, each with a CI (R `interactionR` / `epiR`; Knol & VanderWeele reporting), not only a
     multiplicative product term, because a non-significant multiplicative interaction is
     compatible with a large additive one (and vice versa). Joint categories (high/high vs
     low/low) show joint association, not interaction; "stronger in A than in B" from separate
     stratum estimates is the difference-in-significance fallacy — report the formal interaction
     term.
   - Equivalence or non-inferiority: declare the margin up front (a TOST procedure, or the CI
     compared against a pre-stated MCID); a non-significant difference is not equivalence
     without a margin.
7. **Screen every categorical/binary predictor for separation before fitting anything.** A
   predictor that perfectly predicts the outcome has no finite MLE, and the failure is silent:
   `glm` returns an odds ratio near 0 (or enormous), *p* ≈ 0.99, and an AUC that ends up in a
   table. Pathognomonic imaging signs (T2-FLAIR mismatch, the string sign, a halo sign) cause
   it routinely: 100% specificity means an empty cell by construction.

   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/check_separation.py" \
     --data cohort.csv --outcome idh_mutant --auto --strict
   ```

   `COMPLETE_SEPARATION` (an empty cell) and `QUASI_SEPARATION` (a cell below the sparsity
   floor) both halt the plan. The remedy is a **design** decision, made in the plan: Firth's
   penalised likelihood keeps one model, while a **two-stage rule** — classify the sign-positive
   cases directly, model only the sign-negative remainder — is usually the clinically meaningful
   choice for a pathognomonic sign, because a sign-positive patient is already diagnosed.

Present the plan and **wait for user approval** before executing.

### Phase 3: Execute

Generate and run a Python (preferred) or R script. Every number you report **MUST** come from
its executed output, never estimated or hand-typed, because a number no script reproduces cannot
be verified.

#### Script Structure

Start every script with a reproducibility header:

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

1. **Random seed**: always `np.random.seed(42)` or `set.seed(42)`.
2. **Figure style**: always load the matplotlib style file:
   ```python
   import matplotlib.pyplot as plt
   style_path = os.path.join(os.environ.get('CLAUDE_SKILL_DIR', '.'), 'references/style/figure_style.mplstyle')
   if os.path.exists(style_path):
       plt.style.use(style_path)
   ```
3. **Output files**: save next to the input data, or in a user-specified output directory.
4. **Tables** as CSV plus a printed markdown version (see Output Conventions); **figures** as
   PDF (vector) and PNG (300 DPI).
5. **Console output**: a summary with every number that would appear in the text, formatted for
   direct copy-paste into the Results section.

#### Assumption Checking

Before running parametric tests, check and report:

- **Normality**: Shapiro-Wilk (n < 50) or Kolmogorov-Smirnov (n >= 50), plus a QQ plot.
- **Homogeneity of variance**: Levene's test.
- **If assumptions are violated**: use the non-parametric alternative and say why. Choose by
  these checks, not by convenience.

#### Stratified & Ordinal-Trend Reporting

- **Strata disjointness gate (before any ordinal trend test).** Before a Cochran-Armitage trend
  test (or any analysis that treats tiers as an ordered partition), assert that the strata are
  mutually exclusive and exhaustive: `sum(n per stratum) == unique N` and
  `sum(events per stratum) == total events`. A trend test on overlapping or non-exhaustive strata
  is invalid. Print the per-stratum N/event table and the reconciliation (the analysis-side
  mirror of `/self-review` `check_cohort_arithmetic.py` `PARTITION_OVERLAP`).
- **Secondary stratum HR/OR**: report each with (a) its **reference contrast** (the referent
  category), (b) the **event count** in each stratum, and (c) a **sparse-stratum caveat** when
  any stratum has few events (< 10 is unstable). "HR 1.55 in lean participants" without the
  referent and the events is uninterpretable.
- **Proportion CI lower-bound clamp**: clamp every lower bound to `max(0, lower)`. A zero-event
  Wilson/score interval can print a negative or tiny-exponent bound (e.g. `3.47e-16`) that is a
  display artifact; report `0` (or `0.0%`), and prefer an exact (Clopper-Pearson) interval for
  zero/near-zero cells.

#### Output Manifest

After all analyses complete, save `_analysis_outputs.md` in the output directory, in the format
given in [`references/analysis_run_workflow.md`](references/analysis_run_workflow.md), so
`/make-figures` and `/write-paper` can find the outputs without asking.

For **prespecified binary predictions on independent units**, use the bundled
`scripts/run_analysis.py run` workflow in that file: it embeds data/configuration/code/output
hashes, exact counts, metric-specific denominators and the reproduction command in the same
manifest (`audit` checks recorded versions without rewriting them; `compare` separates declared
context and numeric equality from byte drift). It does not select thresholds or establish study
validity, privacy clearance or reuse rights. Synthetic example:
`python3 ${CLAUDE_SKILL_DIR}/scripts/demo_analysis_run.py --out demo-project`.

### Phase 3.5: Generated-Code Quality Gate

Before reporting any script as final, lint every emitted `.py`/`.R` file:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/check_generated_code.py {script.py} --strict
# or scan a whole output directory:
python3 ${CLAUDE_SKILL_DIR}/scripts/check_generated_code.py --code-dir {analysis_dir} --strict
```

Fix every Major before reporting the script: `MISSING_SEED` (randomness with no seed),
`HARDCODED_DATA_LITERAL` (hand-typed, table-shaped data instead of `read_csv()`/`read.csv()` +
subset), `HARDCODED_ABS_PATH` (non-portable and a PII risk), and `INPLACE_SOURCE_OVERWRITE`
(writing to the path read as input — never modify raw data; write derived outputs to a new
path). Fix the flags `DEBUG_LEFTOVER` and `UNUSED_IMPORT` when tidying.

### Phase 4: Report

After execution, generate manuscript-ready text from the script's output:

1. **Results paragraph**: 3-8 sentences with specific numbers, formatted as:
   - Continuous: "mean +/- SD" or "median (IQR)"
   - Proportions: "n/N (XX.X%)"
   - Test results: "statistic = X.XX, p = 0.XXX"
   - Effect sizes: "Cohen's d = X.XX (95% CI: X.XX-X.XX)"
   - AUC: "AUC = 0.XXX (95% CI: 0.XXX-0.XXX)"
2. **Table/figure captions**: draft captions referencing table/figure numbers.
3. **Methods snippet**: 2-3 sentences describing the statistical methods, for the Methods
   section. Cite only references whose DOI/PMID `/search-lit` confirmed; mark any other
   `[UNVERIFIED - NEEDS MANUAL CHECK]`.

Report statistical results; leave judgments of clinical significance to the user. For designs this
skill does not cover (adaptive or Bayesian trials, complex multilevel or causal-mediation models),
say so and recommend biostatistician review before the results are reported.

## Statistical Reporting Rules (Always Enforced)

1. **Exact p-values**: report exact values (e.g., p = 0.034), not inequalities; below 0.001,
   report p < 0.001.
2. **Confidence intervals**: always report 95% CIs for primary endpoints.
3. **Effect sizes**: report one alongside every p-value (Cohen's d, eta-squared, odds ratio,
   risk ratio, etc., as appropriate).
4. **Multiple comparisons**: for 3+ tests on the same dataset, apply Bonferroni or
   Benjamini-Hochberg correction, state the method, and report both uncorrected and corrected
   p-values.
5. **Sample size**: state n for each group/analysis.
6. **Missing data**: report how many cases were excluded and why.
7. **Decimal places**: p-values to 3 decimals, proportions to 1 decimal, means/SDs to the
   precision of the measurement.
8. **Design/power statistics are code outputs, never hand-computed.** Any minimum detectable
   effect (MDE), a-priori or post-hoc power, or required sample size that will appear in the
   manuscript MUST be printed by the committed script with its method and inputs (n per arm,
   alpha, power, allocation ratio, one/two-sided), not computed in a side tool (G*Power, an
   online calculator) and pasted in, because a manuscript value no script reproduces cannot be
   checked. Use one method family throughout (e.g. the exact noncentral-t via `statsmodels`
   `TTestIndPower` or `scipy`'s `nct`); do not mix a normal approximation for some values with
   exact-t for others.
9. **Estimand & CI output contract.** Every primary point estimate — including quantile
   estimands (T25, median time-to-event), pooled proportions and subdistribution HRs, not just
   ORs/HRs/AUCs — MUST be emitted with its 95% CI, because `/self-review` treats a primary
   metric without one as a defect. In the output CSV carry the interval as explicit columns
   (`estimate, ci_lower, ci_upper`) or as one text column in `est (lo–hi)` form; never a point
   estimate with no interval beside it. Round ORs/HRs/sHRs to 2 decimals and AUC/C-statistic
   to 3.

### Effect-Size Real-World Translation

Whenever a primary result is a correlation, a standardized coefficient, a regression slope, an
OR/HR/RR or a Cohen's d, also report it as a **plain-language unit shift** a non-statistician can
act on — in addition to the effect size (rule 3), not instead of it. This applies to
continuous exposure–outcome associations (Spearman's rho, Pearson's r, standardized slopes), to
relative measures where the audience needs an absolute-risk feel, and to reader or
expert-elicitation studies, clinical-utility framing, abstracts and figure captions.

1. **Pick an anchored contrast on the exposure**, not a 1-unit step. Default: 25th to 75th
   percentile (IQR), both endpoints in native units.
2. **Translate to the outcome scale.**
   - Rank/standardized association (Spearman's rho or a per-SD slope), under an approximately
     monotonic-linear assumption:
     `delta_outcome ~= ((x_p75 - x_p25) / SD_x) * |rho| * SD_outcome`. Report as: "going from
     {x_p25} to {x_p75} {units} is associated with about {delta_outcome} {outcome units} on
     average."
   - Regression slope b: `delta_outcome = b * (x_p75 - x_p25)` (no monotonicity caveat).
   - State the assumption; the IQR translation is a more defensible verbal guide than an
     SD-scaled one.
3. **Bound the claim**: report the contrast, the assumption and a CI on the coefficient; do not
   imply causation from a crude or unadjusted estimate.

**Output contract (clinical utility is a default, not an optional add-on):**
- **OR/HR/RR primary outcomes** → the relative measure **and** the absolute risk at a stated
  baseline, the absolute risk difference, and **NNT** = 1/ARR (or NNH = 1/ARI), with the
  baseline risk explicit. A relative-only headline is incomplete.
- **Continuous outcomes** → the IQR/clinically anchored "Real-world translation" line beneath
  the effect size.
- **Prediction / classification (incl. medical-AI) models** → calibration (Brier score,
  calibration plot, or calibration slope/intercept) alongside discrimination, because AUC alone
  is insufficient; a **decision-curve / net-benefit** pass at the relevant threshold is standard
  output. An incremental claim reports added **net benefit / NRI / IDI over the established
  clinical model**, not the new model's AUC alone. See
  `references/table-standards/table-types/incremental_value.md` and the `make-figures`
  `decision_curve` exemplar (and `render_core_figures.py` for the rendered curve).

## Error Handling

- If a script fails, diagnose the likely cause (missing package, data format mismatch, wrong
  column name) and present a fix. Do not rerun the same script more than once without modifying
  it or asking the user.
- If an R package is unavailable, suggest `install.packages()` and wait for user confirmation.

## Output Conventions

Code, tables, figures and console output are in English.

### Tables

**Before generating any publication table**, load:
1. `${CLAUDE_SKILL_DIR}/references/table-standards/journal-profiles/{journal}.yaml` if a target
   journal is known (it sets footnote markers, P and CI format, title and abbreviation order)
2. `${CLAUDE_SKILL_DIR}/references/table-standards/table-types/{type}.md` for the table type
3. If no journal is specified, default to AMA style (Radiology profile)

**Output formats** (always generate all three): a CSV file (downstream use and archival), a
console markdown rendering (user review), and R `gtsummary` code (Word/LaTeX export). Read
`${CLAUDE_SKILL_DIR}/references/table-standards/table-standards.md` for the gtsummary pipeline
and the footnote placement order (general note, abbreviations, specific notes, probability
notes).

**Validation checklist** (run before finalizing any table):
- [ ] No vertical lines — horizontal rules only (top, below header, bottom)
- [ ] Binary variables show only one level (e.g., Male only)
- [ ] Units in headers, not cells; consistent decimal places per column
- [ ] Variability measure stated: mean (SD) or median (IQR)
- [ ] Statistical test named (footnote or general note); exact P values, never "NS"
- [ ] Effect sizes per clinically meaningful unit (per 10 years, not per 1 year)
- [ ] Reference category stated for categorical predictors
- [ ] Abbreviations defined in footnotes, self-contained per table

### Figures

PDF (vector) + PNG (300 DPI), styled with `figure_style.mplstyle` (Arial, colorblind-safe
palette); width 3.5 inches (single column) or 7.0 inches (double column); axis labels with
units.

## Analysis-Specific Guidelines

Before generating code for any row, read the files listed for it (paths relative to
`${CLAUDE_SKILL_DIR}`); they carry the method rules this file does not repeat.

| Analysis type | Read before generating code | Template |
|---|---|---|
| Table 1 (demographics) | `references/table-standards/table-types/table1_demographics.md` | `references/templates/table1_demographics.py` |
| Diagnostic accuracy (Se, Sp, PPV, NPV, AUC) | `references/analysis_guides/diagnostic_accuracy.md` | `references/templates/diagnostic_accuracy.py` |
| Added value beyond a baseline model (ΔAUC, NRI/IDI, net benefit) | `references/table-standards/table-types/incremental_value.md` | — |
| Reader study (MRMC) | `references/table-standards/table-types/reader_study.md` | — |
| Prediction model (outputs a risk used for a decision) | `references/analysis_guides/calibration.md` | — |
| Inter-rater agreement (kappa, ICC, Bland–Altman) | `references/analysis_guides/agreement_reliability.md`, `references/table-standards/table-types/agreement.md` | `references/templates/agreement_analysis.py` |
| Meta-analysis (pairwise, single-arm proportion, DTA) | `references/analysis_guides/meta_analysis.md` | `references/templates/dta_meta_analysis.R` (DTA) |
| Network meta-analysis (≥3 interventions) | `references/analysis_guides/network_meta_analysis.md` | — |
| Health economic evaluation (CEA, CUA, budget impact) | `references/analysis_guides/health_economic_evaluation.md` | — |
| Survey/Likert (ordinal rating scales) | the Survey/Likert section below | `references/templates/likert_summary.py` |
| Survival, competing risks, interval-censored events | `references/analysis_guides/survival.md`, `references/table-standards/table-types/survival_results.md` | `references/templates/survival_analysis.py` (`--cluster <id>` for nested units) |
| Group comparison, correlation | `references/analysis_guides/test_selection.md` | — |
| Logistic or linear regression | `references/analysis_guides/regression.md` | `references/templates/regression.py` (`regression_type = "logistic"` or `"linear"`) |
| Propensity score (PSM, IPTW, SIPTW, overlap weighting) | `references/analysis_guides/propensity_score.md` | `references/templates/propensity_score.py` |
| Survey-weighted (KNHANES, NHANES, KCHS) | `references/analysis_guides/survey_weighted.md` | `references/templates/survey_weighted_analysis.py` |
| NHIS claims-based studies (ICD-10 definitions) | `references/analysis_guides/nhis_icd10_mapping.md` | — |
| Repeated measures (LMM, GEE, RM ANOVA) | `references/analysis_guides/repeated_measures.md`; if missing > 5%, also `references/analysis_guides/missing_data.md` and apply MICE before analysis | `references/templates/repeated_measures.py` |
| Mediation | `references/analysis_guides/mediation.md` | — |
| Multiple testing, many-exposure scans (ExWAS/EWAS) | `references/analysis_guides/multiplicity.md` | — |
| Mendelian randomization | `references/analysis_guides/mendelian_randomization.md` | — |
| Polygenic risk score | `references/analysis_guides/polygenic_risk_score.md` | — |
| Burden of disease, decomposition, forecasting | `references/analysis_guides/burden_decomposition_forecasting.md` | — |

Comparing models: use a paired DeLong test for two separate scores on the same patients. For a
nested "baseline + new term" model fitted and evaluated on the same data, DeLong is not the
added-value test — test the term (likelihood ratio) and report ΔAUC with its CI.

The rules below have no separate guide.

### Survey/Likert

- Descriptives per item: median, IQR, frequency distribution. Group comparisons: Mann-Whitney
  or Kruskal-Wallis (ordinal data). Visualization: diverging stacked bar chart.
- Internal consistency: Cronbach's alpha with item-total correlations.
- **Reverse-coding guard (run before reliability)**: recode every negatively worded item
  `(min+max) - x` before computing the scale total or Cronbach's alpha. An un-recoded reverse
  item produces a *negative* item-rest correlation and can make alpha negative — a coding bug,
  **not** evidence of a multidimensional construct; do not defend it as one. `likert_summary.py`
  prints per-item item-rest correlations, flags negative ones as reverse-code suspects, warns on
  a negative alpha, and applies the recode with `--reverse-items E3 ...`. To screen at cleaning
  time, run `python3 "${CLAUDE_SKILL_DIR}/../clean-data/scripts/check_reverse_coding.py"`.

### Covariate Pitfalls: Structural Zeros & Dose/Duration Variables

Applies to any multivariable adjustment (logistic / linear / Cox / propensity score / survey-
weighted) with a **dose/duration variable anchored to a categorical exposure** (pack-years under
smoking status, grams/week under alcohol use, cessation duration under former smoker):

- **Structural-zero guard (do not impute):** a never-smoker's `pack_years` is a *structural
  zero* — known to be 0 by definition of the category, not missing. Imputing it (MICE/MNAR)
  fabricates a dose for unexposed subjects and corrupts the exposure contrast. Before imputing a
  dose/duration column, set the implied zero explicitly (`IF status == 'never' THEN dose = 0`)
  and impute only the genuinely missing residual among the exposed. `/clean-data` flags `never`
  rows with a NULL dose (`scripts/check_structural_zero.py`).
- **Complete-case collapse (adjust for status, not dose):** a dose variable in a complete-case
  model drops the unexposed stratum wholesale when its zeros are stored as NULL, collapsing n
  (commonly 40–60%) and distorting subgroup estimates. Adjust for the **categorical status**
  (never/former/current); reserve the continuous **dose** for an exposed-only secondary
  analysis. Report n before and after model fitting and confirm the denominator did not
  silently collapse.

### Covariate Selection: Over-adjustment in a Cross-Sectional Outcome Model

Applies to any cross-sectional / single-visit outcome regression (temporal order is not
observed). Select covariates causally, not statistically:

- **Do not adjust for a consequence or mediator of the outcome** — that is over-adjustment /
  collider bias and removes part of the effect under study. Signature case: with **eGFR** as the
  outcome, serum uric acid is renally excreted (a lower eGFR raises urate), so it is an
  outcome-consequence, not a confounder; blood pressure and HbA1c are often similarly
  downstream. Classify each candidate covariate against a DAG as confounder / mediator /
  outcome-consequence / collider, and keep only confounders in the primary model.
- **"It differs in Table 1" is not a confounder-selection criterion.** Imbalance justifies
  *considering* a variable; a mediator or outcome-consequence stays out however imbalanced it is.
- **Report the suspect-covariate sensitivity + VIF.** Make a parsimonious, history-/design-based
  model primary; report the fuller model as a sensitivity analysis that drops (or adds) the
  suspect covariate and show whether the headline estimate moves. Print VIF and the n actually
  fitted. If dropping the covariate materially changes the estimate, carry that to the abstract
  and conclusion.
- **Compare adjusted vs unadjusted on the SAME frame.** When extended adjustment adds covariates
  with missingness, the analytic n shrinks (e.g. 84 → 49 events), and comparing that estimate
  with the full-frame unadjusted one confounds adjustment with who was dropped. Refit the
  unadjusted model on the reduced complete-case frame and report unadjusted and adjusted on that
  frame beside the full-frame estimate; never describe "adjustment changed the estimate" from a
  comparison across different frames (or use multiple imputation so all models share one frame).
