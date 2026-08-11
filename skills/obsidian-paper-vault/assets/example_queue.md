# PAPER_QUEUE.md — example

Progress tracker for batch note-writing. Lives in the vault so a large backlog survives
across sessions. Markers: ✅ done · 🟡 in progress · ⬜ pending · ⏭️ skipped.

**Batch size**: 5 subagents × 5–6 papers. Update this file after each batch, before starting
the next.

## Status

| | Papers |
|---|---|
| ✅ Completed | 12 |
| 🟡 In progress | 5 |
| ⬜ Pending | 8 |
| ⏭️ Skipped | 2 |
| **Total** | **27** |

## Batch 1 — Clinical reasoning (✅ done 2026-01-18)

| | Source text | Note |
|---|---|---|
| ✅ | `triage_reader_study.txt` | `Synthetic triage reader study.md` |
| ✅ | `cost_aware_agent.txt` | `Cost-aware diagnostic agent.md` |
| ✅ | `simulated_clinic_bench.txt` | `Simulated clinic benchmark.md` |
| ⏭️ | `triage_reader_study_supplement.txt` | supplement to row 1 — no separate note |

## Batch 2 — Evaluation methodology (🟡 running)

| | Source text | Note |
|---|---|---|
| 🟡 | `rubric_agreement.txt` | `Rubric agreement across raters.md` |
| ⬜ | `judge_calibration.txt` | `LLM-as-judge calibration.md` |
| ⬜ | `benchmark_contamination.txt` | `Benchmark contamination.md` |

## Batch 3 — Deployment (⬜ pending)

| | Source text | Note |
|---|---|---|
| ⬜ | `silent_trial.txt` | `Silent-mode deployment trial.md` |
| ⏭️ | `slides_overview.txt` | slide deck, not a paper |

## Concept extraction log

- 2026-01-20: 12 notes reached → extracted `Sequential decision-making`,
  `LLM co-pilot in medicine`, `Uncertainty and hallucination` (all 🌱, awaiting the reader's edits)
- Next pass at ~20 notes

## Notes

- `benchmark_contamination.pdf` is a scan; extraction is thin. Re-extract with more pages or
  check the source before writing the note.
