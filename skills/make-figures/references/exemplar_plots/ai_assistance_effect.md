# Exemplar anatomy — AI-assistance effect (reader-level paired improvement)

A worked **anatomy model** for the signature figure of an **AI-assistance reader study** — the one
that answers "does the AI change what each reader does, and **for whom**". Where `mrmc_roc.md` shows
the reader-study comparison in ROC space, this figure shows the **within-reader change**: each
reader's performance **unaided → AI-aided** on the same cases, as a paired slopegraph (or dumbbell),
so the reader-level effect, its spread, and any reader who is *harmed* are all visible. It carries
the flagship claim of these studies ("AI narrows the non-radiologist gap"). Pairs `mrmc_roc.md`,
`analyze-stats` `table-standards/table-types/reader_study.md`, and the sizing in `calc-sample-size`
(Test 14 / `references/mrmc_reader_study_sample_size.md`). Synthetic — describes *what each element
must show* and the errors to avoid; not an image to copy, no real citations.

## Elements
- **One line (or dumbbell) per reader**, connecting the reader's metric **unaided → aided** on the
  **same cases** (a within-reader, crossover comparison). State the metric — the clinically relevant
  one: accuracy, sensitivity/specificity at the operating point actually used, or per-reader AUC.
- **Stratification by reader group** (experience: resident → attending; or specialty: radiologist vs
  non-radiologist) by colour or small-multiple panels — the "who benefits" axis is usually the point
  of the study.
- The **reader-averaged change (ΔAUC / Δaccuracy) with its MRMC 95% CI** (reader **and** case
  variance — Obuchowski–Rockette), and the **non-inferiority margin** if that is the design.
- **Readers whose performance declined with AI marked** — automation bias / over-reliance is a real
  effect; the figure must be able to show harm, not only benefit.
- A **reading-time companion** (unaided vs aided, same paired layout) when efficiency is a stated
  endpoint.
- Caption states the **design** (crossover + washout), that the **cases were held constant**, and the
  **reader sample** and its generalisation limit.

## Discipline (what the figure must not do)
- **Do not show only the group mean** (a single before/after bar pair) — it hides the reader spread,
  who benefits, and any reader who got **worse** with AI; the per-reader detail is the finding.
- **Do not use an unpaired comparison or a fixed-reader CI** — the readers read the same cases, so the
  uncertainty is the **paired MRMC** variance, not two independent groups.
- **Do not claim "AI helps readers" from an upward mean** without the stratified effect — a mean gain
  can be one subgroup improving while another is unaffected or harmed.
- **Do not omit the harmed readers or the washout** — an unwashed second read is confounded by case
  recognition, and hiding declines overstates benefit.
- **Do not read a subgroup the study was not sized for** as a firm effect — reader subgroups are
  usually underpowered (ties to `calc-sample-size` Test 14).

## Common omission
- The **per-reader lines**, the **stratification by experience/specialty**, the **harmed-reader
  cases**, and the **paired MRMC CI** on the averaged change — the elements this figure most often
  drops, and the ones that turn "AI helps on average" into the defensible, *for-whom* claim a reader
  study exists to make. Cross-reference `mrmc_roc.md`, `critic_rubrics/data_plot.md`, the
  diagnostic-accuracy probes `peer-review/references/domain-probes/diagnostic_accuracy.md`, and
  `analyze-stats` `table-standards/table-types/reader_study.md`.
