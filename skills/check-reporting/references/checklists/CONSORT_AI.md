# CONSORT-AI Checklist

**Consolidated Standards of Reporting Trials -- Artificial Intelligence Extension**
Version: CONSORT-AI 2020 (extends CONSORT 2010)
Source: https://www.consort-spirit.org · EQUATOR Network
Reference: Liu X, Cruz Rivera S, Moher D, et al. Nat Med 2020;26(9):1364-1374. doi:10.1038/s41591-020-1034-x (CC BY 4.0)

> Educational summary, authored in our own words from the CC BY 4.0 source. Use the official
> CONSORT-AI checklist for a submission-ready form and cite Liu et al. 2020.

## Naming and scope (read first)

- CONSORT-AI is an **extension** of **CONSORT 2010**, for reports of randomized clinical trials of
  interventions that **include an AI/ML component**. Apply **both**: every base CONSORT 2010 item
  plus the AI-specific items below; name and cite both instruments (manuscript-style-classical §14).
- It is the **reports** counterpart of **SPIRIT-AI** (trial protocols). For a trial protocol use
  SPIRIT-AI; for the completed-trial report use CONSORT-AI.
- The AI items elaborate existing CONSORT items (numbered to match), so assess them alongside the
  parent item.

## AI-specific extension items

Status each PRESENT / PARTIAL / MISSING / N/A.

### Title and Abstract

| # | Item | Description (intent) |
|---|------|----------------------|
| 1a,b (i) | AI identification | State in the title/abstract that the intervention involves AI/ML and specify the type of model. |
| 1a,b (ii) | Intended use | State the intended use of the AI intervention in the title/abstract. |

### Introduction — Background and objectives

| # | Item | Description (intent) |
|---|------|----------------------|
| 2a (i) | Intended use in context | Explain the intended use of the AI intervention in the context of the clinical pathway, including its purpose and the intended user. |

### Methods

| # | Item | Description (intent) |
|---|------|----------------------|
| 4a (i) | Participant eligibility | State the participant-level inclusion and exclusion criteria. |
| 4a (ii) | Input-data eligibility | State the inclusion and exclusion criteria at the level of the **input data** to the AI system. |
| 4b | Setting integration | Describe how the AI intervention was integrated into the trial setting, including any onsite or offsite requirements. |
| 5 (i) | Algorithm version | State which version of the AI algorithm was used. |
| 5 (ii) | Input acquisition | Describe how the input data were acquired and selected for the AI intervention. |
| 5 (iii) | Poor/unavailable input | Describe how poor-quality or unavailable input data were assessed and handled. |
| 5 (iv) | Human–AI interaction | Specify whether there is human–AI interaction in the handling of the input data, and the expertise required of the user. |
| 5 (v) | AI output | Specify the output of the AI intervention. |
| 5 (vi) | Output to decision | Explain how the AI intervention's outputs contributed to decision-making or other elements of clinical practice. |

### Results

| # | Item | Description (intent) |
|---|------|----------------------|
| 19 | Performance errors | Describe the results of any analysis of performance errors and how errors were identified; if none was done, justify why. |

### Other Information

| # | Item | Description (intent) |
|---|------|----------------------|
| 25 | Code/intervention access | State whether and how the AI intervention and/or its code can be accessed, including any restrictions on access or reuse. |

---

## Notes for Assessors

- Apply CONSORT-AI **with** all base CONSORT 2010 items — the AI items do not replace them.
- **Algorithm version (5 (i))** is non-waivable: a trial result tied to an unspecified model version is
  not interpretable or reproducible. Mark MISSING if absent.
- **Input-data eligibility (4a (ii))** is distinct from participant eligibility — a frequent omission;
  a trial can enroll eligible patients yet feed the AI out-of-distribution inputs.
- **Human–AI interaction (5 (iv))** and **how outputs fed decisions (5 (vi))** determine whether the
  trial evaluated the AI as used in practice; vague "the model assisted clinicians" is PARTIAL.
- **Performance-error analysis (19)** and **code accessibility (25)** are commonly dropped and are
  where AI-specific safety/reproducibility live.
- Use **SPIRIT-AI** for the trial protocol; CONSORT-AI is for the completed-trial report.
