# MI-CLEAR-LLM Checklist — Reporting LLM Accuracy Studies in Healthcare

**Minimum Reporting Items for Clear Evaluation of Accuracy Reports of Large Language Models in Healthcare**

- **Version:** MI-CLEAR-LLM 2025 (8 item categories) — updates and expands the 2024 original (6 items).
- **Citation (2025 update):** Park SH, Suh CH, Lee JH, Tejani AS, You SC, Kahn CE Jr, Moy L. *MI-CLEAR-LLM: 2025 Updates.* Korean J Radiol. 2025;26(12):1123-1132. PMID: 41199132.
- **DOI:** 10.3348/kjr.2025.1522
- **Citation (2024 original):** Park SH, Suh CH, Lee JH, Kahn CE Jr, Moy L. Korean J Radiol. 2024;25(10):865-868. PMID: 39344542.
- **Licence:** CC BY-NC 4.0 (Korean Society of Radiology).

> **Educational summary, authored in our own words.** This file paraphrases the *intent* of each MI-CLEAR-LLM
> 2025 item to drive an item-by-item audit; it does not reproduce the guideline's verbatim wording. For a
> submission-ready checklist, complete the official instrument at the source above and cite Park et al. 2025.

**The 2025 update expanded the original 6 items into 8 item categories.** The three items that are new or
promoted to the top level in 2025 — **Access mode (2)**, **Input data type (3)**, and **Adaptation strategy
used (4)** — were prompted by the growth of API access and self-managed (often open-source) LLMs, which the
2024 six-item version folded into a single "model identification" item. Cite items by the 2025 numbering.

**Scope:** Studies evaluating the accuracy of LLMs in healthcare tasks (diagnosis, triage, clinical decision
support, medical question answering, information extraction, report generation, etc.). This is NOT for
disclosing LLM use in manuscript *writing* — for that, see ICMJE/COPE policies and the write-paper skill's LLM
disclosure feature. MI-CLEAR-LLM supplements, and does not replace, a primary reporting guideline (STARD /
STARD-AI, CLAIM 2024, or TRIPOD+AI) chosen for the study design.

## Checklist Items (8 items)

| # | Item category | What must be reported |
|---|---|---|
| 1 | Model identification | Model name, version, developer, proprietary/open-source status, access date(s), and training-data cutoff. |
| 2 | Access mode | Whether a web chatbot, an API, or a self-managed local deployment was used, with rationale and version/endpoint or weights. |
| 3 | Input data type | The type and format of data supplied with the prompt, in enough detail for a reader to replicate. |
| 4 | Adaptation strategy used | Whether model weights were altered (e.g., fine-tuning) or non-parametric methods (e.g., prompting, RAG) were used — or neither. |
| 5 | Prompt optimization procedures | How prompts were created and optimized, the rationale, and the full executable prompt text. |
| 6 | Prompt execution setup | How queries were submitted (session handling, batching, post-processing); provide the experiment scripts where feasible. |
| 7 | Stochasticity management | Temperature and sampling settings, number of attempts per item, how repeats were synthesized, and reliability across repeats. |
| 8 | Independence of test data | Any overlap between the test data and the model's training data or the data used for prompt development/adaptation. |

## Item detail

### 1. Model identification ⚠️ commonly missed

Fully identify the LLM: model name and version (e.g., GPT-4o, Claude 3.5 Sonnet, Gemini 1.5 Pro), developer
(OpenAI, Anthropic, Google, etc.), whether it is proprietary or open-source, the date(s) the queries were
run, and the training-data cutoff if disclosed. LLMs are frequently updated behind the same name, so a name
alone (e.g., "GPT-4") is insufficient — the exact version and access date are what make the study reproducible.

**Status:** [ ] PRESENT [ ] PARTIAL [ ] MISSING

### 2. Access mode ⚠️ new/expanded in 2025

State how the model was accessed and why: a web-based chatbot interface, a programmatic API, or a self-managed
local deployment. For API access, give the specific API version or endpoint. For self-managed/open-source
models, give the weights version, any quantization, and the hardware. Access mode changes what is controllable
(e.g., a web chatbot may not expose temperature) and what is reproducible.

**Status:** [ ] PRESENT [ ] PARTIAL [ ] MISSING

### 3. Input data type ⚠️ new/expanded in 2025

Describe the type and format of the data supplied to the model with the prompt — free text, structured fields,
tables, images (for vision-language models), or file attachments — in enough detail that a reader could
reconstruct the input. Where images or clinical data are used, describe how they were encoded and presented.

**Status:** [ ] PRESENT [ ] PARTIAL [ ] MISSING

### 4. Adaptation strategy used ⚠️ new/expanded in 2025

State whether the base model was adapted, and how. Distinguish **parametric** adaptation (model weights were
changed, e.g., fine-tuning, instruction-tuning) from **non-parametric** methods that leave weights unchanged
(e.g., prompting strategies, retrieval-augmented generation, tool use) — or state that no adaptation was
applied. Adaptation is a first-class methodological choice, not a footnote.

**Status:** [ ] PRESENT [ ] PARTIAL [ ] MISSING

### 5. Prompt optimization procedures ⚠️ commonly missed

Document how prompts were developed and optimized: who wrote them, how they were iterated, whether prompt
engineering or automated tuning was used, and how many variants were compared. Provide the **full prompt text**
(system, user, and any few-shot examples), preserving exact wording, punctuation, and formatting — in
supplementary material if lengthy. Any dataset used to optimize prompts must be independent of the test data
(see item 8); undisclosed optimization on test-overlapping data inflates apparent performance.

**Status:** [ ] PRESENT [ ] PARTIAL [ ] MISSING

### 6. Prompt execution setup ⚠️ commonly missed

Describe how prompts were run operationally: whether each query was an independent session or a continuing
conversation, whether queries were batched or sequential, whether prior outputs could carry over as context,
and any post-processing applied to outputs (e.g., parsing structured answers from free text). For API studies,
give batch size, rate limiting, and failure handling. Provide the experiment scripts where feasible.

**Status:** [ ] PRESENT [ ] PARTIAL [ ] MISSING

### 7. Stochasticity management ⚠️ commonly missed

LLM outputs are stochastic. Report the number of query attempts per item, how multiple outputs were combined
(majority vote, best-of-N, mean score), and a reliability analysis across repeats (e.g., agreement rate,
kappa). Report the parameters that control randomness — temperature, top-p, top-k, penalties — or, if they were
not controllable (e.g., a web chatbot), state that explicitly. A single-attempt study cannot characterize
reliability and should be scored PARTIAL at best.

**Status:** [ ] PRESENT [ ] PARTIAL [ ] MISSING

### 8. Independence of test data ⚠️ commonly missed

Confirm that the test data were separate from all other data used, and address training-data contamination:
whether the test items could have been in the model's pretraining corpus (a particular risk for published exam
questions and public benchmarks), and any mitigation (unpublished cases, temporal or institution-specific
data). Because most LLM training corpora are undisclosed, contamination cannot be ruled out by inspection and
must be discussed.

**Status:** [ ] PRESENT [ ] PARTIAL [ ] MISSING

## Notes for assessors

- **Apply MI-CLEAR-LLM when the study's outcome is LLM accuracy or performance** (answering board questions,
  clinical reasoning, triage, information extraction, report generation). Do NOT apply it when an LLM is merely
  a pipeline tool whose accuracy is not the outcome, or when the manuscript only discloses writing assistance.
- **"GPT-4" is insufficient (item 1)** — require the exact version (e.g., gpt-4-0613, gpt-4-turbo-2024-04-09)
  and the access date. **Single-run studies (item 7)** are PARTIAL at best. **Published exam questions (item
  8)** demand an explicit contamination discussion.
- **Co-application:** use MI-CLEAR-LLM alongside STARD/STARD-AI (diagnostic accuracy against a reference
  standard), CLAIM 2024 (an LLM processing medical images), or TRIPOD+AI (an LLM used as a prediction model).
  The 8 items here supplement — they do not replace — the primary reporting guideline.
