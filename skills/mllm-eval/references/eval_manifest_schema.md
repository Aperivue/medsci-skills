# eval_manifest.json — declared evaluation axes (mllm-eval)

`check_mllm_eval_completeness.py --manifest eval_manifest.json` reads the evaluation axes as
structured fields instead of searching the plan prose for keywords. A keyword search cannot read
negation or word sense ("No human evaluation was performed" mentions human evaluation); a declared
field can. The gate checks **what is declared, not that the work was done** — keep the manifest in
step with the Methods.

Start from `templates/eval_manifest.json`. Values are compared case-insensitively, with `-` and
spaces read as `_`. Every list value and enum value must be on the field's allow-list, `none`
(declared absent), or `other:<description>` for a method not listed (reported as a Minor
`UNLISTED_METHOD` and counted as covering the axis). Any other value, a wrong type, a non-finite number, or an
unknown key exits 2 and names the field. A field left out counts as not covered, like `none`.

| Field | Type | Allowed values | Verdict when not covered |
|---|---|---|---|
| `task` | string | `report_generation`, `vqa`, `classification` (no `none` or `other:`) | exit 2 if missing and no `--task` |
| `metrics.lexical` | list | `bleu`, `rouge` (also `rouge_l`, `rouge_1`, `rouge_2`), `meteor`, `cider` | — |
| `metrics.clinical` | list | `radgraph_f1`, `chexbert_f1`, `chexpert_labeler`, `radcliq`, `green` | `NGRAM_ONLY` (Major, report generation, when lexical is declared) |
| `faithfulness.methods` | list | `atomic_fact_decomposition`, `false_premise_probe`, `med_halt`, `medvh` | `FAITHFULNESS_MISSING` (Major, report generation and VQA) |
| `reference_standard.type` | string | `adjudicated_expert`; also accepted but **not** clearing: `single_unverified_report`, `model_derived_label` (SKILL.md Phase 2) | `REFERENCE_STANDARD_MISSING` (Major, report generation) |
| `benchmarks` | list or string | any benchmark names, or `none` | — (a non-empty list turns on the contamination check) |
| `contamination.methods` | list | `cutoff_vs_release_date`, `held_out_set`, `canary`, `perturbed_duplicate_gap`, `membership_test` | `CONTAMINATION_UNADDRESSED` (Major, when benchmarks are declared) |
| `reader_study` | object | `performed` (bool), `blinded` (bool), `n_readers` (int ≥ 1, recorded, not gated) | `READER_STUDY_MISSING` unless `performed` and `blinded` are both `true` (report generation): Major if `claims.clinical_deployment` is `true`, else Minor |
| `prompt.template_released` | bool | | `PROMPT_PROVENANCE_MISSING` (Minor) |
| `decoding` | object | `temperature` (finite number ≥ 0), `greedy` (bool); `seed` (int ≥ 0) and `top_p` (0–1] are recorded, not gated | `PROMPT_PROVENANCE_MISSING` (Minor) without `temperature` or `greedy: true` |
| `runs.n` | int ≥ 1 | | `PROMPT_PROVENANCE_MISSING` (Minor) below 3 runs (Phase 4) |
| `answer_matching.method` | string | `exact`, `normalised` (or `normalized`), `llm_as_judge` | `ANSWER_MATCHING_MISSING` (Minor, VQA and classification) |
| `claims.clinical_deployment` | bool | | raises `READER_STUDY_MISSING` to Major |
| `notes` | any | free text, not read | — |

Every value that clears an axis is named in `evaluation_axes.md` (the reference standard in
SKILL.md Phase 2). An LLM judge must itself be validated against a human-labelled subset; the gate
does not check that.

An `other:<description>` value counts as covering its axis, the reference standard included,
and is reported only as a Minor `UNLISTED_METHOD`: read each one by eye. `other: none` is read as
`none`.
