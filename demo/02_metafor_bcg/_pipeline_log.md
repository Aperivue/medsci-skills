# Pipeline Log — Demo 2: BCG Vaccine Meta-Analysis
Generated: 2026-04-14
Mode: --e2e (autonomous)

## Pipeline Steps

| Step | Skill | Status | Output |
|------|-------|--------|--------|
| 1 | `/analyze-stats` (R metafor) | PASS | tables/study_results.csv, tables/summary_table.csv, tables/metaregression_table.csv, tables/leave_one_out.csv, figures/forest_plot.png, figures/funnel_plot.png, figures/funnel_trimfill.png, figures/bubble_plot.png, _analysis_outputs.md |
| 2 | `/make-figures --study-type meta-analysis` | PASS | figures/prisma_flow.svg (D2), figures/_figure_manifest.md (5 entries) |
| 3 | `/write-paper --autonomous` | PASS | manuscript.md (~2,600 words) |
| 4 | Phase 7.1: AI Pattern Scan | PASS | 0 forbidden patterns detected |
| 5 | `/check-reporting --json` (PRISMA 2020) | PASS | reporting_checklist.md, compliance 77.8% (21/27 PRESENT) |
| 6 | `/self-review --json` | PASS | review_comments.md, score 72/100, verdict REVISE, 4 major / 5 minor / 0 fatal |
| 7 | Phase 7.6: DOCX Build | PASS | manuscript_final.docx (pandoc) |
| 8 | `/present-paper` (bonus) | PASS | presentation.pptx (12 slides, speaker notes) |

## Summary

- **Word count**: ~2,600 (excluding abstract, references, legends)
- **Figure count**: 5 (PRISMA flow, forest plot, funnel plot, funnel trimfill, bubble plot)
- **Table count**: 4 (study results, summary, meta-regression, leave-one-out)
- **Reporting guideline**: PRISMA 2020
- **Compliance**: 77.8% (21/27 applicable items PRESENT)
- **Self-review score**: 72/100 (REVISE)
- **References**: 5 (all marked [UNVERIFIED] — demo dataset)
- **AI pattern scan**: PASS (0 forbidden patterns)
- **FATAL flags**: None

## Key Results

| Metric | Value |
|--------|-------|
| Pooled RR | 0.489 (95% CI: 0.344-0.696) |
| Risk reduction | 51.1% (30.4%-65.6%) |
| I² | 92.2% |
| tau² | 0.3132 |
| Prediction interval | 0.155-1.549 |
| Meta-regression R² (latitude) | 75.6% |
| Egger's p | 0.189 |
| Trim-and-fill imputed | 1 study |

## Self-Review Key Issues

| ID | Severity | Category | Issue |
|----|----------|----------|-------|
| M1 | Major | C | Missing GRADE certainty-of-evidence assessment |
| M2 | Major | C | Per-study risk of bias results not reported |
| M3 | Major | D | Limited novelty — classic dataset re-analysis |
| M4 | Major | E | Search strategy not fully reproducible |
| m1 | Minor | F | Unverified references (5 items) |
| m2 | Minor | A | BCG strain not analyzed as moderator |
| m3 | Minor | B | Prediction interval interpretation understated |
| m4 | Minor | D | Generic limitations opener |
| m5 | Minor | E | PRISMA flow numbers simulated for demo |

## Notes

- All 7 pipeline steps completed successfully.
- R metafor/meta used for all statistical computations (not Python).
- Self-review verdict REVISE (score 72) — expected for demo. Major issues M1-M2 (GRADE + RoB) intentionally omitted to demonstrate review output.
- PRISMA flow numbers are constructed for demonstration; in a real analysis, actual search yields would be used.
