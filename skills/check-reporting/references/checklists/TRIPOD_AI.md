# TRIPOD+AI 2024 Checklist

**Transparent Reporting of a multivariable prediction model for Individual Prognosis Or Diagnosis — Artificial Intelligence extension**

- **Version:** TRIPOD+AI 2024
- **Citation:** Collins GS, Moons KGM, Dhiman P, et al. *TRIPOD+AI statement: updated guidance for reporting clinical prediction models that use regression or machine learning methods.* BMJ 2024;385:e078378.
- **DOI:** 10.1136/bmj-2023-078378
- **Source:** https://www.tripod-statement.org — official expanded checklist: https://www.tripod-statement.org/wp-content/uploads/2024/04/TRIPODAI-Supplement.pdf
- **Licence:** CC BY 4.0. Item wording below is reproduced faithfully from the published statement with attribution.

**TRIPOD+AI 2024 supersedes and replaces TRIPOD 2015.** It is not TRIPOD 2015 plus AI addenda — it is a
complete rewrite, applicable to prediction-model studies using **either** regression **or** machine-learning
methods. For any prediction-model study (regression or AI/ML), use this checklist; do **not** apply the 2015
checklist alongside it.

The checklist has **27 main items** and **52 checklist subitems**, in eight sections: Title (1), Abstract (2),
Introduction (3–4), Methods (5–17), Open science (18), Patient and public involvement (19), Results (20–24),
and Discussion (25–27).

**Applicability column:** `D` = relevant only to model **development**; `E` = relevant only to model
**evaluation**; `D;E` = applicable to **both**.

## Checklist Items

### Title

| Item | Topic | D/E | Checklist item |
|---|---|---|---|
| 1 | Title | D;E | Identify the study as developing or evaluating the performance of a multivariable prediction model, the target population, and the outcome to be predicted. |

### Abstract

| Item | Topic | D/E | Checklist item |
|---|---|---|---|
| 2 | Abstract | D;E | See the TRIPOD+AI for Abstracts checklist. |

### Introduction

| Item | Topic | D/E | Checklist item |
|---|---|---|---|
| 3a | Background | D;E | Explain the healthcare context (including whether diagnostic or prognostic) and rationale for developing or evaluating the prediction model, including references to existing models. |
| 3b | Background | D;E | Describe the target population and the intended purpose of the prediction model in the context of the care pathway, including its intended users (e.g., healthcare professionals, patients, public). |
| 3c | Background | D;E | Describe any known health inequalities between sociodemographic groups. |
| 4 | Objectives | D;E | Specify the study objectives, including whether the study describes the development or validation of a prediction model (or both). |

### Methods

| Item | Topic | D/E | Checklist item |
|---|---|---|---|
| 5a | Data | D;E | Describe the sources of data separately for the development and evaluation datasets (e.g., randomised trial, cohort, routine care or registry data), the rationale for using these data, and the representativeness of the data. |
| 5b | Data | D;E | Specify the dates of the collected participant data, including start and end of participant accrual; and, if applicable, end of follow-up. |
| 6a | Participants | D;E | Specify key elements of the study setting (e.g., primary care, secondary care, general population) including the number and location of centres. |
| 6b | Participants | D;E | Describe the eligibility criteria for study participants. |
| 6c | Participants | D;E | Give details of any treatments received, and how they were handled during model development or evaluation, if relevant. |
| 7 | Data preparation | D;E | Describe any data pre-processing and quality checking, including whether this was similar across relevant sociodemographic groups. |
| 8a | Outcome | D;E | Clearly define the outcome that is being predicted and the time horizon, including how and when assessed, the rationale for choosing this outcome, and whether the method of outcome assessment is consistent across sociodemographic groups. |
| 8b | Outcome | D;E | If outcome assessment requires subjective interpretation, describe the qualifications and demographic characteristics of the outcome assessors. |
| 8c | Outcome | D;E | Report any actions to blind assessment of the outcome to be predicted. |
| 9a | Predictors | D | Describe the choice of initial predictors (e.g., literature, previous models, all available predictors) and any pre-selection of predictors before model building. |
| 9b | Predictors | D;E | Clearly define all predictors, including how and when they were measured (and any actions to blind assessment of predictors for the outcome and other predictors). |
| 9c | Predictors | D;E | If predictor measurement requires subjective interpretation, describe the qualifications and demographic characteristics of the predictor assessors. |
| 10 | Sample size | D;E | Explain how the study size was arrived at (separately for development and evaluation), and justify that the study size was sufficient to answer the research question. Include details of any sample size calculation. |
| 11 | Missing data | D;E | Describe how missing data were handled. Provide reasons for omitting any data. |
| 12a | Analytical methods | D | Describe how the data were used (e.g., for development and evaluation of model performance) in the analysis, including whether the data were partitioned, considering any sample size requirements. |
| 12b | Analytical methods | D | Depending on the type of model, describe how predictors were handled in the analyses (functional form, rescaling, transformation, or any standardisation). |
| 12c | Analytical methods | D | Specify the type of model, rationale, all model building steps, including any hyperparameter tuning, and method for internal validation. |
| 12d | Analytical methods | D;E | Describe if and how any heterogeneity in estimates of model parameter values and model performance was handled and quantified across clusters (e.g., hospitals, countries). See TRIPOD-Cluster for additional considerations. |
| 12e | Analytical methods | D;E | Specify all measures and plots used (and their rationale) to evaluate model performance (e.g., discrimination, calibration, clinical utility) and, if relevant, to compare multiple models. |
| 12f | Analytical methods | E | Describe any model updating (e.g., recalibration) arising from the model evaluation, either overall or for particular sociodemographic groups or settings. |
| 12g | Analytical methods | E | For model evaluation, describe how the model predictions were calculated (e.g., formula, code, object, application programming interface). |
| 13 | Class imbalance | D;E | If class imbalance methods were used, state why and how this was done, and any subsequent methods to recalibrate the model or the model predictions. |
| 14 | Fairness | D;E | Describe any approaches that were used to address model fairness and their rationale. |
| 15 | Model output | D | Specify the output of the prediction model (e.g., probabilities, classification). Provide details and rationale for any classification and how the thresholds were identified. |
| 16 | Training versus evaluation | D;E | Identify any differences between the development and evaluation data in healthcare setting, eligibility criteria, outcome, and predictors. |
| 17 | Ethical approval | D;E | Name the institutional research board or ethics committee that approved the study and describe the participant informed consent or the ethics committee waiver of informed consent. |

### Open science

| Item | Topic | D/E | Checklist item |
|---|---|---|---|
| 18a | Funding | D;E | Give the source of funding and the role of the funders for the present study. |
| 18b | Conflicts of interest | D;E | Declare any conflicts of interest and financial disclosures for all authors. |
| 18c | Protocol | D;E | Indicate where the study protocol can be accessed or state that a protocol was not prepared. |
| 18d | Registration | D;E | Provide registration information for the study, including register name and registration number, or state that the study was not registered. |
| 18e | Data sharing | D;E | Provide details of the availability of the study data. |
| 18f | Code sharing | D;E | Provide details of the availability of the analytical code. |

### Patient and public involvement

| Item | Topic | D/E | Checklist item |
|---|---|---|---|
| 19 | Patient and public involvement | D;E | Provide details of any patient and public involvement during the design, conduct, reporting, interpretation, or dissemination of the study or state no involvement. |

### Results

| Item | Topic | D/E | Checklist item |
|---|---|---|---|
| 20a | Participants | D;E | Describe the flow of participants through the study, including the number of participants with and without the outcome and, if applicable, a summary of the follow-up time. A diagram may be helpful. |
| 20b | Participants | D;E | Report the characteristics overall and, where applicable, for each data source or setting, including the key dates, key predictors (including demographics), treatments received, sample size, number of outcome events, follow-up time, and amount of missing data. A table may be helpful. Report any differences across key demographic groups. |
| 20c | Participants | E | For model evaluation, show a comparison with the development data of the distribution of important predictors (demographics, predictors, and outcome). |
| 21 | Model development | D;E | Specify the number of participants and outcome events in each analysis (e.g., for model development, hyperparameter tuning, model evaluation). |
| 22 | Model specification | D | Provide details of the full prediction model (e.g., formula, code, object, application programming interface) to allow predictions in new individuals and to enable third party evaluation and implementation, including any restrictions to access or reuse (e.g., freely available, proprietary). |
| 23a | Model performance | D;E | Report model performance estimates with confidence intervals, including for any key subgroups (e.g., sociodemographic). Consider plots to aid presentation. |
| 23b | Model performance | D;E | If examined, report results of any heterogeneity in model performance across clusters. See TRIPOD-Cluster for additional details. |
| 24 | Model updating | E | Report the results from any model updating, including the updated model and subsequent performance. |

### Discussion

| Item | Topic | D/E | Checklist item |
|---|---|---|---|
| 25 | Interpretation | D;E | Give an overall interpretation of the main results, including issues of fairness in the context of the objectives and previous studies. |
| 26 | Limitations | D;E | Discuss any limitations of the study (such as a non-representative sample, sample size, overfitting, missing data) and their effects on any biases, statistical uncertainty, and generalisability. |
| 27a | Usability of the model in the context of current care | D | Describe how poor quality or unavailable input data (e.g., predictor values) should be assessed and handled when implementing the prediction model. |
| 27b | Usability of the model in the context of current care | D | Specify whether users will be required to interact in the handling of the input data or use of the model, and what level of expertise is required of users. |
| 27c | Usability of the model in the context of current care | D;E | Discuss any next steps for future research, with a specific view to applicability and generalisability of the model. |

---

## MedSci supplemental checks — NOT official TRIPOD+AI items

The following are **not** TRIPOD+AI checklist items. They are engineering-reproducibility prompts this
toolkit adds because they matter for an AI/ML model to be rebuildable, and they extend (do not replace) the
official items noted. Assess them **only as supplements**; never report them as canonical TRIPOD+AI item
numbers, and never let them substitute for an official item.

| Supplemental check | Extends official item | What to look for |
|---|---|---|
| Model architecture | 12c | Network type, depth, layers, activation and loss functions — enough detail to rebuild the model. |
| Training configuration | 12c | Optimizer, learning-rate schedule, batch size, epochs, early-stopping criterion, regularisation. |
| Software and hardware | 18f, 22 | Libraries with version numbers, language, and the compute used (e.g., GPU type for deep learning). |
| Reproducibility | 18e, 18f | Random seeds, the exact data split, and whether code + weights are available to reproduce results. |

Official item **14 (Fairness)**, **18f (Code sharing)**, **22 (Model specification / API)**, and
**7 (Data preparation)** already cover fairness, code/model availability, and preprocessing — assess those
under their official items, not as extras here.

## Notes for assessors

- **Applicability.** Mark items labelled `D` (development-only) or `E` (evaluation-only) as N/A when they do
  not apply to the study design; `D;E` items apply to both.
- **Open science (18a–18f) and PPI (19) are official, mandatory items** — a compliance report that skips them
  is incomplete. Data sharing (18e) and code sharing (18f) are where an AI/ML study's reproducibility is
  assessed.
- **Performance (23a) with confidence intervals is required**, including for key subgroups; heterogeneity
  across clusters (23b) when examined. A study reporting a point estimate without a CI is PARTIAL on 23a.
- **Fairness is an official item (14)** and is reported across demographic groups in 20b and 23a — not an
  optional AI add-on.
- Do **not** apply TRIPOD 2015 alongside this checklist; TRIPOD+AI 2024 supersedes it for both regression and
  AI/ML prediction models.
- For a study that is both a diagnostic-accuracy study and a prediction-model study, cross-reference STARD.
