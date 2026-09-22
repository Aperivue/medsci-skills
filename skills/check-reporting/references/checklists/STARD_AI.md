# STARD-AI Checklist

**Standards for Reporting of Diagnostic Accuracy Studies — Artificial Intelligence**
Version: STARD-AI 2025
Source: https://doi.org/10.1038/s41591-025-03953-8

**Reference:** STARD-AI Steering Committee, STARD-AI Consensus Group, Sounderajah V, Guni A, Liu X, Collins GS, Karthikesalingam A, Markar SR, Golub RM, Denniston AK, Shetty S, Moher D, Bossuyt PM, Darzi A, Ashrafian H. The STARD-AI reporting guideline for diagnostic accuracy studies using artificial intelligence. Nat Med. 2025;31(10):3283-3289. PMID: 40954311. DOI: 10.1038/s41591-025-03953-8

**Author Correction:** Nat Med. 2026;32(9):3493 (published online 13 July 2026). PMID: 42443516. DOI: 10.1038/s41591-026-04570-9. The correction adds one omitted name to the STARD-AI Steering Committee consortium list. It does not touch Table 2 — no item, sub-item, description, numbering or NEW/MODIFIED classification changes, so this checklist is unaffected by it.

**License:** Creative Commons Attribution (CC BY)

**Scope:** AI-centred diagnostic test accuracy studies. Applies to studies evaluating the diagnostic accuracy of AI systems including machine learning, deep learning models, natural language processing tools, and foundation models that generate or support diagnostic outputs. Does NOT apply to static/manually programmed rule-based systems or simple decision trees.

**Relationship to STARD 2015:** STARD-AI extends STARD 2015 (Bossuyt et al. BMJ 2015). The checklist has 40 numbered items rendered as 48 rows (items 15, 16, 17, 26 and 40 have sub-items): 30 rows are UNCHANGED from STARD 2015, 4 are MODIFIED, and 14 are NEW. The published abstract states 18 new or modified items, which matches 14 + 4. Items are numbered to maintain alignment with STARD 2015 where possible.

**Relationship to other guidelines:**
- CONSORT-AI: for clinical trials of AI interventions
- SPIRIT-AI: for trial protocols involving AI
- TRIPOD+AI: for AI prediction/prognostic models
- CLAIM 2024: for AI/ML in medical imaging
- Use STARD-AI when diagnostic accuracy of an AI system is the primary focus

---

## Checklist Items (40 numbered items in 48 rows; items 15, 16, 17, 26, and 40 have sub-items)

### Title and Abstract

| # | Item | Description | Status vs STARD 2015 |
|---|------|-------------|---------------------|
| 1 | Title | Identification as a study reporting AI-centered diagnostic accuracy and reporting at least one measure of accuracy within title or abstract. | MODIFIED |
| 2 | Abstract | Structured summary of study design, methods, results and conclusions (for specific guidance, see STARD for Abstracts). | UNCHANGED |

### Introduction

| # | Item | Description | Status vs STARD 2015 |
|---|------|-------------|---------------------|
| 3 | Scientific background | Scientific and clinical background, including the intended use of the index test, whether it is novel or an established index test and its integration into an existing or new workflow, if applicable. | MODIFIED |
| 4 | Objectives | Study objectives and hypotheses. | UNCHANGED |

### Methods

#### Study Design

| # | Item | Description | Status vs STARD 2015 |
|---|------|-------------|---------------------|
| 5 | Study design | Whether data collection was planned before the index test and reference standard were performed (prospective study) or after (retrospective study). | UNCHANGED |

#### Ethics

| # | Item | Description | Status vs STARD 2015 |
|---|------|-------------|---------------------|
| 6 | Ethics approval | Formal approval from an ethics committee. If not required, justify why. | NEW |

#### Participants

| # | Item | Description | Status vs STARD 2015 |
|---|------|-------------|---------------------|
| 7 | Eligibility criteria | Eligibility criteria: listing separate inclusion and exclusion criteria in the order that they are applied at both participant level and data level. | MODIFIED |
| 8 | Participant identification basis | On what basis potentially eligible participants were identified (such as symptoms, results from previous tests and inclusion in registry). | UNCHANGED |
| 9 | Setting and dates | Where and when potentially eligible participants were identified (setting, location and dates). | UNCHANGED |
| 10 | Participant series | Whether participants formed a consecutive, random or convenience series. | UNCHANGED |

#### Dataset

| # | Item | Description | Status vs STARD 2015 |
|---|------|-------------|---------------------|
| 11 | Data source | Source of the data and whether they have been routinely collected, specifically collected for the purpose of the study or acquired from an open-source repository. | NEW |
| 12 | Dataset annotation | Who undertook the annotations for the dataset (including experience levels and background) and how (within the same clinical context or in a post hoc fashion), if applicable. | NEW |
| 13 | Data capture devices and software | Devices (manufacturer and model) that were used to capture data; software (with version number) used to engineer the index test, highlighting the intended use. | NEW |
| 14 | Data acquisition and preprocessing | Data acquisition protocols (for example, contrast protocol or reconstruction method for medical images) and details of data preprocessing, in sufficient detail to allow replication. | NEW |

#### Test Methods

| # | Item | Description | Status vs STARD 2015 |
|---|------|-------------|---------------------|
| 15a | Index test | Index test, in sufficient detail to allow replication. | UNCHANGED |
| 15b | Index test development | How the index test was developed, including any training, validation, testing and external evaluation, detailing sample sizes, when applicable. | NEW |
| 15c | Index test cut-offs | Definition of and rationale for test positivity cutoffs or result categories of the index test, distinguishing prespecified from exploratory. | UNCHANGED |
| 15d | End-user specification | The specified end-user of the index test and the level of expertise required of users. | NEW |
| 16a | Reference standard | Reference standard, in sufficient detail to allow replication. | UNCHANGED |
| 16b | Reference standard rationale | Rationale for choosing the reference standard (if alternatives exist). | UNCHANGED |
| 16c | Reference standard cut-offs | Definition of and rationale for test positivity cutoffs or result categories of the reference standard, distinguishing prespecified from exploratory. | UNCHANGED |
| 17a | Blinding (index test) | Whether clinical information and reference standard results were available to the performers or readers of the index test. | UNCHANGED |
| 17b | Blinding (reference standard) | Whether clinical information and index test results were available to the assessors of the reference standard. | UNCHANGED |

#### Analysis

| # | Item | Description | Status vs STARD 2015 |
|---|------|-------------|---------------------|
| 18 | Statistical methods | Methods for estimating or comparing measures of diagnostic accuracy. | UNCHANGED |
| 19 | Indeterminate results | How indeterminate index test or reference standard results were handled. | UNCHANGED |
| 20 | Missing data | How missing data on the index test and reference standard were handled. | UNCHANGED |
| 21 | Variability analyses | Any analyses of variability in diagnostic accuracy, distinguishing prespecified from exploratory. | UNCHANGED |
| 22 | Sample size | Intended sample size and how it was determined. | UNCHANGED |
| 23 | Fairness assessment (methods) | Details of any performance error analysis and algorithmic bias and fairness assessments, if undertaken. | NEW |

### Results

#### Participants and Dataset

| # | Item | Description | Status vs STARD 2015 |
|---|------|-------------|---------------------|
| 24 | Flow diagram | Flow of participants, using a diagram. | UNCHANGED |
| 25 | Baseline characteristics | Baseline demographic, clinical and technical characteristics of training, validation and test sets, if applicable. | MODIFIED |
| 26a | Distribution of severity | Distribution of severity of disease in those with the target condition. | UNCHANGED |
| 26b | Alternative diagnoses | Distribution of alternative diagnoses in those without the target condition. | UNCHANGED |
| 27 | Time interval | Time interval and any clinical interventions between index test and reference standard. | UNCHANGED |
| 28 | Test set representativeness | Whether the datasets represent the distribution of the target condition that one would expect from the intended use population. | NEW |
| 29 | External evaluation differences | For external evaluation on an independent dataset, an assessment of how this differs from the training, validation and test sets. | NEW |

#### Test Results

| # | Item | Description | Status vs STARD 2015 |
|---|------|-------------|---------------------|
| 30 | Cross-tabulation | Cross-tabulation of the index test results (or their distribution) by the results of the reference standard. | UNCHANGED |
| 31 | Accuracy estimates | Estimates of diagnostic accuracy and their precision (such as 95% confidence intervals). | UNCHANGED |
| 32 | Adverse events | Any adverse events from performing the index test or the reference standard. | UNCHANGED |

### Discussion

| # | Item | Description | Status vs STARD 2015 |
|---|------|-------------|---------------------|
| 33 | Study limitations | Study limitations, including sources of potential bias, statistical uncertainty and generalizability. | UNCHANGED |
| 34 | Clinical applicability | Implications for practice, including the intended use and clinical role of the index test. | UNCHANGED |
| 35 | Ethical considerations and fairness | Ethical considerations and adherence to ethical standards associated with the use of the index test and issues of fairness. | NEW |

### Other Important Information

| # | Item | Description | Status vs STARD 2015 |
|---|------|-------------|---------------------|
| 36 | Registration | Registration number and name of registry. | UNCHANGED |
| 37 | Protocol | Where the full study protocol can be accessed. | UNCHANGED |
| 38 | Funding | Sources of funding and other support; role of funders. | UNCHANGED |
| 39 | Commercial interests | Commercial interests, if applicable. | NEW |
| 40a | Data and code availability | Availability of datasets and code, detailing any restrictions on their reuse and repurposing. | NEW |
| 40b | Audit and evaluation | Whether outputs are stored, auditable and available for evaluation, if necessary. | NEW |

---

## Summary of Changes from STARD 2015

### MODIFIED Items (4)

| STARD-AI Item | Change Summary |
|---------------|---------------|
| 1 (Title) | Added requirement to identify the study as AI-centered diagnostic accuracy |
| 3 (Introduction) | Added requirement for intended use, novelty, and workflow integration |
| 7 (Eligibility criteria) | Expanded to include eligibility at both participant and data level |
| 25 (Baseline characteristics) | Expanded to include characteristics of training, validation, and test sets |

### NEW Items (14)

| STARD-AI Item | Topic |
|---------------|-------|
| 6 | Ethics approval |
| 11 | Data source and collection method |
| 12 | Dataset annotation |
| 13 | Data capture devices and software |
| 14 | Data acquisition and preprocessing |
| 15b | Index test development (training, validation, testing) |
| 15d | End-user specification and expertise level |
| 23 | Fairness assessment methods |
| 28 | Test set representativeness |
| 29 | External evaluation differences |
| 35 | Ethical considerations and fairness |
| 39 | Commercial interests |
| 40a | Data and code availability |
| 40b | Audit and evaluation of outputs |

---

## Notes for Assessors

### When to Use STARD-AI vs Other AI Guidelines

- **STARD-AI**: When the study evaluates diagnostic accuracy of an AI system as the primary outcome. Includes imaging AI, LLM-based diagnostic tools, pathology AI, EHR-based diagnostic systems.
- **TRIPOD+AI / TRIPOD-LLM**: When the study develops or validates a prediction/prognostic model using AI/ML.
- **CLAIM 2024**: When the study develops or validates an AI model specifically for medical imaging.
- **CONSORT-AI**: When the study is a clinical trial of an AI intervention.
- Authors may refer to multiple checklists and select the one most aligned with the study's primary aim.

### Key Assessment Points

1. **Item 1 (Title)**: The title must explicitly identify the study as reporting AI-centered diagnostic accuracy. Merely mentioning "machine learning" or "deep learning" without connecting it to diagnostic accuracy is PARTIAL.
2. **Item 7 (Eligibility)**: STARD-AI requires eligibility criteria at BOTH participant level (e.g., age, diagnosis) AND data level (e.g., image quality, scanner type). Reporting only participant-level criteria is PARTIAL.
3. **Item 12 (Annotation)**: Must include who annotated, their experience levels and background, and how (within clinical context or post hoc). Missing any of these elements is PARTIAL.
4. **Item 14 (Data acquisition)**: Must describe data acquisition protocols and preprocessing in sufficient detail to allow replication.
5. **Item 23 & 35 (Fairness/Ethics)**: These are paired items — methods/assessment in Item 23, ethical considerations and fairness discussion in Item 35. Both must be present. If the study claims fairness was not assessed, this should be explicitly stated with justification.
6. **Item 25 (Baseline characteristics)**: For AI studies, characteristics must be reported for EACH dataset partition (training, validation, test), not just overall.
7. **Items 39-40b (Other information)**: Commercial interests (39), data/code availability (40a), and audit/evaluation (40b) are NEW and commonly missing. These are increasingly required by journals.

### Relationship to MI-CLEAR-LLM

If the AI system under evaluation is an LLM (e.g., GPT-4, Claude, Gemini), apply MI-CLEAR-LLM (6 items) alongside STARD-AI. MI-CLEAR-LLM addresses LLM-specific concerns (stochasticity, prompt documentation, data contamination) that are not covered by STARD-AI.

### Common Gaps in AI Diagnostic Accuracy Studies

Based on the systematic review that informed STARD-AI development (Aggarwal et al. npj Digit Med 2021):
1. Missing annotation process details
2. Missing data preprocessing description
3. No fairness/bias assessment
4. No external validation or test set representativeness discussion
5. Missing model architecture and training details
6. No commercial interest disclosure
7. No data/code availability statement

---

## Verification Note

**2026-04-11 — item inventory.** This checklist was verified against the published Table 2 of the
STARD-AI paper in Nature Medicine (2025;31(10):3283-3289, DOI 10.1038/s41591-025-03953-8). Item
numbering, descriptions, and NEW/MODIFIED/UNCHANGED classifications match the published version.
Verified via the Nature Medicine online full-size Table 2
(https://www.nature.com/articles/s41591-025-03953-8/tables/2) and the STARD 2015 checklist (EQUATOR
Network). The STARD 2015 original checklist (Bossuyt et al. BMJ 2015) was used to confirm UNCHANGED
items.

**2026-09-22 — header arithmetic, re-verified against Table 2.** The header above previously read
"Of the 40 items, 22 are UNCHANGED from STARD 2015, 4 are MODIFIED, and 14 are NEW". That is 40 − 4 −
14: the *numbered-item* denominator applied to a *row-level* split. The two denominators differ,
because items 15, 16, 17, 26 and 40 carry sub-items. Measured on the table below, the split is 30
UNCHANGED / 4 MODIFIED / 14 NEW = 48 rows across 40 numbered items. The table itself, the Summary of
Changes section and the published statement were all already consistent with 30; only the header
sentence was wrong.

Re-verified row by row against Table 2 in the accepted manuscript deposited at the University of
Birmingham repository (https://pure-oai.bham.ac.uk/ws/files/282528526/STARD_AI_accepted.pdf), the
Nature version of record being paywalled. Every row, sub-item letter and marker matched: Table 2
marks †Modified on items 1, 3, 7, 25 (4 items) and *New on items 6, 11, 12, 13, 14, 15b, 15d, 23,
28, 29, 35, 39, 40a, 40b (14 items), leaving 30 unmarked rows; the same 48 rows in the same order
and grouping appear below. The statement's own body text says the same in prose: "Four items were
modified from the STARD 2015 statement (items 1, 3, 7 and 25), while fourteen new items have been
introduced". The abstract's "18 new or modified items" is 14 + 4. Item descriptions below follow
Nature house style ("for example" for "e.g.", "test sets" for "test set") rather than the accepted
manuscript's wording, consistent with their having been taken from the version of record in the
2026-04-11 pass; no description was changed in this pass.

The 2026 Author Correction (Nat Med 2026;32(9):3493, DOI 10.1038/s41591-026-04570-9) was read in
full at nature.com. Its entire content is the addition of one omitted name to the Steering Committee
consortium list. It changes nothing in Table 2 and nothing in this file's items.
