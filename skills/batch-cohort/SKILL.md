---
name: batch-cohort
description: Use when one validated cohort analysis must be repeated across many exposure/outcome pairs. Generates one R/Python script per combination from a single methodology template, changing only the variables, and aggregates the results into a summary matrix.
triggers: batch cohort, batch analysis, 대량 분석, 변수 교체, variable swap, mass production, 80명 팀, batch generate, 일괄 코드 생성, exposure outcome matrix, combinatorial analysis
tools: Read, Write, Edit, Bash, Grep, Glob
model: opus
---

# Batch Cohort Analysis Skill

Generate one analysis script per exposure/outcome combination from a single validated methodology
template; only the variables change between scripts.

## Inputs

1. **Database path(s)**: CSV/SAS data files (KNHANES, NHANES, NHIS, or any cleaned cohort)
2. **Methodology template**: One of:
   - Path to a validated R/Python analysis script (from /replicate-study or /cross-national)
   - A paper type template name: `nhis_cohort`, `cross_national`, `survey_weighted`
   - A source paper to extract methodology from (falls back to /replicate-study Phase 1)
3. **Combination spec**: A list of exposure/outcome pairs, provided as:
   - Inline list: `exposures: [depression, obesity, smoking]; outcomes: [diabetes, hypertension, CVD]`
   - CSV file with columns: `exposure`, `outcome`, (optional) `subgroup_vars`
   - `"all"` keyword: generates all pairwise combinations from the lists

### Optional Inputs

- **Covariate set**: Fixed covariate list for all analyses (default: use template's set)
- **Subgroup variables**: Variables to stratify by (default: sex, age group)
- **Output format**: `code_only` (just scripts) | `execute` (run + collect results) | `full` (code + results + summary)
- **Cross-national mode**: `cross_national: true` generates paired scripts for both countries per combination (see Cross-National Batch Mode)

Example:

```
/batch-cohort

DB Korea: /path/to/knhanes/HN18.csv
DB US: /path/to/nhanes/
Template: cross_national
Exposures: [depression, obesity, smoking]
Outcomes: [diabetes, hypertension, metabolic_syndrome]
cross_national: true
Mode: execute
```

## Workflow

### Phase 1: Template Validation

1. Read the methodology template (R script or paper type reference).
2. Identify the **slot variables** — parts that change per combination: `EXPOSURE_VAR` (raw
   variable name in the database), `EXPOSURE_LABEL` (label for tables/figures), `EXPOSURE_CODING`
   (derivation of the binary/categorical exposure), and `OUTCOME_VAR`, `OUTCOME_LABEL`,
   `OUTCOME_CODING` likewise.
3. Confirm the survey design: weighted analysis is mandatory for KNHANES/NHANES and is inherited
   from the template; NHIS and other claims databases have no sampling weights (standard regression).
4. Verify the template runs successfully on at least one combination before batch generation.
5. Output: template summary with identified slots → user approval.

### Phase 2: Variable Specification

For each exposure and outcome in the combination spec:

1. **Look up** the variable in the database: KNHANES — the name exists in the CSV header; NHANES —
   which table contains it (codebook.csv if available); NHIS — claims code or variable name.
   For ICD-10 claims algorithms read
   `${CLAUDE_SKILL_DIR}/../analyze-stats/references/analysis_guides/nhis_icd10_mapping.md`; for
   survey variable coding, `survey_weighted.md` in the same folder. If a mapping is
   uncertain, write `[VERIFY: variable_name]` and ask the user to confirm it against the data
   dictionary; never guess a variable name, column name or coding.
2. **Define coding**: binary as a threshold or category mapping (e.g., `HE_glu >= 126 → diabetes = 1`);
   categorical as level definitions (e.g., `smoking: current/former/never`). Outcome definitions
   MUST include physician diagnosis, because lab-only definitions systematically overestimate
   exposure→outcome associations: Diabetes = FPG≥126 OR HbA1c≥6.5 OR physician-diagnosed
   (KNHANES: DE1_dg=1, NHANES: DIQ010="Yes"); Hypertension = SBP≥140 OR DBP≥90 OR
   physician-diagnosed (KNHANES: DI1_dg=1, NHANES: BPQ020="Yes").
3. **Set covariates**: the full 8-covariate set (age, sex, education, income, smoking, alcohol,
   obesity, CVD) is the default unless explicitly justified — minimal models (age+sex+BMI only)
   overestimate effects through residual confounding. Remove self-adjustment: if the exposure is
   (or derives from) a covariate, drop that covariate (exposure = BMI → drop obesity; exposure =
   education/income → drop the same variable); if outcome = MetS, consider dropping obesity.
   Document every removal in the matrix Notes.
4. Output: **combination matrix** (`combination_matrix.csv`) with all variable specifications.

```
| # | Exposure | Exposure Coding | Outcome | Outcome Coding | Covariates (adjusted) | Notes |
|---|----------|-----------------|---------|----------------|----------------------|-------|
| 1 | Depression (PHQ≥10) | BP_PHQ sum ≥10 | Diabetes | HE_glu≥126|HbA1c≥6.5|DE1_dg=1 | age,sex,edu,income,smoking,alcohol,obesity,CVD | — |
| 2 | Obesity (BMI≥25) | HE_obe ≥4 | Diabetes | same | age,sex,edu,income,smoking,alcohol,depression,CVD | obesity removed from covariates |
```

### Phase 3: Batch Code Generation

Never modify the core methodology across combinations — only swap exposure/outcome/covariates.
For each combination in the matrix:

1. **Clone** the template script.
2. **Replace** slot variables with the combination-specific values.
3. **Apply** the combination's adjusted covariate set from the matrix.
4. **Set output paths**: each combination gets its own results subdirectory.
5. **Generate a master runner script** (`run_all.R` or `run_all.sh`) that executes all N scripts
   sequentially (or in parallel via `future`/`parallel`), captures errors per script without
   stopping the batch, and logs execution time per analysis.
6. **Generated-code quality gate**: one reproducibility slip (a missing seed, an absolute path, a
   hand-typed data literal) replicates across the whole batch, so lint the generated scripts with
   the `/analyze-stats` code-quality gate
   (`python3 ${CLAUDE_SKILL_DIR}/../analyze-stats/scripts/check_generated_code.py --code-dir {batch_dir} --strict`)
   and clear every Major (`MISSING_SEED`, `HARDCODED_DATA_LITERAL`, `HARDCODED_ABS_PATH`,
   `INPLACE_SOURCE_OVERWRITE`) before batch execution.

### Phase 4: Batch Execution (if `execute` or `full` mode)

1. **Event count check**: before running, verify each outcome has ≥10 events per covariate (EPV
   rule). Flag underpowered combinations.
2. Run the master script.
3. Collect results from each combination's output directory.
4. Log which combinations failed and why (common: convergence issues, too few events, empty
   subgroups) in `failed_runs.csv`, and suggest fixes.

### Phase 5: Summary Matrix

Aggregate all results into a single summary. Every number comes from a combination's executed
results files; never fill a cell by hand.

**Main Results Matrix** (`summary_matrix.csv`):

| Exposure | Outcome | N | Events | Model 1 OR (95% CI) | Model 2 OR (95% CI) | Model 3 OR (95% CI) | p-value | Significant |
|----------|---------|---|--------|---------------------|---------------------|---------------------|---------|-------------|

**Subgroup Summary** (`subgroup_matrix.csv`): Same format, stratified by subgroup variables.

**Heatmap** (optional): Visual matrix of effect sizes × significance, exposure on Y-axis, outcome on X-axis.

- **Multiple comparisons**: when generating >5 combinations, include a Bonferroni-corrected
  significance column in the summary matrix and a note on exploratory vs confirmatory framing.
- **No p-hacking framing**: the summary matrix is for **hypothesis generation**, not confirmation.
  State this explicitly in README and any manuscript output. Any citation there needs a
  `/search-lit`-confirmed DOI/PMID; otherwise mark it `[UNVERIFIED - NEEDS MANUAL CHECK]`.

## Output Files

```
{working_dir}/batch_{timestamp}/
├── README.md                    — Batch run summary (N combinations, template used, date)
├── combination_matrix.csv       — All exposure/outcome specs with coding
├── template/
│   └── base_template.R          — The validated template (frozen copy)
├── scripts/
│   ├── 01_depression_diabetes.R
│   ├── 02_obesity_diabetes.R
│   ├── ...
│   └── run_all.R                — Master execution script
├── results/
│   ├── 01_depression_diabetes/
│   │   ├── table1.csv
│   │   ├── main_results.csv
│   │   └── subgroup_results.csv
│   └── ...
├── summary/
│   ├── summary_matrix.csv       — Main results across all combinations
│   ├── subgroup_matrix.csv      — Subgroup results across all combinations
│   ├── failed_runs.csv          — Combinations that failed + error messages
│   └── heatmap.png              — Optional effect size × significance visual
└── logs/
    └── batch_execution.log      — Timing + error log
```

**Reproducibility**: freeze the template version (`template/`) and include a SHA256 hash of the
data file in README.

## Cross-National Batch Mode

When `cross_national: true`:
- Generate paired scripts for each combination (Korea + US), using /cross-national's
  dual-survey-design approach
- Summary matrix includes both countries side-by-side, with a direction-agreement column (✓ if
  both countries show the same direction of effect)
