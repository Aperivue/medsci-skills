# Challenge card — core clinical-figure render regression (make-figures)

## Problem
The four highest-yield clinical figures — Kaplan–Meier, ROC, calibration, and
decision-curve — were documented only as **prose anatomy** in
`references/exemplar_plots/`, and the actual matplotlib rendering had **no deterministic
test of any kind**. A regression in figure code (a dropped number-at-risk table, a
missing chance diagonal, a calibration plot without its identity line, a DCA without the
treat-all / treat-none references, or a KM curve extrapolated past follow-up) would pass
every prose read and only be caught by a reviewer — the gap that left the suite's
self-identified weakest area with the same defense/enablement asymmetry the rest of the
repo has closed (42 integrity detectors vs ~0 generative render tests).

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

## Fixture (synthetic only — no real data)
- `fixture/synthetic_inputs.json` — hand-authored step/curve coordinates and summary
  statistics for all four figures.

## Expected (`verify.sh`, network-free)
- All four figures render to PNGs (each > 2 KB) **and** every structural invariant holds
  → exit 0.
- A mutated input that drops a load-bearing element (e.g. a KM curve extended past
  follow-up, or a DCA missing the treat-none reference) raises `AssertionError` → the
  negative cases in `verify.sh` confirm the gate actually fails when it should.

Requires matplotlib + numpy (already make-figures runtime deps); the verifier skips with
a clear message if matplotlib is unavailable, so it never hard-fails a minimal host.
