# ROBINS-I Assessment Guide

Risk Of Bias In Non-randomised Studies - of Interventions.
Version: ROBINS-I (2016), the original version. Tool home: https://www.riskofbias.info
Source: Sterne JAC, Hernán MA, Reeves BC, Savović J, Berkman ND, Viswanathan M, et al. ROBINS-I: a
tool for assessing risk of bias in non-randomised studies of interventions. *BMJ* 2016;355:i4919
(DOI 10.1136/bmj.i4919).

> **Fidelity and licence.** The source article is **CC BY-NC 3.0** — non-commercial. This repository
> is MIT-licensed and redistributed without restriction, so the tool's wording cannot be carried
> verbatim here. This file is an **in-house summary of the tool's structure**: the seven domains,
> their order, the answer options and the judgement levels, all of which were checked against the
> article. The per-domain questions below are abbreviated and are **not** the tool's signalling
> questions. **Complete the official ROBINS-I form from riskofbias.info for any assessment you
> report.**
>
> **A version 2 exists and is still in draft.** ROBINS-I V2 adds algorithms mapping signalling-question
> answers onto domain judgements, and covers bias due to immortal time, which the 2016 version omits.
> A revised draft was posted in November 2025 and is subject to change. Check riskofbias.info before
> choosing which version to appraise against; this file documents the 2016 version.
Reference: Sterne JAC et al. BMJ 2016;355:i4919.

## Structure

ROBINS-I assesses 7 domains + overall judgment.
- **Signalling questions**: Yes / Probably yes / Probably no / No / No information
- **Domain judgment**: Low / Moderate / Serious / Critical / No information
- **Overall judgment**: Lowest of all domain judgments (most conservative)

## Pre-assessment Requirements

Before applying ROBINS-I, specify:
1. The target trial (what RCT would ideally answer this question?)
2. The effect of interest (assignment to intervention vs starting and adhering)
3. Confounders to be controlled

## Domain 1: Bias Due to Confounding

### Key Questions
- Is there potential for confounding not accounted for?
- Did the authors use appropriate methods to control confounding (matching, regression, propensity score)?

### Judgment
- **Low**: All critical confounders appropriately controlled
- **Moderate**: Minor concerns about residual confounding
- **Serious**: Important confounders not adequately controlled
- **Critical**: Confounding so severe that no useful estimate possible

## Domain 2: Bias in Selection of Participants

### Key Questions
- Was selection into the study related to both intervention and outcome?
- Was start of follow-up and intervention aligned?
- Were adjustments made for different start times?

## Domain 3: Bias in Classification of Interventions

### Key Questions
- Were intervention groups clearly defined?
- Was information used to classify interventions recorded at the start of the intervention?
- Could classification of intervention status have been affected by knowledge of the outcome?

## Domain 4: Bias Due to Deviations from Intended Interventions

### Key Questions
- Were there deviations from intended intervention beyond what would be expected?
- Were these deviations unbalanced between groups and likely to affect outcomes?
- Were important co-interventions balanced across groups?

## Domain 5: Bias Due to Missing Data

### Key Questions
- Were outcome data available for all or nearly all participants?
- Were participants excluded due to missing data on intervention or other variables?
- Was the proportion of missing data similar across groups?
- Were appropriate methods used to handle missing data?

## Domain 6: Bias in Measurement of Outcomes

### Key Questions
- Could outcome measurement have been influenced by knowledge of intervention?
- Were outcome assessors blinded?
- Were outcome measures comparable across groups?

## Domain 7: Bias in Selection of Reported Result

### Key Questions
- Were multiple outcome measurements reported?
- Were multiple analyses performed?
- Is the reported result likely selected from among multiple measurements or analyses?

## Overall Risk of Bias

The overall judgment is the most conservative across all domains:
- **Low**: Low risk in all domains
- **Moderate**: Low or moderate in all domains
- **Serious**: Serious in at least one domain, but not critical in any
- **Critical**: Critical in at least one domain

## Recommendation for Synthesis

- Studies at **critical** risk of bias should be excluded from meta-analysis
- Present critical studies in a separate table for completeness
- Conduct sensitivity analysis excluding serious risk of bias studies
