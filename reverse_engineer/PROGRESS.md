# Reverse-engineering progress ledger

One row per completed loop iteration. The loop appends here in Step E.
`Sources` lists `record_id`s (defined in `_corpus/manifest.json`, gitignored).

| # | Date | Batch (record_ids) | Improvement | Target skill | Codex (kept/total) | Branch | Status |
|---|------|--------------------|-------------|--------------|--------------------|--------|--------|
| 0 | 2026-06-11 | — | Infrastructure: PLAYBOOK, licensing firewall, manifest schema, helpers | reverse_engineer/ | — | feat/reverse-engineer-infra | infra only |
| 1 | 2026-06-14 | meningioma_radiomics_sr, breast_cancer_ml_pred, pe_3d_dl_detection, eswl_stonefree_ai_sr, ihd_xai_transfer (5× F1000Research, CC-BY-4.0) | New `exemplar_reviews/optimistic_validation_reporting.md` — best-fold metrics w/o cross-fold CI/SD, unstated decision threshold, accuracy under undisclosed class rebalancing | peer-review | 3/3 (2 SUGGEST stat-precision + 1 NIT xref folded in; 0 blocker) | feat/re-loop-iter1-medai-reviews | committed |
| 2 | 2026-06-14 | (same 5 records as iter 1) | New probe section **AO5 — optimistic / non-reproducible performance reporting** in `domain-probes/ai_overclaiming.md` (best-fold/CI · operating point · prevalence-representative metrics · code-vs-claims), vendored byte-identical to self-review; exemplar cross-ref AO4→AO5 | peer-review + self-review | 3/3 (2 SUGGEST: PPV/NPV prevalence-dependence, AO4/AO5 boundary; 1 NIT count; 0 blocker) | feat/re-loop-iter1-medai-reviews | committed |
| 3 | 2026-06-14 | (same 5 records' reviewer behavior + public instrument item sets) | `reviewer_calibration/compliance_floor.md` — new **AI/radiomics methodological-quality & RoB instrument** floor (PROBAST+AI, METRICS/RQS, APPRAISE-AI), kept distinct from reporting counterparts CLEAR/DECIDE-AI | peer-review | 5/5 (2 BLOCKER folded: CLEAR/DECIDE-AI are reporting not RoB → re-taxonomized; APPRAISE-AI flagged unverified → web-verified JAMA Netw Open 2023 + sourced; 3 SUGGEST/NIT on scope wording) | feat/re-loop-iter1-medai-reviews | merged #128 |
| 4 | 2026-06-14 | ii_breast_us_dl, ii_pnet_radiomics_nomogram, ii_prostate_mri_biopsy_dta, ii_ct_ai_stenosis_vs_ica, plosmed_nsaid_malformation_cohort (5× CC-BY-4.0; Insights into Imaging + PLoS Medicine) | New **`write-paper/exemplar_results/`** set (3 structure models + README): diagnostic-accuracy/STARD, AI-validation/TRIPOD+AI·CLAIM, observational-cohort/STROBE — mirrors `exemplar_methods/` in Methods order; report-only; wired into Phase 4 | write-paper | 5/5 (1 BLOCKER: "paragraph-for-paragraph" overstated → "Methods order"; 3 SUGGEST: threshold-not-test-optimized, error-analysis report-only, STROBE meta-interpretation removed; 1 NIT xref path) | feat/re-loop-iter4-writepaper-exemplar | committed |

## Queue health

- Records in `doi_lists/queue.txt`: iter1–3 F1000 batch consumed + commented `# [consumed #128]`; iter4 consumed 5 Insights into Imaging + PLoS Medicine CC-BY records. Add the next batch at acquire time.
- Next priority item (per PLAYBOOK): **#3 continues — `write-paper/exemplar_discussion/` (the last unbuilt write-paper exemplar set), or rotate to #4 `analyze-stats/exemplar_tables/`. Domain rotated to radiology/clinical OA in iter4; keep rotating.**
