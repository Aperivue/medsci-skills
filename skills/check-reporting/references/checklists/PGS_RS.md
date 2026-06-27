# PGS-RS (PRS-RS) Checklist

**Polygenic Score / Polygenic Risk Score Reporting Standards**
Version: PGS-RS 2021 (also cited as PRS-RS)
Source: Wand H, Lambert SA, Tamburro C, et al. *Improving reporting standards for polygenic scores in risk prediction studies.* Nature 2021;591:211–219. Endorsed by the Clinical Genome Resource (ClinGen) Complex Disease Working Group and the Polygenic Score (PGS) Catalog.

Apply when the manuscript develops, validates, or applies a **polygenic risk score / polygenic score (PRS / PGS)** as a predictor or risk-stratifier. For the design-validity review of the same study, pair with the PG1–PG8 domain probes in `peer-review` / `self-review` `references/domain-probes/polygenic_risk_score.md`; for the analysis, with `analyze-stats` `analysis_guides/polygenic_risk_score.md`. PGS-RS is a domain extension of the TRIPOD prediction-model reporting principles — for the general prediction-model items also consult `TRIPOD.md` / `TRIPOD_AI.md`.

## Checklist Items (22 items)

### Background

| # | Item | Description |
|---|------|-------------|
| 1 | Study type | Specify the development and/or validation status of the polygenic score and provide identifiers (e.g., a PGS Catalog ID) where available. |
| 2 | Risk model purpose and predicted outcome | Define the intended use of the risk model and the outcome it predicts. |

### Study Population and Data

| # | Item | Description |
|---|------|-------------|
| 3 | Study design and recruitment | Describe the cohort/study design, eligibility criteria, and recruitment period for the development and the evaluation samples. |
| 4 | Participant demographic and clinical characteristics | Report age, sex, and relevant clinical/phenotypic characteristics of each sample. |
| 5 | Ancestry | Report the ancestral background of the GWAS (base), training/tuning, and evaluation (target) samples using a standardized ancestry framework; do not assume transferability across ancestries. |
| 6 | Genetic data | Describe genotyping/sequencing methods, imputation, and quality control. |
| 7 | Non-genetic variables | Define any non-genetic variables included in the (integrated) risk model. |
| 8 | Outcome of interest | Define and report how the predicted outcome(s) were ascertained. |
| 9 | Missing data | Explain how missing data (genetic and non-genetic) were handled. |

### Risk Model Development and Application

| # | Item | Description |
|---|------|-------------|
| 10 | Polygenic risk score construction and estimation | Detail the source GWAS, variant selection, weighting/shrinkage method (e.g., P+T, LDpred, PRS-CS), reference panel, and any tuning of hyperparameters (and the data on which tuning was performed). |
| 11 | Risk model type | Describe the statistical method(s) used to estimate risk from the score. |
| 12 | Integrated risk model(s) description and fitting | If the PGS is combined with non-genetic predictors (e.g., a clinical risk model), describe the integrated-model development and fitting procedure. |

### Risk Model Evaluation

| # | Item | Description |
|---|------|-------------|
| 13 | PRS distribution | Describe the distribution of the continuous polygenic score (and any standardization or quantile categorization, with the reference group). |
| 14 | Risk model predictive ability | Report variance explained (e.g., R², liability-scale) and effect estimates (e.g., OR/HR per SD, per quantile) with measures of uncertainty. |
| 15 | Risk model discrimination | Report discrimination (AUROC/C-index; AUPRC where prevalence is low), with confidence intervals — and, for an incremental claim, the change versus the established clinical model (ΔC-statistic, NRI/IDI). |
| 16 | Risk model calibration | Describe how calibration of absolute risk was assessed (calibration plot, slope/intercept, observed vs expected), especially in the target population and across ancestries. |
| 17 | Subgroup analyses | Report performance for relevant subgroups (e.g., ancestry, sex, age) rather than aggregate metrics alone. |

### Limitations and Clinical Implications

| # | Item | Description |
|---|------|-------------|
| 18 | Risk model interpretation | Summarize predictive performance and the incremental value over existing risk factors / clinical models; do not equate a quantile relative-risk gradient with demonstrated clinical actionability. |
| 19 | Limitations | Outline study restrictions and their impact on interpretation. |
| 20 | Generalizability | Discuss applicability to target populations, including ancestries and settings not represented in development/evaluation. |
| 21 | Risk model intended uses | Discuss clinical utility and deployment readiness, scaled to the evidence (calibration, incremental value, and ideally decision-analytic or trial evidence). |
| 22 | Data transparency and availability | Make the PRS parameters (variants and weights) and evaluation results publicly available (e.g., deposit in the PGS Catalog) so the score is reproducible. |

---

## Notes for Assessors

- The highest-yield items are **5 / 17 / 20** (ancestry reporting and per-ancestry/subgroup performance — the central PGS transferability problem), **15** (incremental value over the clinical model, not score-alone discrimination), **16** (absolute-risk calibration, not discrimination alone), and **22** (reproducibility via deposited variants+weights / a PGS Catalog ID).
- PGS-RS is a domain extension of general prediction-model reporting; for items on model development/validation also apply `TRIPOD.md` / `TRIPOD_AI.md`, and cite both the base instrument and PGS-RS rather than PGS-RS alone.
- The guideline is abbreviated both **PGS-RS** and **PRS-RS** in the literature; they refer to the same Wand et al. 2021 standard.
- This checklist was authored as a faithful summary of the PGS-RS standard (Wand H, et al. Nature 2021;591:211–219; checklist as reproduced by the PGS Catalog) for item-by-item assessment; verify against the published Table 1 for full item wording. Verified 2026-06-27.
