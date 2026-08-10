# PROBAST Assessment Guide

Prediction model Risk Of Bias ASsessment Tool.
Version: PROBAST 2019 — 20 signalling questions across 4 domains (2 / 3 / 6 / 9).
Source: Wolff RF, Moons KGM, Riley RD, Whiting PF, Westwood M, Collins GS, et al. PROBAST: A Tool to
Assess the Risk of Bias and Applicability of Prediction Model Studies. *Ann Intern Med*
2019;170(1):51-58 (PMID 30596875; DOI 10.7326/M18-1376). Explanation and Elaboration:
*Ann Intern Med* 2019;170(1):W1-W33.

> **Fidelity and licence.** PROBAST is published in *Annals of Internal Medicine* (© American College
> of Physicians) and carries **no open licence**. The signalling questions below are therefore an
> **in-house summary of what each question asks — not the published wording**. The numbering,
> the domain structure and the count (2 / 3 / 6 / 9) are verified against the statement; the phrasing
> is ours. **Complete the official tool from probast.org or the statement for any assessment you
> report.** Use this file to organise a first pass.

> **PROBAST 2019 is superseded.** PROBAST+AI (2025) replaces it for all new assessments, covering
> regression and AI/ML models alike — see `PROBAST_AI.md`. Use this file only when appraising against
> the 2019 instrument specifically (for example, reproducing an earlier review).

## Structure

PROBAST assesses 4 domains, each for Risk of Bias AND Applicability.
- **Signalling questions**: Yes / Probably yes / No / Probably no / No information
- **Domain judgment**: Low / High / Unclear
- **Overall judgment**: High if any domain is high; Low only if all domains are low

## Domain 1: Participants

### Signalling questions (risk of bias) — what each asks

1.1 Whether the data source suits the question — a cohort, a randomised trial, or nested
    case–control data, rather than a design that distorts the sampling.
1.2 Whether every inclusion and exclusion applied to participants was appropriate.

### Applicability
- Do the participants and setting match the review question?

## Domain 2: Predictors

### Signalling questions (risk of bias) — what each asks

2.1 Whether predictors were defined and assessed the same way for every participant.
2.2 Whether predictors were assessed without knowledge of the outcome.
2.3 Whether every predictor is available at the moment the model is meant to be used.

### Applicability
- Do the predictors, their assessment, and timing match the review question?

## Domain 3: Outcome

### Signalling questions (risk of bias) — what each asks

3.1 Whether the outcome was determined by an appropriate method.
3.2 Whether the outcome definition was prespecified or a standard one.
3.3 Whether predictors were kept out of the outcome definition.
3.4 Whether the outcome was defined and determined the same way for every participant.
3.5 Whether the outcome was determined without knowledge of predictor information.
3.6 Whether the interval between predictor assessment and **outcome determination** was
    appropriate — the question is about when the outcome was *determined*, not merely when it
    occurred.

### Applicability
- Does the outcome and its definition/timing match the review question?

## Domain 4: Analysis

### Signalling questions (risk of bias) — what each asks

4.1 Whether the number of participants with the outcome was reasonable.
4.2 Whether continuous and categorical predictors were handled appropriately.
4.3 Whether every enrolled participant was included in the analysis.
4.4 Whether participants with missing data were handled appropriately.
4.5 Whether selection of predictors on the basis of univariable analysis was avoided.
4.6 Whether complexities in the data were accounted for — the statement names **censoring,
    competing risks, and the sampling of control participants** as the cases to look for.
4.7 Whether relevant measures of model performance were evaluated appropriately.
4.8 Whether **overfitting, underfitting, and optimism** in model performance were accounted for.
    All three, not overfitting alone.
4.9 Whether the predictors and their assigned weights in the final model correspond to the
    **results from** the reported multivariable analysis.

### For validation studies (additional)
- Were the model and its performance evaluated appropriately?

## For AI / machine-learning models

Use **`PROBAST_AI.md`** (PROBAST+AI 2025; Moons KGM et al. *BMJ* 2025;388:e082505,
DOI 10.1136/bmj-2024-082505), which carries the instrument's own 16 development and 18 evaluation
signalling questions. Do not improvise AI addenda on top of the 2019 questions: an earlier version of
this file listed four invented bullets under a heading that implied they were part of the extension,
which they were not.

## When to Use

- Diagnostic prediction models (e.g., AI classifiers for imaging findings)
- Prognostic prediction models (e.g., risk scores, survival prediction)
- Both development AND validation studies
- For any model developed with machine learning or deep learning, and for new assessments generally,
  use PROBAST+AI (`PROBAST_AI.md`) rather than this file
