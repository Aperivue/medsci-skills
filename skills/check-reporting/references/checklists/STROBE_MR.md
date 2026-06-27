# STROBE-MR Checklist

**Strengthening the Reporting of Observational Studies in Epidemiology using Mendelian Randomization**
Version: STROBE-MR 2021 (base STROBE 2007 + Mendelian-randomization extension)
Source: Skidmore ME / Davey Smith G, Davies NM, et al. *BMJ* 2021;375:n2233 (the STROBE-MR statement). https://www.strobe-mr.org/ · EQUATOR Network.

Apply when the manuscript is a **Mendelian randomization (MR)** study (germline genetic variants used as instrumental variables for an exposure). STROBE-MR extends the base STROBE items with MR-specific reporting (instruments, the three IV assumptions, pleiotropy-robust sensitivity analyses). For the design-validity review of the same study, pair with the MR1–MR8 domain probes in `peer-review` / `self-review` `references/domain-probes/mendelian_randomization.md`; for the analysis, with `analyze-stats` `analysis_guides/mendelian_randomization.md`.

## Checklist Items (20 items)

### Title and Abstract

| # | Item | Description |
|---|------|-------------|
| 1 | Title and abstract | Indicate Mendelian randomization (MR) as the study's design in the title and/or the abstract if that is a main purpose of the study. |

### Introduction

| # | Item | Description |
|---|------|-------------|
| 2 | Background | Explain the scientific background and rationale for the reported study. What is the exposure? Is a causal effect plausible? Why use MR? |
| 3 | Objectives | State specific objectives clearly, including prespecified causal hypotheses (if any). |

### Methods

| # | Item | Description |
|---|------|-------------|
| 4 | Study design and data sources | Present key elements of the study design early in the article. Consider including a table listing sources of data for all phases of the study. (4a) Describe the study design and the underlying population, if possible. (4b) Give the eligibility criteria, and the sources and methods of selection of participants. (4c) Describe measurement, quality control, and selection of genetic variants. (4d) For each exposure, outcome, and other relevant variables, describe methods of assessment and diagnostic criteria for diseases. (4e) Provide details of ethics committee approval and participant informed consent, if relevant. |
| 5 | Assumptions | Explicitly state the three core instrumental-variable assumptions (relevance, independence/exchangeability, exclusion restriction) and the conditions under which MR estimates a causal effect. |
| 6 | Statistical methods: main analysis | Describe statistical methods and statistics used. (6a) Describe how quantitative variables were handled in the analyses (e.g., scale, units, transformation). (6b) Describe how genetic variants were handled in the analyses and, if applicable, how their weights were selected. (6c) Describe the MR estimator(s) (e.g., inverse-variance weighted) and their assumptions. (6d) Explain how missing data were addressed. (6e) If applicable, indicate how multiple testing / multiplicity was addressed. |
| 7 | Statistical methods: assessment of assumptions | Describe any methods or prior knowledge used to assess the assumptions or justify their validity. |
| 8 | Statistical methods: sensitivity analyses and additional analyses | Describe any sensitivity analyses or additional analyses performed (e.g., comparison of results from different MR analysis methods, MR-Egger, weighted median/mode, MR-PRESSO, assessment of instrument-outcome and instrument-exposure population overlap, the use of negative controls). |

### Results

| # | Item | Description |
|---|------|-------------|
| 9 | Descriptive data | (9a) Report the numbers of individuals at each stage of the study and reasons for exclusion. Report summary statistics for the genetic variants, the exposure, and the outcome. (9b) If the data sources include meta-analyses of previous studies, provide assessments of heterogeneity across these studies. (9c) Report on data sources, the participants, and whether the exposure and outcome data come from the same or different (non-overlapping) samples. |
| 10 | Main results | (10a) Report the associations between genetic variant and exposure, and between genetic variant and outcome, preferably on an interpretable scale. (10b) Report MR estimates of the association between exposure and outcome, and the measures of uncertainty, on an interpretable scale (e.g., odds ratio or relative risk per standard-deviation difference). (10c) If relevant, consider translating estimates of relative risk into absolute risk for a meaningful time period. (10d) Consider plots to visualize results (e.g., forest plot, scatter plot of variant-outcome vs variant-exposure associations). |
| 11 | Assessment of assumptions | (11a) Report the assessment of the validity of the assumptions. (11b) Report any additional statistics (e.g., assessments of heterogeneity across instruments, such as I² or Cochran's Q). |
| 12 | Sensitivity analyses and additional analyses | (12a) Report any sensitivity analyses to assess the robustness of the main results to violations of the assumptions. (12b) Report any assessment of direction of causal effect (e.g., bidirectional MR, Steiger filtering). (12c) Report any additional analyses (e.g., analyses of subgroups; multivariable MR). (12d) When relevant, report and compare with estimates from non-MR analyses. (12e) Provide indications of any other potential sources of bias (e.g., selection bias, sample overlap, winner's curse). |

### Discussion

| # | Item | Description |
|---|------|-------------|
| 13 | Key results | Summarise key results with reference to study objectives. |
| 14 | Limitations | Discuss limitations of the study, taking into account the validity of the IV assumptions, other sources of potential bias, and imprecision. Discuss both direction and magnitude of any potential bias. |
| 15 | Interpretation | (15a) Give a cautious overall interpretation of results in the context of their limitations and in comparison with other studies. (15b) Discuss underlying biological mechanisms that could drive a potential causal effect, and whether the gene-environment equivalence assumption is reasonable. (15c) Discuss whether the results have clinical or public-policy relevance, and to what extent they inform effect sizes of possible interventions. |
| 16 | Generalizability | Discuss the generalizability (external validity) of the study results, including the relevance of the population(s) and ancestry to which the findings apply. |

### Other Information

| # | Item | Description |
|---|------|-------------|
| 17 | Funding | Describe sources of funding and the role of funders in the present study and, if applicable, for the databases and original study or studies on which the present study is based. |
| 18 | Data and data sharing | Provide the data used to perform all analyses, or report where and how the data can be accessed, and reference these sources in the article. Provide the statistical code needed to reproduce the results in the article, or report where and how it can be accessed. |
| 19 | Conflicts of interest | All authors should declare all potential conflicts of interest. |
| 20 | Other | Where applicable, report other study registration, protocol availability, or supplementary reporting (e.g., a completed STROBE-MR checklist). |

---

## Notes for Assessors

- STROBE-MR is an **extension of STROBE**; for the non-MR-specific items the base `STROBE.md` guidance also applies. Report both the base instrument and the extension when describing methods (do not cite STROBE-MR as if it replaced STROBE).
- The highest-yield MR-specific items are **5** (the three IV assumptions stated explicitly), **8 / 12** (pleiotropy-robust sensitivity suite — not the IVW estimate alone), **9c / 12e** (sample overlap, winner's curse), and **16** (ancestry generalizability). A study that reports only an IVW estimate with no assumption assessment and no sensitivity analyses is non-compliant on items 5/8/11/12.
- Item numbering follows the STROBE-MR statement's grouping by STROBE section; some sources present the same content as a 20-item list with lettered sub-items. Map the manuscript's content to the items rather than to exact numbering.
- This checklist was authored as a faithful summary of the STROBE-MR statement (Davey Smith G, et al. *BMJ* 2021;375:n2233, CC BY) for item-by-item assessment; verify against the published statement and its explanation-and-elaboration document for full item wording. Verified 2026-06-27.
