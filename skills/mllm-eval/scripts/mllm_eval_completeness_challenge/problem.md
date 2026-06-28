# Challenge card — MLLM evaluation completeness (mllm-eval)

## Problem
An LLM/MLLM clinical evaluation is only as good as what it measures. The recurrent
failures: report quality reported with **BLEU/ROUGE only** (weakly correlated with
clinical correctness — a report can score well while inverting laterality; Yu et al.,
*Patterns* 2023), **no faithfulness / hallucination** evaluation (a fluent answer is not
a faithful one), an **unadjudicated reference standard**, a public benchmark scored with
**no pretraining-contamination** statement (a high score may be memorisation), and a
deployment claim with **no reader study**. These pass a prose read.

## What the gate does
`scripts/check_mllm_eval_completeness.py` is a conservative, task-aware presence linter on
the evaluation plan / methods. It flags the missing axes (`NGRAM_ONLY`,
`FAITHFULNESS_MISSING`, `REFERENCE_STANDARD_MISSING`, `CONTAMINATION_UNADDRESSED`,
`READER_STUDY_MISSING`, `PROMPT_PROVENANCE_MISSING`, `ANSWER_MATCHING_MISSING`). It checks
the protocol's coverage, not the results, and is model-agnostic (closed API or open
weights).

## Fixture (synthetic only — no real model)
- `fixture/plan_bad.md` — report generation scored with BLEU/ROUGE on SLAKE/VQA-RAD; no
  faithfulness, no adjudicated reference, no contamination check.
- `fixture/plan_good.md` — RadGraph-F1/CheXbert-F1 + faithfulness + adjudicated reference +
  contamination check + prompt/temperature/multi-run + reader study.

## Expected (`verify.sh`, network-free)
- `plan_bad` flags `NGRAM_ONLY` + `FAITHFULNESS_MISSING` + `REFERENCE_STANDARD_MISSING` +
  `CONTAMINATION_UNADDRESSED` (exit 1).
- `plan_good` passes (exit 0).
