---
name: clean-data
description: Interactive data profiling and cleaning assistant for medical research. Three-stage workflow (profile, flag, code-generate) with user approval gates at each step. Handles missing values, outliers, duplicates, and type mismatches in CSV/Excel clinical data. Does NOT auto-clean — all decisions require researcher confirmation.
triggers: clean data, data cleaning, data preprocessing, data profiling, missing values, outliers, check my data, data quality
tools: Read, Write, Edit, Bash, Grep, Glob
model: inherit
---

# Data Profiling and Cleaning Skill

Profile, flag, and generate cleaning code for a clinical dataset in three stages, each ending at a
user-approval gate. You generate code and reports; you do NOT auto-clean data. Every cleaning decision
needs the researcher's explicit confirmation, because clinical cleaning calls need domain knowledge.

**PHI first.** If the dataset contains PHI or PII, run `/deidentify` before proceeding, and use
`*_deidentified.*` files when they exist in the working directory. Otherwise work from the data
dictionary / codebook alone, or in a local-only environment with no network access. The skill writes
code that runs on the data; it does not need to see the raw rows to write it.

## Three-Stage Workflow

### Stage 1: Profiling

**Input**: CSV/Excel file path OR data dictionary/codebook

1. Adapt `${CLAUDE_SKILL_DIR}/references/profiling_template.py` (pandas) to the dataset. It reports:
   variable and row counts, data types; missing count and percentage per variable; unique counts for
   categorical variables; min/max/mean/median/SD for numeric variables; histograms and bar charts.
2. If the user provides a codebook, cross-reference variable names, expected types, and expected
   ranges. Never guess a column name or coding: when a mapping is uncertain, write
   `[VERIFY: variable_name]` and ask the user to confirm it against the data dictionary.
3. Present the summary (see Output Format). Every count and statistic comes from the executed
   script's output.

**Gate**: The user reviews the profile. Ask whether to proceed to Stage 2 (Flagging) and whether any
variables should be excluded or focused on.

### Stage 2: Flagging

Read `${CLAUDE_SKILL_DIR}/references/cleaning_patterns.md` for missing-data mechanisms, outlier
decision rules, duplicate detection, date handling, and clinical pitfalls (inequality-prefixed lab
values, mixed units, sentinel values). Flag issues in these categories:

1. **Missing values**: variables with >5% missing; pattern analysis (MCAR/MAR/MNAR heuristic).
2. **Statistical outliers**: IQR method (Q1 - 1.5*IQR, Q3 + 1.5*IQR) and Z-score (|z| > 3).
3. **Duplicates**: exact row duplicates AND near-duplicates (same patient ID, different dates).
4. **Type mismatches**: numeric stored as string, dates in inconsistent formats.
5. **Implausible values**: flag against the codebook's valid range or, when the codebook is silent,
   the domain-default hard physiologic bounds in `references/implausible_value_rules.md` §1. An
   implausible value is a likely data-entry/unit/sentinel error (correct or set missing); a
   statistical outlier (#2) is biologically possible (keep + sensitivity analysis). Check units before
   calling a bound violation an error. Never auto-fix.
5b. **Cross-field inconsistencies**: logical contradictions per `references/implausible_value_rules.md`
   §2 — temporal ordering (birth ≤ event ≤ death, admission ≤ discharge), derived-vs-source (recomputed
   BMI/age; subset ≤ superset; total = sum of parts), sex-/state-specific fields, and min ≤ max /
   diastolic < systolic pairs. Name the rule that fired; a hard contradiction is High severity.
6. **Category inconsistencies**: typos and variants in categorical values ("Male", "male", "M", "MALE").
7. **Categorical-implied zeros**: when a category defines a natural zero for a dose/duration variable
   (`smoking_status == 'never'` implies `pack_years == 0`; `alcohol_use == 'never'` implies
   `grams_per_week == 0`), flag records that store the implied zero as NULL. This is a contradiction,
   not a missing-data pattern: complete-case models silently drop those never-smokers and MICE imputes
   them a non-zero dose, corrupting the exposure contrast. Suggested action: "Set dose = 0 where
   category == reference level; impute only the residual missingness among the exposed." Detected by
   `scripts/check_structural_zero.py` given the category↔dose mapping; pairs with `/analyze-stats`
   "Covariate Pitfalls: Structural Zeros & Dose/Duration Variables".
8. **Reverse-coded scale items**: in a multi-item Likert scale that mixes positively and negatively
   worded items, every reverse item must be recoded `(min+max) - x` *before* the scale total or
   Cronbach's alpha is computed. An un-recoded reverse item correlates negatively with the rest and
   collapses alpha, often to a **negative** value. A negative alpha is a reverse-coding bug, not
   "multidimensional structure". Suggested action: "Recode reverse-worded items, then recompute
   reliability." Detected by `scripts/check_reverse_coding.py` (negative item-rest correlation and
   negative raw alpha, given the scale item columns); the recode itself is applied downstream by
   `/analyze-stats` `likert_summary.py --reverse-items`.

Present the flag report as a table:

| Variable | Issue Type | Count | Severity | Suggested Action |
|----------|-----------|-------|----------|-----------------|
| age | Outlier (IQR) | 3 | Medium | Review: values 150, 200, -5 |
| pack_years | Categorical-implied zero | 12421 | High | Set 0 where smoking_status=='never' (structural zero, not missing) |

Severity levels:
- **High**: likely data errors that will affect analysis (type mismatches, impossible values)
- **Medium**: potential issues that need expert review (statistical outliers, moderate missingness)
- **Low**: minor inconsistencies that are easy to fix (category labels, trailing whitespace)

**Gate**: The user marks each row (A) Approve the suggested action, (R) Reject / keep as-is, or
(M) Modify the action. Only approved actions generate cleaning code.

### Stage 3: Code Generation

For ONLY user-approved actions, generate Python (or R if requested) code:

- **Missing value handling**: listwise deletion, mean/median imputation, or MICE setup (code only, the
  user runs it and picks the variables and method)
- **Outlier handling**: winsorization, removal, or keep-and-flag
- **Duplicate removal**: exact dedup with logging
- **Type conversion**: standardize dates, numeric parsing
- **Category harmonization**: mapping table for inconsistent labels

All generated code MUST include:
- Before/after row counts printed to console
- Logging of every modification to a cleaning log DataFrame
- Reproducibility: `np.random.seed(42)` and `random.seed(42)` where applicable
- Output: cleaned CSV (a new file; the input file is never overwritten) + `cleaning_log.csv`
- Clear comments explaining each cleaning step

End the generated script with this notice:
> "This code implements ONLY the cleaning rules you approved. Review the cleaning_log.csv
> output to verify all changes before proceeding to analysis."

Out of scope: free-text extraction from clinical notes, and image data or DICOM metadata. After
cleaning, hand off to `/analyze-stats`. Take any citation from `/search-lit`, never from memory.

## Output Format

Structure all reports using this template:

```
## Data Profiling Report

### Dataset Overview
- Rows: [N]
- Columns: [N]
- File size: [size]
- Date range: [if applicable]

### Variable Summary
| Variable | Type | Missing N (%) | Unique | Min | Max | Mean | SD |
|----------|------|---------------|--------|-----|-----|------|-----|
| ...      | ...  | ...           | ...    | ... | ... | ...  | ... |

### Flags
| Variable | Issue | Count | Severity | Suggested Action |
|----------|-------|-------|----------|-----------------|
| ...      | ...   | ...   | ...      | ...             |

### Cleaning Code
[Python/R script -- only for approved actions]

### Cleaning Log
[What was changed, how many rows affected, before/after counts]
```
