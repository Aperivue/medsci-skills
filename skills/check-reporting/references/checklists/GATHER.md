# GATHER Checklist

**Guidelines for Accurate and Transparent Health Estimates Reporting**
Version: GATHER 2016 (18 items). Source: Stevens GA, Alkema L, Black RE, et al. *The Lancet* 2016;388(10062):e19–e23, published simultaneously in *PLoS Medicine* 2016;13(6):e1002056, https://doi.org/10.1371/journal.pmed.1002056 (CC BY 4.0). https://gather-statement.org · EQUATOR Network. The item text below is an in-house faithful summary of each official item's intent; cite the source statement for the canonical wording.

Apply when the manuscript **reports population health estimates produced by a statistical or mathematical model that synthesizes multiple data sources** — Global Burden of Disease (GBD/IHME) analyses and satellite papers, WHO/UN-agency burden estimates, attributable-burden (comparative-risk / population-attributable-fraction) studies, cause-of-death modeling, prevalence/incidence/mortality estimation, disability-adjusted or quality-adjusted life-year estimation, and their forecasts. GATHER is the reporting standard those estimates are held to; it is orthogonal to STROBE/RECORD (which govern primary and routinely-collected-data studies of *individuals*). A single-institution cohort that only **contextualizes** its finding against a published burden number does not itself trigger GATHER, but a paper that **re-estimates or re-projects** burden does. Pair the analytic methods with `/analyze-stats` `references/analysis_guides/burden_decomposition_forecasting.md` (decomposition, joinpoint/AAPC, forecasting, PAF); pair the reproducibility items (15, 17) with `/verify-refs` and the project's data/code-availability discipline.

## Checklist Items (18 items)

### Objectives and funding

| # | Item | Description |
|---|------|-------------|
| 1 | Objectives | Define the indicator(s), the population(s) — including age, sex, and geographic entities — and the time period(s) for which estimates were made. |
| 2 | Funding | List the funding sources for the work. |

### Data inputs

| # | Item | Description |
|---|------|-------------|
| 3 | Data identification and access | Describe how the input data were identified and how they were accessed. |
| 4 | Inclusion/exclusion criteria | Specify the inclusion and exclusion criteria for input data, and identify all ad-hoc exclusions. |
| 5 | Source characteristics | Provide information on all included data sources and their main characteristics: for each source, report reference/contact information, the population represented, the data-collection method, the year(s) of collection, the sex and age range, the diagnostic criteria or measurement method, and the sample size, as relevant. |
| 6 | Input-data bias | Identify and describe any categories of input data that carry potentially important biases (for example, based on the characteristics listed in item 5). |
| 7 | Sampling | For data inputs that involve sampling, describe and quantify the sampling. |
| 8 | Bias/misclassification correction | For measurements corrected as part of the analysis, describe the methods and give the definitions used to correct for known biases or misclassification. |
| 9 | Comparability adjustments | Describe how, if at all, data were modified to be made comparable with other data (for example, crosswalks between case definitions or measurement methods). |

### Data analysis

| # | Item | Description |
|---|------|-------------|
| 10 | Analysis overview | Provide a conceptual overview of the data-analysis method. |
| 11 | Analysis detail | Provide a detailed description of all steps of the analysis, including mathematical formulae. Cover, as relevant, data cleaning, pre-processing, adjustments, weighting of data sources, and the mathematical or statistical model(s). |
| 12 | Model selection | Describe how candidate models were evaluated and how the final model(s) were selected. |
| 13 | Model performance | Provide the results of an evaluation of model performance, if done, together with the results of any relevant sensitivity analysis. |
| 14 | Uncertainty methods | Describe the methods for calculating the uncertainty of the estimates, and state which sources of uncertainty were, and were not, accounted for. |
| 15 | Source-code access | State how the analytic or statistical source code used to generate the estimates can be accessed. |

### Results and discussion

| # | Item | Description |
|---|------|-------------|
| 16 | Accessible results | Provide the published estimates in a way that is accessible to a broad audience — for example, in tabular form, as maps, as charts, or as a supplementary file. |
| 17 | Citable results file | Provide a citable and machine-readable file of the results. |
| 18 | Quantitative uncertainty | Report a quantitative measure of the uncertainty of the estimates (for example, uncertainty intervals). |

## MedSci application notes

- **Uncertainty intervals, not confidence intervals (items 14, 18).** Model-based estimates report 95% **uncertainty intervals (UIs)** from posterior/Monte-Carlo draws (commonly 250–500), taken as the 2.5th–97.5th percentiles. A UI crossing the null is "insufficient evidence for direction," not a non-significant test — do not translate it into *P*-value language.
- **Robustness is uncertainty propagation plus honest disclosure (items 13, 14).** Burden papers rarely carry a confounding-control toolkit (DAG, E-value, negative controls); that toolkit belongs to individual-level cohorts (STROBE/RECORD). For an estimate paper, the substitute is a propagated UI at every modeling step **plus an itemized limitations paragraph** stating which biases were and were not addressed. State it explicitly rather than implying a sensitivity suite that was not run.
- **Reproducibility by pointer (items 15, 17).** Estimate papers satisfy code/data availability by pointing to the standing pipeline's public repository (for GBD: a GHDx data citation and the IHME/analysis GitHub), not by curating a study-specific dataset.
- **Provenance of any add-on layer.** If the contribution is a forecast, a decomposition, or a policy-stratified re-slice on top of an existing platform's estimates, report items 10–15 for that added layer specifically — the base platform's methods do not document it.
