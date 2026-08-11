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
> **Verification.** The seven domains, their order, their pre-/at-/post-intervention grouping and
> the five judgement levels with their across-domain criteria were compared against Tables 1 and 2
> of the article (Europe PMC full text, PMC5062054). All matched. The **No information** overall
> judgement, which the file omitted, has been added.
>
> **A version 2 exists and is still in draft.** ROBINS-I V2 adds algorithms mapping signalling-question
> answers onto domain judgements, and covers bias due to immortal time, which the 2016 version omits.
> A revised draft was posted in November 2025 and is subject to change. Check riskofbias.info before
> choosing which version to appraise against; this file documents the 2016 version.
Reference: Sterne JAC et al. BMJ 2016;355:i4919.

## Structure

ROBINS-I assesses 7 domains + overall judgment. The article groups them by when the bias arises:
**pre-intervention** (domains 1–2, where assessment is mainly distinct from randomised trials),
**at intervention** (domain 3, also mainly distinct), and **post-intervention** (domains 4–7,
which overlap substantially with assessments of randomised trials).
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

## Domain 2: Bias in Selection of Participants into the Study

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

## Domain 7: Bias in Selection of the Reported Result

### Key Questions
- Were multiple outcome measurements reported?
- Were multiple analyses performed?
- Is the reported result likely selected from among multiple measurements or analyses?

## Overall Risk of Bias

The overall judgment follows the criteria in the article's Table 2:
- **Low**: the study is judged at low risk of bias for all domains — comparable to a well performed randomised trial
- **Moderate**: low or moderate for all domains — sound evidence for a non-randomised study, but not comparable to a well performed randomised trial
- **Serious**: serious in at least one domain, but not critical in any
- **Critical**: critical in at least one domain — too problematic to provide useful evidence, and should not be included in any synthesis
- **No information**: no clear indication that the study is at serious or critical risk of bias, and information is lacking in one or more key domains

## Recommendation for Synthesis

- Studies at **critical** risk of bias should be excluded from meta-analysis
- Present critical studies in a separate table for completeness
- Conduct sensitivity analysis excluding serious risk of bias studies
