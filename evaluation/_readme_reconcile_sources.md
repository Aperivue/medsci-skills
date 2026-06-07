# README "Live Demos" reconcile — number provenance (v3.8 Option A)

Every README Live-Demos number below is re-derived from a QC/result artifact,
not hand-typed. Body word counts are measured by stripping headings, table
lines, and the References section, then counting `\b[\w'-]+\b`
(`evaluation/_readme_reconcile_sources` method; reproducible).

## Demo 1 — Wisconsin BC
- STARD compliance **60.9% (14/23 applicable)** — `demo/01_wisconsin_bc/qc/reporting_checklist.md` L22 ("PRESENT / applicable = 14 / 23 = 60.9%"). (was: 82.1% 23/28)
- Self-review **initial 82 REVISE (1 major/1 minor) → final 88 PASS (0 major/1 minor), 1 fix iteration** — `qc/self_review.md` L9–L10, L12–L15. (was: 83/100, 2 iter, initial 74, 4 major/5 minor)
- Body prose **~1,800 words** — strip method on `manuscript/manuscript.md` (1,794). (was: ~1,900)
- STARD flow figure path **figures/stard_flow.svg** (file is at demo-root `figures/`, not `analysis/figures/`).
- Confusion matrices exist at **analysis/figures/confusion_matrices.png** (added).
- presentation.pptx and submission/cover_letter **do not exist** → rows removed.

## Demo 2 — BCG Vaccine
- Pooled **RR 0.489 (95% CI 0.344–0.696)** — `analysis/tables/meta_results.csv` (pooled_RR 0.4894, lci 0.3441, uci 0.6962). (unchanged)
- PRISMA compliance **57.1% (24/42 applicable)** — `qc/reporting_checklist.md` L20, L26. (was: 77.8% 21/27). Note: the target table's "61.9% (26/42) after fix" is NOT present in the current checklist artifact, so the QC-substantiated 57.1% is used.
- Self-review **initial 78 → final 82 (REVISE) after 1 fix iteration; 3 major / 4 minor** — `qc/self_review.md` L11, L49, L71–L73, L81–L87. The 3 majors (RoB 2, GRADE, reference adequacy) are all `fixable_by_ai:false`, out of scope for a clean-room demo. (was: 82/100, initial 72, 4 major/5 minor)
- Body prose **~2,200 words** — strip method (2,188). (was: ~2,600)
- Forest figure path **analysis/figures/forest.png** (was forest_plot.png).
- Funnel exists at **analysis/figures/funnel.png** (added).
- Bubble plot / latitude meta-regression / **R² 75.6% removed** — no meta-regression was run (self_review m1 confirms "no meta-regression on latitude"); no bubble_plot.png exists.
- presentation.pptx does not exist → row removed.

## Demo 3 — NHANES Obesity
- Adjusted **OR 3.03 (95% CI 2.29–4.02)** — `analysis/tables/regression_or.csv` ("Obesity (BMI>=30 vs <30)", estimate 3.0316, ci 2.287–4.019). (was: 4.50, 3.23–6.27)
- STROBE compliance **83.3% (25/30 applicable)** — `qc/reporting_checklist.md` L12. (was: 81.8% 18/22)
- Self-review **ACCEPT-WITH-NOTES after 1 fix iteration; 0 genuine majors remaining** — `qc/self_review.md` FINAL section ("Verdict: ACCEPT-WITH-NOTES", "Genuine content issues: 0 remaining"). (was: 85/100 PASS, 2 iter, initial 75, 4 major/5 minor)
- Analytic **N = 5,010** — `manuscript/manuscript.md` Results ("final analytic sample comprised 5,010 adults"). (was: 4,866)
- Body prose **~1,850 words** — strip method (1,853). (was: ~2,800)
- OR forest figure path **analysis/figures/forest_or.png** (was or_forest_plot.png).
- prevalence_by_bmi.png **does not exist** → row removed.
- presentation.pptx does not exist → row removed.

## Global
- Section intro: drop "and presentation slides" claim (no slides produced under Option A).
- `<summary>` lines: drop "slides" from the output-list descriptions.
- Decision: **Option A** (relink + trim; no slide/cover-letter/plot regeneration).
- Preserved: commit `e5c6c56` (maintainer line + ORCID, CITATION.cff/.zenodo.json affiliation). Only version/date bumped to v3.8.0 in CITATION.cff + .zenodo.json (`catalog_counts.json` has no version field — untouched).
