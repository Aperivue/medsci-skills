# TRIPOD+AI Checklist

**Transparent Reporting of a multivariable prediction model for Individual Prognosis Or Diagnosis -- AI Extension**
Version: TRIPOD+AI 2024
Source: https://www.tripod-statement.org

## Checklist Items

Items marked with **(AI)** are specific to the AI extension. All other items are from TRIPOD 2015.

### Title and Abstract

| # | Item | Description |
|---|------|-------------|
| 1 | Title | Identify the study as developing and/or validating a multivariable prediction model, the target population, and the outcome to be predicted. |
| 1-AI | Title (AI) | Identify that the prediction model uses AI/ML methods. |
| 2 | Abstract | Provide a summary of objectives, study design, setting, participants, sample size, predictors, outcome, statistical analysis, results, and conclusions. |

### Introduction

| # | Item | Description |
|---|------|-------------|
| 3a | Background | Explain the medical context (including whether diagnostic or prognostic) and rationale for developing or validating the multivariable prediction model, including references to existing models. |
| 3b | Objectives | Specify the objectives, including whether the study describes the development or validation of the model or both. |

### Methods

#### Source of Data

| # | Item | Description |
|---|------|-------------|
| 4a | Source of data | Describe the study design or source of data (e.g., randomized trial, cohort, or registry data), separately for the development and validation data sets, if applicable. |
| 4b | Source of data | Specify the key study dates, including start of accrual; end of accrual; and, if applicable, end of follow-up. |
| 4-AI | Source of data (AI) | Describe the source of all input data types (e.g., imaging modality, laboratory system, free text, structured data). |

#### Participants

| # | Item | Description |
|---|------|-------------|
| 5a | Participants | Specify key elements of the study setting (e.g., primary care, secondary care, general population) including number and location of centres. |
| 5b | Participants | Describe eligibility criteria for participants. |
| 5c | Participants | Give details of treatments received, if relevant. |

#### Outcome

| # | Item | Description |
|---|------|-------------|
| 6a | Outcome | Clearly define the outcome that is predicted by the prediction model, including how and when assessed. |
| 6b | Outcome | Report any actions to blind assessment of the outcome to be predicted. |

#### Predictors

| # | Item | Description |
|---|------|-------------|
| 7a | Predictors | Clearly define all predictors used in developing or validating the multivariable prediction model, including how and when they were measured. |
| 7b | Predictors | Report any actions to blind assessment of predictors for the outcome and other predictors. |
| 7-AI | Predictors (AI) | Describe data preprocessing steps: normalization, augmentation, feature extraction, handling of missing inputs, and any dimensionality reduction. |

#### Sample Size

| # | Item | Description |
|---|------|-------------|
| 8 | Sample size | Explain how the study size was arrived at. |
| 8-AI | Sample size (AI) | Report the effective sample size relative to model complexity (e.g., events per variable, events per parameter). |

#### Missing Data

| # | Item | Description |
|---|------|-------------|
| 9 | Missing data | Describe how missing data were handled (e.g., complete-case analysis, single imputation, multiple imputation) with details of any imputation method. |

#### Statistical Analysis Methods

| # | Item | Description |
|---|------|-------------|
| 10a | Model development | Describe how predictors were handled in the analyses. |
| 10b | Model development | Specify type of model, all model-building procedures (including any predictor selection), and method for internal validation. |
| 10c | Validation | For validation, describe how the predictions were calculated. |
| 10d | Model performance | Specify all measures used to assess model performance and, if relevant, to compare multiple models. |
| 10e | Model updating | Describe any model updating (e.g., recalibration) arising from the validation, if done. |
| 10-AI-a | Model architecture (AI) | Describe the model architecture in sufficient detail for replication (e.g., network type, number of layers, activation functions, loss function). |
| 10-AI-b | Training procedure (AI) | Describe the training procedure: optimizer, learning rate (schedule), batch size, number of epochs, early stopping criteria, regularization methods. |
| 10-AI-c | Software and hardware (AI) | Report software libraries (with version numbers), programming language, and hardware used (especially GPU type for deep learning). |
| 10-AI-d | Reproducibility (AI) | Report measures taken to ensure reproducibility (random seeds, data splits, code availability). |

#### Risk Groups

| # | Item | Description |
|---|------|-------------|
| 11 | Risk groups | Provide details on how risk groups were created, if done. |

### Results

| # | Item | Description |
|---|------|-------------|
| 13a | Participants | Describe the flow of participants through the study, including the number of participants with and without the outcome and, if applicable, a summary of the follow-up time. A diagram may be helpful. |
| 13b | Participants | Describe the characteristics of the participants (basic demographics, clinical features, available predictors), including the number of participants with missing data for predictors and outcome. |
| 13c | Participants | For validation, show a comparison with the development data of the distribution of important variables (demographics, predictors, and outcome). |
| 14a | Model development | Specify the number of participants and outcome events in each analysis. |
| 14b | Model development | If done, report the unadjusted association between each candidate predictor and outcome. |
| 15a | Model specification | Present the full prediction model to allow predictions for individuals (i.e., all regression coefficients, and model intercept or baseline survival at a given time point). |
| 15b | Model specification | Explain how to use the prediction model. |
| 15-AI | Model specification (AI) | If the full model cannot be presented as coefficients: report model availability (e.g., open-source repository, API, executable), and describe the input/output specification. |
| 16 | Model performance | Report performance measures (with CIs) for the prediction model. Report discrimination (e.g., C-statistic/AUC) and calibration (e.g., calibration plot, Hosmer-Lemeshow, calibration slope and intercept). |
| 16-AI | Fairness assessment (AI) | Report model performance stratified by relevant demographic subgroups (age, sex, ethnicity) if data are available. |

### Discussion

| # | Item | Description |
|---|------|-------------|
| 18 | Limitations | Discuss any limitations of the study (such as nonrepresentative sample, few events per predictor, missing data). |
| 19a | Interpretation | For validation, discuss the results with reference to performance in the development data, and any other validation data. |
| 19b | Interpretation | Give an overall interpretation of the results, considering objectives, limitations, results from similar studies, and other relevant evidence. |
| 19-AI | Interpretation (AI) | Discuss potential sources of bias in the AI model: data bias, label noise, distribution shift between development and deployment settings. |
| 20 | Implications | Discuss the potential clinical use of the model and implications for future research. |

### Other Information

| # | Item | Description |
|---|------|-------------|
| 21 | Supplementary information | Provide information about the availability of supplementary resources, such as study protocol, Web calculator, and data sets. |
| 21-AI | Code and model availability (AI) | State whether the trained model and/or source code are publicly available, and provide the repository URL or access instructions. |
| 22 | Funding | Give the source of funding and the role of the funders for the present study. |

---

## Notes for Assessors

- TRIPOD applies to both development and validation studies. Some items (e.g., 10c, 13c, 19a) are specific to validation studies; mark as N/A for development-only studies.
- The AI extension items are mandatory for any study using machine learning or deep learning methods.
- Item 15a (full model specification) is often not feasible for deep learning models; in that case, item 15-AI (model availability) becomes critical.
- Item 16 must include BOTH discrimination and calibration. A study reporting only AUC without calibration assessment is PARTIAL on this item.
- Item 16-AI (fairness) is increasingly expected but may be marked N/A if the study population lacks demographic diversity data, with a note explaining this limitation.
- For studies that are both diagnostic accuracy and prediction model studies, consider cross-referencing with STARD as well.
