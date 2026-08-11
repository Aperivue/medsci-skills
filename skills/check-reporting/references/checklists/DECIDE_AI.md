# DECIDE-AI Checklist

**Developmental and Exploratory Clinical Investigations of DEcision support systems driven by Artificial Intelligence**
Version: DECIDE-AI 2022
Source: https://www.equator-network.org · https://www.decide-ai.org
Reference: Vasey B, et al. Nat Med 2022;28(5):924-933. doi:10.1038/s41591-022-01772-9

> Educational summary, authored in our own words. DECIDE-AI materials are CC BY-NC; this file
> paraphrases the *intent* of each item and copies no verbatim guideline wording. Complete the
> official DECIDE-AI checklist for a submission-ready form and cite Vasey et al. 2022.

Verification: all 17 AI-specific items and all 10 generic items were compared, by number, label and
order, against Table 2 of the *BMJ* co-publication of the same guideline (Europe PMC full text,
PMC9116198). 17/17 and 10/10 match, and the 28 AI-specific sub-items were counted from that table.
The generic items had been glossed with a list that named things the guideline does not contain
and omitted two that it does; they are now listed. Wording stays paraphrased: DECIDE-AI is
CC BY-**NC**, which cannot be redistributed under this repository's MIT licence.

## Naming and scope (read first)

- DECIDE-AI reports the **early-stage (live) clinical evaluation** of an AI decision-support system —
  the development-to-implementation gap *between* offline model validation (TRIPOD+AI / STARD-AI /
  CLAIM) and a definitive trial (CONSORT-AI). It is **not** a model-accuracy guideline; it is about
  how the AI behaves, is used, and is kept safe in real clinical workflow during first-in-human use.
- It has **17 AI-specific items** (28 subitems) plus **10 generic** reporting items (study identifiers,
  objectives, setting, sample-size rationale, statistics, funding/COI, registration, etc. — apply
  these like any reporting guideline). The AI-specific items below are the core.
- Distinct from CONSORT-AI (definitive RCT report) and SPIRIT-AI (trial protocol); use DECIDE-AI for
  the exploratory/early live-clinical evaluation stage.

## AI-specific items (17)

Status each PRESENT / PARTIAL / MISSING / N/A.

### Title / Abstract

| # | Item | Description (intent) |
|---|------|----------------------|
| 1 | Title | Identify the study as an early-stage clinical evaluation of an AI/ML-driven decision-support system. |

### Introduction

| # | Item | Description (intent) |
|---|------|----------------------|
| 2 | Intended use | Describe the targeted medical condition(s), the decision the system supports, and the intended users and use context. |

### Methods

| # | Item | Description (intent) |
|---|------|----------------------|
| 3 | Participants | Describe how patients were recruited and the inclusion/exclusion criteria at both patient and data level, how the number was arrived at, and the corresponding information for the **users** (clinicians). |
| 4 | AI system | Describe the system: algorithm type, training data and provenance, inputs, outputs, and version. |
| 5 | Implementation | Describe how the system was integrated into the **clinical workflow** and the evaluation settings (how/where it was used in practice). |
| 6 | Safety and errors | Pre-define what counts as a significant error/malfunction and how such events were identified and captured. |
| 7 | Human factors | Describe the human-factors approach: tools, methods/frameworks, and the users involved (usability evaluation plan). |
| 8 | Ethics | Describe whether specific methodologies were used to fulfil an ethics-related goal (such as algorithmic fairness), and their rationale. |

### Results

| # | Item | Description (intent) |
|---|------|----------------------|
| 9 | Participants | Report baseline characteristics of patients/users and data missingness. |
| 10 | Implementation | Report user exposure to the system and adherence to the intended use (how it was actually used). |
| 11 | Modifications | Report any changes made to the AI system during the study (versioning, retraining, threshold changes). |
| 12 | Human–computer agreement | Report how often and how users agreed with / overrode the AI recommendations. |
| 13 | Safety and errors | List significant errors, malfunctions, and patient-safety events observed. |
| 14 | Human factors | Report usability results and **learning curves** over the evaluation. |

### Discussion

| # | Item | Description (intent) |
|---|------|----------------------|
| 15 | Support for intended use | Discuss whether the results support the stated intended clinical use, within the early-stage limits. |
| 16 | Safety and errors | Discuss the safety profile and the implications of the observed errors for wider deployment. |

### Other

| # | Item | Description (intent) |
|---|------|----------------------|
| 17 | Data availability | Disclose availability of data and code (with access constraints). |

---

## Notes for Assessors

- Apply the **10 generic items** as well. They are, in the guideline's own order: **I** Abstract,
  **II** Objectives, **III** Research governance, **IV** Outcomes, **V** Analysis, **VI** Patient
  involvement, **VII** Main results, **VIII** Subgroups analysis, **IX** Strengths and limitations,
  **X** Conflicts of interest. DECIDE-AI assumes standard reporting underneath.
- **Human factors / learning curve (7, 14)** and **human–computer agreement / override (12)** are what
  make DECIDE-AI distinct from offline-accuracy guidelines; a study that reports only model metrics and
  no real-use human-interaction data is PARTIAL/MISSING on the core of DECIDE-AI.
- **Safety and errors (6/13/16)** must run end-to-end: pre-defined → captured → discussed. A safety
  claim with no pre-defined error capture is PARTIAL.
- **Implementation (5/10)** is about *workflow integration and actual use*, not just deployment intent.
- **Modifications (11)**: silent mid-study model/threshold changes without disclosure undermine the
  evaluation — mark MISSING if changes are implied but not reported.
- Use **CONSORT-AI** for a definitive trial and **TRIPOD+AI / STARD-AI / CLAIM** for offline model
  development/accuracy; DECIDE-AI covers the early live-clinical evaluation between them.
