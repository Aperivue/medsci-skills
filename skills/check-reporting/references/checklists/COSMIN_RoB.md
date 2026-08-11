# COSMIN Risk of Bias Assessment Guide

COnsensus-based Standards for the selection of health Measurement INstruments — Risk of Bias tool for reliability and measurement error.
Reference: Mokkink LB et al. BMC Medical Research Methodology 2020;20:293.
Website: https://www.cosmin.nl

Version: COSMIN Risk of Bias tool for reliability and measurement error (2020 Delphi study)
Source: Mokkink LB, Boers M, van der Vleuten CPM, Bouter LM, Alonso J, Patrick DL, et al. COSMIN Risk of Bias tool to assess the quality of studies on reliability or measurement error of outcome measurement instruments: a Delphi study. *BMC Med Res Methodol* 2020;20:293 (DOI 10.1186/s12874-020-01179-5). The four-point rating system and the 'worst score counts' principle: Mokkink LB, de Vet HCW, Prinsen CAC, Patrick DL, Alonso J, Bouter LM, Terwee CB. COSMIN Risk of Bias checklist for systematic reviews of Patient-Reported Outcome Measures. *Qual Life Res* 2018;27(5):1171-1179 (DOI 10.1007/s11136-017-1765-4). Review workflow: Prinsen CAC, et al. *Qual Life Res* 2018;27(5):1147-1157 (DOI 10.1007/s11136-018-1798-3).
Licence: CC BY 4.0 for all three — confirmed via Crossref.
Verification: the seven Part A elements and every Part B standard were compared against Tables 4–7
of the 2020 Delphi paper (Europe PMC full text, PMC7712525). **The counts were right and the
standards were not**: this file previously carried invented standards for *Missing data*, *Sample
size* ("minimum 30 recommended, 50+ preferred") and *Reporting* — the words "missing" and "sample
size" appear nowhere in the source, and the 2018 paper states that standards concerning reporting
only were deleted. Official design standard 6 and statistical standards 8 and 9 were absent. The
SOURCE line also cited Prinsen 2018, which does not contain these standards.

## Purpose

The COSMIN Risk of Bias tool assesses the methodological quality of studies on **reliability** and **measurement error** of outcome measurement instruments (e.g., questionnaires, imaging measurements, lab tests).

## Structure

Two parts:
- **Part A**: Understanding how the study informs on reliability/measurement error (7 elements of a comprehensive research question)
- **Part B**: Assessing quality using standards (9 for reliability, 8 for measurement error)

Quality rating per standard: Very good / Adequate / Doubtful / Inadequate. Each standard also
carries **NA**.

Overall quality uses the **worst score counts** principle — the lowest rating of any standard in
the box (Mokkink 2018). There is no averaging and no summary score.

Note what is **not** here: this tool has no sample-size standard, no missing-data standard and no
reporting standard. Standards that concerned reporting only were deliberately removed when the
COSMIN checklist became a risk-of-bias checklist.

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

Element 5 of the research question asks which **components** are repeated. The Delphi panel agreed
on five, in two variants.

### Without biological sampling
1. **Equipment** — all equipment used in preparation, administration, and assigning scores
2. **Preparatory actions** — 'first time only' general actions (required expertise or training) and actions repeated for each measurement
3. **Unprocessed data collection** — what the patient and/or professional(s) actually do to obtain the unprocessed data
4. **Data processing and storage** — all actions on the unprocessed data that allow a score to be assigned
5. **Assignment of the score** — methods used to transform processed data into a final score

### With biological sampling
1. **Equipment** — all equipment used in preparation, administration, and determination of values
2. **Preparatory actions preceding sample collection** — by professionals, patients, and others as applicable
3. **Collection of the biological sample** — all actions to collect the sample, before any processing
4. **Biological sample processing and storage** — preserving, transporting and storing the sample for determination
5. **Determination of the value of the sample** — methods used to count or quantify the substance or entity of interest

## Part B: Standards for Studies on Reliability

Design requirements (standards 1–6) are the same for reliability and measurement error; only the
statistical standards differ.

### Design requirements (standards 1–6)

| # | Standard |
|---|----------|
| 1 | Were patients stable in the time between the repeated measurements on the construct to be measured? |
| 2 | Was the time interval between the repeated measurements appropriate? |
| 3 | Were the measurement conditions similar for the repeated measurements — except for the condition being evaluated as a source of variation? |
| 4 | Did the professional(s) administer the measurement without knowledge of scores or values of other repeated measurement(s) in the same patients? |
| 5 | Did the professional(s) assign the scores or determine the values without knowledge of the scores or values of other repeated measurement(s) in the same patients? |
| 6 | Were there any other important flaws in the design or statistical methods of the study? |

Standard 6 is rated in the opposite direction: **No** = very good, minor methodological flaws =
doubtful, **Yes** = inadequate.

### Preferred statistical methods — reliability (standards 7–9)

| # | Standard | Very good |
|---|----------|-----------|
| 7 | For continuous scores: was an Intraclass Correlation Coefficient (ICC) calculated? | ICC calculated; the model or formula was described and matches the study design and the data |
| 8 | For ordinal scores: was a (weighted) Kappa calculated? | Kappa calculated; the weighting scheme was described and matches the study design and the data |
| 9 | For dichotomous/nominal scores: was Kappa calculated for each category against the other categories combined? | Kappa calculated for each category against the other categories combined |

For standard 7, a Pearson or Spearman correlation **without** evidence that no systematic
difference occurred between measurements rates *doubtful*; an ICC whose model or formula is not
described rates *adequate*.

## Part B: Standards for Studies on Measurement Error

### Design requirements (standards 1–6)

Identical to the reliability design requirements above.

### Preferred statistical methods — measurement error / agreement (standards 7–8)

| # | Standard | Very good |
|---|----------|-----------|
| 7 | For continuous scores: was the Standard Error of Measurement (SEM), Smallest Detectable Change (SDC), Limits of Agreement (LoA) or Coefficient of Variation (CV) calculated? | SEM, SDC, LoA or CV calculated; the model or formula for the SEM/SDC is described and matches the study design and the data |
| 8 | For dichotomous/nominal/ordinal scores: was the percentage specific (e.g. positive and negative) agreement calculated? | Percentage *specific* agreement calculated (percentage agreement alone rates only adequate) |

A SEM calculated from Cronbach's alpha, or using the SD from another population, rates
*inadequate*.

Total: **9 standards for reliability** (6 design + 3 statistical) and **8 for measurement error**
(6 design + 2 statistical).

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
