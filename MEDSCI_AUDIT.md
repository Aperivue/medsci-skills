# MedSci-Audit

**MedSci-Audit** is the named deterministic verification layer inside [MedSci Skills](README.md): a suite of **25 stdlib-only detectors** that catch fabricated, drifted, or non-compliant content in a medical manuscript *before* it reaches a reviewer. The detectors run inside the skills that own them (e.g. `/self-review`, `/check-reporting`, `/sync-submission`, `/verify-refs`); this document names and indexes that suite so it can be cited and reasoned about as one thing.

The detectors are **deterministic** — same input, same verdict, no LLM in the decision path — so a flagged defect is reproducible and a clean run is meaningful.

## What it is (and is not)

MedSci-Audit detectors **find** integrity problems; they deliberately do **not** auto-fix the load-bearing ones. The split:

- **Anti-hallucination (never auto-fixed).** Fabricated or mismatched citations, numbers that do not reconcile across artifacts, and pool/cohort arithmetic that does not add up are reported for a human to correct against the source — an AI must not "repair" a number it may have invented. These are marked `fixable_by_ai: false` where the skill surfaces them.
- **Mechanical hygiene (safe to fix).** Style/format and structural issues (classical-style lint, checklist routing) can be addressed in place.

## The detector suite

The authoritative, machine-readable list is **[`metadata/detectors_catalog.json`](metadata/detectors_catalog.json)** — generated from the detectors under `skills/*/scripts/` by [`scripts/gen_detectors_catalog_json.py`](scripts/gen_detectors_catalog_json.py) and CI-gated with `--check` (it uses the same discovery glob as `validate_catalog_consistency.py`, so its `detector_count` always equals `catalog_counts.json::integrity_detectors`). Do not hand-maintain a parallel list; read the JSON.

The 25 detectors fall into six audit families:

| Family | Count | Examples |
|--------|------:|----------|
| Numerical, cohort & pool arithmetic | 5 | `check_cohort_arithmetic`, `check_pool_consistency`, `check_artifact_coverage`, `detect_copy_divergence` |
| Citation & reference integrity | 6 | `verify_refs`, `check_citation_keys`, `check_xref`, `check_csl_render`, `check_reference_adequacy`, `check_placeholders` |
| Style & review-process integrity | 4 | `check_classical_style`, `check_generated_code`, `check_panel_diversity`, `check_reviewer_team_consistency` |
| Confounding, scope & estimand contracts | 3 | `check_scope_coherence`, `check_confounding_completeness`, `check_claim_artifact` |
| Reporting compliance | 4 | `check_framework_naming`, `check_checklist_exists`, `check_checklist_version`, `check_prisma_figure` |
| Data preparation & validation | 3 | `check_structural_zero`, `check_asset_anonymization`, `check_cross_artifact_stale` |

## Evidence

The suite's evaluation evidence and its current size are **two separate facts** — they are reported at different versions, and should not be collapsed into a single "25 detectors, validated by E1/E7" claim.

- **Current detector catalog: 25** (the enumerated list in `metadata/detectors_catalog.json`).
- **Canonical evaluation runs are v3.8-era and validate the then-current subset.** The seeded-defect benchmark (**E1**) is built on **19 `DefectSpec` rows / 17 deterministic injectors** ([`evaluation/h1_seeded_defects/DEFECT_RATIONALE.md`](evaluation/h1_seeded_defects/DEFECT_RATIONALE.md)), and the coverage inventory (**E7**) is **n=21** ([`evaluation/runs/canonical/E7/limitations.md`](evaluation/runs/canonical/E7/limitations.md)). Both predate the A1–A4 detectors that brought the catalog to 24. The frozen canonical runs under [`evaluation/runs/canonical/`](evaluation/runs/canonical/) are pinned to the published methods artifacts and are intentionally left unchanged.
- **Detectors added since v3.8 are covered by their own per-skill CI tests** (e.g. `skills/sync-submission/tests/test_asset_anonymization.sh`, `skills/check-reporting/tests/test_checklist_version.sh`, `skills/write-paper/tests/test_placeholders.sh`), run on every push via [`.github/workflows/validate.yml`](.github/workflows/validate.yml) — not by a re-run of the frozen E1/E7. A refresh of E1/E7 to cover all 25 detectors is a separate evaluation effort and is **not** part of this registry.

For the broader evaluation harness (E1–E9: seeded-defects, LLM baseline, cost/time, fresh-clone reproducibility, audit-trail completeness, portability, inventory, drift, self-review convergence), see [`evaluation/`](evaluation/).

## Cite

If you use MedSci-Audit (or MedSci Skills) in your research, cite via [`CITATION.cff`](CITATION.cff). The methods manuscript is [`paper.md`](paper.md); the archived release is on Zenodo (concept DOI [10.5281/zenodo.20155321](https://doi.org/10.5281/zenodo.20155321), always resolving to the latest version).
