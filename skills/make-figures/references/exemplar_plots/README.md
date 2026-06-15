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
- `decision_curve.md` — decision curve (net-benefit/DCA): threshold-probability vs net benefit,
  treat-all/treat-none references, justified threshold range, calibrated model curve, proposed
  operating threshold; the clinical-utility counterpart to roc_pr/calibration. Pairs the
  `analyze-stats` incremental_value table-type.
- `mrmc_roc.md` — multi-reader multi-case (MRMC) reader-study ROC: per-reader curves + bold
  reader-averaged curve, MRMC (reader+case) AUC CI, ΔAUC with margin, per-patient/per-lesion unit,
  fully-crossed/washout note. Pairs the analyze-stats reader-study table-type.
- `bland_altman.md` — Bland–Altman agreement: difference vs mean-of-the-two-methods, bias line +
  CI, ±1.96·SD limits of agreement with CIs on each limit, proportional-bias check, % within LoA,
  pre-defined clinical-acceptability band, not a correlation plot, repeated-measures handling.
  Pairs the analyze-stats agreement table-type.
- `confusion_matrix.md` — confusion matrix: TP/FP/FN/TN with explicit Predicted/Actual axes, raw
  counts AND row-normalized (recall) / column-normalized (precision) views, class-imbalance caveat,
  stated operating threshold, per-class metrics, multi-class macro-average. Pairs roc_pr.
- `clinical_timeline.md` — CARE case-report timeline: relative time axis, symptoms/tests/treatment/
  outcome lanes, index presentation marker, final follow-up endpoint, de-identification discipline,
  and annotated imaging-panel pairing when imaging is the teaching point. Pairs `write-paper`
  `exemplar_case_report.md`.
- `imaging_panel.md` — annotated multimodality/multi-sequence imaging panel for a radiology case
  report or series: lettered sub-panels per modality/sequence/timepoint, arrow to the key finding in
  each, quantitative labels (size/SUVmax/category), same-lesion correspondence for discordance or
  treatment response, and de-identification discipline. Pairs `clinical_timeline.md` (chronology) and
  `write-paper` `exemplar_case_report.md`.

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
  `visual_abstract` anatomy.
