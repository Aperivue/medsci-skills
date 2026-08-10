# PROBAST+AI Assessment Guide

Prediction model Risk Of Bias ASsessment Tool — updated for AI/ML methods.
Reference: Moons KGM et al. PROBAST+AI: an updated quality, risk of bias, and applicability assessment tool for prediction models using regression or artificial intelligence methods. BMJ 2025;388:e082505. doi: 10.1136/bmj-2024-082505.
Website: https://www.probast.org

Version: PROBAST+AI (2025) — 16 development / 18 evaluation signalling questions
Licence: CC BY-NC 4.0 (non-commercial) — confirmed via Crossref (DOI 10.1136/bmj-2024-082505). Not redistributable verbatim under this repository's MIT licence.
Verification: the development and evaluation signalling-question counts and the four-step process were checked against the statement and its supplements during this audit.

## Purpose

PROBAST+AI is the updated version of PROBAST (2019) that extends the original tool to cover prediction models developed using **machine learning and artificial intelligence** methods, in addition to traditional regression-based models. It replaces PROBAST-2019 for all new assessments.

## What Changed from PROBAST-2019

- Updated signalling questions to address AI/ML-specific methodological considerations
- Expanded from 20 to **16 targeted signalling questions** for model development and **18 for model evaluation**
- Covers all prediction model types: regression, ML, DL, ensemble methods
- Applicable regardless of whether the model uses statistical or AI/ML techniques
- Original PROBAST Explanation and Elaboration document still provides useful background

## Structure

PROBAST+AI has two distinct parts:
1. **Model development** assessment: quality and applicability
2. **Model evaluation** assessment: risk of bias and applicability

Both parts assess 4 domains:
- Domain 1: Participants
- Domain 2: Predictors
- Domain 3: Outcome
- Domain 4: Analysis

Signalling questions answered: Yes / Probably Yes / No / Probably No / No Information

## Four Steps of Assessment

1. Specify the intended purpose of the prediction model assessment or systematic review
2. Classify the type of prediction model study (development or evaluation or both)
3. Assess quality/applicability (development) or risk of bias/applicability (evaluation) for each domain
4. Assess overall quality (development) or risk of bias (evaluation)

## Domain 1: Participants

### For Model Development (Quality)
- Were participants representative of the target population?
- Was the study setting appropriate?
- Were inclusion/exclusion criteria clearly defined?

### For Model Evaluation (Risk of Bias)
- Were participants selected appropriately for the evaluation?
- Were participants representative of the intended target population?

### Applicability
- Do the participants match the intended target population for the model?

## Domain 2: Predictors

### For Model Development (Quality)
- Were predictors defined and assessed in a standardized way?
- Were predictors available at the intended moment of use?
- Were all candidate predictors assessed appropriately?

### For Model Evaluation (Risk of Bias)
- Were predictors assessed in the same way as in the development study?
- Were predictors assessed without knowledge of the outcome?

### Applicability
- Do the predictor definitions and assessments match the intended use?

## Domain 3: Outcome

### For Model Development (Quality)
- Was the outcome clearly defined?
- Was the outcome determined appropriately?
- Was the time horizon appropriate?

### For Model Evaluation (Risk of Bias)
- Was the outcome determined in the same way as in development?
- Was the outcome determined without knowledge of predictor information?

### Applicability
- Does the outcome definition and assessment match the intended target?

## Domain 4: Analysis

### For Model Development (Quality — key AI/ML considerations)
- Was the sample size adequate for the modeling approach?
- Were missing data handled appropriately?
- Was the choice of algorithm/method appropriate?
- Were hyperparameters tuned appropriately (for ML/DL models)?
- Was overfitting addressed (regularization, early stopping, cross-validation)?
- Was model performance assessed using appropriate metrics?
- Was internal validation performed adequately (bootstrapping, cross-validation)?
- Were relevant performance measures reported (discrimination, calibration)?

### For Model Evaluation (Risk of Bias — key AI/ML considerations)
- Was the evaluation dataset independent from the development dataset?
- Were appropriate performance measures used (discrimination AND calibration)?
- Was the statistical analysis appropriate?
- Were model updates or recalibration described if performed?

### Applicability
- Does the analysis approach and validation strategy support the intended clinical use?

## Overall Judgment

### For Model Development: Overall Quality
- **High quality**: Low concern across all domains
- **Unclear quality**: Unclear in at least one domain
- **Low quality**: High concern in at least one domain

### For Model Evaluation: Overall Risk of Bias
- **Low risk**: Low risk in all domains
- **Unclear risk**: Unclear in at least one domain, no high risk in any
- **High risk**: High risk in at least one domain

## Key Differences from Original PROBAST-2019

| Aspect | PROBAST-2019 | PROBAST+AI |
|--------|-------------|------------|
| Scope | Regression models | Regression + AI/ML models |
| Development assessment | Risk of bias | **Quality** (more appropriate term) |
| Evaluation assessment | Risk of bias | Risk of bias (unchanged) |
| AI-specific items | None | Hyperparameter tuning, overfitting mitigation, algorithm choice |
| Signalling questions | 20 per assessment | 16 (development) / 18 (evaluation) |

## When to Use

- Systematic reviews of prediction model studies (development, validation, or both)
- Applies to ALL prediction models regardless of algorithm (logistic regression, random forest, deep learning, etc.)
- Replaces PROBAST-2019 for new assessments
- Use alongside TRIPOD+AI for reporting quality assessment
