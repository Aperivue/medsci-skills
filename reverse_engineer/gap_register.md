# Skill gap register

A living, scored ledger of **skill weaknesses the loop targets**. This supersedes the old
fixed "priority order" — each iteration consults this register (PLAYBOOK Step 0), works the
highest-scoring **open** gap, and feeds newly discovered gaps back in (Step B). The point is to
find the weaknesses across the *whole* suite — including ones we did not know about — by
reading strong papers and noticing what our skills do not yet cover or check.

## Scoring

`score = impact × frequency × deficit` (each 1–5; higher = work it sooner).

- **impact** — how much a real manuscript benefits when this gap is filled.
- **frequency** — how often the relevant study type / task actually shows up.
- **deficit** — how missing it is now (5 = absent, 1 = minor polish).

**status:** `open` · `in-progress` · `shipped (#PR)` · `saturated` (lane's gaps are filled —
stop adding marginal items there).

## How gaps enter the register

1. **Paper-driven (Step B).** While analyzing a strong paper/review, note not only what *it*
   does well but **what a strong paper in this area needs that our skills do not cover or
   check** — a missing exemplar, table-type, figure anatomy, probe, checklist item, or
   template. Add it as a row.
2. **Cross-skill audit (every ~4 iterations).** Pick one skill the loop has not touched
   recently and scan its `references/` against the common cases in its domain (what table
   types / figure types / probes / templates a practitioner expects). Record what is absent.
   Rotate the audited skill so coverage spreads beyond the obvious (figures, review skills).
3. **User-flagged.** Areas the user calls out (e.g., figures).

## Open gaps (work highest score first)

| id | skill | gap | impact | freq | deficit | score | status |
|----|-------|-----|:------:|:----:|:-------:|:-----:|--------|
| G1 | make-figures | `exemplar_plots/km_curve.md` — KM survival-curve anatomy (number-at-risk, censoring marks, CI band, no extrapolation past follow-up); pairs the survival table-type | 4 | 5 | 5 | 100 | shipped (this PR) |
| G2 | analyze-stats | `table-types/agreement.md` — reliability table (ICC / weighted κ / Bland–Altman LoA) — supported by `agreement_analysis.py` but no table-type template | 4 | 4 | 5 | 80 | shipped (this PR) |
| G3 | make-figures | `exemplar_plots/roc_pr.md` — ROC / precision-recall anatomy (CI band, operating point, AUPRC under imbalance) | 4 | 5 | 5 | 100 | shipped (this PR) |
| G4 | make-figures | `exemplar_plots/calibration_plot.md` — calibration anatomy (bins/loess, slope/intercept, distribution rug) | 4 | 4 | 5 | 80 | shipped (this PR) |
| G5 | peer-review + self-review | `domain-probes/` RCT / intervention-trial probe (CONSORT: randomisation, allocation concealment, blinding, ITT, selective-outcome) — no trial probe despite trials being common | 5 | 4 | 5 | 100 | shipped (this PR) |
| G6 | make-figures | `exemplar_plots/bland_altman.md` + `confusion_matrix.md` | 3 | 3 | 5 | 45 | open |
| G7 | write-paper | `exemplar_introduction.md` + `exemplar_abstract.md` (the two sections without exemplars; section_guides exist) | 3 | 5 | 3 | 45 | intro shipped; abstract open |
| G8 | check-reporting | `checklists/METRICS.md` — radiomics methodological-quality tool (named in the critical-item floor but no checklist) | 3 | 3 | 4 | 36 | open |
| G9 | calc-sample-size | `references/justification_examples.md` — reviewer-safe sample-size justification prose per design (found via cross-skill audit; SKILL.md promised "IRB-ready justification text" but no exemplar library) | 4 | 4 | 4 | 64 | shipped (this PR) |
| G10 | present-paper | `scripts/inject_speaker_notes.py` run-level markdown parser — general speaker notes rendered `**bold**` literally (the failure mode pptx-speaker-notes.md warns against); the parser existed only in inject_pronunciation_notes.py. Found while triaging the unmerged `present-paper-md-notes-glossary` branch (whose verify_refs/academic-aio parts were already superseded by main) | 3 | 4 | 4 | 48 | shipped (rescue PR) |
| G11 | manage-refs | `scripts/render_pandoc.sh` had no pre-render reference audit — a direct render call could ship fabricated/mismatched citations (the master pre_submission_gate audits, but direct calls bypass it). Found while triaging the unmerged present-paper-md-notes-glossary branch | 4 | 3 | 4 | 48 | shipped (cleanup PR) |
| G16 | check-reporting | `checklists/CONSORT_AI.md` — CONSORT-AI extension (AI clinical-trial **reports**). Already routed in Step 1 + aliased (`consortai`) but unvendored — the fail-fast test asserts it as a MISSING_CHECKLIST_CONTRACT_VIOLATION. Vendoring closes that contract gap. Found reverse-engineering the AI-RCT reporting area | 5 | 3 | 5 | 75 | in-progress (this PR) |
| G17 | check-reporting | `checklists/SPIRIT_AI.md` — SPIRIT-AI extension (AI clinical-trial **protocols**). Same unvendored-but-routed contract gap as CONSORT-AI; the protocol counterpart | 5 | 3 | 5 | 75 | in-progress (this PR) |
| G18 | peer-review + self-review | `domain-probes/rct_trial.md` AI-extension subsection — the RCT probe (RC0–RC7) checks trial design but not the CONSORT-AI/SPIRIT-AI reporting flow (algorithm version, input-data criteria, human–AI interaction, poor-input handling, performance-error analysis, code accessibility) | 4 | 3 | 4 | 48 | in-progress (this PR) |

> Numbering note: G12–G15 belong to the still-open sibling PR (decision-curve + TRIPOD-LLM); this branch is off origin/main and skips them to avoid post-merge collision.

## Lane status

- **make-figures** (figure exemplars): forest shipped (#130); km/roc/calibration/bland-altman/
  confusion/visual-abstract open — **the suite's weakest area, keep returning here.**
- **write-paper exemplars**: methods/results/discussion trio shipped; intro/abstract open.
- **review domain-probes**: 6 modules; RCT/trial + survey/qualitative/economic still open.

## Shipped (audit trail)

| id | shipped | skill | note |
|----|---------|-------|------|
| — | #128–#130 | peer-review/self-review/write-paper/analyze-stats/make-figures/check-reporting | optimistic-validation seam, exemplar trio, survival table, forest exemplar, critical-item floor, selective-outcome exemplar |
