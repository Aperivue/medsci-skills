---
name: batch-cohort
description: Generate N analysis scripts from a single methodology template × multiple exposure/outcome combinations. The "80-person team" pattern — same validated method, swap variables only. Produces batch R/Python code + summary matrix.
triggers: batch cohort, batch analysis, 대량 분석, 변수 교체, variable swap, mass production, 80명 팀, batch generate, 일괄 코드 생성, exposure outcome matrix, combinatorial analysis
tools: Read, Write, Edit, Bash, Grep, Glob
model: opus
---

# Batch Cohort Analysis Skill

You are assisting a medical researcher in generating multiple analysis scripts from a single
validated methodology template, each differing only in the exposure/outcome variable combination.
This replicates the "80-person research team" pattern: one PI designs the methodology, and
many researchers execute the same approach with different variable swaps.

## When to Use

- Researcher has a **validated analysis template** (e.g., from /replicate-study or /cross-national)
- Wants to explore **multiple exposure → outcome combinations** on the same database
- Goal: systematic variable-swap code generation + batch execution + result matrix

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
- **Cross-national mode**: If TRUE, generates paired scripts for both countries per combination

## Workflow

### Phase 1: Template Validation

1. Read the methodology template (R script or paper type reference).
2. Identify the **slot variables** — parts that change per combination:
   - `EXPOSURE_VAR`: raw variable name in the database
   - `EXPOSURE_LABEL`: human-readable label for tables/figures
   - `EXPOSURE_CODING`: how to derive binary/categorical exposure
   - `OUTCOME_VAR`: raw variable name
   - `OUTCOME_LABEL`: human-readable label
   - `OUTCOME_CODING`: how to derive binary outcome
3. Verify the template runs successfully on at least one combination before batch generation.
4. Output: template summary with identified slots → user approval.

### Phase 2: Variable Specification

For each exposure and outcome in the combination spec:

1. **Look up** the variable in the database:
   - KNHANES: check variable name exists in the CSV header
   - NHANES: check which table contains the variable (use codebook.csv if available)
   - NHIS: check claims code or variable name
2. **Define coding**:
   - Binary: threshold or category mapping (e.g., `HE_glu >= 126 → diabetes = 1`)
   - Categorical: level definitions (e.g., `smoking: current/former/never`)
3. **Check covariate overlap**: If the exposure IS one of the standard covariates, remove it from the adjustment set for that analysis (no self-adjustment).
4. Output: **combination matrix** with all variable specifications.

```
| # | Exposure | Exposure Coding | Outcome | Outcome Coding | Covariates (adjusted) | Notes |
|---|----------|-----------------|---------|----------------|----------------------|-------|
| 1 | Depression (PHQ≥10) | BP_PHQ sum ≥10 | Diabetes | HE_glu≥126|HbA1c≥6.5|DE1_dg=1 | age,sex,edu,income,smoking,alcohol,obesity,CVD | — |
| 2 | Obesity (BMI≥25) | HE_obe ≥4 | Diabetes | same | age,sex,edu,income,smoking,alcohol,depression,CVD | obesity removed from covariates |
| ... | | | | | | |
```

### Phase 3: Batch Code Generation

For each combination in the matrix:

1. **Clone** the template script.
2. **Replace** slot variables with the combination-specific values.
3. **Adjust covariates**: Remove exposure variable from covariate list if present.
4. **Set output paths**: Each combination gets its own results subdirectory.
5. **Generate a master runner script** (`run_all.R` or `run_all.sh`) that:
   - Executes all N scripts sequentially (or in parallel via `future`/`parallel`)
   - Captures errors per script without stopping the batch
   - Logs execution time per analysis

### Phase 4: Batch Execution (if `execute` or `full` mode)

1. Run the master script.
2. Collect results from each combination's output directory.
3. Handle failures gracefully:
   - Log which combinations failed and why
   - Common failures: convergence issues, too few events, empty subgroups
   - Suggest fixes for failed combinations

### Phase 5: Summary Matrix

Aggregate all results into a single summary:

**Main Results Matrix** (`summary_matrix.csv`):

| Exposure | Outcome | N | Events | Model 1 OR (95% CI) | Model 2 OR (95% CI) | Model 3 OR (95% CI) | p-value | Significant |
|----------|---------|---|--------|---------------------|---------------------|---------------------|---------|-------------|
| Depression | Diabetes | 5,811 | 487 | 2.14 (1.52–3.01) | 1.89 (1.33–2.69) | 1.36 (0.91–2.05) | 0.137 | No |
| Obesity | Diabetes | 5,811 | 487 | 3.45 (2.71–4.39) | 3.38 (2.65–4.32) | 3.12 (2.42–4.02) | <0.001 | Yes |
| ... | | | | | | | | |

**Subgroup Summary** (`subgroup_matrix.csv`): Same format, stratified by subgroup variables.

**Heatmap** (optional): Visual matrix of effect sizes × significance, exposure on Y-axis, outcome on X-axis.

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
│   ├── 02_obesity_diabetes/
│   │   └── ...
│   └── ...
├── summary/
│   ├── summary_matrix.csv       — Main results across all combinations
│   ├── subgroup_matrix.csv      — Subgroup results across all combinations
│   ├── failed_runs.csv          — Combinations that failed + error messages
│   └── heatmap.png              — Optional effect size × significance visual
└── logs/
    └── batch_execution.log      — Timing + error log
```

## Critical Rules

1. **Never modify the core methodology** across combinations — only swap exposure/outcome/covariates.
2. **Remove self-adjustment**: If exposure = BMI, remove obesity from covariates. If exposure = education/income, remove the same variable from covariates. If outcome = MetS, consider removing obesity from covariates. Document all removals.
3. **Weighted analysis mandatory** for KNHANES/NHANES/NHIS — inherited from template.
4. **Event count check**: Before running, verify each outcome has ≥10 events per covariate (EPV rule). Flag underpowered combinations.
5. **Multiple comparisons**: When generating >5 combinations, include a Bonferroni-corrected significance column in the summary matrix. Add a note about exploratory vs confirmatory framing.
6. **Reproducibility**: Freeze the template version. Include a SHA256 hash of the data file in README.
7. **No p-hacking framing**: The summary matrix is for **hypothesis generation**, not confirmation. State this explicitly in README and any manuscript output.
8. **Outcome definitions MUST include physician diagnosis**: Diabetes = FPG≥126 OR HbA1c≥6.5 OR physician-diagnosed (KNHANES: DE1_dg=1, NHANES: DIQ010="Yes"). Hypertension = SBP≥140 OR DBP≥90 OR physician-diagnosed (KNHANES: DI1_dg=1, NHANES: BPQ020="Yes"). Lab-only definitions systematically overestimate exposure→outcome associations (validated: Joo 2026 replication showed US depression→DM wOR 1.92 without vs 1.54 with physician dx).
9. **Full covariate set is default**: Always use 8 covariates (age, sex, education, income, smoking, alcohol, obesity, CVD) unless explicitly justified. Minimal models (age+sex+BMI only) overestimate effects due to residual confounding.
10. **Generated-code quality gate**: Because this skill emits N near-identical scripts, a single reproducibility slip (a missing seed, an absolute path, a hand-typed data literal) replicates across the whole batch. After Phase 3, lint the generated scripts with the `/analyze-stats` code-quality gate (`check_generated_code.py --code-dir {batch_dir} --strict`) and clear every Major (`MISSING_SEED`, `HARDCODED_DATA_LITERAL`, `HARDCODED_ABS_PATH`, `INPLACE_SOURCE_OVERWRITE`) before batch execution.

## Cross-National Batch Mode

When `cross_national: true`:
- Generate paired scripts for each combination (Korea + US)
- Summary matrix includes both countries side-by-side
- Direction agreement column: ✓ if both countries show same direction of effect
- Uses /cross-national skill's dual-survey-design approach

## Integration with Upstream Skills

| Need | Skill |
|------|-------|
| Variable coding lookup | `analyze-stats` survey_weighted guide |
| Template creation from paper | `/replicate-study` Phase 1–3 |
| Cross-national paired analysis | `/cross-national` |
| ICD-10 claims algorithms | `analyze-stats` nhis_icd10_mapping guide |
| Write manuscript from results | `/write-paper` (nhis_cohort or cross_national type) |
| Figure generation | `/make-figures` (forest plot of all combinations) |

## Example Invocations

### Basic: Single DB, Multiple Exposures × Single Outcome

```
/batch-cohort

DB: /path/to/knhanes/HN18.csv
Template: /path/to/validated_analysis.R
Exposures: [depression, obesity, smoking, heavy_drinking, low_income, low_education]
Outcome: diabetes
Mode: full
```

### Cross-National: Full Matrix

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

### NHIS Cohort: Claims-Based Batch

```
/batch-cohort

DB: /path/to/nhis_sample_cohort.csv
Template: nhis_cohort
Exposures: [atrial_fibrillation, heart_failure, COPD, CKD]
Outcomes: [all_cause_mortality, cardiovascular_death, stroke]
Mode: code_only
```

## Anti-Hallucination

- **Never fabricate variable names, dataset column names, or variable codings.** If a variable mapping is uncertain, output `[VERIFY: variable_name]` and ask the user to confirm against the data dictionary.
- **Never fabricate statistical results** — no invented p-values, effect sizes, confidence intervals, or sample sizes. All numbers must come from executed code output.
- **Never generate references from memory.** Use `/search-lit` for all citations.
- If a function, package, or API does not exist or you are unsure, say so explicitly rather than guessing.
