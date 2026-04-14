# Pipeline Log — Demo 1: Wisconsin Breast Cancer
Generated: 2026-04-14
Mode: --e2e (autonomous)

## Pipeline Steps

| Step | Skill | Status | Output |
|------|-------|--------|--------|
| 1 | `/analyze-stats` | PASS | tables/table1_demographics.csv, tables/diagnostic_accuracy.csv, tables/predictions.csv, figures/roc_curve.png, figures/confusion_matrices.png, _analysis_outputs.md |
| 2 | `/make-figures --study-type diagnostic` | PASS | figures/stard_flow.svg (D2), figures/_figure_manifest.md (3 entries) |
| 3 | `/write-paper --autonomous` | PASS | manuscript.md (~1,800 words) |
| 4 | Phase 7.1: AI Pattern Scan | PASS | 0 forbidden patterns detected |
| 5 | `/check-reporting --json` (STARD 2015) | PASS | reporting_checklist.md, 5 items auto-fixed (compliance 67.9% → 82.1%) |
| 6 | `/self-review --json` | PASS | review_comments.md, score 74/100, verdict REVISE, 4 major / 5 minor / 0 fatal |
| 7 | Phase 7.6: DOCX Build | PASS | manuscript_final.docx (pandoc) |
| 8 | `/present-paper` (bonus) | PASS | presentation.pptx (12 slides, speaker notes) |

## Summary

- **Word count**: ~1,900 (excluding abstract, references, legends)
- **Figure count**: 3 (STARD flow, ROC curves, confusion matrices)
- **Table count**: 2 (demographics, diagnostic accuracy)
- **Reporting guideline**: STARD 2015
- **Compliance**: 82.1% (23/28 applicable items PRESENT)
- **Self-review score**: 74/100 (REVISE)
- **References**: 4 (all marked [UNVERIFIED] — demo dataset)
- **AI pattern scan**: PASS (0 forbidden patterns)
- **FATAL flags**: None

## Check-Reporting Auto-Fixes Applied

| Item | Fix |
|------|-----|
| 13 (Sample size) | Added sample size justification paragraph |
| 28 (Funding) | Added "no specific funding" statement |
| 6 (Eligibility) | Added explicit inclusion criteria |
| 7 (Sampling) | Added convenience sample description |
| 10a (Cut-offs) | Added pre-specified 0.5 threshold statement |

## Self-Review Key Issues

| ID | Severity | Category | Issue |
|----|----------|----------|-------|
| M1 | Major | C | Missing calibration assessment (Brier score + calibration plot) |
| M2 | Major | A | No external/temporal validation |
| M3 | Major | D | Limited novelty — well-studied benchmark dataset |
| M4 | Major | E | No hyperparameter tuning rationale |
| m1 | Minor | F | Unverified references (4 items) |
| m2 | Minor | C | Missing CIs for sensitivity/specificity/PPV/NPV |
| m3 | Minor | D | Generic limitations opener |
| m4 | Minor | A | Synthetic age variable transparency |
| m5 | Minor | D | "Screening" vs "diagnostic workup" in conclusion |

## Notes

- All 5 pipeline steps completed successfully.
- Self-review verdict is REVISE (score 74) — expected for a demo manuscript. Major issues M1-M4 are all fixable but intentionally left unfixed to demonstrate the review output.
- References marked [UNVERIFIED] as expected for a demo — citation verification was not run to conserve context.
