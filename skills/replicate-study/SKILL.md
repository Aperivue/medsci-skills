---
name: replicate-study
description: Replicate an existing cohort study's methodology on a different database. Extracts study design from a source paper, maps variables to the target DB via harmonization table, generates analysis code, and produces a replication difference report.
triggers: replicate study, replicate paper, 논문 복제, 방법론 복제, reproduce study, replication, 다른 DB로, swap database, 데이터 교체
tools: Read, Write, Edit, Bash, Grep, Glob
model: opus
---

# Replicate Study Skill

Apply a published study's methodology to a different database and report every place the target
database forced a deviation.

## Inputs

1. **Source paper**: PDF, DOI, or markdown of the paper to replicate
2. **Target database path**: CSV/SAS data file(s) to use
3. **Harmonization table** (optional): CSV mapping source → target variables
   - Default: `${CLAUDE_SKILL_DIR}/references/harmonization_knhanes_nhanes.csv` (if KNHANES↔NHANES)

## Reference Files

- `${CLAUDE_SKILL_DIR}/references/methodology_extraction_template.md` — checklist for extracting study design
- `${CLAUDE_SKILL_DIR}/references/harmonization_knhanes_nhanes.csv` — KNHANES↔NHANES variable mapping (67 rows)
- `${CLAUDE_SKILL_DIR}/references/harmonization_3country.csv` — KNHANES+NHANES+CHNS 3-country mapping (46 rows)
- Upstream templates (read on demand):
  - `${CLAUDE_SKILL_DIR}/../write-paper/references/paper_types/nhis_cohort.md`
  - `${CLAUDE_SKILL_DIR}/../write-paper/references/paper_types/cross_national.md`
  - `${CLAUDE_SKILL_DIR}/../analyze-stats/references/analysis_guides/survey_weighted.md`
  - `${CLAUDE_SKILL_DIR}/../analyze-stats/references/analysis_guides/propensity_score.md`

## Workflow

### Phase 1: Source Paper Analysis

1. Read the source paper (PDF → text, or markdown).
2. Extract the methodology by filling `methodology_extraction_template.md`: study design, database
   (name, country, years, N), population (inclusion/exclusion, age range), exposure and outcome
   (variable, definition, coding), covariates with definitions, statistical methods (regression
   type, adjustment models, subgroup analyses), survey design (weights, strata, PSU), and every
   sensitivity analysis.
3. **Outdated source definitions**: if the source used a pre-2023 definition that has since been
   superseded (e.g., NAFLD → MASLD 2023, CKD-EPI 2009 → 2021 race-free), call `/define-variables`
   to cross-check whether to mirror the legacy definition (pure replication) or upgrade to the
   current one (extension). Record the choice in the difference report.
4. Output: structured extraction summary for user review.

### Phase 2: Variable Mapping

1. Load the harmonization table (columns: `domain`, `concept`, `concept_en`, one variable/label
   column set per database such as `knhanes_var` / `nhanes_var`, and `harmonization_notes`).
2. For each extracted variable (exposure, outcome, covariates), find the matching row and flag it
   DIRECT_MATCH / RECODE_NEEDED / NOT_AVAILABLE / PROXY_AVAILABLE. If a mapping is uncertain,
   write `[VERIFY: variable_name]` and ask the user to confirm it against the data dictionary;
   never guess a variable name, column name or coding.
3. Generate a **mapping report**:
   - Green: directly available (no recoding)
   - Yellow: available but needs recoding (document transformation)
   - Red: not available in target DB (propose proxy or exclusion)
4. Output: variable mapping table (`variable_mapping.csv`) for user approval.

### Phase 3: Code Generation

1. Generate self-contained, reproducible analysis code (Python with `pandas` + R via
   `subprocess` for survey-weighted analysis):
   a. **Data loading & cleaning**: read target DB, apply inclusion/exclusion
   b. **Variable derivation**: recode variables per mapping table
   c. **Survey design setup**: define svydesign object (strata, PSU, weights). Weighted analysis
      is mandatory for KNHANES/NHANES — never run unweighted models. Never pool data across
      surveys; analyze each country's data with its own survey design.
   d. **Table 1**: demographics by exposure group (weighted)
   e. **Main analysis**: replicate the primary model (logistic/Cox/linear regression)
   f. **Subgroup analyses**: if specified in source paper
   g. **Sensitivity analyses**: replicate all listed in source paper
2. Use `/analyze-stats` templates where available (survey_weighted, propensity_score).
3. Use **Asian BMI cutoffs** (≥25 for obesity) for Korean data, even if the source used WHO (≥30).
4. Run the code on the target data; every number in `results/` and the report comes from that
   executed output.

### Phase 4: Difference Report

Save `replication_report.md` in the working directory, documenting every deviation from the
source methodology:

| Section | Content |
|---------|---------|
| Study Design | Same / Modified (explain) |
| Database | Source DB → Target DB (N, years, country) |
| Population | Inclusion/exclusion differences |
| Variable Mapping | Full mapping table with match status |
| Unavailable Variables | What's missing and how handled |
| Methodological Differences | Any forced changes (e.g., BMI cutoffs, LDL direct measurement vs Friedewald) |
| Expected Differences | Why results may differ (population, measurement, cultural) |

Note that KNHANES/NHANES are de-identified public data (IRB exempt or waived). Cite only with a
`/search-lit`-confirmed DOI/PMID; otherwise mark the reference `[UNVERIFIED - NEEDS MANUAL CHECK]`.

### Phase 5: Validation Checklist

Before reporting completion, verify:

- [ ] All source paper covariates accounted for (mapped, proxied, or documented as missing)
- [ ] Survey weights correctly applied (NEVER analyze unweighted if source used weights)
- [ ] Obesity/BMI cutoffs match target population standards (Asian vs WHO)
- [ ] Fasting requirements matched (fasting glucose, lipids)
- [ ] Age restrictions applied correctly
- [ ] Code runs without errors on target data
- [ ] Output tables match source paper structure

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
