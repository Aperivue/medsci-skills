---
name: mllm-eval
description: >
  Design or audit a model-agnostic evaluation harness for an LLM or multimodal LLM on a clinical task
  (radiology report generation, visual question answering, clinical text extraction/classification) —
  the adjudicated reference standard, clinical-efficacy metrics (RadGraph-F1 / CheXbert-F1 beyond
  BLEU/ROUGE), faithfulness and hallucination, pretraining-contamination of public benchmarks,
  prompt-sensitivity and determinism, answer-matching, and a reader study — and gate the plan for those
  axes. Works on a closed API or open weights. Never fabricates outputs or scores, and never reports
  n-gram overlap as clinical correctness.
triggers: MLLM evaluation, LLM evaluation, multimodal LLM, report generation, radiology report generation, visual question answering, VQA, RadGraph, CheXbert, faithfulness, hallucination, prompt sensitivity, contamination, GPT, LLaVA-Med, clinical LLM, medical VLM, reader study for reports
tools: Read, Write, Edit, Bash, Grep, Glob
model: inherit
---

# MLLM-Eval Skill

## Purpose

This skill makes an **LLM / MLLM clinical evaluation defensible**: a real adjudicated reference standard,
faithfulness measured not assumed, clinical-efficacy metrics beyond n-gram overlap, a pretraining-
contamination check, prompt-sensitivity disclosed, and a reader study where text is generated. It is
**model-agnostic** — every check applies to a closed API and to open weights — and **read-only** (an
advisory design/audit skill): it audits the evaluation design and **specifies and routes** the
clinical-efficacy metrics (RadGraph-F1 / CheXbert-F1 via their published extractors) rather than running
the model or computing the metrics itself.

It is the LLM/MLLM **evaluation-design counterpart** in the lane — an auditor that hands the specified
metrics to their extractors and `/analyze-stats`, parallel to how `/model-validation` audits an imaging
model's design (the imaging metrics themselves are computed by `/model-evaluation`). The reviewer-side
audit of a finished manuscript uses the `mllm_evaluation.md` (ME0–ME8) probe via `/self-review` and
`/peer-review`; this skill is the author-side harness design. It routes the reader study to
`/design-ai-benchmarking`, the sizing to `/calc-sample-size`, and TRIPOD-LLM / MI-CLEAR-LLM compliance to
`/check-reporting`.

## When to use
- You are designing or auditing an evaluation of an LLM/MLLM on a clinical task and want it to cover the
  axes a reviewer will check (reference standard, faithfulness, contamination, prompt sensitivity, reader
  study).

## When NOT to use
- AI-vs-human-expert benchmark with a rated rubric → `/design-ai-benchmarking`.
- Imaging prediction/segmentation model → `/model-evaluation` + `/model-validation`.
- Image-to-image generative model → the `image_synthesis` probe.
- Training / serving the LLM → out of scope.
- Item-level TRIPOD-LLM / MI-CLEAR-LLM audit of a finished manuscript → `/check-reporting`.

## Workflow

### Phase 1 — Pin the task, model, comparator, decoding (ME0)
State the task (report generation / VQA / extraction-classification), the exact model + version/date
(closed API or open-weights id), the decoding settings (temperature, seed, max tokens), and what the
outputs are scored against.

### Phase 2 — Reference standard + metrics (ME1, ME2)
Require an **adjudicated expert reference** (not a single unverified report or a model-derived label).
For report generation, report a **clinical-efficacy metric** — **RadGraph-F1** (Jain et al., NeurIPS
2021) or **CheXbert-F1** (Smit et al., 2020), or the composite **RadCliQ** (Yu et al., *Patterns* 2023)
— **alongside** any BLEU/ROUGE, with CIs. For VQA/classification, report accuracy at the
real prevalence with a stated answer-matching rule.

### Phase 3 — Faithfulness + contamination (ME3, ME4)
Add an **atomic-fact faithfulness** measure + a **false-premise / abstention** probe (MedVH, Med-HALT) —
report a hallucination rate, not just accuracy. For any public benchmark (VQA-RAD, SLAKE, MIMIC-CXR-
derived, MedQA), add a **contamination** statement: training cutoff vs benchmark release, a held-out /
post-cutoff set, or a contamination probe.

### Phase 4 — Prompt sensitivity + reader study (ME5, ME7)
Disclose the **exact prompt(s)**, temperature/seed, **≥ 3 runs** with variance, and a prompt-robustness
check. For a deployment/utility claim, design a **blinded reader study** with an error taxonomy (route
the rubric/IRR to `/design-ai-benchmarking`, ICC/κ to `/analyze-stats`, sizing to `/calc-sample-size`).

### Phase 5 — Gate the plan (deterministic)
```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/check_mllm_eval_completeness.py \
  --plan plan.md --task report_generation|vqa|classification --strict
```
`NGRAM_ONLY` / `FAITHFULNESS_MISSING` / `REFERENCE_STANDARD_MISSING` / `CONTAMINATION_UNADDRESSED` /
`READER_STUDY_MISSING` must be resolved.

### Phase 6 — Hand off
Methods/Results → `/write-paper`; compliance (TRIPOD-LLM / MI-CLEAR-LLM) → `/check-reporting`; reviewer
audit → `/self-review` (loads ME0–ME8).

## Anti-Hallucination

- **Never fabricate model outputs, reference labels, or metric scores.** Compute only what the supplied
  outputs allow; if a reference standard or outputs are missing, say so and stop.
- **Never report n-gram overlap (BLEU/ROUGE) as clinical correctness** — pair it with a clinical-efficacy
  metric, and flag the n-gram score for what it is.
- **Never claim "no contamination" without a stated check** when a public benchmark is used.
- If a metric (RadGraph-F1 / CheXbert-F1) or its extractor is uncertain, flag `[VERIFY]` and ask rather
  than inventing a number.

## Deterministic gate
`scripts/check_mllm_eval_completeness.py` — task-aware presence gate on the evaluation plan (stdlib,
network-free). Reproducible challenge:
`bash ${CLAUDE_SKILL_DIR}/scripts/mllm_eval_completeness_challenge/verify.sh`.

## Boundaries

```
mllm-eval (this skill: harness design + completeness gate, model-agnostic)
  ├─ design-ai-benchmarking (reader-study rubric / IRR)
  ├─ calc-sample-size (reader + case sizing)
  ├─ write-paper + check-reporting (TRIPOD-LLM / MI-CLEAR-LLM)
  └─ self-review / peer-review (ME0–ME8 reviewer probe)
```
