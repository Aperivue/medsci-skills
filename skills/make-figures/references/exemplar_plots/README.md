# Exemplar plots — non-flow figure anatomy models

`make-figures` carries flow-diagram exemplars (`exemplar_diagrams/{consort,prisma,stard,strobe}/`)
and a non-flow **checklist** (`critic_rubrics/data_plot.md` §C: ROC, forest, KM, calibration,
Bland–Altman, confusion matrix). What it lacked is a worked **anatomy model** for the non-flow
figures — what a complete, publication-grade plot of each type contains, element by element.
This directory fills the gap that `data_plot.md` §F ("Exemplar comparison, if exemplars exist")
anticipates.

These are **authored from scratch as teaching models**, not extracted from any published
figure. Use them to compose a figure that has every load-bearing element, then score the draft
against `critic_rubrics/data_plot.md`; do not copy an image.

## Contents

- `forest_plot.md` — meta-analysis forest plot: per-study square-by-weight + CI, pooled diamond
  with the model named, prediction interval, I²/τ²/Q, no-pool discipline under extreme
  heterogeneity, subgroup-difference test, funnel/Egger only at k ≥ 10.
- `km_curve.md` — Kaplan–Meier survival curve: number-at-risk table, censoring marks, CI band,
  median/log-rank/HR annotation, no extrapolation past the thin-risk-set tail, CIF for competing
  risks. Pairs the survival table-type.
- `roc_pr.md` — ROC + precision–recall: fixed 0–1 axes, AUC CI / curve band, marked operating
  point, DeLong for AUC differences, PR + AUPRC (baseline = prevalence) under imbalance.
- `calibration_plot.md` — calibration: predicted-vs-observed with 45° line, flexible curve,
  slope/intercept, predicted-risk distribution, external set, not HL-test-alone; pairs roc_pr.

## Curator guidelines (for adding more)

- **Synthetic only.** Describe the anatomy with placeholder specifics; never paste or trace a
  real figure, use no real citations, no PII, English only.
- **One figure type per file**, element by element, each line stating *what the element must
  show* — plus a "Discipline" block of what the figure must not do and the type's most common
  omission.
- **Complement, do not duplicate, `critic_rubrics/data_plot.md` §C** — the rubric scores; the
  exemplar composes. Cross-reference the rubric and the relevant `analyze-stats` template
  (e.g., `forest_plot.py` / `meta_analysis.R` for the forest) rather than restating them.
- Keep each file ~40–60 lines. Future candidates (see `reverse_engineer/gap_register.md`):
  `bland_altman.md`, `confusion_matrix.md`, `visual_abstract` anatomy.
