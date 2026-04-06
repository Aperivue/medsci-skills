# STARD 2015 Checklist

**Standards for Reporting of Diagnostic Accuracy Studies**
Version: STARD 2015
Source: https://www.stard-statement.org

## Checklist Items (30 items)

### Title and Abstract

| # | Item | Description |
|---|------|-------------|
| 1 | Title | Identification as a study of diagnostic accuracy using at least one measure of accuracy (such as sensitivity, specificity, predictive values, or AUC). |
| 2 | Abstract | Structured abstract with: study design, methods (participants, index test, reference standard), results (number of participants, estimates of diagnostic accuracy with confidence intervals), conclusions. |

### Introduction

| # | Item | Description |
|---|------|-------------|
| 3 | Scientific background | Scientific and clinical background, including the intended use and clinical role of the index test. |
| 4 | Objectives | Study objectives and hypotheses. |

### Methods

#### Participants

| # | Item | Description |
|---|------|-------------|
| 5 | Study design | Whether data collection was planned before the index test and reference standard were performed (prospective study) or after (retrospective study). |
| 6 | Eligibility criteria | Eligibility criteria: inclusion and exclusion criteria, settings and locations where data were collected. |
| 7 | Sampling | Whether participants formed a consecutive, random, or convenience series. |

#### Test Methods

| # | Item | Description |
|---|------|-------------|
| 8a | Index test | Index test, in sufficient detail to allow replication. |
| 8b | Reference standard | Reference standard, in sufficient detail to allow replication. |
| 9 | Rationale for reference standard | Rationale for choosing the reference standard (if alternatives exist). |
| 10a | Pre-specification | Definition of and rationale for test positivity cut-offs or result categories of the index test, distinguishing pre-specified from exploratory. |
| 10b | Pre-specification | Definition of and rationale for test positivity cut-offs or result categories of the reference standard, distinguishing pre-specified from exploratory. |
| 11 | Blinding | Whether clinical information and reference standard results were available to the performers/readers of the index test and vice versa. |
| 12 | Additional analyses | Methods for estimating or comparing measures of diagnostic accuracy. Methods for calculating test reproducibility, if done. |
| 13 | Sample size | How the sample size was determined (power analysis, convenience, or other rationale). |

### Results

#### Participants

| # | Item | Description |
|---|------|-------------|
| 14 | Dates and setting | When the study was done, including beginning and end dates of recruitment. |
| 15 | Demographics | Clinical and demographic characteristics of participants (age, sex, disease spectrum, comorbidities, current treatments, recruitment centers). |
| 16 | Participant numbers | The number of participants satisfying the criteria for inclusion who did or did not undergo the index test and/or the reference standard; describe why participants failed to receive either test (a flow diagram is strongly recommended). |

#### Test Results

| # | Item | Description |
|---|------|-------------|
| 17 | Time interval | Time interval and any clinical interventions between index test and reference standard. |
| 18 | Distribution of severity | Distribution of severity of disease in those with the target condition; distribution of alternative diagnoses in those without the target condition. |
| 19 | Cross-tabulation | A cross tabulation of the index test results (or their distribution) by the results of the reference standard. |
| 20 | Indeterminate results | Any adverse events from performing the index test or the reference standard. |
| 21 | Accuracy estimates | Estimates of diagnostic accuracy and their precision (such as 95% confidence intervals). |
| 22 | Handling of indeterminate | How indeterminate index test or reference standard results were handled. |
| 23 | Subgroup analyses | Any analyses of variability in diagnostic accuracy, distinguishing pre-specified from exploratory (subgroup analyses by age, sex, disease severity, etc.). |

### Discussion

| # | Item | Description |
|---|------|-------------|
| 24 | Study limitations | Study limitations, including sources of potential bias, statistical uncertainty, and generalisability. |
| 25 | Clinical applicability | Implications for practice, including the intended use and clinical role of the index test. |

### Other Information

| # | Item | Description |
|---|------|-------------|
| 26 | Registration | Registration number and name of registry. |
| 27 | Protocol | Where the full study protocol can be accessed. |
| 28 | Funding | Sources of funding and other support; role of funders. |

---

## STARD Flow Diagram

The STARD flow diagram is **strongly recommended** (item 16). It should show:

```
Eligible patients (N = ?)
  |
  v
Enrolled (N = ?)
  |
  +-- Did not receive index test (N = ?, reasons)
  |
  v
Received index test (N = ?)
  |
  +-- Did not receive reference standard (N = ?, reasons)
  |
  v
Received both index test AND reference standard (N = ?)
  |
  +-- Index test results:
  |     Positive (N = ?)
  |     Negative (N = ?)
  |     Inconclusive (N = ?)
  |
  +-- Reference standard results:
        Target condition present (N = ?)
        Target condition absent (N = ?)
```

---

## STARD-AI Extension

For studies evaluating AI-based diagnostic tests, also report:

| # | Item | Description |
|---|------|-------------|
| AI-1 | AI system description | Name, version, manufacturer, and regulatory status of the AI system. |
| AI-2 | Training data | Description of training data: source, size, demographic characteristics. |
| AI-3 | Data preprocessing | Description of any preprocessing or augmentation applied to the input data. |
| AI-4 | Intended use | The intended use of the AI system in clinical practice. |
| AI-5 | Integration | How the AI output was integrated into the diagnostic pathway (standalone, assistive, replacement). |
| AI-6 | Human comparators | If comparing AI to human readers: experience level, specialty, and reading conditions. |
| AI-7 | Failure analysis | Analysis of cases where the AI system produced incorrect or indeterminate results. |

---

## Notes for Assessors

- Item 16 (flow diagram): if not provided as a figure, check whether the same information is conveyed in the text.
- Item 11 (blinding): in retrospective studies with AI, consider whether the AI had access to clinical information beyond the intended input.
- Item 19 (cross-tabulation): a 2x2 table is the minimum; report TP, FP, TN, FN counts.
- Items 26-27 (registration/protocol): many diagnostic accuracy studies are not registered, but this is increasingly expected. Mark as MISSING if absent, with a note that registration is recommended.
- For AI studies, always also apply the STARD-AI extension items.
