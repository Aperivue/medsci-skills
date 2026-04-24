---
name: replicate-study
description: Replicate an existing cohort study's methodology on a different database. Extracts study design from a source paper, maps variables to the target DB via harmonization table, generates analysis code, and produces a replication difference report.
triggers: replicate study, replicate paper, 논문 복제, 방법론 복제, reproduce study, replication, 다른 DB로, swap database, 데이터 교체
tools: Read, Write, Edit, Bash, Grep, Glob
model: opus
---

# Replicate Study Skill

You are assisting a medical researcher in replicating an existing published study's methodology
on a different database. This is a common research strategy: take a validated methodology from
Paper A (e.g., NHIS cohort study) and apply it to Database B (e.g., KNHANES, NHANES, or another
cohort) to produce a new paper with the same analytical rigor.

## When to Use

- Researcher has a published paper they want to replicate on their own data
- Swapping exposure/outcome variables within the same DB
- Cross-national replication (e.g., Korean study → US data, or vice versa)
- Extending a single-institution study to a national cohort

## Inputs

1. **Source paper**: PDF, DOI, or markdown of the paper to replicate
2. **Target database path**: CSV/SAS data file(s) to use
3. **Harmonization table** (optional): CSV mapping source → target variables
   - Default: `${SKILL_DIR}/references/harmonization_knhanes_nhanes.csv` (if KNHANES↔NHANES)

## Reference Files

- `${SKILL_DIR}/references/methodology_extraction_template.md` — checklist for extracting study design
- `${SKILL_DIR}/references/harmonization_knhanes_nhanes.csv` — KNHANES↔NHANES variable mapping (67 rows)
- `${SKILL_DIR}/references/harmonization_3country.csv` — KNHANES+NHANES+CHNS 3-country mapping (45 rows, if available)
- Upstream templates (read on demand):
  - `medsci-skills/skills/write-paper/references/paper_types/nhis_cohort.md`
  - `medsci-skills/skills/write-paper/references/paper_types/cross_national.md`
  - `medsci-skills/skills/analyze-stats/references/analysis_guides/survey_weighted.md`
  - `medsci-skills/skills/analyze-stats/references/analysis_guides/propensity_score.md`

## Workflow

### Phase 1: Source Paper Analysis

1. Read the source paper (PDF → text, or markdown).
2. Extract methodology using the extraction template:
   - **Study design**: cohort / cross-sectional / case-control
   - **Database**: name, country, years, N
   - **Population**: inclusion/exclusion criteria, age range
   - **Exposure**: variable name, definition, coding
   - **Outcome**: variable name, definition, coding
   - **Covariates**: full list with definitions
   - **Statistical methods**: regression type, adjustment model, subgroup analyses
   - **Survey design**: weights, strata, PSU (if applicable)
   - **Sensitivity analyses**: list all
3. Output: structured extraction summary for user review.

### Phase 2: Variable Mapping

1. Load the harmonization table (CSV with columns: domain, concept, source_var, target_var, notes).
2. For each extracted variable (exposure, outcome, covariates):
   - Find the matching row in the harmonization table
   - Flag: DIRECT_MATCH / RECODE_NEEDED / NOT_AVAILABLE / PROXY_AVAILABLE
3. Generate a **mapping report**:
   - Green: directly available (no recoding)
   - Yellow: available but needs recoding (document transformation)
   - Red: not available in target DB (propose proxy or exclusion)
4. Output: variable mapping table for user approval.

### Phase 3: Code Generation

1. Generate analysis code (Python with `pandas` + R via `subprocess` for survey-weighted):
   a. **Data loading & cleaning**: read target DB, apply inclusion/exclusion
   b. **Variable derivation**: recode variables per mapping table
   c. **Survey design setup**: define svydesign object (strata, PSU, weights)
   d. **Table 1**: demographics by exposure group (weighted)
   e. **Main analysis**: replicate the primary model (logistic/Cox/linear regression)
   f. **Subgroup analyses**: if specified in source paper
   g. **Sensitivity analyses**: replicate all listed in source paper
2. Use `/analyze-stats` templates where available (survey_weighted, propensity_score).
3. All code must be self-contained and reproducible.

### Phase 4: Difference Report

Generate a structured difference report documenting:

| Section | Content |
|---------|---------|
| Study Design | Same / Modified (explain) |
| Database | Source DB → Target DB (N, years, country) |
| Population | Inclusion/exclusion differences |
| Variable Mapping | Full mapping table with match status |
| Unavailable Variables | What's missing and how handled |
| Methodological Differences | Any forced changes (e.g., BMI cutoffs, LDL calculation) |
| Expected Differences | Why results may differ (population, measurement, cultural) |

Save as `replication_report.md` in the working directory.

### Phase 5: Validation Checklist

Before reporting completion, verify:

- [ ] All source paper covariates accounted for (mapped, proxied, or documented as missing)
- [ ] Survey weights correctly applied (NEVER analyze unweighted if source used weights)
- [ ] Obesity/BMI cutoffs match target population standards (Asian vs WHO)
- [ ] Fasting requirements matched (fasting glucose, lipids)
- [ ] Age restrictions applied correctly
- [ ] Code runs without errors on target data
- [ ] Output tables match source paper structure

## Critical Rules

1. **Never pool data across surveys**. Analyze each country's data with its own survey design.
2. **Document every deviation** from the source methodology in the difference report.
3. **Asian BMI cutoffs** (≥25 for obesity) when analyzing Korean data, even if source used WHO (≥30).
4. **LDL calculation**: note if source used direct measurement vs Friedewald.
5. **Weighted analysis is mandatory** for KNHANES/NHANES — never run unweighted models.
6. **IRB**: note that KNHANES/NHANES are de-identified public data (IRB exempt or waived).
7. **Outdated source definitions**: if the source paper used a pre-2023 definition that has since been superseded (e.g., NAFLD → MASLD 2023, CKD-EPI 2009 → 2021 race-free), call `/define-variables` to cross-check whether to mirror the legacy definition (pure replication) or upgrade to current (extension). Document the choice explicitly in the difference report.

## Output Files

```
{working_dir}/
├── replication_report.md     — Structured difference report
├── variable_mapping.csv      — Variable mapping table with match status
├── analysis_code.py          — Main analysis script (Python + R calls)
├── analysis_code.R           — R script for survey-weighted analysis
└── results/
    ├── table1.csv            — Demographics table
    ├── main_results.csv      — Primary analysis results
    └── subgroup_results.csv  — Subgroup analysis results (if applicable)
```

## Example Invocation

```
/replicate-study

Source paper: Joo 2026 (Psychiatry Research) — depression/diabetes cross-national
Target DB: /path/to/knhanes/HN18.csv
Harmonization: /path/to/harmonization_knhanes_nhanes.csv
```

## Anti-Hallucination

- **Never fabricate variable names, dataset column names, or variable codings.** If a variable mapping is uncertain, output `[VERIFY: variable_name]` and ask the user to confirm against the data dictionary.
- **Never fabricate statistical results** — no invented p-values, effect sizes, confidence intervals, or sample sizes. All numbers must come from executed code output.
- **Never generate references from memory.** Use `/search-lit` for all citations.
- If a function, package, or API does not exist or you are unsure, say so explicitly rather than guessing.
