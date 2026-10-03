# eval_manifest.json — declared evaluation axes (mllm-eval)

`check_mllm_eval_completeness.py --manifest eval_manifest.json` reads the evaluation axes as
structured fields instead of searching the plan prose for keywords. A keyword search cannot read
negation or word sense ("No human evaluation was performed" mentions human evaluation); a declared
field can. The gate checks **what is declared, not that the work was done** — keep the manifest in
step with the Methods.

Start from `templates/eval_manifest.json`. Values are compared case-insensitively, with `-` and
spaces read as `_`. Every list value and enum value must be on the field's allow-list, `none`
(declared absent), or `other:<description>` for a method not listed (reported as a Minor
`UNLISTED_METHOD` and counted as covering the axis). Any other value, a wrong type, or an unknown
key exits 2 and names the field. A field left out counts as not covered, like `none`.

| Field | Type | Allowed values | Verdict when not covered |
|---|---|---|---|
| `task` | string | `report_generation`, `vqa`, `classification` | exit 2 if missing and no `--task` |
| `metrics.lexical` | list | `bleu`, `rouge`, `rouge_l`, `meteor`, `cider` | — |
| `metrics.clinical` | list | `radgraph_f1`, `chexbert_f1`, `chexpert_labeler`, `radcliq`, `green` | `NGRAM_ONLY` (Major, report generation, when lexical is declared) |
| `faithfulness.methods` | list | `atomic_fact_check`, `expert_hallucination_rating`, `false_premise_probe`, `med_halt`, `medvh` | `FAITHFULNESS_MISSING` (Major, report generation and VQA) |
| `reference_standard.type` | string | `radiologist_report`, `expert_consensus`, `adjudicated_panel`, `pathology`, `clinical_follow_up`, `benchmark_label` | `REFERENCE_STANDARD_MISSING` (Major, report generation) |
| `benchmarks` | list | any benchmark names | — (a non-empty list turns on the contamination check) |
| `contamination.methods` | list | `post_cutoff_split`, `private_holdout`, `canary`, `membership_inference`, `ngram_overlap_audit` | `CONTAMINATION_UNADDRESSED` (Major, when benchmarks are declared) |
| `reader_study` | object | `performed` (bool), `n_readers` (int ≥ 1), `blinded` (bool) | `READER_STUDY_MISSING` when `performed` is not `true` (report generation): Major if `claims.clinical_deployment` is `true`, else Minor |
| `prompt.template_released` | bool | | `PROMPT_PROVENANCE_MISSING` (Minor) |
| `decoding` | object | `temperature` (number ≥ 0), `greedy` (bool), `seed` (int ≥ 0), `top_p` (0–1] | `PROMPT_PROVENANCE_MISSING` (Minor) without `temperature` or `greedy: true` |
| `runs.n` | int ≥ 1 | | `PROMPT_PROVENANCE_MISSING` (Minor) below 3 runs (Phase 4) |
| `answer_matching.method` | string | `exact`, `normalised`, `semantic`, `llm_judge`, `clinician_adjudicated` | `ANSWER_MATCHING_MISSING` (Minor, VQA and classification) |
| `claims.clinical_deployment` | bool | | raises `READER_STUDY_MISSING` to Major |
| `notes` | any | free text, not read | — |

Every listed metric and method is described, with its source, in `evaluation_axes.md`.
