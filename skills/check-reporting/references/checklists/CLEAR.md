# CLEAR Checklist

**CheckList for EvaluAtion of Radiomics research**

- **Version:** CLEAR 2023
- **Citation:** Kocak B, Baessler B, Bakas S, et al. *CheckList for EvaluAtion of Radiomics research (CLEAR): a step-by-step reporting guideline for authors and reviewers endorsed by ESR and EuSoMII.* Insights Imaging. 2023;14(1):75.
- **DOI:** 10.1186/s13244-023-01415-8
- **Source:** https://pmc.ncbi.nlm.nih.gov/articles/PMC10160267/ · official item list: https://clearchecklist.github.io/clear_checklist/CLEAR.html
- **Licence:** CC BY 4.0. Item wording below is reproduced faithfully from the published statement with attribution.

CLEAR is a **58-item** step-by-step reporting guideline for radiomics research, ordered by **manuscript
section** to follow a paper from title to open science: Title (1), Abstract (2), Keywords (3),
Introduction (4–6), Methods (7–43), Results (44–48), Discussion (49–52), and Open Science (53–58). The
Methods block is subdivided into Study design (7–12), Data (13–18), Segmentation (19–20), Pre-processing
(21–24), Feature extraction (25–28), Data preparation (29–33), Modeling (34–37), and Evaluation (38–43).

Two items — **53** and **58** — are marked **[n/e]** ("not essential" but recommended). All other items are
essential; score a missing essential item as a reporting gap, and a missing [n/e] item as N/A only when
justified. CLEAR is written for **hand-crafted radiomics**; for deep-learning pipelines without radiomic
features, CLAIM 2024 or TRIPOD+AI may fit better (a study that does both should be assessed against both).

## Checklist Items

### Title

| Item | Checklist item |
|---|---|
| 1 | Relevant title, specifying the radiomic methodology (generally identifying the study as radiomics-related). |

### Abstract

| Item | Checklist item |
|---|---|
| 2 | Structured summary with relevant information (with a structured or unstructured summary presenting key information). |

### Keywords

| Item | Checklist item |
|---|---|
| 3 | Relevant keywords for radiomics (providing keywords most relevant to the topic). |

### Introduction

| Item | Checklist item |
|---|---|
| 4 | Scientific or clinical background (mentioning the current scientific or clinical background). |
| 5 | Rationale for using a radiomic approach (explaining the rationale for using a radiomic approach). |
| 6 | Study objective(s) (stating the study objectives, hypotheses, or aims). |

### Methods — Study design

| Item | Checklist item |
|---|---|
| 7 | Adherence to guidelines or checklists (e.g., CLEAR checklist). |
| 8 | Ethical details (e.g., approval, consent, data protection). |
| 9 | Sample size calculation (with a statistical power analysis, if performed). |
| 10 | Study nature (e.g., retrospective, prospective). |
| 11 | Eligibility criteria (with inclusion and exclusion criteria). |
| 12 | Flowchart for technical pipeline (presenting a technical pipeline flowchart). |

### Methods — Data

| Item | Checklist item |
|---|---|
| 13 | Data source (e.g., private, public). |
| 14 | Data overlap (declaring any data overlap with previous studies). |
| 15 | Data split methodology (describing how the data were split, e.g., training/validation/test). |
| 16 | Imaging protocol (i.e., image acquisition and processing). |
| 17 | Definition of non-radiomic predictor variables. |
| 18 | Definition of the reference standard (i.e., outcome variable). |

### Methods — Segmentation

| Item | Checklist item |
|---|---|
| 19 | Segmentation strategy (2D/3D, manual/automatic, software, region of interest). |
| 20 | Details of operators performing segmentation (number, experience, qualifications). |

### Methods — Pre-processing

| Item | Checklist item |
|---|---|
| 21 | Image pre-processing details. |
| 22 | Resampling method and its parameters. |
| 23 | Discretization method and its parameters (e.g., fixed bin width or count). |
| 24 | Image types (e.g., original, filtered, transformed). |

### Methods — Feature extraction

| Item | Checklist item |
|---|---|
| 25 | Feature extraction method (software and version). |
| 26 | Feature classes (e.g., shape, first-order, texture). |
| 27 | Number of features (extracted per region and in total). |
| 28 | Default configuration statement for remaining parameters. |

### Methods — Data preparation

| Item | Checklist item |
|---|---|
| 29 | Handling of missing data. |
| 30 | Details of class imbalance. |
| 31 | Details of segmentation reliability analysis (e.g., inter-/intra-observer agreement). |
| 32 | Feature scaling details (e.g., normalization, standardization). |
| 33 | Dimension reduction details (e.g., feature selection). |

### Methods — Modeling

| Item | Checklist item |
|---|---|
| 34 | Algorithm details (name and characteristics of the modeling algorithm[s]). |
| 35 | Training and tuning details (including hyperparameter optimization). |
| 36 | Handling of confounders. |
| 37 | Model selection strategy. |

### Methods — Evaluation

| Item | Checklist item |
|---|---|
| 38 | Testing technique (e.g., internal, external). |
| 39 | Performance metrics and rationale for choosing. |
| 40 | Uncertainty evaluation and measures (e.g., confidence intervals). |
| 41 | Statistical performance comparison (e.g., DeLong's test). |
| 42 | Comparison with non-radiomic and combined methods. |
| 43 | Interpretability and explainability methods. |

### Results

| Item | Checklist item |
|---|---|
| 44 | Baseline demographic and clinical characteristics (across data partitions). |
| 45 | Flowchart for eligibility criteria (participant flow). |
| 46 | Feature statistics (e.g., reproducibility, feature selection). |
| 47 | Model performance evaluation (with the pre-specified metrics). |
| 48 | Comparison with non-radiomic and combined approaches. |

### Discussion

| Item | Checklist item |
|---|---|
| 49 | Overview of important findings. |
| 50 | Previous works with differences from the current study. |
| 51 | Practical implications. |
| 52 | Strengths and limitations (e.g., bias and generalizability issues). |

### Open Science — Data availability

| Item | Checklist item |
|---|---|
| 53 | Sharing images along with segmentation data **[n/e]**. |
| 54 | Sharing radiomic feature data. |

### Open Science — Code availability

| Item | Checklist item |
|---|---|
| 55 | Sharing pre-processing scripts or settings. |
| 56 | Sharing source code for modeling. |

### Open Science — Model availability

| Item | Checklist item |
|---|---|
| 57 | Sharing final model files. |
| 58 | Sharing a ready-to-use system **[n/e]**. |

---

## Notes for assessors

- **Order is by manuscript section, not by topic.** CLEAR numbers items in the order they appear in a paper
  (Title → Abstract → … → Open Science). When you cite a CLEAR item, cite it by this official number — item 1
  is the title, item 44 is baseline demographics in the Results, item 58 is sharing a ready-to-use system.
- **Items 53 and 58 are the only non-essential ([n/e]) items** — recommended best practice for open science.
  Every other item is essential; a missing essential item is a reporting gap, not an optional extra.
- **Segmentation items (19–20)** may be N/A for studies using fully automated, atlas-based segmentation with
  no reader involvement — note this rather than scoring MISSING.
- **Open Science (53–58)** is where a radiomics study's reproducibility is assessed and is increasingly
  required by journals; missing items here commonly draw reviewer comments.
- CLEAR was endorsed by the European Society of Radiology (ESR) and the European Society of Medical Imaging
  Informatics (EuSoMII). For methodological quality (as opposed to reporting completeness), pair CLEAR with
  METRICS (Kocak et al. 2024).
