# TRIPOD-LLM Checklist

**Transparent Reporting of a multivariable prediction model for Individual Prognosis Or Diagnosis -- Large Language Models**
Version: TRIPOD-LLM 2025 (living guideline)
Source: https://www.tripod-statement.org · interactive checklist: https://tripod-llm.vercel.app
Reference: Gallifant J, ..., Bitterman DS. Nat Med 2025;31(1):60-69. doi:10.1038/s41591-024-03425-5

> **Educational summary, authored in our own words.** This file paraphrases the *intent* of each
> TRIPOD-LLM item to drive an item-by-item audit; it does **not** reproduce the guideline's verbatim
> wording. The published article is subscription-access. For a submission-ready checklist, complete
> the official instrument at the source above and cite Gallifant et al. 2025.

## Naming and scope (read first)

- TRIPOD-LLM is an **extension** of the **TRIPOD** family (TRIPOD 2015 → TRIPOD+AI 2024 →
  TRIPOD-LLM 2025). In Methods, name **both** the base instrument and the extension and cite each
  (manuscript-style-classical §14): "reported per TRIPOD (Collins et al. 2015) and its large-language-model
  extension TRIPOD-LLM (Gallifant et al. 2025)."
- **Applies to** studies that develop, fine-tune, prompt, or evaluate **large language models** for a
  biomedical/clinical task (classification, extraction, summarization, generation, question
  answering, etc.) — not only to risk-prediction models.
- **Modular.** A universal core (≈14 main items / 32 subitems) applies to every LLM study; the
  remaining items/subitems are **task- or design-specific** (e.g., Annotation, Prompting,
  Summarization, Instruction-tuning) and are **N/A** when that component is absent — justify N/A.
- **Pairs with, does not replace, MI-CLEAR-LLM** (the 6-item LLM-accuracy supplement). Apply
  MI-CLEAR-LLM alongside when LLM accuracy is an outcome.

## Checklist Items

Items are grouped as in the guideline. Status each PRESENT / PARTIAL / MISSING / N/A.

### Title and Abstract

| # | Item | Description (intent) |
|---|------|----------------------|
| 1 | Title | Identify the study as developing, fine-tuning, prompting, and/or evaluating an LLM, and name the clinical task and target setting. |
| 2 | Abstract | Provide a structured summary (objectives, data, LLM and version, task, evaluation approach, human oversight, key results, limitations). Follow the TRIPOD-LLM-for-Abstracts items. |

### Introduction

| # | Item | Description (intent) |
|---|------|----------------------|
| 3 | Background | Explain the healthcare problem and context, the intended role of the LLM, and the target population/users. |
| 4 | Objectives | State the specific study objectives and the LLM task(s) addressed. |

### Methods — Data

| # | Item | Description (intent) |
|---|------|----------------------|
| 5 | Data sources | Describe all data sources and input data types (clinical text, notes, structured fields, images-to-text). |
| 6 | Data distribution / splits | Describe how data were partitioned (train / tune / validation / held-out test, internal vs external) and steps to prevent train-test contamination and leakage of evaluation data into pretraining/prompts. |
| 7 | Study dates | Specify key dates (data accrual start/end, model knowledge-cutoff relative to the data). |
| 8 | Preprocessing | Describe text preprocessing, de-identification, tokenization-relevant steps, and any filtering. |
| 9 | Missing / inadequate input | Describe handling of missing, truncated, or out-of-context inputs. |

### Methods — Analytical / LLM methods

| # | Item | Description (intent) |
|---|------|----------------------|
| 10 | LLM identity and version | Name the model, exact version/snapshot or weights, provider/access route (API vs local), and date of access — versions drift, so this is essential for reproducibility. |
| 11 | Development / adaptation | Describe how the LLM was developed or adapted (zero/few-shot prompting, retrieval augmentation, fine-tuning, instruction-tuning) in enough detail to reproduce. |
| 12 | Text generation settings | Report decoding/generation parameters (temperature, top-p, max tokens, stop criteria, seed/determinism where available). |
| 13 | Output specification | Define the expected output format and how free-text outputs were mapped to the study endpoint. |
| 14 | Output handling / post-processing | Describe parsing, constraint enforcement, and any human or rule-based post-processing of outputs. |

### Methods — LLM output evaluation

| # | Item | Description (intent) |
|---|------|----------------------|
| 15 | Evaluation metrics | Specify all performance/quality metrics, including task-specific and human-evaluation measures; define the outcome/reference standard and who set it. |
| 16 | Subjective / human evaluation | Describe any human rating: rubric, anchors, number and expertise of raters, blinding, and inter-rater agreement. |
| 17 | Comparators | Describe comparators (clinicians, prior models, guidelines) and ensure same-data, same-task comparison. |

### Methods — Task/design-specific components (N/A if absent; justify)

| # | Item | Description (intent) |
|---|------|----------------------|
| 18 | Annotation | If labels/references were annotated: describe the labeling process, number and background of annotators, and adjudication. |
| 19 | Prompting | If prompting was used: describe prompt design/templates, prompt-selection procedure, and the data used to develop prompts (kept separate from test data). |
| 20 | Summarization | If summarization was a task: describe inputs, preprocessing, and how summaries were assessed for faithfulness/omission. |
| 21 | Instruction tuning / alignment | If instruction-tuning/alignment was applied: describe the instructions and the data and procedure used. |

### Methods — Compute and Ethics

| # | Item | Description (intent) |
|---|------|----------------------|
| 22 | Compute | Report computational resources (hardware, and for fine-tuning, scale/cost relevant to reproducibility and environmental reporting). |
| 23 | Ethical approval | Report IRB/ethics approval (or exemption) and consent/data-governance for the data used. |

### Open Science

| # | Item | Description (intent) |
|---|------|----------------------|
| 24 | Funding | Source of funding and role of funders. |
| 25 | Conflicts of interest | Declare conflicts, including relationships with model providers. |
| 26 | Protocol / registration | State protocol availability and any registration. |
| 27 | Data availability | State availability of data (and access constraints for clinical text). |
| 28 | Code / prompt availability | State availability of code, prompts, and (where applicable) model weights or access instructions. |

### Patient and Public Involvement

| # | Item | Description (intent) |
|---|------|----------------------|
| 29 | PPI | Describe patient/public involvement in design/conduct, or state that there was none. |

### Results

| # | Item | Description (intent) |
|---|------|----------------------|
| 30 | Participants / data flow | Describe the flow of cases/records through the study, characteristics, and any comparison between development and external data. |
| 31 | Performance | Report performance/quality results with appropriate uncertainty, including human-evaluation results and, where relevant, subgroup/fairness performance. |
| 32 | LLM updating | If the model or prompts were updated during the study, report results before and after. |

### Discussion

| # | Item | Description (intent) |
|---|------|----------------------|
| 33 | Interpretation | Interpret results in light of objectives, comparators, and the clinical task. |
| 34 | Limitations | Discuss limitations (data, evaluation, generalizability, version drift, hallucination/safety). |
| 35 | Usability and context | Discuss the deployment context and conditions required for safe use. |
| 36 | Intended use and oversight | State the intended use and the required human oversight; avoid claims beyond the evidence. |
| 37 | Data-quality / failure handling | Discuss handling of poor-quality inputs and observed failure modes. |
| 38 | User interaction | Discuss requirements for how users should interact with the system. |
| 39 | Future research | Outline implications and future work. |

---

## Notes for Assessors

- The numbering above groups the guideline's 19 main items (and ~50 subitems) into an
  assessment-friendly list; use the official interactive checklist for submission-ready item
  numbers and the abstract sub-checklist.
- **Version reporting (item 10) is non-waivable** for an LLM study: a result tied to an unnamed or
  undated model snapshot is not reproducible. Mark MISSING if the exact version/access date is absent.
- **Leakage/contamination (item 6)** is the LLM-specific analogue of train-test separation: evaluation
  data must not have entered pretraining, fine-tuning, or prompt-development. Probe explicitly.
- **Human evaluation (item 16)** that drives a quality claim needs a rubric with anchors, rater
  expertise, blinding, and inter-rater agreement — a bare "two physicians reviewed the outputs" is
  PARTIAL.
- Task-specific items (Annotation, Prompting, Summarization, Instruction-tuning) are **N/A** when the
  component is absent — record a one-line justification rather than a blank.
- TRIPOD-LLM is a **living guideline**; confirm the current item set at the source before a formal
  submission checklist, and pair with MI-CLEAR-LLM when LLM accuracy is an evaluated outcome.
