<!-- AUTO-GENERATED from skills/mllm-eval/SKILL.md by scripts/gen_skill_docs.py. Do not edit by hand. -->

# mllm-eval

> Design or audit a model-agnostic evaluation harness for an LLM or multimodal LLM on a clinical task (radiology report generation, visual question answering, clinical text extraction/classification) — the adjudicated reference standard, clinical-efficacy metrics (RadGraph-F1 / CheXbert-F1 beyond BLEU/ROUGE), faithfulness and hallucination, pretraining-contamination of public benchmarks, prompt-sensitivity and determinism, answer-matching, and a reader study — and gate the plan for those axes. Works on a closed API or open weights. Never fabricates outputs or scores, and never reports n-gram overlap as clinical correctness.

**Invoke:** `/mllm-eval` · **Tools:** Read, Write, Edit, Bash, Grep, Glob · **Model:** inherit

## When to use

`mllm-eval` activates on requests such as: MLLM evaluation, LLM evaluation, multimodal LLM, report generation, radiology report generation, visual question answering, VQA, RadGraph, CheXbert, faithfulness, hallucination, prompt sensitivity, contamination, GPT, LLaVA-Med, clinical LLM, medical VLM, reader study for reports.

## Quality Card

**Purpose** — Make an LLM/MLLM clinical evaluation defensible — a real adjudicated reference standard, faithfulness measured not assumed, clinical-efficacy metrics beyond n-gram overlap, a pretraining-contamination check, prompt-sensitivity disclosed, and a reader study where text is generated — and gate the plan for those axes.

**Safety boundaries**

- Model-agnostic and read-only: it never runs or fine-tunes the model; it audits the eval design and specifies / routes the clinical-efficacy metrics (RadGraph-F1 / CheXbert-F1 via their published extractors) rather than computing them itself.
- It never converts BLEU/ROUGE into a clinical-correctness claim, and never asserts no contamination without a stated check.

**Known limitations**

- RadGraph-F1 / CheXbert-F1 require their published extractors; the skill specifies and routes to them but does not vendor model weights.
- Closed-API non-determinism and undisclosed pretraining corpora cap how strongly contamination can be excluded.

**Validation**

- `python3 scripts/check_mllm_eval_completeness.py --plan <plan.md> --task report_generation|vqa|classification --strict`
- `bash scripts/mllm_eval_completeness_challenge/verify.sh  # deterministic, network-free`

**Evidence** — `ci_validator`

## Bundled resources

**Scripts** (`skills/mllm-eval/scripts/`):

- `check_mllm_eval_completeness.py`
- `mllm_eval_completeness_challenge/` (4 files)

## Source

Canonical definition: [`skills/mllm-eval/SKILL.md`](../../skills/mllm-eval/SKILL.md)

---

*Part of [MedSci Skills](../../README.md) — Claude Code skills for the medical research lifecycle. This page is generated from the skill's `SKILL.md`; edit that file and re-run `scripts/gen_skill_docs.py`.*
