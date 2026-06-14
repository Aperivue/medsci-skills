# Reverse-engineering progress ledger

One row per completed loop iteration. The loop appends here in Step E.
`Sources` lists `record_id`s (defined in `_corpus/manifest.json`, gitignored).

| # | Date | Batch (record_ids) | Improvement | Target skill | Codex (kept/total) | Branch | Status |
|---|------|--------------------|-------------|--------------|--------------------|--------|--------|
| 0 | 2026-06-11 | — | Infrastructure: PLAYBOOK, licensing firewall, manifest schema, helpers | reverse_engineer/ | — | feat/reverse-engineer-infra | infra only |
| 1 | 2026-06-14 | meningioma_radiomics_sr, breast_cancer_ml_pred, pe_3d_dl_detection, eswl_stonefree_ai_sr, ihd_xai_transfer (5× F1000Research, CC-BY-4.0) | New `exemplar_reviews/optimistic_validation_reporting.md` — best-fold metrics w/o cross-fold CI/SD, unstated decision threshold, accuracy under undisclosed class rebalancing | peer-review | 3/3 (2 SUGGEST stat-precision + 1 NIT xref folded in; 0 blocker) | feat/re-loop-iter1-medai-reviews | committed |
| 2 | 2026-06-14 | (same 5 records as iter 1) | New probe section **AO5 — optimistic / non-reproducible performance reporting** in `domain-probes/ai_overclaiming.md` (best-fold/CI · operating point · prevalence-representative metrics · code-vs-claims), vendored byte-identical to self-review; exemplar cross-ref AO4→AO5 | peer-review + self-review | 3/3 (2 SUGGEST: PPV/NPV prevalence-dependence, AO4/AO5 boundary; 1 NIT count; 0 blocker) | feat/re-loop-iter1-medai-reviews | committed |
| 3 | 2026-06-14 | (same 5 records' reviewer behavior + public instrument item sets) | `reviewer_calibration/compliance_floor.md` — new **AI/radiomics methodological-quality & RoB instrument** floor (PROBAST+AI, METRICS/RQS, APPRAISE-AI), kept distinct from reporting counterparts CLEAR/DECIDE-AI | peer-review | 5/5 (2 BLOCKER folded: CLEAR/DECIDE-AI are reporting not RoB → re-taxonomized; APPRAISE-AI flagged unverified → web-verified JAMA Netw Open 2023 + sourced; 3 SUGGEST/NIT on scope wording) | feat/re-loop-iter1-medai-reviews | committed |

## Queue health

- Pending records in `doi_lists/queue.txt`: 5 F1000Research records consumed in iterations 1–3 (kept as resolved audit trail). Add the next batch at acquire time.
- Next priority item (per PLAYBOOK priority order): **rotate domain to avoid over-fitting to medical-AI. Candidates: #3 `write-paper` exemplar_methods/results/discussion from radiology/biostatistics OA articles, or #2 a compliance floor for a non-AI study type. The medical-AI review seam (exemplar + AO5 probe + appraisal-instrument floor) is now well covered.**
