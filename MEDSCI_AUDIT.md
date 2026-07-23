# MedSci-Audit

**MedSci-Audit** is the named deterministic verification layer inside [MedSci Skills](README.md): a suite of **80 stdlib-only detectors** that catch fabricated, drifted, or non-compliant content in a medical manuscript *before* it reaches a reviewer. The detectors run inside the skills that own them (e.g. `/self-review`, `/check-reporting`, `/sync-submission`, `/verify-refs`); this document names and indexes that suite so it can be cited and reasoned about as one thing.

The detectors are **deterministic** — same input, same verdict, no LLM in the decision path — so a flagged defect is reproducible and a clean run is meaningful.

## What it is (and is not)

MedSci-Audit detectors **find** integrity problems; they deliberately do **not** auto-fix the load-bearing ones. The split:

- **Anti-hallucination (never auto-fixed).** Fabricated or mismatched citations, numbers that do not reconcile across artifacts, and pool/cohort arithmetic that does not add up are reported for a human to correct against the source — an AI must not "repair" a number it may have invented. These are marked `fixable_by_ai: false` where the skill surfaces them.
- **Mechanical hygiene (safe to fix).** Style/format and structural issues (classical-style lint, checklist routing) can be addressed in place.

## The detector suite

The authoritative, machine-readable list is **[`metadata/detectors_catalog.json`](metadata/detectors_catalog.json)** — generated from the detectors under `skills/*/scripts/` by [`scripts/gen_detectors_catalog_json.py`](scripts/gen_detectors_catalog_json.py) and CI-gated with `--check` (it uses the same discovery glob as `validate_catalog_consistency.py`, so its `detector_count` always equals `catalog_counts.json::integrity_detectors`). Do not hand-maintain a parallel list; read the JSON.

The 80 detectors fall into six audit families:

The per-family rows below are the **complete** enumeration, not a sample, and are CI-gated
against `metadata/detectors_catalog.json` (`validate_catalog_consistency.py`): each row's count
must equal that family's size in the catalog, and the names listed must be exactly that family's
members. The gate exists because the total and the rows drifted apart once — the sentence above
said 80 while these rows enumerated 72.

| Family | Count | Detectors |
|--------|------:|----------|
| Numerical, cohort & pool arithmetic | 11 | `check_cohort_arithmetic`, `check_effect_stability`, `check_table_percentages`, `check_reported_p_from_counts`, `check_dta_denominators`, `check_paired_difference_estimator`, `check_pool_consistency`, `check_artifact_coverage`, `check_rounded_delta`, `detect_copy_divergence`, `derive_figure_legend_counts` |
| Citation & reference integrity | 8 | `verify_refs`, `check_citation_keys`, `check_xref`, `check_csl_render`, `check_reference_adequacy`, `check_placeholders`, `check_reference_duplication`, `check_bib_title_markup` |
| Style & review-process integrity | 24 | `check_classical_style`, `check_generated_code`, `check_panel_diversity`, `check_reviewer_team_consistency`, `check_paren_spans`, `check_training_hygiene`, `check_editorial_impression`, `check_emphasis_density`, `check_response_claims`, `check_pdf_injection`, `check_marked_manuscript`, `check_self_improvement_claims`, `check_slide_tells`, `check_deck_budget`, `check_density_complaint`, `check_review_request_types`, `check_review_length`, `check_review_boxes`, `check_aphorism_density`, `check_baseline_drift`, `check_perspective_structure`, `check_rewrite_fidelity`, `check_rhetorical_density`, `check_sentence_variety` |
| Confounding, scope & estimand contracts | 7 | `check_scope_coherence`, `check_incorporation_bias`, `check_confounding_completeness`, `check_nested_group_comparison`, `check_claim_artifact`, `check_null_calibration`, `check_analysis_definitions` |
| Reporting compliance | 15 | `check_framework_naming`, `check_checklist_exists`, `check_checklist_version`, `check_prisma_figure`, `check_figure_citation`, `check_wordcount_cap`, `check_disclosure_availability`, `check_summary_box`, `check_supplement_hygiene`, `check_citation_order`, `check_model_card_complete`, `check_mllm_eval_completeness`, `check_explainability_report`, `check_uncertainty_reporting`, `check_exclusion_code_validity` |
| Data preparation & validation | 15 | `check_structural_zero`, `check_reverse_coding`, `check_asset_anonymization`, `check_cross_artifact_stale`, `check_checklist_dump_leak`, `check_binning_consistency`, `check_cv_leakage`, `check_split_leakage`, `check_metric_reporting`, `check_preprocessing_leakage`, `check_radiomics_ml`, `check_separation`, `check_contribution_safety`, `check_portal_field_residue`, `check_dataset_profile` |

## The artifact contract

Every detector that emits JSON names itself in the envelope:

```json
{
  "detector": "check_reported_p_from_counts",
  "manuscript": "manuscript.md",
  "claims": [ ... ]
}
```

The filename is chosen at the call site (`--out qc/anything.json`) and therefore cannot
identify the check that produced a finding. Without the key, two runs of one detector under
different filenames read as two detectors, and a run under an unexpected filename reads as
none — so any consumer that aggregates a project's `qc/` directory (an audit trail, a
dashboard, a precision ledger) is guessing. `scripts/check_detector_envelopes.py` enforces
the key in CI, so a new detector cannot ship without it.

## Evidence

The suite's evaluation evidence and its current size are **two separate facts** — they are reported at different versions, and should not be collapsed into a single "N detectors, validated by E1/E7" claim.

- **Current detector catalog: 80** (the enumerated list in `metadata/detectors_catalog.json`).
- **Canonical evaluation runs are v3.8-era and validate the then-current subset.** The seeded-defect benchmark (**E1**) is built on **19 `DefectSpec` rows / 17 deterministic injectors** ([`evaluation/h1_seeded_defects/DEFECT_RATIONALE.md`](evaluation/h1_seeded_defects/DEFECT_RATIONALE.md)), and the coverage inventory (**E7**) is **n=21** ([`evaluation/runs/canonical/E7/limitations.md`](evaluation/runs/canonical/E7/limitations.md)). Both predate the A1–A4 detectors that brought the catalog to 24. The frozen canonical runs under [`evaluation/runs/canonical/`](evaluation/runs/canonical/) are pinned to the published methods artifacts and are intentionally left unchanged.
- **Detectors added since v3.8 are covered by their own per-skill CI tests** (e.g. `skills/sync-submission/tests/test_asset_anonymization.sh`, `skills/check-reporting/tests/test_checklist_version.sh`, `skills/write-paper/tests/test_placeholders.sh`), run on every push via [`.github/workflows/validate.yml`](.github/workflows/validate.yml) — not by a re-run of the frozen E1/E7. A refresh of E1/E7 to cover all 80 detectors is a separate evaluation effort and is **not** part of this registry — it is pre-registered as a protocol in [`evaluation/REFRESH_PROTOCOL.md`](evaluation/REFRESH_PROTOCOL.md), which also states why an injection benchmark cannot report precision, and why its clean-manuscript arm should not be run to completion without an external adjudicator.

For the broader evaluation harness (E1–E9: seeded-defects, LLM baseline, cost/time, fresh-clone reproducibility, audit-trail completeness, portability, inventory, drift, self-review convergence), see [`evaluation/`](evaluation/).

## Cite

If you use MedSci-Audit (or MedSci Skills) in your research, cite via [`CITATION.cff`](CITATION.cff). The methods manuscript is [`paper.md`](paper.md); the archived release is on Zenodo (concept DOI [10.5281/zenodo.20155321](https://doi.org/10.5281/zenodo.20155321), always resolving to the latest version).
