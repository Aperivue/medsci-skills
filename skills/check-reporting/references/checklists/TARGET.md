# TARGET Checklist

**Transparent Reporting of Observational Studies Emulating a Target Trial**
Version: TARGET 2025 (21 items across 6 sections; items 6 and 7 pair the target-trial *specification* with its *emulation* in the data)
Source: In-house faithful summary of the TARGET item intents (own-words paraphrase, not verbatim). Cashin AG, Hansford HJ, Hernán MA, et al. Transparent Reporting of Observational Studies Emulating a Target Trial: The TARGET Statement. JAMA 2025;334(12):1084-1093. DOI 10.1001/jama.2025.13350. Official checklist: https://target-guideline.org. Complete the official TARGET instrument for a submission checklist. Pairs with the `/design-study` target-trial-emulation design module.

Licence: *JAMA* (© American Medical Association) — no open licence.
Verification: all 39 sub-items across the 21 numbered items were compared, by number and order,
against the checklist tables of the published statement (PubMed Central record PMC13084563).
39/39 are present, including the paired 6a–h specification and 7a–7h(ii) emulation columns.
Items that had dropped a required clause (1a, 4, 5, 6c, 6d, 6g, 6h, 7d, 7f, 7h, 8, 10, 13, 16,
19) are corrected. Wording stays paraphrased —
the statement is © American Medical Association with no open licence.

## Checklist Items (21 items)

### Title and Abstract

| # | Item | Description |
|---|------|-------------|
| 1a | Study type | Identify that the study attempts to emulate a target trial using observational data; state the objectives and give a brief summary of the target trial that was specified. |
| 1b | Data sources | Report the data sources used for the emulation. |
| 1c | Key elements | Summarize the key assumptions, statistical methods, findings, and conclusions. |

### Introduction

| # | Item | Description |
|---|------|-------------|
| 2 | Background | Describe the scientific background and the gap in knowledge the study addresses. |
| 3 | Causal question | Summarize the causal question specified by the target-trial protocol. |
| 4 | Rationale | Describe the rationale for emulating a target trial with the available data; where applicable, cite the randomized trials that informed the target-trial design. |

### Methods

| # | Item | Description |
|---|------|-------------|
| 5 | Data sources | Cite the data sources and describe their original purpose, type, geographic locations, setting, and time period; if relevant, describe how data were linked or pooled. |

#### Target-trial specification (the protocol you would run)

| # | Item | Description |
|---|------|-------------|
| 6a | Eligibility criteria | Describe the eligibility criteria defining the target population. |
| 6b | Treatment strategies | Describe the treatment strategies to be compared, in sufficient detail (e.g., dose, duration, start/stop rules). |
| 6c | Assignment | Report that eligible individuals would be randomly assigned to the treatment strategies, and may be aware of their treatment allocation. |
| 6d | Follow-up | Clarify that follow-up would start at the time of assignment to the treatment strategies, and specify when follow-up would end. |
| 6e | Outcomes | Describe the outcomes, including their measurement and timing. |
| 6f | Causal contrasts | Describe the causal contrasts of interest, including the effect measures. |
| 6g | Identifying assumptions | Describe the assumptions that would be made to identify each causal estimand, and any variables related to those assumptions. |
| 6h | Data analysis plan | For each causal estimand, describe the data-analysis procedures and the statistical modelling assumptions, including how missing data would be handled. |

#### Target-trial emulation (mapping to the observational data)

| # | Item | Description |
|---|------|-------------|
| 7a | Eligibility (emulation) | Describe how the eligibility criteria were operationalized with the data. |
| 7b | Treatment strategies (emulation) | Describe how the treatment strategies were operationalized with the data. |
| 7c | Assignment (emulation) | Describe how assignment to treatment strategies was operationalized with the data. |
| 7d | Follow-up (emulation) | Clarify that follow-up starts at the time individuals were assigned to the treatment strategies, and describe how the end of follow-up was operationalized with the data. *(Misaligning eligibility, assignment and start of follow-up is what introduces immortal-time bias.)* |
| 7e | Outcomes (emulation) | Describe how the outcomes were operationalized with the data. |
| 7f | Causal contrasts (emulation) | Describe how the causal contrasts, including the effect measures, were operationalized with the data. |
| 7g(i) | Identifying assumptions (emulation) | For each causal estimand, describe the assumptions made, including baseline confounding. |
| 7g(ii) | Assumption variables | Describe how the variables related to those assumptions were operationalized. |
| 7h(i) | Data analysis (emulation) | For each causal estimand, describe the data-analysis procedures and statistical modelling assumptions used in the emulation, including how missing data were handled. |
| 7h(ii) | Sensitivity analyses | For each causal estimand, describe any additional analyses assessing how sensitive the results are to the operationalization, assumption, and analysis choices. |

### Results

| # | Item | Description |
|---|------|-------------|
| 8 | Participant selection | Report the numbers of individuals assessed for eligibility, eligible, and assigned to each treatment strategy; a flow diagram is strongly recommended. |
| 9 | Baseline data | Describe the distribution of baseline characteristics of individuals, by treatment strategy. |
| 10 | Follow-up | Summarize the length of follow-up and describe the reasons for its end, for each treatment strategy and causal contrast. |
| 11 | Missing data | Describe the frequency of missing data in all variables, by treatment strategy. |
| 12 | Outcomes | Describe the frequency or distribution of each outcome, by treatment strategy. |
| 13 | Effect estimates | Report the effect estimate for each causal contrast, with its corresponding measure of precision, giving both absolute and relative effect measures when applicable. |
| 14 | Additional analyses | Report the results of all analyses assessing the sensitivity of the estimates to the choices made. |

### Discussion

| # | Item | Description |
|---|------|-------------|
| 15 | Interpretation | Provide an interpretation of the key findings in the context of the causal question. |
| 16 | Limitations | Discuss limitations, considering differences between the target trial and its emulation and how plausible the assumptions are, including those about baseline confounding in the absence of randomization. |

### Other Information

| # | Item | Description |
|---|------|-------------|
| 17 | Ethics | Provide the institutional review board or ethics committee approval information. |
| 18 | Registration | State whether, when, and where the study protocol was registered. |
| 19 | Data sharing | State whether the data, analytic code, and materials are accessible, and where and how they can be obtained. |
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
