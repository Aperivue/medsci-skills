---
name: cross-national
description: Use when comparing an exposure-outcome association across countries with parallel national surveys (KNHANES, NHANES, CHNS). Harmonizes variables, runs parallel weighted analyses and builds comparison tables for 2-country (KR+US) or 3-country (KR+US+CN) designs.
model: opus
metadata:
  triggers: "cross-national, 한미 비교, Korea US comparison, KNHANES NHANES, 양국 비교, binational, cross-country, 비교연구, 3국 비교, CHNS, 한미중"
---

# Cross-National Comparison Study Skill

## Inputs

1. **Research question**: exposure → outcome association to compare across countries
2. **Korean data path**: KNHANES CSV file
3. **US data path**: NHANES CSV directory (multiple tables to merge)
4. **Harmonization table** (optional): CSV mapping variables across surveys
   - Default: `/replicate-study`'s `references/harmonization_knhanes_nhanes.csv`

## Reference Files

- `/write-paper`'s `references/paper_types/cross_national.md` — writing template
- `/analyze-stats`'s `references/analysis_guides/survey_weighted.md` — survey-weighted analysis guide
- `references/chns_coding.md` — CHNS files, merge keys, coding and warnings; read it when the design
  includes China (3-country design)
- `references/additional_variables.md` — asthma, sleep, physical activity, diet, treatment and
  non-HDL-cholesterol coding, plus composite-score (LE8) warnings; read it when the study uses any of them

## Workflow

### Phase 1: Study Definition

1. Confirm research question: Exposure → Outcome
2. Define variable coding for both countries:
   - Exposure: PHQ-9, BMI category, smoking, etc.
   - Outcome: diabetes, hypertension, mortality, etc.
   - Covariates: age, sex, education, income, smoking, alcohol, obesity, CVD
3. Check harmonization table for variable availability
4. Output: study protocol summary for user approval

### Phase 2: Data Preparation

Never guess a variable name, dataset column name, or variable coding. If a mapping is uncertain,
output `[VERIFY: variable_name]` and ask the user to confirm it against the data dictionary.

**KNHANES (single CSV)**:
1. Load CSV and keep every row — the age ≥20 (or per-protocol) restriction is applied to the design in step 3
2. Derive variables using KNHANES coding:

   | Variable | Raw Var | Coding |
   |----------|---------|--------|
   | Smoking | BS3_1 | 1,2=Current; 3=Former; 8=Never |
   | Alcohol | BD1_11 | 2-6=Frequent (current drinker); 1=Occasional (past-year abstainer); 8=Never |
   | Obesity | HE_obe | 1-3=Normal; 4-6=Obesity (BMI≥25, Asian cutoff) |
   | Depression | BP_PHQ_1~9 | Sum ≥10 = depression |
   | Diabetes | HE_glu, HE_HbA1c, DE1_dg | FPG≥126 or HbA1c≥6.5 or DE1_dg=1 |
   | CVD | DI4_dg, DI5_dg, DI6_dg | Any = 1 → CVD yes |
   | Education | edu | 1-3=Non-college; 4=College |
   | Income | incm | Quartile (1=lowest … 4=highest): 1-3=Bottom 75%; 4=Top quartile |

3. Set survey design on the full file, then restrict to the analytic domain:
   des <- svydesign(id=~psu, strata=~kstrata, weights=~wt_itvex, nest=TRUE, data=df);
   des_ad <- subset(des, age >= 20). Never filter rows before svydesign() — dropping them
   changes the standard errors (see `survey_weighted.md`, subpopulation analysis)

**NHANES (multiple CSVs)**:
1. Load and merge tables by SEQN (DEMO_J, DPQ_J, GHB_J, GLU_J, BMX_J, SMQ_J, ALQ_J, DIQ_J, MCQ_J, BPQ_J, BPXO_J)
2. Derive variables using NHANES coding. **CRITICAL**: NHANES data downloaded via R `nhanesA` package
   uses TEXT LABELS, not numeric codes.

   | Variable | Raw Var | Coding (text labels) |
   |----------|---------|----------------------|
   | Sex | RIAGENDR | "Male" / "Female" (NOT 1/2) |
   | Smoking | SMQ020 + SMQ040 | 100 cigs (SMQ020 "Yes" / "No") + now smoke (SMQ040 "Every day" / "Some days" / "Not at all") |
   | Alcohol | ALQ121 + ALQ111 | Frequent (current drinker): any ALQ121 frequency except "Never in the last year"; Occasional (past-year abstainer): "Never in the last year"; Never (lifetime non-drinker): ALQ111 == "No" (ALQ121 will be NA) |
   | Obesity | BMXBMI (BMX_J, kg/m²) | ≥30 (WHO cutoff, NOT Asian) |
   | PHQ-9 | DPQ010~DPQ090 | "Not at all"→0, "Several days"→1, "More than half the days"→2, "Nearly every day"→3; sum ≥10 = depression |
   | Diabetes | LBXGLU (GLU_J, fasting subsample, mg/dL), LBXGH (GHB_J, %), DIQ010 | LBXGLU≥126 \| LBXGH≥6.5 \| DIQ010=="Yes" (DIQ010: "Yes" / "No" / "Borderline"). CRITICAL: fasting glucose is GLU_J LBXGLU, not BIOPRO_J LBXSGL — CDC says the serum LBXSGL should not be used to determine undiagnosed diabetes; an analysis that uses LBXGLU needs the fasting-subsample weight (step 3) |
   | CVD | MCQ160B/C/D/E | MCQ160B=="Yes" (CHF) \| MCQ160C=="Yes" (CHD) \| MCQ160D=="Yes" (angina) \| MCQ160E=="Yes" (MI); labels "Yes" / "No" / "Don't know" |
   | HTN | BPXOSY3, BPXODI3, BPQ020 | BPXOSY3≥140 \| BPXODI3≥90 \| BPQ020=="Yes" |
   | Education | DMDEDUC2 | 5 text levels |

3. Set survey design on the full file, then `subset()` the design object to the analytic domain
   (e.g. RIDAGEYR >= 20): svydesign(id=~SDMVPSU, strata=~SDMVSTRA, weights=~WTMECPRP, nest=TRUE) — WTMECPRP
   for the pre-pandemic pooled files; for a single cycle (e.g. the `_J` tables) use weights=~WTMEC2YR.
   When a variable comes from the fasting subsample (GLU_J LBXGLU, TRIGLY_J LBXTR/LBDLDL), use the
   fasting-subsample weight instead: WTSAF2YR (single cycle) or WTSAFPRP (pre-pandemic)

**CHNS (3-country design)**: read `references/chns_coding.md` before preparing China data.

### Phase 3: Parallel Analysis

For EACH country independently:
1. **Table 1**: Baseline characteristics by exposure (weighted counts + percentages)
2. **Main analysis**: Sequential logistic regression models
   - Model 1 (unadjusted)
   - Model 2 (age + sex)
   - Model 3 (fully adjusted: + education, income, smoking, alcohol, obesity, CVD)
3. **Subgroup analyses**: By sex, age group, education, income, alcohol, smoking, CVD, obesity
4. **Dose-response** (if applicable): RCS with 3 knots

### Phase 4: Cross-National Comparison Table

Generate a side-by-side comparison:

| Analysis | Korea wOR (95% CI) | US wOR (95% CI) | Direction Agreement |
|----------|-------------------|-----------------|---------------------|
| Overall (fully adjusted) | ... | ... | ✓/✗ |
| Male | ... | ... | |
| Female | ... | ... | |
| ... | ... | ... | |

Every number comes from executed code output (`analysis_korea.R`, `analysis_us.R`) — never an
invented p-value, effect size, confidence interval, or sample size.

### Phase 5: Output Files

```
{working_dir}/
├── cross_national_report.md    — Study summary + comparison tables
├── variable_mapping.csv        — Variable mapping with match status
├── analysis_korea.R            — KNHANES analysis (self-contained)
├── analysis_us.R               — NHANES analysis (self-contained)
├── results/
│   ├── table1_korea.csv
│   ├── table1_us.csv
│   ├── main_results_comparison.csv
│   └── subgroup_comparison.csv
└── manuscript_draft/           — Optional: Methods + Results draft
    ├── methods_draft.md
    └── results_draft.md
```

Take every citation in the report or draft from `/search-lit` (confirmed DOI/PMID); mark any other
`[UNVERIFIED - NEEDS MANUAL CHECK]`, and never generate references from memory.

## Critical Rules

1. **NEVER pool data across countries**. Each country analyzed with its own survey design.
2. **Country-specific BMI cutoffs**: Korea ≥25 (Asian), US ≥30 (WHO).
3. **Country-specific income**: KNHANES quartile, NHANES PIR → harmonize to binary.
4. **Weighted analysis mandatory**: Both KNHANES and NHANES are complex surveys. CHNS has no
   survey weights — analyse it unweighted (see `references/chns_coding.md`).
5. **Document all harmonization decisions**: What matches, what needed recoding, what differs.
6. **Same analytic approach**: Identical model specifications for both countries for fair comparison.
