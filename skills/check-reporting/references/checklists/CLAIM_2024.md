# CLAIM 2024 Checklist

**Checklist for Artificial Intelligence in Medical Imaging**
Version: CLAIM 2024 Update
Source: https://pubs.rsna.org/doi/10.1148/ryai.240300
Reference: Tejani AS, Klontzas ME, Gatti AA, Mongan JT, Moy L, Park SH, Kahn CE Jr. Checklist for Artificial Intelligence in Medical Imaging (CLAIM): 2024 Update. Radiol Artif Intell 2024;6(4):e240300.

> Note: The 2024 update replaces "ground truth" with "reference standard" and discourages "validation" in favour of "internal/external testing". Each item is answered Yes / No / Not Applicable with the manuscript location cited.

## Checklist Items (44 items)

### Title and Abstract

| # | Item | Description |
|---|------|-------------|
| 1 | Title | Identify the study as employing AI methodology and name the specific technology category (e.g., deep learning). |
| 2 | Abstract | Structured summary including study design, methods, results, and conclusions; population details, data partitions, prospective/retrospective status, statistical analysis, outcomes, and availability of resources. |

### Introduction

| # | Item | Description |
|---|------|-------------|
| 3 | Background | Scientific and clinical background, current practice, intended use, and clinical role of the AI approach. |
| 4 | Objectives | Study aims, objectives, and hypotheses (if not data-driven). |

### Methods — Study Design

| # | Item | Description |
|---|------|-------------|
| 5 | Study design | Prospective or retrospective study. |
| 6 | Study goal | Goal of the study (e.g., model creation, feasibility, trial type, intended use for the classification task). |

### Methods — Data

| # | Item | Description |
|---|------|-------------|
| 7 | Data sources | State data sources; provide links to publicly available datasets. |
| 8 | Eligibility | Inclusion and exclusion criteria and selection methodology for the data. |
| 9 | Preprocessing | Data preprocessing steps (e.g., normalization, resampling, window/level adjustment). |
| 10 | Subset selection | Selection of data subsets and training of personnel involved. |
| 11 | De-identification | De-identification methods meeting HIPAA/GDPR/AI Act standards. |
| 12 | Missing data | How missing data were handled and potential biases from imputation. |
| 13 | Acquisition protocol | Image acquisition protocol parameters (e.g., manufacturer, sequences, resolution). |

### Methods — Reference Standard

| # | Item | Description |
|---|------|-------------|
| 14 | Reference standard definition | Method for obtaining the reference standard, with precise and replicable definitions. |
| 15 | Reference standard rationale | Rationale for choosing the reference standard versus alternatives. |
| 16 | Annotators | Source, qualifications, and training materials of annotators. |
| 17 | Annotation procedures | Test-set annotation procedures, software version, and any NLP/automated approaches. |
| 18 | Annotation variability | Measurement of inter- and intra-rater variability and method of discrepancy resolution. |

### Methods — Data Partitions

| # | Item | Description |
|---|------|-------------|
| 19 | Partition assignment | Partition assignment (train/tune/test), proportions, justification, and class-imbalance handling. |
| 20 | Partition disjointness | Level of partition disjointness (patient-, series-, or image-level). |

### Methods — Testing Data

| # | Item | Description |
|---|------|-------------|
| 21 | Test set size | Testing-set size derived from a power calculation or AUC-based estimation. |

### Methods — Model

| # | Item | Description |
|---|------|-------------|
| 22 | Model architecture | Complete model architecture (inputs, outputs, layers, pooling, normalization). |
| 23 | Software | Software libraries, frameworks, packages, and version numbers. |
| 24 | Initialization | Parameter initialization; transfer-learning sources, if used. |

### Methods — Training

| # | Item | Description |
|---|------|-------------|
| 25 | Training procedures | Training procedures, data augmentation, convergence monitoring, and all hyperparameters. |
| 26 | Model selection | Method and metrics for selecting the best-performing model. |
| 27 | Ensembling | If an ensemble approach is used, details of each model and how outputs are combined. |

### Methods — Evaluation

| # | Item | Description |
|---|------|-------------|
| 28 | Performance metrics | Performance metrics and comparison to published models. |
| 29 | Uncertainty | Measures of uncertainty (e.g., standard deviation, confidence intervals) and statistical significance tests. |
| 30 | Robustness | Robustness or sensitivity analysis. |
| 31 | Explainability | If applied, explainability/interpretability methods and their validation. |
| 32 | Internal testing | Internal-data evaluation and consistency between training and test performance. |
| 33 | External testing | External-data testing, or justification for its omission. |
| 34 | Trial registration | If applicable, compliance with ICMJE clinical-trial registration requirements. |

### Results — Data

| # | Item | Description |
|---|------|-------------|
| 35 | Inclusion/exclusion numbers | Numbers of patients/examinations included and excluded, with a flowchart. |
| 36 | Demographics | Demographic and clinical characteristics per partition; identify potential sources of bias. |

### Results — Model Performance

| # | Item | Description |
|---|------|-------------|
| 37 | Performance reporting | Final model performance benchmarked against the reference standard across partitions and subgroups. |
| 38 | Accuracy estimates | Diagnostic accuracy estimates with 95% confidence intervals; ROC analysis; address class imbalance. |
| 39 | Failure analysis | Failure analysis with a confusion matrix; examples of incorrect classifications in the medical context. |

### Discussion

| # | Item | Description |
|---|------|-------------|
| 40 | Limitations | Study limitations (methods, materials, biases, generalisability). |
| 41 | Implications | Clinical implications, intended use, practice changes, and barriers to translation. |

### Other Information

| # | Item | Description |
|---|------|-------------|
| 42 | Full protocol | Reference to the full protocol or technical details if exceeding journal word limits. |
| 43 | Availability | Availability of software, model, and data, and access conditions. |
| 44 | Funding | Funding sources and the role of funders. |

---

*Educational summary of the CLAIM 2024 Update checklist (© RSNA, open access). Cite the original (Tejani et al., Radiol Artif Intell 2024;6(4):e240300) and consult the RSNA article for the authoritative, full checklist.*
