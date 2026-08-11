# GRRAS Checklist

**Guidelines for Reporting Reliability and Agreement Studies**
Version: GRRAS 2011
Source: https://doi.org/10.1016/j.jclinepi.2010.03.002
Reference: Kottner J, Audige L, Brorson S, et al. Guidelines for Reporting Reliability and Agreement Studies (GRRAS) were proposed. J Clin Epidemiol. 2011;64(1):96-106. doi:10.1016/j.jclinepi.2010.03.002

Licence: Crossref returns no Creative Commons licence (Elsevier).
Verification: **NOT VERIFIED — no accessible copy exists.** GRRAS was published simultaneously in
*J Clin Epidemiol* 2011;64(1):96-106 and *Int J Nurs Stud* 2011;48(6):661-671, both Elsevier and
both paywalled. **Two independent open-access indexes agree there is no free copy of either**:
OpenAlex returns no OA location and Unpaywall returns `is_oa: false` with an empty location list
for both DOIs. Neither has a PubMed Central record; the EQUATOR page links only to PubMed; the
GRRAS authors publish no tool document of their own (unlike QUADAS, ROBIS, RoB 2, TRIPOD, NOS and
CARE, whose own sites carry the instrument). ScienceDirect serves a CAPTCHA to automated retrieval,
which this audit does not complete.

**What is confirmed** is only internal: the file declares 15 items and carries 15, numbered 1–15
with no gaps, across Title/Abstract, Introduction, Methods, Results and Discussion. That says
nothing about whether they are GRRAS's items — the count matched on GATHER, REMARK and COSMIN
while the items underneath were wrong.

**To finish this file**: download either article through an institutional subscription and compare
its checklist table item by item. Until then the items below are an in-house summary, and anything
you report should be scored against the published instrument.

## Checklist Items (15 items)

### Title and Abstract

| # | Item | Description |
|---|------|-------------|
| 1 | Identification | Identify in title or abstract that the study addresses reliability and/or agreement. Specify the statistic(s) used (e.g., kappa, ICC, Bland-Altman). |

### Introduction

| # | Item | Description |
|---|------|-------------|
| 2 | Rationale | Provide the scientific background and rationale for the reliability/agreement study. |
| 3 | Objectives | State the specific objectives, including any pre-specified hypotheses (e.g., expected level of agreement). |

### Methods

| # | Item | Description |
|---|------|-------------|
| 4 | Study design | Describe the study design, including: fully crossed vs nested, raters as random or fixed effect, number of measurement occasions. |
| 5 | Sample | Describe the sample: how subjects were sampled, eligibility criteria, settings and locations, and intended variation in the measurand. |
| 6 | Measurement methods and devices | Describe the measurement methods and devices used, including any preparation, training, or calibration. |
| 7 | Raters | Describe the raters: number, relevant qualifications and experience, any rater training specific to the study, and whether raters represent the target population of users. |
| 8 | Measurement procedure | Describe the measurement procedure: setting, timing, number of measurements per subject, time interval between repeated measurements, and standardization of conditions. |
| 9 | Order of measurements | State how the order of examination was varied (e.g., randomized order, blinding to previous measurements). |
| 10 | Statistical methods | State the statistical methods used to estimate reliability and/or agreement, including: software, specific statistical model (e.g., ICC model and type), handling of missing data, methods for estimating CIs, and any additional analyses (e.g., Bland-Altman, SEM, MDC). |

### Results

| # | Item | Description |
|---|------|-------------|
| 11 | Sample and raters | Report the number of raters and subjects included in the analysis (and any exclusions). Report relevant demographic and clinical characteristics of the sample. |
| 12 | Reliability/agreement estimates | Report reliability and/or agreement estimates with confidence intervals or standard errors. For continuous measurements, report LoA or SEM/MDC as applicable. |
| 13 | Additional analyses | Report results of any additional analyses performed (e.g., effect of rater experience, subgroup analyses, time-trend analysis). |

### Discussion

| # | Item | Description |
|---|------|-------------|
| 14 | Clinical relevance | Discuss the practical and clinical relevance of the results. Include comparison with previously reported reliability/agreement values, interpretation relative to measurement purpose, and implications for clinical use. |
| 15 | Limitations | Discuss the limitations of the study, including: spectrum of measurand values, generalizability to other raters/settings, potential sources of bias (e.g., memory effects, learning effects), and any factors that may have inflated or deflated estimates. |

---

## Notes for Assessors

- GRRAS applies to all reliability and agreement studies, including inter-rater, intra-rater, test-retest, and method-comparison designs across any medical discipline.
- **Reliability vs Agreement**: These are distinct concepts. Reliability (e.g., ICC, kappa) reflects the ability to distinguish between subjects; agreement (e.g., Bland-Altman limits of agreement, SEM) reflects how close scores are on repeated measurements. A study may report one or both.
- Item 4 (Study design): The ICC model choice (one-way random, two-way random, two-way mixed) and type (single measures, average measures) must match the study design. Flag mismatches as a Major Comment.
- Item 7 (Raters): Rater characteristics strongly influence reliability estimates. Studies using expert raters only will overestimate reliability in general clinical practice. Note this if raters are not representative.
- Item 9 (Order of measurements): Randomization of measurement order is critical for avoiding memory and learning effects. Its absence should be flagged as a limitation.
- Item 12: For ICC, report the model, type, and definition (consistency vs absolute agreement). For kappa, specify weighted vs unweighted and the weighting scheme. Bare numbers without these specifications are PARTIAL.
- Common in radiology: inter-reader agreement for measurements (Bland-Altman, ICC), segmentation agreement (Dice, ICC of volumes), and diagnostic classification agreement (kappa, percent agreement).
- GRRAS is complementary to study-type checklists. For example, a diagnostic accuracy study reporting inter-reader agreement should follow STARD for the main analysis and GRRAS for the agreement component.
