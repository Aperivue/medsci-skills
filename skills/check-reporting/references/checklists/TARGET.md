# TARGET Checklist

**Transparent Reporting of Observational Studies Emulating a Target Trial**
Version: TARGET 2025 (21 items across 6 sections; items 6 and 7 pair the target-trial *specification* with its *emulation* in the data)
Source: In-house faithful summary of the TARGET item intents (own-words paraphrase, not verbatim). Cashin AG, Hansford HJ, Hernán MA, et al. Transparent Reporting of Observational Studies Emulating a Target Trial: The TARGET Statement. JAMA 2025;334(12):1084-1093. DOI 10.1001/jama.2025.13350. Official checklist: https://target-guideline.org. Complete the official TARGET instrument for a submission checklist. Pairs with the `/design-study` target-trial-emulation design module.

## Checklist Items (21 items)

### Title and Abstract

| # | Item | Description |
|---|------|-------------|
| 1a | Study type | Identify that the study attempts to emulate a target trial using observational data. |
| 1b | Data sources | Report the data sources used for the emulation. |
| 1c | Key elements | Summarize the key assumptions, statistical methods, findings, and conclusions. |

### Introduction

| # | Item | Description |
|---|------|-------------|
| 2 | Background | Describe the scientific background and the gap in knowledge the study addresses. |
| 3 | Causal question | Summarize the causal question specified by the target-trial protocol. |
| 4 | Rationale | Describe the rationale for emulating a target trial with the available data. |

### Methods

| # | Item | Description |
|---|------|-------------|
| 5 | Data sources | Cite the data sources and describe their original purpose, type, geographic locations, setting, and time period. |

#### Target-trial specification (the protocol you would run)

| # | Item | Description |
|---|------|-------------|
| 6a | Eligibility criteria | Describe the eligibility criteria defining the target population. |
| 6b | Treatment strategies | Describe the treatment strategies to be compared, in sufficient detail (e.g., dose, duration, start/stop rules). |
| 6c | Assignment | State that eligible individuals would be randomly assigned to the treatment strategies. |
| 6d | Start of follow-up | Clarify that follow-up would start at the time of assignment to a treatment strategy (time zero). |
| 6e | Outcomes | Describe the outcomes, including their measurement and timing. |
| 6f | Causal contrasts | Describe the causal contrasts of interest, including the effect measures. |
| 6g | Identifying assumptions | Describe the assumptions that would be made to identify each causal estimand. |
| 6h | Data analysis plan | For each causal estimand, describe the data-analysis procedures and statistical models. |

#### Target-trial emulation (mapping to the observational data)

| # | Item | Description |
|---|------|-------------|
| 7a | Eligibility (emulation) | Describe how the eligibility criteria were operationalized with the data. |
| 7b | Treatment strategies (emulation) | Describe how the treatment strategies were operationalized with the data. |
| 7c | Assignment (emulation) | Describe how assignment to treatment strategies was operationalized with the data. |
| 7d | Start of follow-up (emulation) | Clarify that follow-up starts at the time individuals were assigned to a strategy; misaligning eligibility, assignment, and start of follow-up introduces immortal-time bias. |
| 7e | Outcomes (emulation) | Describe how the outcomes were operationalized with the data. |
| 7f | Causal contrasts (emulation) | Describe how the causal contrasts were operationalized with the data. |
| 7g(i) | Identifying assumptions (emulation) | For each causal estimand, describe the assumptions made, including baseline confounding. |
| 7g(ii) | Assumption variables | Describe how the variables related to those assumptions were operationalized. |
| 7h(i) | Data analysis (emulation) | Describe modifications to the data-analysis methods needed for the observational emulation. |
| 7h(ii) | Sensitivity analyses | Describe any additional analyses assessing the sensitivity of results to the operationalization choices. |

### Results

| # | Item | Description |
|---|------|-------------|
| 8 | Participant selection | Report the numbers of individuals assessed for eligibility, eligible, and assigned to each treatment strategy. |
| 9 | Baseline data | Describe the distribution of baseline characteristics of individuals, by treatment strategy. |
| 10 | Follow-up | Summarize the length of follow-up and describe the reasons for its end. |
| 11 | Missing data | Describe the frequency of missing data in all variables, by treatment strategy. |
| 12 | Outcomes | Describe the frequency or distribution of each outcome, by treatment strategy. |
| 13 | Effect estimates | Report the effect estimate for each causal contrast, with its corresponding measure of precision. |
| 14 | Additional analyses | Report the results of all analyses assessing the sensitivity of the estimates to the choices made. |

### Discussion

| # | Item | Description |
|---|------|-------------|
| 15 | Interpretation | Provide an interpretation of the key findings in the context of the causal question. |
| 16 | Limitations | Discuss limitations, considering differences between the target trial and its emulation. |

### Other Information

| # | Item | Description |
|---|------|-------------|
| 17 | Ethics | Provide the institutional review board or ethics committee approval information. |
| 18 | Registration | State whether, when, and where the study protocol was registered. |
| 19 | Data sharing | State whether the data, analytic code, and materials are accessible. |
| 20 | Funding | Provide the sources of funding and detail the role of the funders. |
| 21 | Conflicts of interest | State any conflicts of interest and financial disclosures for all authors. |

---

## Notes for Assessors

- The distinctive TARGET structure is the paired **specification (item 6)** and **emulation (item 7)**: for each protocol element — eligibility, treatment strategies, assignment, start of follow-up, outcomes, causal contrast, identifying assumptions, analysis — the study must state both the target-trial version and how it was operationalized in the data. A study that reports the emulation without ever specifying the target trial it emulates is a gap.
- The single most consequential defect this catches is **time-zero misalignment → immortal-time bias** (items 6d / 7d): eligibility, treatment assignment, and start of follow-up must coincide.
- Items 6g / 7g require an **explicit causal estimand and its identifying assumptions (including baseline confounding)** — an association reported with no stated estimand or assumptions is a gap, not merely thin reporting.
- TARGET is the **reporting** side; pair it with the `/design-study` **target-trial-emulation module** (the design side, which enforces the same seven-component protocol before data extraction). Use **RECORD / STROBE** for the routinely-collected-data and general observational items not specific to the emulation.
- Not needed for a purely descriptive, prevalence, or diagnostic-accuracy study — TARGET applies to a **causal / comparative-effectiveness** question emulated on observational data.
- The vendored checklist is an educational own-words summary of item intent; complete the official TARGET instrument (target-guideline.org) for a submission checklist.
