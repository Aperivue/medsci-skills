# Reverse-engineering progress ledger

One row per completed loop iteration. The loop appends here in Step E.
`Sources` lists `record_id`s (defined in `_corpus/manifest.json`, gitignored).

| # | Date | Batch (record_ids) | Improvement | Target skill | Codex (kept/total) | Branch | Status |
|---|------|--------------------|-------------|--------------|--------------------|--------|--------|
| 0 | 2026-06-11 | — | Infrastructure: PLAYBOOK, licensing firewall, manifest schema, helpers | reverse_engineer/ | — | feat/reverse-engineer-infra | infra only |
| 1 | 2026-06-14 | meningioma_radiomics_sr, breast_cancer_ml_pred, pe_3d_dl_detection, eswl_stonefree_ai_sr, ihd_xai_transfer (5× F1000Research, CC-BY-4.0) | New `exemplar_reviews/optimistic_validation_reporting.md` — best-fold metrics w/o cross-fold CI/SD, unstated decision threshold, accuracy under undisclosed class rebalancing | peer-review | 3/3 (2 SUGGEST stat-precision + 1 NIT xref folded in; 0 blocker) | feat/re-loop-iter1-medai-reviews | committed |

## Queue health

- Pending records in `doi_lists/queue.txt`: 5 F1000Research records consumed in iteration 1 (kept as resolved audit trail). Add the next batch at acquire time.
- Next priority item (per PLAYBOOK priority order): **#1 continues — a matching peer-review/self-review *probe section* (e.g., a validation-reporting probe: best-fold/CI, operating-point, prevalence-representative metrics) OR `reviewer_calibration/` compliance floors (#2). The new exemplar pairs naturally with a probe section as the next iteration.**
