# Cross-National Comparison Study — Paper Type Template

## Overview

Template for cross-national (binational) comparative studies using nationally representative datasets from two or more countries. Covers three study architectures: (A) Parallel Survey Analysis using cross-sectional surveys (e.g., KNHANES + NHANES), (B) Discovery/Validation Cohort using claims databases (e.g., NHIS + JMDC), and (C) Binational Birth/Longitudinal Cohort with sibling comparison. Applicable to prevalence comparisons, association studies, trend analyses, and composite health metric evaluations.

---

## Title

- Include "Cross-National," "Binational," or country names.
- Specify the study design in a subtitle.
- Under 20 words preferred.

### Title Templates

| Pattern | Example |
|---------|---------|
| `Cross-national comparison of {X} and {Y} in {Country A} and {Country B}: a nationwide representative comparative study` | Depression and diabetes in Korea and the US |
| `Binational association between {X} and {Y} in {Country A} and {Country B}: a nationally representative cross-sectional study` | PUFA and depression in Korea and the US |
| `Maternal {exposure} and {outcome} in offspring: a binational cohort study` | Pregestational diabetes and neuropsychiatric risk |
| `Burden of {outcome} after {exposure} in {Country A} and {Country B}: a binational population-based cohort study` | Cardiovascular outcomes after infection |
| `Trends in {outcome} among {population}, {year range}: a nationwide representative study` | Physical activity trends (single-country variant) |

Notes:
- "Binational" is increasingly preferred over "Cross-national" for two-country studies.
- Always include the year range for trend studies.
- The subtitle pattern is consistent: "a nationwide representative {comparative/cross-sectional/cohort} study."

---

## Abstract (Structured, 250 words max)

### Background
- State the known relationship and the cross-national evidence gap.
- Template: "Although {known relationship} has been suggested, evidence remains limited across cultural contexts. This study {compared/examined} {association} in {Country A} and {Country B}."

### Methods
- Name both datasets with years and sample sizes.
- State that datasets were analyzed independently.
- Name the harmonization approach and statistical methods.

### Results
- Report sample sizes from each dataset.
- Key findings with weighted odds ratios (wOR) or aHRs and 95% CIs from each country.
- Highlight convergent or divergent findings across countries.

### Conclusion
- Main conclusion emphasizing cross-national consistency or divergence.
- Implication for policy or future research.

#### Discovery/Validation Variant
- Results structure: "In the {weighted} discovery cohort, {N} individuals were included... Similar patterns were observed in the validation cohort."

---

## Introduction (3-4 paragraphs, ~400-500 words)

### Paragraph 1: Global Burden Statement
- Cite GBD or WHO prevalence figures with projections.
- Template: "{Condition} remains a {highly prevalent / growing} global health {threat/challenge}."

### Paragraph 2: Prior Evidence (Single-Country Limitations)
- Summarize existing single-country evidence.
- Flag limitations: "were limited to single-country cohorts," "did not adjust for key confounders," "have not taken broad population approaches."
- If relevant, cite Mendelian randomization evidence showing ancestral or population differences.

### Paragraph 3: Cross-National Gap and Study Aim
- Template: "To our knowledge, no prior study has evaluated {association} within a cross-national comparative framework."
- Template: "To address this gap, we analyzed nationally representative data from {Dataset A} and {Dataset B} collected between {years} to compare {outcome} in {Country A} and {Country B}."
- Optional: justify the country pairing with cultural, genetic, or healthcare system differences.

### Variation: Trend Studies
- Replace the cross-national gap with a temporal gap: "there is a lack of large-scale studies examining how {X} patterns have evolved across pre-, intra-, and post-pandemic periods."

---

## Materials and Methods (~1000-1400 words)

### 3.1 Data Sources

Describe each dataset separately with parallel structure:

Template:
> This study utilized {Dataset A} for {years} and {Dataset B} for {years}.
>
> {Dataset A} is a {population-based, cross-sectional / cohort} survey conducted by {Agency A} using a stratified, multistage probability sampling design to assess the health and nutritional status of the noninstitutionalized {Country A} population.
>
> {Dataset B}, administered by {Agency B}, is a {biennial / annual} survey designed to represent the noninstitutionalized {Country B} population using a similar multistage probability sampling approach.
>
> Both surveys include standardized health interviews, physical examinations, and laboratory tests, and collect extensive information on sociodemographic characteristics, health behaviors, and medical conditions.

#### Common Dataset Pairings

| Country A Dataset | Country B Dataset | Use Case |
|-------------------|-------------------|----------|
| KNHANES (Korea) | NHANES (US) | Nutrition, metabolic, mental health, composite score comparisons |
| NHIS (Korea) | JMDC (Japan) | Claims-based cohort and birth cohort studies |
| K-COV-N (NHIS+KDCA) | JMDC (Japan) | Disease-specific cohort (discovery/validation) |
| KCHS (Korea) | — (single-country) | National trend studies with temporal phases |

Notes:
- Survey years may be non-consecutive if specific variables are only collected in certain cycles. Always explain excluded years.
- For claims-based binational studies, shift the description to: "This binational cohort study included {N} individuals from {Country A} and {N} from {Country B}, from {start} to {end}."

### 3.2 Ethics Approval

- Separate IRB approvals per country, listed together.
- Template: "The {Dataset A} protocol was approved by {IRB A} ({numbers}), and the {Dataset B} protocol was approved by {IRB B} ({numbers}). All participants provided written informed consent. Both surveys comply with the ethical principles outlined in the Declaration of Helsinki, and their de-identified data are publicly accessible for research purposes."

### 3.3 Variable Harmonization

Three-layer harmonization framework:

#### Layer 1: Identical Instruments
- Variables measured with the same validated instrument in both datasets (e.g., PHQ-9 for depression, fasting glucose + HbA1c for diabetes).
- Template: "{Instrument} was used in both {Dataset A} and {Dataset B}."

#### Layer 2: Country-Specific Cutoffs with Clinical Justification
- Variables where clinical thresholds differ by national guidelines.
- Template: "{Variable} was defined using country-specific standards: {cutoff A} in {Country A} and {cutoff B} in {Country B}, reflecting established national guidelines."
- Common example: BMI >=25 in East Asia (Asia-Pacific cutoff) vs. BMI >=30 in US/Europe (WHO Western cutoff).

#### Layer 3: Operationally Different Variables Mapped to Equivalent Categories
- Variables measured differently but mappable to equivalent categories.
- Common examples:
  - Income: quintiles (Korea) vs. poverty-income ratio (US) → binary high/low.
  - Smoking/alcohol: mapped to equivalent categorical levels.

#### Key Harmonization Decisions (Reference Table)

| Variable | Typical Resolution |
|----------|-------------------|
| Obesity | Country-specific BMI cutoffs with justification |
| Income | Equivalent binary or tertile split |
| Depression | Identical instrument (PHQ-9) with same cutoff |
| Diabetes | Identical lab criteria (FG >=126 or HbA1c >=6.5%) |
| Physical activity | Identical framework (IPAQ-SF → MET-min/week) |

#### Core Principle
> "We applied harmonized variable definitions and conducted weighting and preprocessing separately for each dataset to preserve internal validity."

**Never pool raw data across countries.** Each dataset is analyzed independently.

#### ICD-10-Level Harmonization (Claims-Based Studies)
For binational cohort studies using claims databases, harmonization is done at the ICD-10 code level rather than questionnaire items. Apply the same code definitions, exposure/outcome assessments, and analytical approaches to both cohorts.

### 3.4 Study Population

- State inclusion/exclusion criteria applied to each dataset separately.
- For composite score studies (e.g., Life's Essential 8): calculate the score identically in both countries.
- For cohort studies: apply parallel exclusion cascades to each country's dataset.

### 3.5 Statistical Analysis

#### Architecture A: Parallel Survey Analysis

```
Step 1 — Separate analysis per country
  "Data from {Dataset A} and {Dataset B} were analyzed separately."
  Complex survey design: "appropriate stratification, clustering, and sampling weights were applied."

Step 2 — Sequential model building
  Model 1: adjusted for age and sex
  Model 2: additionally adjusted for {income, education, smoking, alcohol, BMI, comorbidities}
  Results as weighted odds ratios (wOR) with 95% CI

Step 3 — Subgroup / interaction analyses
  Stratified by: sex, age group, education, income, alcohol, smoking, obesity, comorbidities
  "Weighted odds ratios are adjusted for all covariates except the stratification variable."

Step 4 — Advanced modeling (choose as appropriate)
  - Restricted cubic spline (RCS) with 3 knots for nonlinear dose-response
  - Weighted quantile sum (WQS) regression for composite exposure component contribution
  - Beta-coefficient comparison across time periods (trend studies)
```

Notes:
- Never pool datasets into a single regression.
- Compare results side-by-side in the same table.
- Multicollinearity: check via VIF; values <2.0 acceptable.
- Missing data: variables with <5% missingness → complete case; higher → multiple imputation (5 datasets).

#### Architecture B: Discovery/Validation Cohort

```
Step 1 — Full analysis in discovery cohort
  PS-based balancing (overlap weighting, SIPTW, or matching)
  Cox proportional hazards → aHR with 95% CI
  Stratification and time-dependent analyses

Step 2 — Replication in validation cohort
  "The study applied similar methodologies to the {validation cohort} as those used for the discovery cohort."
  Same ICD-10 codes, exposure/outcome definitions, follow-up duration, and PS approach.

Step 3 — Subgroup analyses
  Disease severity, treatment dosage, temporal era stratification
```

#### Architecture C: Binational Birth/Longitudinal Cohort

```
Step 1 — Full-cohort SIPTW-weighted Cox regression (primary)
Step 2 — Sibling comparison analysis (addresses unmeasured familial confounding)
Step 3 — Independent validation in second country (sibling pairs or full cohort)
```

For multiple primary outcomes: apply Bonferroni correction (p < 0.05/K).

#### Software and Significance
- SAS for survey-weighted analyses and Cox regression.
- R for WQS regression and advanced modeling.
- Python for ML components if applicable.
- "A two-sided p value of less than 0.05 was considered statistically significant."

---

## Results (~800-1200 words)

### 4.1 Study Population
- Report sample sizes from each dataset: "{N_A} from {Dataset A} and {N_B} from {Dataset B}."
- Demographics table (Table 1) with columns per country.

### 4.2 Primary Findings
- Present results from each country in parallel.
- For parallel survey studies: wORs from both countries in the same table.
- For discovery/validation: primary results from discovery, confirmation from validation.

### 4.3 Subgroup and Advanced Analyses
- Stratification results by country.
- Dose-response (RCS) or component contribution (WQS) results.
- Time-dependent or era-specific results if applicable.

### 4.4 Sensitivity Analyses
- Confirm findings with alternative definitions, negative controls, or sibling comparisons.

### Rules
- Same as original article: no interpretation, no causal language.
- Present both countries' results for every analysis.

---

## Discussion (4-5 paragraphs, ~800-1200 words)

### Paragraph 1: Summary of Key Findings
- Highlight cross-national consistency or divergence.
- State whether findings were replicated across countries.

### Paragraphs 2-3: Comparison with Prior Literature
- Compare with prior single-country and cross-national studies.
- Discuss population-specific factors (cultural, genetic, healthcare system) that may explain differences.

### Paragraph 4: Clinical and Policy Implications
- Policy relevance across different healthcare systems.
- Public health recommendations.

### Paragraph 5: Limitations

Standard limitation categories for cross-national studies:

| # | Category | Template |
|---|----------|----------|
| 1 | Cross-sectional design | "The cross-sectional design precludes inference of causality." Mitigation: "the dose-response relationship and consistency across subgroups support plausibility." |
| 2 | Dataset differences | "Differences exist between {Dataset A} and {Dataset B} in data collection methods, diagnostic criteria, and survey protocols." Mitigation: "we applied harmonized variable definitions and conducted weighting and preprocessing separately for each dataset to preserve internal validity." |
| 3 | Temporal coverage mismatch | "{Dataset A} included selected survey years, whereas {Dataset B} provided continuous data." Mitigation: "appropriate sampling weights and consistent analytic criteria." |
| 4 | Self-report bias | "The use of self-reported data may introduce recall bias." Mitigation: "both surveys utilize validated instruments administered by trained personnel." |
| 5 | Country-specific definitions | "Obesity and income were defined using country-specific standards." Mitigation: "these definitions reflect established national guidelines and were applied consistently within each dataset, allowing for valid within-country comparisons." |
| 6 | Multiple comparisons | "Subgroup analyses were not adjusted for multiple comparisons." Mitigation: "based on prespecified variables of clinical and epidemiological relevance." |
| 7 | Unmeasured confounders | "Differences in healthcare systems, cultural factors, and unmeasured confounders may influence the relationship." |
| 8 | Population representativeness | "Both cohorts are from East Asian and Western populations; extrapolation to other regions requires caution." |

Each limitation followed by mitigation. End with strength-as-buffer: "our use of large, nationally representative samples allows for a broad understanding of population-level trends."

### Conclusion
- Citable statement emphasizing cross-national convergence or divergence.
- Specific policy or clinical recommendation.

---

## Tables

- **Table 1**: Baseline characteristics by country (separate columns per dataset).
- **Table 2**: Primary association results (wOR or aHR with 95% CI) from both countries in parallel columns.
- **Table 3**: Subgroup analyses by country.
- **Table S1+**: Variable harmonization details, ICD-10 codes, sensitivity analysis results.

## Figures

- **Figure 1**: Study flow diagram (per country or combined with country-specific branches).
- **Figure 2**: Forest plot of primary associations by country and subgroup.
- **Figure 3**: Restricted cubic spline dose-response curves (if applicable).
- Optional: Trend plots for temporal studies, WQS component weight bar charts.

---

## Boilerplate Sentences (Reusable)

### Survey Design
> "To account for the complex survey designs and ensure nationally representative estimates, appropriate stratification, clustering, and sampling weights were applied."

### Ethical
> "Both surveys comply with the ethical principles outlined in the Declaration of Helsinki, and their de-identified data are publicly accessible for research purposes."

### Separate Analysis Justification
> "For cross-national comparisons, data from {Dataset A} and {Dataset B} were analyzed separately."

### Within-Country Validity Defense
> "These definitions reflect established national guidelines and were applied consistently within each dataset, allowing for valid within-country comparisons and minimizing potential bias in the overall findings."

### Data Availability
> "Study protocol and statistical code: available from the corresponding author. Dataset: {public access URLs}."

---

## Checklist Before Submission

- [ ] Both datasets described with sampling design, years, and agency
- [ ] Separate IRB approvals per country listed
- [ ] Harmonization approach explicitly stated for all key variables
- [ ] Country-specific cutoffs justified with national guideline references
- [ ] Datasets analyzed independently (never pooled)
- [ ] Survey weights applied for cross-sectional surveys
- [ ] Results presented in parallel for both countries
- [ ] Subgroup analyses consistent across both datasets
- [ ] Limitations address dataset differences and temporal mismatch
- [ ] Within-country validity defense included
- [ ] Numbers consistent between text, tables, and figures
- [ ] Reporting guideline (STROBE) items addressed
