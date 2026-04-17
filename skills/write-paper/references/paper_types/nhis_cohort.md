# NHIS Cohort Study — Paper Type Template

## Overview

Template for population-based cohort studies using national health insurance claims databases (e.g., Korean NHIS, HIRA, KDCA, or equivalent national registries). Follows the IMRAD structure with specific patterns for emulated target trial frameworks, propensity score balancing, and claims-based outcome definitions. Applicable to vaccination effectiveness, disease-risk, and longitudinal exposure-outcome studies using administrative health data.

---

## Title

- Include study design: "A Nationwide Population-Based Cohort Study" or "An Emulated Target Trial."
- Specify the population or exposure: "Among Adults Aged 50 Years and Older."
- Under 20 words preferred.
- Good: "Association Between Statin Use and Dementia Risk: A Nationwide Population-Based Cohort Study"
- Bad: "Investigating Statins and Brain Health Using Big Data"

---

## Abstract (Structured, 250 words max)

### Background / Purpose
- One to two sentences. State the clinical question and gap.
- Template: "Evidence on the association between {exposure} and {outcome} at the population level remains limited."

### Methods
- Data source (nationwide cohort, N, date range).
- Emulated target trial or standard cohort design.
- Propensity score method (overlap weighting, SIPTW, or 1:1 matching).
- Cox proportional hazards model for aHRs with 95% CIs.
- Three to four sentences maximum.

### Results
- Final analytic cohort size after exclusions.
- Primary aHR with 95% CI.
- Key subgroup or time-dependent findings.
- Three to four sentences maximum.

### Conclusion
- One to two sentences. Restate the main finding and population-level implication.
- Be specific about effect magnitude and clinical relevance.

---

## Introduction (3-4 paragraphs, ~400-500 words)

### Paragraph 1: Disease Burden and Clinical Context
- Establish the clinical importance with global or national prevalence data.
- Cite GBD, WHO, or national registry statistics.
- Describe current clinical practice or public health approach.

### Paragraph 2: Prior Evidence and Knowledge Gap
- Summarize key prior studies (single-country cohorts, small sample sizes, limited follow-up).
- Flag specific limitations: "were limited to single-country cohorts," "did not adjust for key confounders," "lacked population-level data."
- State what remains unknown.

### Paragraph 3: Study Objective
- State the specific aim.
- If using emulated target trial: "Using an emulated target trial framework, we evaluated the association between {exposure} and {outcome} in a nationwide cohort of {N} individuals."
- Optional: preview key methodological strengths (large cohort, long follow-up, claims-linked data).

---

## Materials and Methods (~1000-1400 words)

### 3.1 Data Source

Describe the national claims database linkage. Standard components:

1. **Database identification**: Name the data sources (e.g., national health insurance claims, health examination records, disease registry).
2. **Population coverage**: State the coverage rate (e.g., "covers approximately 98% of the national population").
3. **Data domains**: Specify linked domains — outpatient and inpatient claims, pharmaceutical records, health examination results, death certificates, and any disease-specific registries.
4. **Anonymization**: State how personally identifiable information was handled.

Template:
> This {study type} utilized a large-scale, population-based, nationwide cohort comprising {N} individuals aged {X} years and older from {START DATE} to {END DATE}. The national universal health insurance system enables the integration of comprehensive health data across multiple domains. We integrated outpatient and inpatient data, pharmaceutical records, and death certificates from the national claims database, along with health examination data from the national health insurance service.

### 3.2 Ethics Approval

- State the approving body and protocol number.
- For claims-based studies: informed consent is typically waived due to use of anonymized records.
- Template: "This study was approved by {IRB/authority} (approval no. {NUMBER}). The requirement for informed consent was waived due to the use of anonymized health records."

### 3.3 Study Design Framework

If using the emulated target trial approach:
- State explicitly: "This study was designed and analysed following the emulated target trial framework, which mimics a randomized controlled trial."
- Reference a supplementary table mapping the target trial components (eligibility, treatment strategy, assignment, follow-up, outcome, causal contrast, analysis plan).

### 3.4 Study Population (Inclusion/Exclusion)

Standard three-tier exclusion cascade:
1. Death before index date.
2. Prevalent outcome (any documented diagnosis of the study outcome prior to the index date).
3. Missing demographic or health examination data (complete-case approach).

For disease-specific studies, add:
4. Disease-specific exclusion (e.g., diagnosis after the index date for subcohort studies).

Template:
> Participants were excluded if they (1) died before their assigned index date (n = {X}), (2) had any documented {outcome} diagnosis prior to the index date (n = {X}), or (3) lacked complete demographic information or health examination data (n = {X}). Following exclusions, {N} individuals were included in the final analytic cohort (Fig. 1).

Always include a CONSORT-style flow diagram (Fig. 1).

### 3.5 Exposure Definition

- Define the exposure with specific dates, codes, or criteria.
- For time-dependent exposures: address immortal time bias.
- Template for index date assignment: "To address immortal time bias, index dates for unexposed individuals were randomly assigned to match the distribution of index dates in the exposed group."
- Specify follow-up: "Participants were followed from the index date until the first occurrence of an outcome, death, or the end of follow-up ({END DATE}), whichever occurred first."

### 3.6 Outcome Definition

- Define using ICD-10 codes (defer code lists to supplementary table).
- For composite outcomes: define each component and the time windows.
- Template: "The primary outcomes were: (1) {OUTCOME 1}, (2) {OUTCOME 2}. Outcomes were identified using ICD-10 codes (Table S{X}). {COMPLICATION} was defined as a claim occurring within {X days} to {Y year} after the incident event."
- For stricter definitions: "An outcome was considered valid if at least two ICD-10 diagnostic claims within 1 year and related medication prescriptions were recorded."

### 3.7 Covariate Adjustment

Standard covariate set for national health insurance cohort studies:

| Category | Variables | Typical Categorization |
|----------|-----------|----------------------|
| Demographics | Age | 5-year bins or clinical cutoffs |
| | Sex | Male, Female |
| | Region of residence | Urban, Rural |
| | Household income | Low, Middle, High (percentile-based) |
| Clinical (exam) | BMI | Country-specific cutoffs (e.g., Asia-Pacific: <23.0, 23.0-24.9, >=25.0 kg/m2) |
| | Blood pressure | SBP/DBP threshold-based (e.g., SBP >=140 or DBP >=90 mmHg) |
| | Fasting blood glucose | Threshold-based (e.g., <100, >=100 mg/dL) |
| | GFR | Categories (e.g., <60, 60-89, >=90 mL/min/1.73 m2) |
| Comorbidity (claims) | Charlson comorbidity index | 0, 1, >=2 |
| | Medication history | Hypertension, Hyperlipidemia, Coronary artery disease |
| Behavioral (survey) | Smoking | Never, Former, Current |
| | Alcohol consumption | Frequency categories |
| | Physical activity | Sufficient/Insufficient (MET-based) |

Notes:
- BMI cutoffs should follow country-specific guidelines with explicit justification.
- Covariates are collected from the most recent data available prior to the individual index date.
- State the missing data approach (complete-case or multiple imputation with chained equations).

### 3.8 Statistical Analysis

#### Propensity Score Balancing

Three validated methods (choose one):

1. **Overlap weighting**: Maintains full sample size; weights each individual by the probability of being assigned to the opposite group.
2. **Stabilized IPTW**: Maintains full sample size; stabilized weights reduce variance.
3. **1:1 Propensity score matching**: Greedy nearest-neighbor within a specified caliper (e.g., 0.001 SD), without replacement.

Template:
> Propensity scores were estimated using multivariable logistic regression incorporating {list all covariates from 3.7}. Covariate balance was evaluated using standardized mean differences, with values <0.1 indicating adequate balance.

#### Effect Estimation

- Cox proportional hazards models for adjusted hazard ratios (aHRs) with 95% CIs.
- Optional: restricted mean survival time (RMST) for absolute clinical benefit.
- Censoring: outcome, death, or administrative end date (competing-risks framework).

#### Stratification and Time-Dependent Analysis

- Stratify by all major covariates (age, sex, income, region, BMI, smoking, alcohol, physical activity, comorbidities).
- Time-dependent effectiveness in interval bins (e.g., <1, 1-2, 2-4, 4-6, 6-8, >=8 years).
- Note: "Stratified analyses were adjusted for all covariates except the stratification variable."

#### Sensitivity Analyses

Common approaches for claims-based cohort studies:
- Stricter outcome definition (e.g., 2+ claims + medication prescription).
- Negative control outcomes (outcomes with no expected association).
- Mediation analysis (if plausible intermediate pathway exists).
- Alternative PS method (e.g., matching vs. weighting).
- Subgroup by exposure timing or severity.

#### Software and Significance

- State software and version (e.g., SAS 9.4, R, Python).
- "A two-sided p value of less than 0.05 was considered statistically significant."
- For multiple primary outcomes: consider Bonferroni correction.

---

## Results (~800-1200 words)

### 4.1 Study Population
- Total screened, excluded (with per-criterion counts), and final cohort.
- Reference the flow diagram (Fig. 1).
- Baseline characteristics table (Table 1) showing pre- and post-weighting/matching balance.
- Report SMDs to confirm adequate balance (<0.1).

### 4.2 Primary Endpoint
- aHR with 95% CI for the primary outcome.
- Event counts and incidence rates in exposed vs. unexposed groups.
- Template: "In the {weighted/matched} cohort, {exposure} was associated with a {increased/decreased} risk of {outcome} (aHR, {value}; 95% CI, {lower}-{upper})."

### 4.3 Secondary Endpoints and Subgroup Analyses
- Present secondary outcomes with aHRs and 95% CIs.
- Stratification results: forest plot (Fig. 2) or table.
- Time-dependent effectiveness: present by time interval.

### 4.4 Sensitivity Analyses
- Confirm or qualify main findings with sensitivity results.
- Reference supplementary tables and figures.

### Rules
- Same rules as original article: no interpretation in Results.
- Every table and figure must be referenced.
- Numbers must match tables exactly.
- Use "was associated with," not causal language.

---

## Discussion (4-5 paragraphs, ~800-1200 words)

### Paragraph 1: Summary of Key Findings
- Restate principal findings in context of the study aim.
- Paraphrase, do not repeat exact numbers.

### Paragraphs 2-3: Comparison with Prior Literature
- Anchor paper-driven comparison.
- Address concordant and discordant findings.
- Discuss potential reasons for discrepancies (population, exposure definition, follow-up duration, confounding adjustment).

### Paragraph 4: Clinical Implications
- Population-level public health implications.
- Policy relevance (screening, vaccination, treatment guidelines).

### Paragraph 5: Limitations

Standard limitation categories for claims-based cohort studies (ordered by severity):

| # | Category | Template |
|---|----------|----------|
| 1 | Generalizability | "The study population comprised predominantly {nationality/ethnicity} adults, which may limit generalizability to other populations." |
| 2 | Residual confounding | "Despite {PS method}, residual confounding from unmeasured variables cannot be entirely excluded." |
| 3 | ICD-based misclassification | "Both exposure and outcomes were identified through administrative records, which may be subject to misclassification." |
| 4 | Unmeasured confounders | "Data on {specific confounders} were unavailable." |
| 5 | Rare outcome precision | "Effectiveness estimates for rare outcomes should be interpreted cautiously due to low event counts and wide confidence intervals." |
| 6 | Missing comparator | "{Alternative treatment} was not widely available during the study period, precluding direct comparison." |
| 7 | Administrative coding accuracy | "ICD-based outcome definitions may not capture all clinically relevant cases." |

Follow each limitation with a mitigation sentence. End with a strengths paragraph.

### Conclusion
- One to two sentences. Citable statement with effect magnitude and implication.

---

## Tables

- **Table 1**: Baseline characteristics, pre- and post-weighting/matching, with SMDs.
- **Table 2**: Primary and secondary outcome aHRs with 95% CIs (overall and by subgroup).
- **Table S1+**: ICD-10 code definitions (supplementary).
- **Table S{X}**: Emulated target trial specification (if applicable).

## Figures

- **Figure 1**: Patient flow diagram (exclusion cascade with counts).
- **Figure 2**: Forest plot of stratified analyses.
- **Figure 3**: Time-dependent effectiveness plot (aHR by follow-up interval).
- Optional: Kaplan-Meier curves, RMST difference plots.

---

## ML Prediction Model Variant

When the NHIS cohort study is a machine learning prediction model (rather than Cox regression):

### Key Differences
- **Exposure → Prediction target**: Define the outcome prediction window (e.g., 5-year incidence).
- **PS balancing → Train/test split**: Stratified 80:20 split of discovery cohort.
- **Class imbalance**: Address with SMOTE or other oversampling techniques.
- **Model selection**: List candidate models with hyperparameters; ensemble top performers.
- **Evaluation**: Sensitivity, specificity, balanced accuracy, AUROC. Primary metric justified by class imbalance.
- **Feature importance**: MDI or SHAP values; ablation study for validation.
- **External validation**: Independent cohort with same preprocessing pipeline.
- **Software**: Python (TensorFlow/Scikit-learn) for ML; SAS for descriptive/inferential statistics.

---

## Checklist Before Submission

- [ ] Data source described with coverage rate, linked domains, and anonymization
- [ ] Ethics approval with specific protocol number
- [ ] Emulated target trial table in supplementary (if applicable)
- [ ] Exclusion cascade with per-criterion counts and flow diagram
- [ ] Immortal time bias addressed (random index date assignment or equivalent)
- [ ] All covariates listed with categorization and country-specific cutoff justification
- [ ] PS method specified with balance assessment (SMD < 0.1)
- [ ] ICD-10 codes deferred to supplementary table
- [ ] Time-dependent analysis with interval bins
- [ ] At least 2 sensitivity analyses performed
- [ ] Limitation paragraph covers generalizability, residual confounding, and misclassification
- [ ] Numbers consistent between text, tables, and figures
- [ ] Reporting guideline (STROBE or RECORD) items addressed
