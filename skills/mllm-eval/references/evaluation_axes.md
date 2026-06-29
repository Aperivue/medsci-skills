# Evaluation axes (mllm-eval)

Load-on-demand reference behind the ME2–ME7 axes: the clinical-efficacy metrics,
faithfulness, contamination, prompt-sensitivity, answer-matching, and reader-study
machinery an LLM/MLLM clinical evaluation must cover. Anchored to the radiology-NLP
metric literature — **RadGraph** (Jain et al., NeurIPS Datasets & Benchmarks 2021),
**CheXbert** (Smit et al., 2020), the rule-based **CheXpert** labeler (Irvin et al., 2019),
and **RadCliQ** (Yu et al., *Patterns* 2023) — and to the reporting standards CLAIM 2024,
**TRIPOD-LLM**, and **MI-CLEAR-LLM**. This skill **specifies and routes** these metrics to
their published extractors and to `/analyze-stats`; it does not run the model or compute the
scores itself. Never report n-gram overlap as clinical correctness, and never fabricate a
score.

## Clinical-efficacy metrics beyond n-gram overlap (ME2 → `NGRAM_ONLY`)

- **Why n-gram overlap fails.** BLEU / ROUGE / METEOR / CIDEr measure surface lexical
  overlap. A report can score high while inverting laterality or omitting a pneumothorax, and
  low while paraphrasing a correct finding. Yu et al. (*Patterns* 2023, RadCliQ) showed these
  metrics correlate weakly with radiologist-assessed clinical error — so an n-gram score is a
  **fluency proxy, not a correctness claim**.
- **RadGraph-F1.** Overlap of the (entity, relation) tuples the RadGraph schema (Jain et al.,
  2021) extracts from the reference and the candidate report — it rewards getting the *same
  findings and their relationships*, not the same words.
- **CheXbert-F1 / CheXpert labeler.** Agreement on the structured CheXpert observation labels
  extracted by CheXbert (Smit et al., 2020) or by the rule-based CheXpert labeler (Irvin et
  al., 2019) — a finding-label–level correctness signal.
- **RadCliQ.** A composite (Yu et al., 2023) that combines metrics to better predict the count
  of radiologist-judged errors. Report it as a composite **alongside** its components, not as a
  one-number replacement.
- **Advise:** report a clinical-efficacy metric (RadGraph-F1 / CheXbert-F1 / RadCliQ)
  **with bootstrap CIs over reports** and a **per-finding / per-label breakdown**, and present
  any BLEU/ROUGE explicitly labelled as a surface-overlap measure — never as the headline.

## Faithfulness & hallucination (ME3 → `FAITHFULNESS_MISSING`)

- **Fluency is not faithfulness.** A high-overlap, well-formed report can still assert findings
  the image does not support. Measure faithfulness directly; do not infer it from an accuracy
  number.
- **Atomic-fact decomposition.** Break the generated text into atomic clinical claims and check
  each against the image / source, then report a **faithfulness (or hallucination) rate** — the
  fraction of generated claims that are grounded.
- **Direction matters.** Separate **omission** (a true finding the model missed) from
  **fabrication** (a false finding the model asserted); they carry different clinical risk and
  should be reported separately, not folded into one error count.
- **False-premise / abstention probe.** Ask about an absent finding or an unanswerable
  question; a faithful model abstains rather than confabulates. Named instruments: **MedVH**,
  **Med-HALT**.
- **Advise:** a generation or VQA claim with no faithfulness and no false-premise/abstention
  evaluation is the central MLLM gap — require both, with rates, before any clinical claim.

## Pretraining / benchmark contamination (ME4 → `CONTAMINATION_UNADDRESSED`)

- **Why public benchmarks are suspect.** VQA-RAD, SLAKE, MIMIC-CXR–derived sets, MedQA,
  PMC-VQA, PathVQA, OpenI, and PubMedQA may sit inside the model's pretraining corpus, so a
  high score can be **memorisation, not capability**. For a closed API the corpus is undisclosed,
  so contamination cannot be excluded — only **bounded** and stated.
- **Three accepted checks (any one, stated explicitly):**
  - **Cutoff vs release date** — compare the model's training cutoff against the benchmark's
    release date; a benchmark that predates the cutoff is at risk.
  - **Held-out / post-cutoff set** — evaluate on a private, institution-collected, or
    after-cutoff set the model could not have seen.
  - **Contamination probe** — canary strings, a perturbed-duplicate performance gap (score on
    verbatim items vs lightly perturbed copies), or a membership/quiz test (ask the model to
    reproduce held-out items).
- **Advise:** never write "no contamination" (or evaluate on a pre-cutoff public benchmark in
  silence) without one of the checks above; an acknowledged-but-unmitigated risk is a stated
  limitation, not a clean result.

## Prompt-sensitivity & determinism (ME5 → `PROMPT_PROVENANCE_MISSING`)

- **Outputs move with the prompt and the sampler.** Phrasing, format, the system prompt,
  temperature, top-p/top-k, and run-to-run sampling all shift results. A single-prompt
  single-run number overstates stability.
- **Closed APIs are non-deterministic even at temperature 0** — identical inputs can yield
  different outputs across calls. Treat any single-run figure as a point estimate of a
  distribution, not a fixed value.
- **Disclose (MI-CLEAR-LLM transparency):** the **exact prompt(s)** including the system prompt,
  the **decoding settings** (temperature / top-p / seed), **≥ 3 runs** with reported variance
  (e.g., mean ± SD), and a **prompt-robustness** check across **≥ 2 phrasings/formats** for the
  headline result.

## Answer-matching for VQA / classification (ME6 → `ANSWER_MATCHING_MISSING`)

- **State the matching rule.** Free-text answers must be mapped to the key by a declared rule:
  **exact** string match, **normalised** match (case/punctuation/synonym folding), or
  **LLM-as-judge**. An unspecified rule makes the accuracy unreproducible.
- **An LLM judge is itself a model.** If a model adjudicates correctness, **validate the judge
  against a human-labelled subset** and report its agreement; route judge validation to
  `/design-ai-benchmarking`. An unvalidated LLM judge can launder the system's own errors.
- **Operating discipline.** Report accuracy **at the real clinical prevalence**, not on an
  artificially balanced QA set, and state **how refusals/abstentions are scored** (counted
  wrong, excluded, or credited) — the choice can move the headline.

## Reader study for generated reports (ME7 → `READER_STUDY_MISSING`)

- **Automated metrics do not establish clinical acceptability.** Even RadGraph-F1 / CheXbert-F1
  measure agreement, not whether a clinician would act on the report safely. A deployment or
  utility claim for generated text needs a **blinded clinical reader study**.
- **Design elements:** a pre-defined **error taxonomy** (clinically significant vs insignificant;
  omission vs fabrication), a **severity scale**, and **inter-reader agreement**.
- **Route:** the rubric and the IRR design → `/design-ai-benchmarking`; the ICC/κ computation →
  `/analyze-stats`; reader and case **sizing** → `/calc-sample-size`.

## Gate mapping

The deterministic gate (`scripts/check_mllm_eval_completeness.py`) is a presence check on the
plan text, task-aware. This reference is the *why* behind each verdict:

| Axis (this doc) | Gate verdict | Severity |
|---|---|---|
| n-gram only, no clinical metric (report-gen) | `NGRAM_ONLY` | Major |
| no adjudicated reference standard (report-gen) | `REFERENCE_STANDARD_MISSING` | Major |
| no faithfulness / false-premise (report-gen, vqa) | `FAITHFULNESS_MISSING` | Major |
| public benchmark, no contamination handling | `CONTAMINATION_UNADDRESSED` | Major |
| no blinded reader study (report-gen) | `READER_STUDY_MISSING` | Major (deploy) / Minor |
| prompt / decoding / multi-run incomplete | `PROMPT_PROVENANCE_MISSING` | Minor |
| no answer-matching rule (vqa, classification) | `ANSWER_MATCHING_MISSING` | Minor |

A Major verdict is a presence gap, not proof the work is wrong — resolve it by adding the axis
to the plan (or recording, with a stated reason, why it does not apply).

## Reporting fit & hand-off

Methods / Results stub → `/write-paper`. Item-level compliance with **TRIPOD-LLM**,
**MI-CLEAR-LLM**, **CLAIM 2024** (and STARD-AI / TRIPOD+AI where a diagnostic/prognostic claim
is made) → `/check-reporting`. Reviewer-side audit of a finished manuscript uses the
`mllm_evaluation.md` (ME0–ME8) probe via `/self-review` and `/peer-review`.

## Verification notes

Each claim here is grounded in a named public method/standard or described qualitatively; no
numbers, thresholds, or dataset contents are invented.

- **n-gram metrics correlate weakly with clinical error; clinical-efficacy metrics needed** —
  Yu et al., *Patterns* 2023 (RadCliQ). Named public methods paper (matches the citation already
  vendored in the `mllm_evaluation.md` probe).
- **RadGraph-F1 (entity-relation overlap)** — Jain et al., NeurIPS Datasets & Benchmarks 2021.
  Named public methods paper.
- **CheXbert-F1 / CheXpert observation labels** — Smit et al., 2020 (CheXbert); Irvin et al.,
  2019 (CheXpert labeler). Named public methods papers; the CheXpert label set is a factual
  artifact, not invented.
- **RadCliQ as a composite** — Yu et al., *Patterns* 2023. Named public methods paper.
- **Atomic-fact faithfulness, omission-vs-fabrication, false-premise/abstention** — described as
  established evaluation principles; **MedVH** and **Med-HALT** named as instruments only (as in
  the probe), no scores invented.
- **Contamination of public benchmarks; closed-corpus unknowability; cutoff/held-out/probe
  checks (canary, perturbed-duplicate gap, membership test)** — stated as accepted principles and
  practices, qualitatively; benchmark **names** (VQA-RAD, SLAKE, MIMIC-CXR, MedQA, PMC-VQA,
  PathVQA, OpenI, PubMedQA) are factual public-dataset names, no contents reproduced.
- **Closed-API non-determinism even at temperature 0; prompt/format/sampling sensitivity** —
  described qualitatively as documented behavior; no figure attached.
- **Prompt + decoding + ≥3 runs + ≥2 phrasings disclosure** — MI-CLEAR-LLM transparency
  (named standard); the ≥3 / ≥2 conventions are this skill's own house thresholds (carried from
  SKILL.md / the ME-probe), not literature values.
- **LLM-as-judge must be validated against human labels** — stated as a methodological principle;
  judge validation routed to `/design-ai-benchmarking`.
- **Reader study for deployment/utility claims; error taxonomy, severity, IRR** — consistent with
  CLAIM 2024 / TRIPOD-LLM reporting expectations (named standards); sizing/IRR routed to
  `/calc-sample-size` and `/analyze-stats`.
- **Metrics Reloaded / CLAIM 2024 / TRIPOD-LLM / MI-CLEAR-LLM / Model Cards (Mitchell 2019) /
  Datasheets (Gebru 2021)** — named public standards, cited by name only.
