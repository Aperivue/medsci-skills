# GATHER Checklist

**Guidelines for Accurate and Transparent Health Estimates Reporting**
Version: GATHER 2016 (18 items). Source: Stevens GA, Alkema L, Black RE, et al. *The Lancet* 2016;388(10062):e19–e23, published simultaneously in *PLoS Medicine* 2016;13(6):e1002056, https://doi.org/10.1371/journal.pmed.1002056 (CC BY 4.0). https://gather-statement.org · EQUATOR Network. The item text below is reproduced from the published checklist under CC BY 4.0 with attribution; cite the source statement.

Apply when the manuscript **reports population health estimates produced by a statistical or mathematical model that synthesizes multiple data sources** — Global Burden of Disease (GBD/IHME) analyses and satellite papers, WHO/UN-agency burden estimates, attributable-burden (comparative-risk / population-attributable-fraction) studies, cause-of-death modeling, prevalence/incidence/mortality estimation, disability-adjusted or quality-adjusted life-year estimation, and their forecasts. GATHER is the reporting standard those estimates are held to; it is orthogonal to STROBE/RECORD (which govern primary and routinely-collected-data studies of *individuals*). A single-institution cohort that only **contextualizes** its finding against a published burden number does not itself trigger GATHER, but a paper that **re-estimates or re-projects** burden does. Pair the analytic methods with `/analyze-stats` `references/analysis_guides/burden_decomposition_forecasting.md` (decomposition, joinpoint/AAPC, forecasting, PAF); pair the reproducibility items (8, 14, 15) with `/verify-refs` and the project's data/code-availability discipline.

Source: Stevens GA, Alkema L, Black RE, Boerma JT, Collins GS, Ezzati M, et al. Guidelines for Accurate and Transparent Health Estimates Reporting: the GATHER statement. *Lancet* 2016;388(10062):e19-e23 (DOI 10.1016/S0140-6736(16)30388-9); also *PLoS Med* 2016;13(6):e1002056 (DOI 10.1371/journal.pmed.1002056).
Verification: all 18 items were extracted from the checklist table of the *PLoS Medicine* version
(Europe PMC full text, PMC4924581) and compared item by item. **The count matched while almost
nothing else did**: this file previously invented four items (Sampling, Bias/misclassification
correction, Comparability adjustments, Citable results file), dropped four real ones (7, 8, 17,
18), renumbered everything from official item 9 onwards, and rewrote item 15's requirement.

## Checklist Items (18 items)

### Objectives and funding

| # | Item | Description |
|---|------|-------------|
| 1 | Objectives | Define the indicator(s), populations (including age, sex, and geographic entities), and time period(s) for which estimates were made. |
| 2 | Funding | List the funding sources for the work. |

### Data inputs

*Items 3–6 apply to all data inputs from multiple sources that are synthesized as part of the study.*

| # | Item | Description |
|---|------|-------------|
| 3 | Data identification and access | Describe how the data were identified and how the data were accessed. |
| 4 | Inclusion/exclusion criteria | Specify the inclusion and exclusion criteria. Identify all ad-hoc exclusions. |
| 5 | Source characteristics | Provide information about all included data sources and their main characteristics. For each data source used, report reference information or contact name/institution, population represented, data collection method, year(s) of data collection, sex and age range, diagnostic criteria or measurement method, and sample size, as relevant. |
| 6 | Input-data bias | Identify and describe any categories of input data that have potentially important biases (e.g., based on characteristics listed in item 5). |

*Item 7 applies to data inputs that contribute to the analysis but were not synthesized as part of the study.*

| # | Item | Description |
|---|------|-------------|
| 7 | Other data inputs | Describe and give sources for any other data inputs. |

*Item 8 applies to all data inputs.*

| # | Item | Description |
|---|------|-------------|
| 8 | Data inputs in an extractable format | Provide all data inputs in a file format from which data can be efficiently extracted (e.g., a spreadsheet rather than a PDF), including all relevant meta-data listed in item 5. For any data inputs that cannot be shared because of ethical or legal reasons, such as third-party ownership, provide a contact name or the name of the institution that retains the right to the data. |

### Data analysis

| # | Item | Description |
|---|------|-------------|
| 9 | Analysis overview | Provide a conceptual overview of the data analysis method. A diagram may be helpful. |
| 10 | Analysis detail | Provide a detailed description of all steps of the analysis, including mathematical formulae. This description should cover, as relevant, data cleaning, data pre-processing, data adjustments and weighting of data sources, and mathematical or statistical model(s). |
| 11 | Model selection | Describe how candidate models were evaluated and how the final model(s) were selected. |
| 12 | Model performance | Provide the results of an evaluation of model performance, if done, as well as the results of any relevant sensitivity analysis. |
| 13 | Uncertainty methods | Describe methods of calculating uncertainty of the estimates. State which sources of uncertainty were, and were not, accounted for in the uncertainty analysis. |
| 14 | Source-code access | State how analytic or statistical source code used to generate estimates can be accessed. |

### Results and discussion

| # | Item | Description |
|---|------|-------------|
| 15 | Estimates in an extractable format | Provide published estimates in a file format from which data can be efficiently extracted. |
| 16 | Quantitative uncertainty | Report a quantitative measure of the uncertainty of the estimates (e.g., uncertainty intervals). |
| 17 | Interpretation | Interpret results in light of existing evidence. If updating a previous set of estimates, describe the reasons for changes in estimates. |
| 18 | Limitations | Discuss limitations of the estimates. Include a discussion of any modelling assumptions or data limitations that affect interpretation of the estimates. |

## MedSci application notes

- **Uncertainty intervals, not confidence intervals (items 13, 16).** Model-based estimates report 95% **uncertainty intervals (UIs)** from posterior/Monte-Carlo draws (commonly 250–500), taken as the 2.5th–97.5th percentiles. A UI crossing the null is "insufficient evidence for direction," not a non-significant test — do not translate it into *P*-value language.
- **Robustness is uncertainty propagation plus honest disclosure (items 12, 13, 18).** Burden papers rarely carry a confounding-control toolkit (DAG, E-value, negative controls); that toolkit belongs to individual-level cohorts (STROBE/RECORD). For an estimate paper, the substitute is a propagated UI at every modeling step **plus an itemized limitations paragraph** stating which biases were and were not addressed. State it explicitly rather than implying a sensitivity suite that was not run.
- **Reproducibility by pointer (items 8, 14, 15).** Estimate papers satisfy code/data availability by pointing to the standing pipeline's public repository (for GBD: a GHDx data citation and the IHME/analysis GitHub), not by curating a study-specific dataset.
- **Provenance of any add-on layer.** If the contribution is a forecast, a decomposition, or a policy-stratified re-slice on top of an existing platform's estimates, report items 9–14 for that added layer specifically — the base platform's methods do not document it.
