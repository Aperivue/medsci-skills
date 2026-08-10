# STROBE-MR Checklist

**Strengthening the Reporting of Observational Studies in Epidemiology using Mendelian Randomization**
Version: STROBE-MR 2021 — **20 items and 30 sub-items** across six sections.
Source (the statement): Skrivankova VW, Richmond RC, Woolf BAR, Yarmolinsky J, Davies NM, Swanson SA,
et al. Strengthening the Reporting of Observational Studies in Epidemiology Using Mendelian
Randomization: The STROBE-MR Statement. *JAMA* 2021;326(16):1614-1621 (DOI 10.1001/jama.2021.18236).
Explanation and Elaboration: Skrivankova VW, et al. *BMJ* 2021;375:n2233. Also: https://www.strobe-mr.org

> **Fidelity and licence.** The statement is published in *JAMA* (© American Medical Association) under
> **no open licence**. The descriptions below state what each item asks **in our own words**; the
> structure — 20 items, which sub-items exist and under which item, the section grouping — is
> **verified against the statement**. **Complete the official checklist for anything you submit**, and
> read the Explanation and Elaboration for the rationale and worked examples.

> **What this file used to be.** It cited "Skidmore ME / Davey Smith G, Davies NM, et al. *BMJ*
> 2021;375:n2233" as the statement — a non-existent first author, and the E&E paper rather than the
> statement. It carried **items 1–20 with none of the 30 sub-items**, which is where every
> MR-specific requirement lives. From item 17 on it was shifted by one (Funding at 17 instead of 18)
> and it **invented an item 20, "Other"**, where the statement has Conflicts of interest. It also
> claimed the statement was CC BY, and carried a "Verified" stamp. None of that survived contact with
> the published table.

**Scope.** Covers 1-sample and 2-sample MR, single or multiple exposures and outcomes, and MR
following a GWAS reported in the same article. Does **not** cover GWAS themselves (use STREGA),
sequencing or expression studies, or ordinary observational epidemiology (use `STROBE.md`). For MR
that does not use instrumental-variable estimation — some gene-by-environment interaction studies —
some items will not apply.

**Relationship to STROBE.** A stand-alone extension: STROBE has 22 items and 18 sub-items, STROBE-MR
has 20 items and 30 sub-items. Every item and sub-item was modified for MR **except sub-item 6d**
(missing data), which is unchanged. Name both instruments in Methods.

**Not a quality instrument.** The statement says explicitly that the checklist is not to be used to
evaluate the quality of MR research.

## Title and Abstract

| # | Item | What to check is reported |
|---|------|---------------------------|
| 1 | Title and abstract | MR is named as the study design in the title and/or abstract, where that is a main purpose of the study. |

## Introduction

| # | Item | What to check is reported |
|---|------|---------------------------|
| 2 | Background | The scientific background and rationale; what the exposure is; whether a causal exposure–outcome relationship is plausible; and **a justification of why MR helps answer this question**. |
| 3 | Objectives | Specific objectives, including **prespecified causal hypotheses** if any, and a statement that MR estimates causal effects only under stated assumptions. |

## Methods

| # | Item | What to check is reported |
|---|------|---------------------------|
| 4 | Study design and data sources | Key design elements early in the article; consider a table of data sources for every phase. Then, **for each data source**: |
| 4a | — Setting | The design and underlying population; setting, locations and relevant dates, including recruitment, exposure, follow-up and data collection. |
| 4b | — Participants | Eligibility criteria, how participants were selected, sample size, and whether any power or sample-size calculation was done **before** the main analysis. |
| 4c | — Genetic variants | **Measurement, quality control and selection of the genetic variants.** |
| 4d | — Variables | Assessment methods and diagnostic criteria for each exposure, outcome and other relevant variable. |
| 4e | — Ethics | Ethics committee approval and participant informed consent, where relevant. |
| 5 | Assumptions | **The three core IV assumptions stated explicitly** — relevance, independence, exclusion restriction — plus the assumptions of any additional or sensitivity analysis. |
| 6 | Statistical methods: main analysis | The statistical methods and statistics used: |
| 6a | — Quantitative variables | How they were handled — scale, units, model. |
| 6b | — Genetic variants | How variants were handled and, if applicable, how their weights were chosen. |
| 6c | — MR estimator | **Which estimator** (two-stage least squares, Wald ratio, …) and its related statistics; the covariates included; and for 2-sample MR whether the same covariate set was used in both samples. |
| 6d | — Missing data | How missing data were addressed. *(The only sub-item unchanged from STROBE.)* |
| 6e | — Multiple testing | How multiple testing was addressed, if applicable. |
| 7 | Assessment of assumptions | The methods or prior knowledge used to **assess** the assumptions or justify their validity. |
| 8 | Sensitivity and additional analyses | Any sensitivity or additional analyses — comparison of estimates from different approaches, independent replication, bias-analytic techniques, instrument validation, simulations. |
| 9 | Software and preregistration | |
| 9a | — Software | Statistical software and packages, **with version and settings**. |
| 9b | — Preregistration | **Whether the protocol and details were preregistered**, and when and where. |

## Results

| # | Item | What to check is reported |
|---|------|---------------------------|
| 10 | Descriptive data | |
| 10a | — Flow | Numbers of individuals at each stage of the included studies and reasons for exclusion; consider a flow diagram. |
| 10b | — Summary statistics | For phenotypic exposures, outcomes and other relevant variables — means, SDs, proportions. |
| 10c | — Heterogeneity | Where data sources include meta-analyses of previous studies, the assessments of heterogeneity across them. |
| 10d | — 2-sample MR | (i) **Justification that the variant–exposure associations are similar** between the exposure and outcome samples; (ii) **the number of individuals overlapping** between the two studies. |
| 11 | Main results | |
| 11a | — Associations | The variant–exposure and variant–outcome associations, preferably on an interpretable scale. |
| 11b | — MR estimates | The MR estimate of the exposure–outcome relationship with its uncertainty, on an interpretable scale such as an odds ratio or relative risk per SD. |
| 11c | — Absolute risk | Where relevant, relative risk translated into absolute risk over a meaningful period. |
| 11d | — Plots | Consider plots — forest plot, or variant–outcome against variant–exposure associations. |
| 12 | Assessment of assumptions | |
| 12a | — Validity | The assessment of the validity of the assumptions. |
| 12b | — Statistics | Additional statistics — heterogeneity across variants (I², Q) or an E-value. |
| 13 | Sensitivity and additional analyses | |
| 13a | — Robustness | Sensitivity analyses testing robustness to violations of the assumptions. |
| 13b | — Other | Results of other sensitivity or additional analyses. |
| 13c | — Direction | **Any assessment of the direction of the causal relationship**, e.g. bidirectional MR. |
| 13d | — Non-MR comparison | Where relevant, comparison with estimates from non-MR analyses. |
| 13e | — Plots | Consider additional plots, e.g. leave-one-out analyses. |

## Discussion

| # | Item | What to check is reported |
|---|------|---------------------------|
| 14 | Key results | The key results summarised against the study objectives. |
| 15 | Limitations | Limitations, taking in the validity of the IV assumptions, other sources of bias, and imprecision — with **the direction and magnitude** of any potential bias and what was done about it. |
| 16 | Interpretation | |
| 16a | — Meaning | A cautious overall interpretation in the light of the limitations and of other studies. |
| 16b | — Mechanism | The biological mechanisms that could drive the relationship, and **whether the gene-environment equivalence assumption is reasonable**; causal language used carefully, making clear that IV estimates are causal only under certain assumptions. |
| 16c | — Clinical relevance | Whether the results have clinical or public-policy relevance, and what they imply about the size of possible interventions. |
| 17 | Generalizability | Generalisability of the results **(a) to other populations, (b) across other exposure periods or timings, and (c) across other levels of exposure**. |

## Other Information

| # | Item | What to check is reported |
|---|------|---------------------------|
| 18 | Funding | Sources of funding and the role of funders for this study and, where applicable, for the databases and original studies it rests on. |
| 19 | Data and data sharing | The data used, or where and how it can be accessed, referenced in the article; and **the statistical code needed to reproduce the results**, or where it is publicly accessible. |
| 20 | Conflicts of interest | Declared by **all** authors. |

## Notes for Assessors

- **The sub-items are the extension.** Items 1–20 alone are close to a re-lettered STROBE. What makes
  a report an MR report is 4c (variant measurement, QC and selection), 6c (the estimator), 9b
  (preregistration), 10d (2-sample similarity and **participant overlap**), 12a/12b (assumption
  validity, heterogeneity across variants), 13c (direction of causation), and 16b (gene-environment
  equivalence). Score them.
- **Item 5 is the one most often skipped**: the three IV assumptions named explicitly — relevance,
  independence, exclusion restriction — not gestured at.
- A study reporting only an inverse-variance-weighted estimate, with no assessment of the assumptions
  (7, 12) and no sensitivity analyses (8, 13), is non-compliant regardless of how well it reads.
- **Name both instruments.** STROBE-MR is a stand-alone extension of STROBE; cite each. See
  `STROBE.md` for the base items.
- Authors are expected to address every item and sub-item, using supplementary material where space
  is short.
- For the design-validity review of the same study, pair with the MR domain probes in
  `peer-review` / `self-review` `references/domain-probes/mendelian_randomization.md`; for the
  analysis, with `analyze-stats` `analysis_guides/mendelian_randomization.md`.
