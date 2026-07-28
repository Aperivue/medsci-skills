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

## Runnable render layer (tested)

Ten of the highest-yield clinical figures — **Kaplan–Meier, ROC, calibration,
decision-curve, forest, Bland–Altman, confusion matrix, multi-reader ROC (MRMC),
Manhattan, and clinical timeline** — have a matching **runnable, deterministic generator**
in `../../scripts/render_core_figures.py`. It renders already-computed inputs
(the statistical estimation stays in `/analyze-stats`; the render layer never recomputes a
number) into the canonical anatomy and asserts each figure's load-bearing elements
(number-at-risk table, chance diagonal, identity line, treat-all/treat-none references,
no extrapolation past follow-up; forest per-study CI rows + null line + pooled diamond;
Bland–Altman bias + 95% limits of agreement; confusion Predicted/Actual axes + annotated
cells; MRMC per-reader + averaged curves; Manhattan significance-threshold line; timeline
baseline + event markers). A network-free render-regression challenge
(`scripts/render_core_figures_challenge/`, wired into `skill.yml` validation) renders all
ten from a synthetic fixture and confirms the structural gate fails on a malformed figure.

`imaging_panel.md` stays a **prose-only** exemplar by design: it composes real medical
images with panel labels, scale bars, and arrows — an image-arrangement task, not a plot of
computed numbers — so a synthetic generator would only draw placeholder boxes. Use the
prose model to compose it against real images.
Use the generator to produce these four directly; use the prose models below to compose
the figure types that do not yet have a generator.

## Contents

- `forest_plot.md` — meta-analysis forest plot: per-study square-by-weight + CI, pooled diamond
  with the model named, prediction interval, I²/τ²/Q, no-pool discipline under extreme
  heterogeneity, subgroup-difference test, funnel/Egger only at k ≥ 10.
- `external_validation_comparison.md` — performance across cohorts (internal vs external / by
  site·scanner·vendor·sequence) with the **honest drop**: forest/dumbbell, internal as reference,
  per-cohort N + bootstrap-BCa CI, Δ-from-internal annotation, subgroup/structure faceting, failed
  cohorts marked; a suspiciously flat external result is the leakage signature. The visual of the
  #1 acceptance lever; pairs `/model-validation` and `calc-sample-size` segmentation-metric sizing.
- `model_comparison_leaderboard.md` — model-vs-model leaderboard (**across models, one cohort** — the
  mirror of `external_validation_comparison.md`): one row per model with a bootstrap-Dice / DeLong
  CI, the **paired Δ vs a strong fairly-tuned reference baseline** with its CI/significance, ranking
  honesty (the paired Δ decides, not marginal-CI overlap; critical-difference / seed-stability), per-structure faceting, and a
  **matched-budget caption**; no "bold-our-row" cherry-pick. Pairs `design-study` multi-model-comparison
  design + `calc-sample-size` Test 16 + the `analyze-stats` model_comparison table-type.
- `segmentation_failure_panel.md` — segmentation usability (**across cases, one model** — the third
  axis beside the two above): every case plotted rather than a bar of means, the **acceptability
  threshold drawn with the fraction below it labelled**, failures coloured by the pre-specified class
  (boundary drift / missed / hallucinated / catastrophic), stratification that explains the tail, and
  a **qualitative panel of the actual worst cases** — an anatomically impossible output is invisible
  in every summary statistic. Pairs `design-study` segmentation-usability design + `calc-sample-size`
  Test 17.
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
- `ai_assistance_effect.md` — AI-assistance effect (reader-level paired improvement): one line per
  reader **unaided → aided** on the same cases, stratified by experience/specialty, reader-averaged
  ΔAUC/Δaccuracy with paired MRMC CI, **harmed readers marked** (automation bias), reading-time
  companion, crossover/washout. The within-reader-change counterpart to `mrmc_roc.md` (ROC space);
  pairs the analyze-stats reader-study table-type and `calc-sample-size` Test 14.
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
- `manhattan_plot.md` — Manhattan / volcano figure for an agnostic many-exposure scan (ExWAS / EWAS /
  MWAS / proteome-/nutrient-wide): named significance-threshold line + the number of tests, effect-size
  channel (volcano axis or Manhattan direction track), sparse hit labelling with the full set in a
  supplement, domain banding, and replication encoding. Pairs `analyze-stats` `multiplicity.md` and
  review probe O17.

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
