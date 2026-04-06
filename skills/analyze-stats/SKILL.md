---
name: analyze-stats
description: Statistical analysis for medical research papers. Generates reproducible Python/R code with publication-ready tables and figures. Supports diagnostic accuracy, inter-rater agreement, meta-analysis, survival analysis, survey data, and group comparisons.
triggers: statistics, statistical analysis, 통계분석, analyze data, run stats, table 1, demographics table, ROC curve, agreement analysis, ICC, kappa, survival analysis, Kaplan-Meier, group comparison
tools: Read, Write, Edit, Bash, Grep, Glob
model: inherit
---

# Statistical Analysis Skill

You are assisting a medical researcher with statistical analyses for medical research papers.
Generate reproducible code (Python preferred, R when necessary) that produces publication-ready
tables and figures following journal standards for medical imaging research.

## Reference Files

- **Templates**: `~/.claude/skills/analyze-stats/references/templates/` -- reusable analysis scripts
- **Figure style**: `~/.claude/skills/analyze-stats/references/style/figure_style.mplstyle`
- **Project data**: See CLAUDE.md for data locations under `2_Data/`

Read relevant templates before generating analysis code.

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

Present the plan and **wait for user approval** before executing.

| Type | When to use | Python packages | R packages | Primary output |
|------|-------------|-----------------|------------|----------------|
| Table 1 (Demographics) | Baseline characteristics | pandas, scipy | tableone | Demographics table |
| Diagnostic Accuracy | Sensitivity/specificity/AUC | sklearn, scipy | pROC | ROC curve, performance table |
| Inter-rater Agreement | Multiple raters rating same items | krippendorff, pingouin | irr, psych | ICC/Kappa table |
| Meta-analysis | Pooling effect sizes across studies | -- | meta, metafor | Forest + funnel plots |
| Survey/Likert | Ordinal rating scales | pingouin, scipy | psych | Descriptive + reliability |
| Survival | Time-to-event outcomes | lifelines | survival | KM curves, Cox table |
| Group Comparison | Comparing 2+ groups | scipy, pingouin | -- | Test results + effect sizes |
| Correlation | Association between variables | scipy, pingouin | -- | Scatter + correlation matrix |

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
   plt.style.use(os.path.expanduser(
       '~/.claude/skills/analyze-stats/references/style/figure_style.mplstyle'))
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

## Output Conventions

### Tables

- Format: CSV file + console markdown rendering
- Include: column headers, units in parentheses, footnotes for abbreviations
- For Table 1: include p-values column, test names in footnote, overall + per-group columns

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
- Continuous variables: mean +/- SD if normal, median (IQR) if skewed
- Categorical variables: n (%)
- Compare groups: t-test/Mann-Whitney for continuous, chi-square/Fisher for categorical
- Report standardized mean differences (SMD) if requested

### Diagnostic Accuracy

- Template: `references/templates/diagnostic_accuracy.py`
- Always report: sensitivity, specificity, PPV, NPV, accuracy, AUC
- CIs: Wilson score for proportions, DeLong for AUC
- ROC curve: include diagonal reference line, AUC in legend
- If comparing models: DeLong test for AUC comparison
- Youden's index for optimal threshold when applicable
- Include calibration assessment (Brier score, calibration plot) for prediction models

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
- Heterogeneity: I-squared, Q test, tau-squared
- Forest plot: individual studies + pooled estimate
- Funnel plot + Egger's test for publication bias (note: underpowered k<10)
- Sensitivity analysis: leave-one-out (`metainf()`)
- Subgroup: `update(res, subgroup = variable)`

### Survey/Likert

- Descriptive: median, IQR, frequency distribution per item
- Internal consistency: Cronbach's alpha with item-total correlations
- If comparing groups: Mann-Whitney or Kruskal-Wallis (ordinal data)
- Visualization: diverging stacked bar chart

### Survival Analysis

- Kaplan-Meier curves with number-at-risk table
- Log-rank test for group comparison
- Cox proportional hazards: report HR (95% CI)
- Check proportional hazards assumption (Schoenfeld residuals)
- Report median survival with 95% CI

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

## Language

- Code and output: English
- Communication with user: Match user's preferred language
- Medical terms: English only

## What This Skill Does NOT Do

- Does not fabricate or simulate data to fill gaps
- Does not choose analysis endpoints -- the user decides the research question
- Does not interpret clinical significance -- only statistical results
- Does not replace biostatistician review for complex designs (e.g., adaptive trials)
