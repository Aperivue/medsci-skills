# COSMIN Risk of Bias Assessment Guide

COnsensus-based Standards for the selection of health Measurement INstruments — Risk of Bias tool for reliability and measurement error.
Reference: Mokkink LB et al. BMC Medical Research Methodology 2020;20:293.
Website: https://www.cosmin.nl

Version: COSMIN Risk of Bias tool (2018 guideline)
Source: Prinsen CAC, Mokkink LB, Bouter LM, Alonso J, Patrick DL, de Vet HCW, et al. COSMIN guideline for systematic reviews of patient-reported outcome measures. *Qual Life Res* 2018;27(5):1147-1157 (DOI 10.1007/s11136-018-1798-3).
Licence: CC BY 4.0 — confirmed via Crossref.
Verification: **NOT VERIFIED.** The items below have not been compared against the published table. They are an in-house summary; complete the official instrument for anything you report.

## Purpose

The COSMIN Risk of Bias tool assesses the methodological quality of studies on **reliability** and **measurement error** of outcome measurement instruments (e.g., questionnaires, imaging measurements, lab tests).

## Structure

Two parts:
- **Part A**: Understanding how the study informs on reliability/measurement error (7 elements of a comprehensive research question)
- **Part B**: Assessing quality using standards (9 for reliability, 8 for measurement error)

Quality rating per standard: Very Good / Adequate / Doubtful / Inadequate

Overall quality uses the **worst-score-counts** principle (lowest rating across all standards).

## Part A: Elements of a Comprehensive Research Question

Extract these 7 elements from the study:

| # | Element |
|---|---------|
| 1 | Name of the outcome measurement instrument |
| 2 | Version or operationalization of the measurement protocol |
| 3 | Construct measured by the instrument |
| 4 | Reliability parameter (ICC, kappa, etc.) or measurement error parameter (SEM, LoA, SDC) |
| 5 | Components of the instrument that will be repeated |
| 6 | Source(s) of variation that will be varied (time, rater, machine, etc.) |
| 7 | Patient population studied |

## Components of Outcome Measurement Instruments

### Without biological sampling
- Equipment (questionnaire forms, imaging device, software)
- Preparatory actions (training, calibration, patient instructions)
- Collection of raw data (patient completing questions, rater observing)
- Data processing and storage (digitization, image reconstruction)
- Assignment of score (formula, algorithm, clinical judgment)
- Optional further use (conversion to another scale/classification)

### With biological sampling
- Equipment (collection tools, containers, lab equipment)
- Preparatory actions (patient prep, equipment calibration)
- Collection of sample (blood draw, biopsy)
- Processing and storage (centrifugation, freezing)
- Determination of value (assay, measurement)
- Optional further use (conversion to classification)

## Part B: Standards for Studies on Reliability

### Standard 1: Study Design
- Were patients measured independently by raters (inter-rater) or on separate occasions (test-retest)?
- Was the time interval appropriate (short enough to avoid true change, long enough to avoid memory)?

### Standard 2: Missing Data
- Were missing data adequately handled?
- Was the percentage of missing data acceptable?

### Standard 3: Sample Size
- Was the sample size adequate? (minimum 30 recommended, 50+ preferred)

### Standard 4: Patients
- Were patients selected to represent a range of the construct being measured?
- Were patients stable between measurements (for test-retest)?

### Standard 5: Independent Measurements
- Were measurements performed independently of each other?
- Were raters blinded to previous measurements or other rater's results?

### Standard 6: Similar Conditions
- Were measurement conditions similar across repeated measurements?
- Were there important differences in testing conditions?

### Standard 7: Appropriate Statistical Methods
- Was the appropriate reliability parameter calculated (ICC for continuous, kappa for categorical)?
- Was the correct ICC model used (one-way, two-way, agreement vs consistency)?

### Standard 8: ICC Model and Formula
- Were the ICC model and formula correctly specified?
- Was the ICC type appropriate for the study design (single measures vs average measures)?

### Standard 9: Reporting
- Were sufficient statistics reported (ICC/kappa with 95% CI)?
- Were descriptive statistics reported (means, SDs)?

## Part B: Standards for Studies on Measurement Error

### Standard 1: Study Design
Same as reliability Standard 1.

### Standard 2: Missing Data
Same as reliability Standard 2.

### Standard 3: Sample Size
Same as reliability Standard 3.

### Standard 4: Patients
Same as reliability Standard 4.

### Standard 5: Independent Measurements
Same as reliability Standard 5.

### Standard 6: Similar Conditions
Same as reliability Standard 6.

### Standard 7: Appropriate Parameter
- Was the appropriate measurement error parameter calculated (SEM, LoA, SDC, or percentage agreement)?

### Standard 8: Reporting
- Were sufficient statistics reported (SEM, LoA, or SDC with 95% CI)?
- Were Bland-Altman plots provided where appropriate?

## Overall Quality Rating

Uses the **worst-score-counts** principle:
- Rate each standard as: Very Good / Adequate / Doubtful / Inadequate
- Overall rating = lowest rating across all applicable standards

| Rating | Interpretation |
|--------|---------------|
| Very Good | Study design and methods are optimal for this measurement property |
| Adequate | Study design and methods are acceptable |
| Doubtful | Study design or methods raise some concerns |
| Inadequate | Study design or methods are clearly flawed |

## When to Use

- Systematic reviews of measurement properties of health measurement instruments
- Selecting outcome measurement instruments for clinical trials or research
- Developing core outcome sets (COS)
- Evaluating reliability/agreement of imaging measurements, scoring systems, clinical tests
- Typically used alongside other COSMIN boxes (content validity, structural validity, etc.)
