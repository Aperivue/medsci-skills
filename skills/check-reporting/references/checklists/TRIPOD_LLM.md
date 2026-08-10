# TRIPOD-LLM Checklist

**Transparent Reporting of a multivariable prediction model for Individual Prognosis Or Diagnosis -- Large Language Models**
Version: TRIPOD-LLM 2025 (living guideline)
Source: https://www.tripod-statement.org · interactive checklist: https://tripod-llm.vercel.app
Reference: Gallifant J, ..., Bitterman DS. Nat Med 2025;31(1):60-69. doi:10.1038/s41591-024-03425-5

> **Educational summary, authored in our own words.** This file paraphrases the *intent* of each
> TRIPOD-LLM item to drive an item-by-item audit; it does **not** reproduce the guideline's verbatim
> wording. The published article is subscription-access. For a submission-ready checklist, complete
> the official instrument at the source above and cite Gallifant et al. 2025.
>
> **Item numbers below follow the official TRIPOD-LLM scheme: 19 main items (1–19) with letter
> subitems (≈50 subitems).** 14 main items / 32 subitems apply to every LLM study; 5 main items /
> 18 subitems are **task- or design-specific** (marked *task-specific*) and are N/A when that
> component is absent — justify the N/A.

Licence: The published *Nature Medicine* article returns no Creative Commons licence via Crossref (DOI 10.1038/s41591-024-03425-5); the author-accepted manuscript is CC BY 4.0 through institutional rights retention.
Verification: **NOT VERIFIED.** The items below have not been compared against the published table. They are an in-house summary; complete the official instrument for anything you report.

## Naming and scope (read first)

- TRIPOD-LLM is an **extension** of the **TRIPOD** family (TRIPOD 2015 → TRIPOD+AI 2024 →
  TRIPOD-LLM 2025). In Methods, name **both** the base instrument and the extension and cite each
  (manuscript-style-classical §14): "reported per TRIPOD (Collins et al. 2015) and its large-language-model
  extension TRIPOD-LLM (Gallifant et al. 2025)."
- **Applies to** studies that develop, fine-tune, prompt, or evaluate **large language models** for a
  biomedical/clinical task (classification, extraction, summarization, generation, question
  answering, etc.) — not only to risk-prediction models.
- **Pairs with, does not replace, MI-CLEAR-LLM** (the 6-item LLM-accuracy supplement). Apply
  MI-CLEAR-LLM alongside when LLM accuracy is an outcome.

## Checklist Items (official numbering 1–19)

Status each PRESENT / PARTIAL / MISSING / N/A.

### Title and Abstract

| # | Item | Description (intent) |
|---|------|----------------------|
| 1 | Title | Identify the study as developing, fine-tuning, prompting, and/or evaluating an LLM, and name the clinical task and target setting. |
| 2 | Abstract | Provide a structured summary (objectives, data, LLM and version, task, evaluation approach, human oversight, key results, limitations). Follow the TRIPOD-LLM-for-Abstracts items. |

### Introduction

| # | Item | Description (intent) |
|---|------|----------------------|
| 3a | Background — context | Explain the healthcare problem, the clinical context, and the rationale for using an LLM. |
| 3b | Background — population & use | Describe the target population/users and the intended use of the LLM. |
| 4 | Objectives | State the specific study objectives and the LLM task(s) addressed. |

### Methods — Data (item 5, a–e)

| # | Item | Description (intent) |
|---|------|----------------------|
| 5a | Data sources | Describe all data sources and input data types (clinical text, notes, structured fields, image-to-text). |
| 5b | Data description / distribution | Describe the dataset and how data were partitioned (train / tune / validation / held-out test, internal vs external), and steps to prevent train–test contamination and leakage of evaluation data into pretraining/prompts. |
| 5c | Study dates | Specify key dates (data accrual start/end, and the model knowledge-cutoff relative to the data). |
| 5d | Preprocessing | Describe text preprocessing, de-identification, and any filtering. |
| 5e | Missing / inadequate / imbalanced data | Describe handling of missing, truncated, out-of-context, or class-imbalanced inputs. |

### Methods — Analytical / LLM methods (item 6, a–e)

| # | Item | Description (intent) |
|---|------|----------------------|
| 6a | LLM identity and version | Name the model, exact version/snapshot or weights, provider/access route (API vs local), and date of access — versions drift, so this is essential for reproducibility. |
| 6b | Development / adaptation | Describe how the LLM was developed or adapted (zero/few-shot prompting, retrieval augmentation, fine-tuning, instruction-tuning) in enough detail to reproduce. |
| 6c | Text generation settings | Report decoding/generation parameters (temperature, top-p, max tokens, stop criteria, seed/determinism where available). |
| 6d | Output | Define the expected output format and how free-text outputs were mapped to the study endpoint. |
| 6e | Output handling / classification | Describe parsing, constraint enforcement, and any human or rule-based post-processing/classification of outputs. |

### Methods — LLM output evaluation (item 7, a–e)

| # | Item | Description (intent) |
|---|------|----------------------|
| 7a | Quality / performance metrics | Specify all performance/quality metrics, including task-specific measures. |
| 7b | Downstream / clinical relevance | Describe how the metrics relate to downstream clinical relevance. |
| 7c | Outcome definition | Define the outcome / reference standard and who set it. |
| 7d | Subjective / human assessment | Describe any human rating: rubric, anchors, number and expertise of raters, blinding, and inter-rater agreement. |
| 7e | Comparisons | Describe comparators (clinicians, prior models, guidelines) and ensure same-data, same-task comparison. |

### Methods — Annotation (item 8, a–c)

| # | Item | Description (intent) |
|---|------|----------------------|
| 8a | Labeling process | Describe the labeling/annotation process and adjudication. |
| 8b | Annotator count | Report the number of annotators. |
| 8c | Annotator background | Report annotator expertise/background. |

### Methods — task/design-specific components (N/A if absent; justify)

| # | Item | Description (intent) |
|---|------|----------------------|
| 9a | Prompting — design *(task-specific)* | If prompting was used: describe prompt design/templates and the prompt-selection procedure. |
| 9b | Prompting — data *(task-specific)* | Describe the data used to develop prompts (kept separate from test data). |
| 10 | Summarization preprocessing *(task-specific)* | If summarization was a task: describe inputs/preprocessing and how summaries were assessed for faithfulness/omission. |
| 11 | Instruction tuning / alignment *(task-specific)* | If instruction-tuning/alignment was applied: describe the instructions and the data and procedure used. |

### Methods — Compute and Ethics

| # | Item | Description (intent) |
|---|------|----------------------|
| 12 | Compute | Report computational resources (hardware, and for fine-tuning, scale/cost relevant to reproducibility and environmental reporting). |
| 13 | Ethical approval | Report IRB/ethics approval (or exemption) and consent/data-governance for the data used. |

### Open Science (item 14, a–f)

| # | Item | Description (intent) |
|---|------|----------------------|
| 14a | Funding | Source of funding and role of funders. |
| 14b | Conflicts of interest | Declare conflicts, including relationships with model providers. |
| 14c | Protocol | State protocol availability. |
| 14d | Registration | State any study registration. |
| 14e | Data availability | State availability of data (and access constraints for clinical text). |
| 14f | Code / prompt availability | State availability of code, prompts, and (where applicable) model weights or access instructions. |

### Patient and Public Involvement

| # | Item | Description (intent) |
|---|------|----------------------|
| 15 | PPI | Describe patient/public involvement in design/conduct, or state that there was none. |

### Results

| # | Item | Description (intent) |
|---|------|----------------------|
| 16a–d | Participants / data flow *(task-specific)* | Describe the flow of cases/records through the study, characteristics, available clinical variables, and sample sizes, including comparison between development and external data. |
| 17 | Performance | Report performance/quality results with appropriate uncertainty, including human-evaluation results and, where relevant, subgroup/fairness performance. |
| 18 | LLM updating | If the model or prompts were updated during the study, report results before and after. |

### Discussion (item 19, a–g)

| # | Item | Description (intent) |
|---|------|----------------------|
| 19a | Interpretation | Interpret results in light of objectives, comparators, and the clinical task. |
| 19b | Limitations | Discuss limitations (data, evaluation, generalizability, version drift, hallucination/safety). |
| 19c | Usability and context | Discuss the deployment context and conditions required for safe use. |
| 19d | Intended use | State the intended use and avoid claims beyond the evidence. |
| 19e | Input-data / poor-quality handling | Discuss handling of poor-quality inputs and observed failure modes. |
| 19f | User expertise / oversight | Discuss the user expertise and human oversight required for safe use. |
| 19g | Future research | Outline implications and future work. |

---

## Notes for Assessors

- The numbering follows the official TRIPOD-LLM scheme (19 main items, ~50 subitems). Use the
  official interactive checklist for the submission form and the separate TRIPOD-LLM-for-Abstracts
  sub-checklist (item 2).
- **Version reporting (item 6a) is non-waivable** for an LLM study: a result tied to an unnamed or
  undated model snapshot is not reproducible. Mark MISSING if the exact version/access date is absent.
- **Leakage/contamination (item 5b)** is the LLM-specific analogue of train–test separation:
  evaluation data must not have entered pretraining, fine-tuning, or prompt-development. Probe explicitly.
- **Human evaluation (item 7d)** that drives a quality claim needs a rubric with anchors, rater
  expertise, blinding, and inter-rater agreement — a bare "two physicians reviewed the outputs" is PARTIAL.
- Task-specific items (Prompting 9, Summarization 10, Instruction-tuning 11, Results-participants 16)
  are **N/A** when the component is absent — record a one-line justification rather than a blank.
- TRIPOD-LLM is a **living guideline**; confirm the current item set at the source before a formal
  submission checklist, and pair with MI-CLEAR-LLM when LLM accuracy is an evaluated outcome.
