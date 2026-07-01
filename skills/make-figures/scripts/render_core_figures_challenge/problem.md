# Challenge card — core clinical-figure render regression (make-figures)

## Problem
The highest-yield clinical figures — Kaplan–Meier, ROC, calibration, decision-curve,
forest, Bland–Altman, and confusion matrix — were documented only as **prose anatomy** in
`references/exemplar_plots/`, and the actual matplotlib rendering had **no deterministic
test of any kind**. A regression in figure code (a dropped number-at-risk table, a
missing chance diagonal, a calibration plot without its identity line, a DCA without the
treat-all / treat-none references, a KM curve extrapolated past follow-up, a forest without
its pooled diamond or null line, a Bland–Altman without its limits of agreement, or a
confusion matrix without annotated cells) would pass every prose read and only be caught by
a reviewer — the gap that left the suite's self-identified weakest area with the same
defense/enablement asymmetry the rest of the repo has closed (integrity detectors have
challenge fixtures; the figure generators did not).

## What the generator does
`scripts/render_core_figures.py` is the **render** layer for the exemplar anatomies. It
turns each prose model into a runnable, deterministic matplotlib generator that takes
**already-computed inputs** (the analysis SoT stays in `/analyze-stats`; this never
recomputes a statistic) and renders the canonical anatomy. `assert_structure` then
introspects the actual matplotlib artists and asserts each figure's load-bearing
elements are present:

- **KM** — step curve(s), number-at-risk table, monotonic non-increasing survival,
  x-axis clipped to follow-up (no extrapolation).
- **ROC** — chance diagonal, AUC annotation, operating-point marker.
- **Calibration** — identity (y = x) line, slope + intercept annotation,
  predicted-vs-observed axes.
- **Decision curve** — model + treat-all + treat-none strategies, the treat-none
  (net benefit = 0) reference, a net-benefit y-axis.
- **Forest** — a per-study CI whisker for every study, the null reference line, and the
  pooled diamond; study + pooled row labels.
- **Bland–Altman** — the difference scatter, the bias line, and the 95% limits of
  agreement (bias ± 1.96·SD); difference-vs-mean axes.
- **Confusion matrix** — a matrix image with every cell annotated and Predicted/Actual axes.
- **MRMC ROC** — a curve per reader + the reader-averaged curve, the chance diagonal, and
  the averaged-AUC annotation.
- **Manhattan** — the point scatter, the named significance-threshold line, and a
  −log10(p) y-axis.
- **Clinical timeline** — the time baseline, an event marker + label at each event, and a
  time x-axis.

(`imaging_panel` stays a prose-only exemplar — it composes real images, not computed
numbers, so it has no synthetic generator.)

## Fixture (synthetic only — no real data)
- `fixture/synthetic_inputs.json` — hand-authored coordinates and summary statistics for
  all ten figures.

## Expected (`verify.sh`, network-free)
- All ten figures render to PNGs (each > 2 KB) **and** every structural invariant holds
  → exit 0.
- Mutated inputs that drop a load-bearing element (a non-monotonic KM curve; a non-square
  confusion matrix) raise `AssertionError` → the negative cases in `verify.sh` confirm the
  gate actually fails when it should.

Requires matplotlib + numpy (already make-figures runtime deps); the verifier skips with
a clear message if matplotlib is unavailable, so it never hard-fails a minimal host.
