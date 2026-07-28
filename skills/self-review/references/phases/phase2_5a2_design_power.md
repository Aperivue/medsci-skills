# Phase 2.5a-2 — Design & power statistic provenance (computed, not extracted)

Phase 2.5a traces data-derived numbers back to a CSV and a primary source. **Design and power
statistics are a different class and a common blind spot**: the minimum detectable effect
(MDE), a-priori or post-hoc power, the required sample size for a future trial, and the
a-priori effect-size assumptions behind them are *computed*, not extracted, so they have no
CSV row or source-paper Table to trace to. They routinely escape both the internal-consistency
check and the source-fidelity audit above.

**Precedent failure pattern:**
> A pilot study reported a minimum detectable effect of d = 1.67. No standard two-sample method
> reproduces it (the correct value at the stated n, alpha, and power was about 1.24). It survived
> several review rounds because no committed script computed it — the value had been hand-entered —
> and one reviewer even cited the figure approvingly. In the same manuscript, a set of future-trial
> sample sizes was numerically correct but had been produced with an exact noncentral-t tool, while
> the committed script used a normal approximation and printed different numbers: right value, no
> reproducible provenance.

**Procedure:**

1. **Inventory design/power claims.** Search for: "minimum detectable", "detectable effect",
   "MDE", "power" (80% / 90% / "1 − beta"), "sample size", "n = N per arm/group", "to detect",
   "powered to", "a priori", and any a-priori planning effect size (Cohen's d / f / OR used for
   sizing).

2. **Require a reproducible source for each.** Every such value must be produced by committed
   code (e.g. `statsmodels` `TTestIndPower`, a G*Power-equivalent, or an explicit noncentral-t
   computation), with the inputs stated in the manuscript: n per arm, alpha, power, allocation
   ratio, and one- vs two-sided. A value with no committed-code source is the highest-risk case.

3. **Recompute independently** with a standard tool, then classify:
   - **Not reproducible by any standard method** → likely a calculation error (Major; P0 if it
     is a headline claim). This is the d = 1.67-vs-1.24 case above.
   - **Reproducible only by a method the committed script does not implement** (e.g. the
     manuscript value is noncentral-t but the script is a normal approximation) → provenance /
     method drift. The number may be correct, but update the committed code so it reproduces the
     reported value (Major: reproducibility, not correctness).

4. **Method-consistency across the manuscript.** All power, sample-size, and MDE statistics in
   one paper should share a single method family (e.g. all noncentral-t). A mix of normal
   approximation and exact-t within one manuscript signals that some values were computed in an
   ad-hoc side tool.

5. **Any non-reproducible design/power value is a Major Comment;** a non-reproducible headline
   power or MDE claim is a P0 submission blocker.

**Hand-entered design/power statistics are a code smell even when correct.** If no committed
function emits the value, flag it: the next revision will re-introduce the risk, and a reviewer
who recomputes will not match the manuscript.

**`POWER_MODEL_MISSPEC` — the power/MDE simulation's adjustment set must match the primary model.**
For cohort "negative findings," the whole conclusion leans on the MDE ("the literature effect of
1.2–1.5 cannot be excluded"), so the MDE must be computed under the **same covariate set as the
primary analysis**. When a committed power/MDE script exists, read its model formula: if it fits
`y ~ exposure + age` (2 covariates) while the primary model adjusts for 6, it **overstates power**
(omitted covariates inflate the apparent precision) — the MDE is too small and the negative claim
too strong. Re-running a parametric bootstrap under the full model is the fix (in one worked case
MDE moved from a 2-covariate "OR 1.67" to a full-model "OR ≈ 1.70"). A power/MDE whose script omits
primary-model covariates → Major (P0 when the MDE is a headline). This is `requires_reanalysis`
(re-simulate, not a prose edit). **`POWER_VALUE_INTERPOLATED`** — any `interpolat`/`approx`/`interp`
token in a power/MDE CSV's provenance column means the headline value was never simulated on the
grid; treat a non-reproducible headline power/MDE as Major.
