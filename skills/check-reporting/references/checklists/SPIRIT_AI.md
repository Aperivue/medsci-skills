# SPIRIT-AI Checklist

**Standard Protocol Items: Recommendations for Interventional Trials -- Artificial Intelligence Extension**
Version: SPIRIT-AI 2020 (extends SPIRIT 2013)
Source: https://www.consort-spirit.org · EQUATOR Network
Reference: Cruz Rivera S, Liu X, Chan AW, et al. Nat Med 2020;26(9):1351-1363. doi:10.1038/s41591-020-1037-7 (CC BY 4.0)

> Educational summary, authored in our own words from the CC BY 4.0 source. Use the official
> SPIRIT-AI checklist for a submission-ready form and cite Cruz Rivera et al. 2020.

## Naming and scope (read first)

- SPIRIT-AI is an **extension** of **SPIRIT 2013**, for **protocols** of randomized clinical trials of
  interventions that **include an AI/ML component**. Apply **both**: every base SPIRIT 2013 item plus
  the AI-specific items below; name and cite both instruments (manuscript-style-classical §14).
- It is the **protocol** counterpart of **CONSORT-AI** (completed-trial reports). For a finished trial
  report use CONSORT-AI.
- The AI items elaborate existing SPIRIT items (numbered to match); assess each alongside its parent.

## AI-specific extension items

Status each PRESENT / PARTIAL / MISSING / N/A.

### Administrative Information

| # | Item | Description (intent) |
|---|------|----------------------|
| 1 (i) | AI identification | State in the title that the intervention involves AI/ML and specify the type of model. |
| 1 (ii) | Intended use | State the intended use of the AI intervention. |

### Introduction — Background and rationale

| # | Item | Description (intent) |
|---|------|----------------------|
| 6a (i) | Role in pathway | Explain the intended use of the AI intervention within the clinical pathway, including its purpose and the intended users. |
| 6a (ii) | Prior validation | Describe any pre-existing evidence for the AI intervention (e.g., prior validation studies). |

### Methods — Participants, interventions, outcomes

| # | Item | Description (intent) |
|---|------|----------------------|
| 9 | Setting integration | Describe the onsite and offsite requirements needed to integrate the AI intervention into the trial setting. |
| 10 (i) | Participant eligibility | State the participant-level inclusion and exclusion criteria. |
| 10 (ii) | Input-data eligibility | State the inclusion and exclusion criteria at the level of the **input data**. |
| 11a (i) | Algorithm version | Specify which version of the AI algorithm will be used. |
| 11a (ii) | Input acquisition | Specify how the input data will be acquired and selected. |
| 11a (iii) | Poor-quality input | Specify how poor-quality or unavailable input data will be assessed and handled. |
| 11a (iv) | Human–AI interaction | Specify any human–AI interaction in handling input data and the expertise required of the user. |
| 11a (v) | AI output | Specify the output of the AI intervention. |
| 11a (vi) | Output to decision | Explain how the AI intervention's outputs will contribute to decision-making or other elements of clinical practice. |

### Methods — Monitoring

| # | Item | Description (intent) |
|---|------|----------------------|
| 22 | Error analysis plan | Specify the plans to identify and analyze performance errors, and any planned mitigation. |

### Ethics and Dissemination

| # | Item | Description (intent) |
|---|------|----------------------|
| 29 | Code/intervention access | State whether and how the AI intervention and/or its code can be accessed, including any restrictions. |

---

## Notes for Assessors

- Apply SPIRIT-AI **with** all base SPIRIT 2013 items — the AI items do not replace them.
- **Algorithm version (11a (i))** and an explicit **error-analysis plan (22)** are the protocol-stage
  commitments that make the eventual CONSORT-AI report verifiable; mark MISSING if absent.
- **Input-data eligibility (10 (ii))** is distinct from participant eligibility — a common gap.
- **Setting integration (9)** and **human–AI interaction (11a (iv))** define whether the protocol
  evaluates the AI as it will actually be used; vague phrasing is PARTIAL.
- Use **CONSORT-AI** for the completed-trial report; SPIRIT-AI is for the protocol.
