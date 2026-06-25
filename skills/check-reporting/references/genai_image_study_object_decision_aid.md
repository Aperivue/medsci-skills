# Decision aid — reporting studies where generative AI images ARE the study object

**When this applies:** the study evaluates **images that a generative AI model synthesized**
(realism, controllability/steerability, whether human readers can distinguish synthetic from
real, or model-vs-model quality). The generative model's *output* is the object under study.

**When this does NOT apply:** a model (incl. a vision-language model) *interprets* images and
you measure its diagnostic accuracy — that is an AI-accuracy study; use the relevant
accuracy guideline directly (e.g., STARD-AI, CLAIM, TRIPOD+AI, MI-CLEAR-LLM).

## There is no single dominant checklist for this study type
Generative-image-as-study-object work (e.g., RSNA reader studies on AI-synthesized or
"deepfake" medical images) is reported by **assembling** existing guidelines plus a precedent
bar. Do not claim wholesale compliance with any one checklist; map applicable items and cite
the base guideline together with any AI extension (verify each item against the published
source — never invent items).

### Generator / provenance side
- **CLAIM 2024** — medical-imaging-AI umbrella; the 2024 revision covers generative/foundation
  models. If commercial models are used **as-is** (no training/fine-tuning by the authors),
  the model-development / training / validation-split items are **N/A**; report data sources,
  reference/real comparators, evaluation, transparency, and limitations.
- **FUTURE-AI** — use the **Traceability** principle: persist verbatim prompts, a generation
  manifest, model + version + access date, and parameters (a prompt/generation registry).
- **MI-CLEAR-LLM — transparency *items* only, not study-level compliance.** MI-CLEAR-LLM is
  scoped to **LLM *accuracy* studies in healthcare** (including VLMs interpreting images); it
  is **not** a guideline for generative-output studies. Borrow its reporting *items* for
  prompt-driven foundation models — verbatim prompt(s), model name + version + access date,
  access channel/API, sampling parameters, number of runs, handling of non-determinism,
  responsible party — to document generation provenance. Cite it as the basis for prompt
  logging, not as the study's reporting guideline.

### Reader / evaluation side
- **STARD 2015 + STARD-AI** — if the reader task is **real-vs-synthetic discrimination**, that
  is a diagnostic-accuracy structure: report the reference standard (what counts as
  "real"/"synthetic"), reader blinding, flow, and accuracy with intervals. Cite base STARD
  **and** the STARD-AI extension.
- **GRRAS** (Guidelines for Reporting Reliability and Agreement Studies) — for inter-reader
  feature/quality ratings: number and qualification of readers, blinding, the agreement
  statistic (ICC / weighted kappa) with 95% CI, and separate reporting of any anchor/control
  items.
- **MRMC reporting** — for multi-reader multi-case designs: a-priori power, per-reader
  randomization/seed, and a real-control arm matched on non-content attributes (resolution,
  cropping, compression) so a format-only classifier cannot rival the readers.

### Precedent bar (de-facto standard for this study type)
Match the methodological bar set by published generative-image-as-study-object reader studies
in high-impact radiology venues: a-priori power, MRMC reader platform with per-reader seeds,
real-control matching on non-content attributes, and **explicit, pre-specified handling of
failed / low-quality generations** (count them rather than silently excluding survivors).

## Cross-cutting cautions
- **No overclaim:** state which items of which guideline the study satisfies, verified against
  the published checklist; do not assert blanket "reported per [guideline]".
- **Manuscript's own AI-use disclosure** (writing assistance) is separate from the study-object
  reporting above — see ICMJE/COPE and the write-paper LLM-disclosure feature.
- **Pre-registration** of the primary estimand, frequency/realism references, and the
  fresh-only firewall (pilot/calibration images excluded from the confirmatory set) belongs in
  a study registry (e.g., OSF) for non-clinical reader studies — not PROSPERO (systematic
  reviews) or a clinical-trial registry (no health-outcome intervention).
