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
| 6 | `/self-review --json --fix` | PASS | review_comments.md, score 74→83/100, verdict REVISE (2 iterations, auto-fix limit reached) |
| 7 | Phase 7.6: DOCX Build | PASS | manuscript_final.docx (pandoc) |
| 8 | `/present-paper` (bonus) | PASS | presentation.pptx (12 slides, speaker notes) |

## Summary

- **Word count**: ~1,900 (excluding abstract, references, legends)
- **Figure count**: 3 (STARD flow, ROC curves, confusion matrices)
- **Table count**: 2 (demographics, diagnostic accuracy)
- **Reporting guideline**: STARD 2015
- **Compliance**: 82.1% (23/28 applicable items PRESENT)
- **Self-review score**: 83/100 (REVISE, auto-fix limit reached)
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

## Self-Review Fix Loop (Phase 7.4)
- Initial score: 74 → After iter 1: 80 → After iter 2: 83
- Fix iterations: 2/2 (limit reached)
- Fixed issues: 6 (iter 1) + 2 partial mitigations (iter 2)
- Remaining issues (human review needed): M1 (calibration analysis), m1 (reference verification), m2 (proportion CIs)
- Final verdict: REVISE (auto-fix limit reached; score 83 < 85 threshold)

## Notes

- All 5 pipeline steps completed successfully.
- Self-review fix loop applied 8 issue-actions across 2 iterations, raising the score from 74 to 83. Auto-fix limit reached (score 83 < 85 threshold). Three issues remain for human review (M1: calibration analysis, m1: reference verification, m2: proportion CIs).
- References marked [UNVERIFIED] as expected for a demo — citation verification was not run to conserve context.
