# Research Protocol Template

Complete 10-section structure for IRB/ethics committee submission.
Use this template as a formatting reference when generating protocol drafts.

---

## Header

```
Research Protocol

Title: [Full study title]
Short Title: [Acronym or abbreviated title]
Protocol Version: [e.g., 1.0]
Date: [YYYY-MM-DD]
Principal Investigator: [Name, Degree, Affiliation]
Co-Investigators: [Names, Degrees, Affiliations]
Institution: [Institution name and department]
```

---

## 1. Background and Rationale

**Target length**: 400-600 words
**Format**: Full prose paragraphs, no bullet points

### Content guidance

**Paragraph 1 -- Clinical context (100-150 words)**
- Describe the disease or clinical problem
- State the burden (incidence, prevalence, morbidity, mortality)
- Describe current clinical practice or standard of care

Example phrasing:
> "[Disease] affects approximately [N] patients annually worldwide and remains a
> significant cause of [morbidity/mortality]. Current standard of care involves
> [intervention/diagnostic approach], which [limitation]."

**Paragraph 2 -- Literature review (150-200 words)**
- Summarize key prior studies (3-5 references minimum)
- Identify what is known and what remains uncertain
- Highlight the specific knowledge gap this study addresses

Example phrasing:
> "Several studies have investigated [topic]. [Author] et al. reported [finding]
> in a [study type] of [N] patients (DOI: [verified DOI]). However, [limitation
> of prior work]. To date, no study has [specific gap]."

**Paragraph 3 -- Rationale and hypothesis (100-150 words)**
- State why this study is needed
- Describe what this study will add
- Present the hypothesis or research question

Example phrasing:
> "This study aims to [objective]. We hypothesize that [specific, testable
> hypothesis]. The results of this study will [clinical or scientific impact]."

### What to avoid
- Overly broad introductions unrelated to the research question
- Unsupported claims or citations without DOI/PMID
- AI-pattern phrases: "it is worth noting", "plays a crucial role", "comprehensive"

---

## 2. Study Design and Eligibility Criteria

**Target length**: 300-500 words
**Format**: Full prose with numbered criteria lists

### Content guidance

**Study design statement (50-80 words)**

Example phrasing:
> "This is a [retrospective/prospective] [cohort/cross-sectional/case-control/
> diagnostic accuracy] study conducted at [institution]. This design was selected
> because [justification -- e.g., the outcome has already occurred and medical
> records are available, or a prospective comparison is needed to minimize bias]."

**Setting and study period (30-50 words)**

> "The study will be conducted at [institution name], a [bed count]-bed
> [academic/community] [hospital/medical center] in [city, country]. The study
> period spans from [start date] to [end date]."

**Inclusion criteria (numbered list)**

> Patients will be included if they meet all of the following criteria:
> 1. Age >= [X] years at the time of [index event]
> 2. [Diagnosis/procedure/exposure] confirmed by [method]
> 3. [Imaging/lab/clinical data] available within [timeframe]
> 4. [Additional criterion as needed]

**Exclusion criteria (numbered list)**

> Patients will be excluded if any of the following apply:
> 1. [Condition that would confound results]
> 2. [Missing critical data -- specify which variables]
> 3. [Prior treatment that alters the natural history]
> 4. [Additional criterion as needed]

### What to avoid
- Vague inclusion criteria (e.g., "patients with cancer" without specifying type, stage, or confirmation method)
- Overly restrictive criteria that limit generalizability without justification
- Missing the analysis unit declaration (patient vs lesion vs exam)

---

## 3. Sample Size Justification

**Target length**: 150-300 words
**Format**: Full prose, single paragraph or two short paragraphs

### Content guidance

State all of the following:
- Statistical test used for sample size calculation
- Expected effect size and its source (prior study with citation)
- Alpha level (typically 0.05, two-sided)
- Power (typically 0.80 or 0.90)
- Attrition or dropout adjustment (typically 10-20%)
- Final enrollment target

Example phrasing:
> "Sample size was calculated based on [test type]. Based on prior data from
> [Author] et al. (DOI: [verified DOI]), we assumed [effect size specification --
> e.g., a difference of X% between groups, an AUC of 0.85 under the alternative
> hypothesis]. With a two-sided alpha of 0.05 and 80% power, [N] subjects per
> group are required. Accounting for an anticipated [X]% attrition rate, we plan
> to enroll [N_adjusted] participants in total."

For diagnostic accuracy studies:
> "Using the method of [Flahault/Buderer/Obuchowski], assuming a target
> sensitivity of [X]% with a 95% confidence interval lower bound no less than
> [Y]%, and an expected prevalence of [Z]%, a minimum of [N] subjects is required."

### What to avoid
- Missing the source of the assumed effect size
- Power < 0.80 without explicit justification
- Failure to account for attrition or clustering

---

## 4. Statistical Analysis Plan

**Target length**: 300-500 words
**Format**: Full prose with structured subsections

### Content guidance

**Descriptive statistics (40-60 words)**

> "Continuous variables will be reported as mean (standard deviation) or median
> (interquartile range) depending on normality assessed by the Shapiro-Wilk test.
> Categorical variables will be reported as frequency (percentage)."

**Primary analysis (80-120 words)**

> "The primary outcome [outcome name] will be compared between [groups] using
> [specific test]. [State assumptions and how violations will be handled -- e.g.,
> if the normality assumption is violated, the Wilcoxon rank-sum test will be
> used as an alternative.] Results will be reported as [effect measure] with 95%
> confidence intervals."

For diagnostic accuracy:
> "Sensitivity, specificity, positive predictive value, and negative predictive
> value will be calculated with exact binomial 95% confidence intervals. The area
> under the receiver operating characteristic curve (AUC) will be estimated using
> [DeLong/bootstrap] method."

**Secondary analyses (60-80 words)**

> "Secondary outcomes will be analyzed as follows: [list each secondary outcome
> and its corresponding test]. These analyses are considered exploratory and will
> not be adjusted for multiple comparisons unless otherwise specified."

**Subgroup analyses (40-60 words)**

> "Pre-specified subgroup analyses will be conducted by [variables -- e.g., age
> group, sex, disease severity]. Interaction terms will be tested in regression
> models to assess effect modification. Subgroup results will be interpreted with
> caution given the reduced statistical power."

**Missing data (40-60 words)**

> "The extent and pattern of missing data will be assessed. If missing data
> exceed [X]%, [multiple imputation / inverse probability weighting] will be
> applied. A complete-case sensitivity analysis will be conducted to assess the
> robustness of results."

**Software and significance level (20-30 words)**

> "All analyses will be performed using [R version X.X.X / Python X.X / SAS X.X].
> A two-sided p-value < 0.05 will be considered statistically significant."

### What to avoid
- Listing tests without connecting them to specific outcomes
- Missing the missing data strategy
- Unspecified software version
- "Appropriate statistical tests will be used" (too vague)

---

## 5. Study Title and Registration

**Format**: TODO markers only

```
[TODO: Full study title]
[TODO: Short title / acronym]
[TODO: Clinical trial registry number if applicable (e.g., ClinicalTrials.gov, CRIS)]
[TODO: Protocol version number and date]
```

---

## 6. Data Collection and Management

**Format**: TODO markers with guidance notes

```
[TODO: List variables to be collected -- use your institution's CRF template]
[TODO: Data collection method (chart review / prospective forms / electronic extraction)]
[TODO: Data storage and security measures (encrypted database, access controls)]
[TODO: Quality assurance procedures (double data entry, range checks)]
[TODO: Data retention period per institutional policy]
```

---

## 7. Ethical Considerations

**Format**: TODO markers with jurisdiction-specific guidance

```
[TODO: IRB/Ethics committee name and expected submission date]
[TODO: Informed consent process -- or justification for waiver]
[TODO: Patient privacy and data protection measures]
[TODO: Confirm applicable regulations with your IRB office]
```

Jurisdiction guidance:
- Korea: PIPA, Bioethics and Safety Act
- United States: HIPAA, Common Rule (45 CFR 46)
- European Union: GDPR Article 9, Clinical Trials Regulation (EU 536/2014)

See `ethics_checklist.md` for the full checklist.

---

## 8. Timeline and Milestones

**Format**: TODO table

```
[TODO: Adapt to your project schedule]

| Phase | Activity                              | Duration    | Target Date |
|-------|---------------------------------------|-------------|-------------|
| 1     | IRB approval                          | [X] weeks   | [TODO]      |
| 2     | Data collection / Patient enrollment  | [X] months  | [TODO]      |
| 3     | Data cleaning and analysis            | [X] months  | [TODO]      |
| 4     | Manuscript preparation                | [X] months  | [TODO]      |
| 5     | Submission                            | --          | [TODO]      |
```

---

## 9. Budget

**Format**: TODO markers with common categories

```
[TODO: Use your institution's budget template]

Common cost categories (delete or add as needed):
- Personnel (research coordinator, statistician)
- Equipment and supplies
- Software licenses
- Statistical consultation
- Publication fees (open access APC)
- Patient compensation (if applicable)
```

---

## 10. References

**Format**: Numbered list, every entry with DOI or PMID

```
1. [Author] et al. [Title]. [Journal]. [Year];[Vol]:[Pages]. DOI: [DOI]
2. [Author] et al. [Title]. [Journal]. [Year];[Vol]:[Pages]. PMID: [PMID]
...
```

References are generated from:
- Section 1 (Background and Rationale) citations
- Section 3 (Sample Size Justification) effect size sources
- Any additional references from cross-skill outputs

Mark unverified references as: `[UNVERIFIED - NEEDS MANUAL CHECK]`
