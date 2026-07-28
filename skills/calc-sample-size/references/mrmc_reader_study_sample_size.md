# MRMC reader-study sample size (multi-reader multi-case)

For a **reader study** — the design that asks "do radiologists read better *with* the AI than
without", or "is the AI non-inferior to radiologists" — the single-reader AUC-precision
calculation (Test 1) **under-sizes the study**, often badly. This reference is the design-time
sizing for that class of study. It is the sizing counterpart to the flagship "clearing move" in
`design-study/references/venue_accept_recipe.md` (a reader study measuring clinical impact is
what lifts a study to the flagship tier) — and an under-sized reader study cannot deliver it.

## Why a single-reader power calculation is the wrong tool

A reader study generalizes to **radiologists in general**, not to the specific readers you hired.
So **both the readers and the cases are random effects**, and the uncertainty of the
reader-averaged AUC (or of the AI−reader ΔAUC) carries a **reader-variance** term the single-reader
calculation omits entirely. Size on case variance alone and the study is powered to detect an
effect *in your particular readers*, not in the population of readers — which is exactly the claim
a reviewer reads the paper as making. The practical consequence: studies sized as if readers were
fixed are routinely **under-powered**, and a null result from an under-sized reader study is
**inconclusive, not negative**.

## The framework — Obuchowski–Rockette / Hillis (OR)

The multi-reader multi-case (MRMC) analysis of variance treats the figure of merit (usually AUC,
or a difference in AUC between modalities/AI-conditions) as an outcome with **reader**, **case**,
and **reader×case** (plus modality) random components. Sizing inverts the OR variance formula:

- You choose the **number of readers `J`** and the **case counts** (diseased `N⁺`, non-diseased
  `N⁻`), and the OR formula returns the power to detect the target effect.
- Power depends on the **variance components** — the error variance and the between-reader /
  within-reader covariances (`Cov1`, `Cov2`, `Cov3` in the OR parameterization, or Hillis'
  equivalent `σ²` terms). **You cannot size an MRMC study without these**, and they are the real
  bottleneck: take them from a **pilot** (a handful of readers on a subset) or from **published
  component estimates** for a similar task/modality, and state the source.

## The inputs to pre-specify (before any data)

1. **The effect**: the ΔAUC to detect (superiority) *or* the non-inferiority margin (an AI-vs-reader
   claim is usually **non-inferiority**, so state the margin, not a difference).
2. **The expected AUC level** of the reference arm (variance of an AUC estimate depends on where it
   sits).
3. **The variance components** (pilot or literature — the hard part; §above).
4. **The design**: **fully-crossed** (every reader reads every case in every condition) is the
   default and the most efficient; a **crossover with washout** (readers read with and without AI,
   separated by a washout so the first read does not cue the second) is the standard AI-assistance
   design.
5. **Power and α** (commonly 80–90% at two-sided 0.05).

## Readers vs cases — where the power comes from

Because the **reader-variance term usually dominates** the generalization uncertainty, past a
modest case count **adding readers often buys more power than adding cases** — yet readers are the
scarcer, costlier resource. Report the **`J × N` power grid**, not a single number, so the
reader/case trade-off is an explicit, defensible design choice. A study with many cases but only
3–4 readers is a common, predictable under-powering.

## Compute it — integrate, do not reimplement

- **`RJafroc`** (R; Chakraborty) — `SsPowerGivenJK` / sample-size functions for ROC & FROC MRMC.
- **`MRMCaov`** (R) — OR analysis + power.
- **`iMRMC`** (Gallas, FDA) — MRMC sizing/analysis, widely accepted by regulators.
- **OR-DBM / DBM** procedures for the variance-component estimation from a pilot.

Feed the pilot/literature variance components + the target effect into one of these; do not hand-roll
the OR variance algebra.

## Grounding exemplars (accepted reader studies)

Realistic `J × N` and design choices from accepted open-access papers:
- **8-reader MRMC crossover, 500 cases** — PCN CT model, *npj Digital Medicine* 2025
  (`10.1038/s41746-025-01970-y`): readers spanning residents→seniors, accuracy **and** reading-time
  endpoints.
- **26 physicians × 150 cases × 3 conditions with ≥2-week washout** — pelvic-radiograph AI-support,
  *npj Digital Medicine* 2025 (`10.1038/s41746-025-01923-5`): a crossover across no-AI / alert /
  heatmap, specialty-stratified.

These illustrate the crossover-with-washout design and the reader-count range a flagship reader
study lands in; they are patterns, not templates.

## Reporting (what the Methods must state)

The number of readers `J`, the case split `N⁺`/`N⁻`, the **design** (fully-crossed / crossover +
washout), the **target effect** (ΔAUC or NI margin) and power/α, the **source of the variance
components** (pilot vs literature), and the **software**. Analysis of the completed study uses the
matching OR/DBM procedure (see `analyze-stats` `reader_study` table-type + `diagnostic_accuracy`
guide); the reader-study *design internals* (rubric, blinding, washout, experience mix) are in
`design-study/references/reader_elicitation_design.md`, and an AI-vs-human-expert benchmark routes
to `/design-ai-benchmarking`.

## References (methodology — cite, do not copy)

- Obuchowski NA, Rockette HE. *Commun Stat Simul Comput* 1995 (the OR method).
- Hillis SL, Berbaum KS, Metz CE. *Acad Radiol* 2008 (OR/DBM equivalence, sizing).
- Hillis SL. *Stat Med* 2007 (degrees of freedom for MRMC).
- Chakraborty DP. *Observer Performance Methods for Diagnostic Imaging* (RJafroc).
