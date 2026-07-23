# Burden of Disease, Decomposition & Forecasting

Methodology reference for the **value-add analytic layers** that turn a plain descriptive
result into a top-journal burden/estimate paper: population-attributable burden, rate
decomposition, trend-break analysis, and forecasting. These are the reusable moves a
high-output epidemiology group bolts onto a standing data platform (GBD/IHME, WHO Mortality
Database, or a national registry): the disease is swapped, the shell stays fixed, and **one**
value-add layer supplies the novelty. Report the estimate against **GATHER** (`/check-reporting`)
and, for any individual-level cohort component, STROBE/RECORD.

Load this guide before generating code for: a burden-of-disease estimate, an attributable-risk
analysis, a temporal-trend / joinpoint analysis, a decomposition, or a forecast.

---

## 0. The value-add-layer playbook (pick ONE per paper)

A descriptive number (an age-standardized rate, a prevalence) is rarely publishable alone. The
lever is a single added analytic layer answering a *why / how-much / where-to* question:

| Layer | Question it answers | Method | When the clinical need supports it |
|---|---|---|---|
| **Decomposition** | *Why* did the rate change? | Das Gupta (rate → aging / population growth / epidemiological change) | a rising/falling count where "is it just ageing?" is the reviewer's first question |
| **Attribution** | *How much* is modifiable? | Comparative risk assessment / population-attributable fraction (PAF) vs a TMREL | an exposure with an established dose–response and a policy angle |
| **Trend-break** | Did a *shock* bend the trend? | Joinpoint / AAPC, pre- vs post-period | a datable policy, guideline, or event (COVID, a screening-guideline change, a reimbursement shift) |
| **Forecast** | *Where is it going*? | Age-period-cohort projection (BAPC / APC) | serial or repeated cross-sectional data with a stable trend |
| **Life-expectancy decomposition** | Which ages/causes drove ΔLE? | Arriaga (age × cause partition) | a mortality/life-table framing |

**For a single-institution health-checkup cohort** (no GBD platform): you cannot out-scale a
burden study, but three of these layers port directly onto your existing follow-up —
(1) **trend-break**: reslice your accrued follow-up around a datable guideline/scanner-era break
rather than collecting new data; (2) **forecast**: project a serial imaging trajectory (CAC,
emphysema, body-composition) forward; (3) **global framing by contextualization**: place your
individual-level effect next to the *published* GBD burden number for that disease (free from the
GHDx results tool) — this borrows the global frame without claiming to re-estimate it, so it does
**not** trigger GATHER. The one thing you cannot borrow from the ecological template is its
"robustness = uncertainty-interval propagation, no confounding control" shortcut: your data is
individual-level, so the DAG / E-value / negative-control toolkit (see `propensity_score.md`,
`survival.md`, `../style/`) still applies.

---

## 1. Uncertainty intervals (UI), not confidence intervals

Model-based estimates carry a **95% uncertainty interval** = the 2.5th–97.5th percentile of the
posterior/Monte-Carlo draws (GBD uses 250–500 draws), propagated through every modeling step.

- Report a **UI**, not a CI; a UI crossing the null means "insufficient evidence for direction,"
  not "non-significant test." Never translate a UI into *P*-value language.
- Propagate draws end-to-end: sample each input's distribution, run the full pipeline per draw,
  summarise percentiles of the output — do not add variances analytically at the end.

```r
# draw-based UI for any derived quantity f(x)
draws <- replicate(500, f(rinput()))                  # rinput() samples the input distribution
est   <- quantile(draws, c(0.5, 0.025, 0.975))        # median + 95% UI
```

---

## 2. Attributable burden — comparative risk assessment / PAF

Partition a disease burden into the fraction attributable to a modifiable exposure, against a
**theoretical minimum-risk exposure level (TMREL)**.

- **PAF** = Σ over exposure levels of `P(exposure) · (RR − 1)` / `[1 + Σ P(exposure)·(RR − 1)]`,
  evaluated relative to the TMREL. Attributable burden = PAF × total burden.
- **Relative risks** come from a meta-analysis of prospective cohorts; carry the RR curve's
  uncertainty into the draws. Reclassify the dose–response shape honestly (monotonic vs J-shaped);
  a strictly harmful exposure has TMREL = 0.
- **Mediation to avoid double-counting**: when risks act through measured mediators (a dietary
  factor → blood pressure / LDL / glucose → IHD), estimate the mediation matrix so combined PAFs
  do not exceed 100%.
- Report against **GATHER** items 8–14 (bias correction, comparability, analysis detail,
  uncertainty). R: `epitools`, `graphPAF`, or a manual draw-based implementation.

## 3. Das Gupta decomposition — why did the count change?

Partition a change in an aggregate count/rate into **population growth**, **population ageing**,
and **epidemiological (rate) change** — the three components a reviewer of any "rising burden"
claim asks to see separated.

```r
# DemoDecomp implements Das Gupta / Horiuchi decomposition of a rate function
# install.packages("DemoDecomp")
library(DemoDecomp)
# func: maps a parameter vector (age-specific rates, age structure, total pop) -> summary measure
delta <- horiuchi(func = burden_fn, pars1 = year1_vec, pars2 = year2_vec, N = 20)
# sum(delta) == observed change; group delta by its structural / rate / size components
```

Report each component with a UI; the headline is usually "X% of the increase was population
growth/ageing, not a real rise in risk."

## 4. Trend-break — joinpoint / AAPC, pre- vs post-shock

Detect where a log-linear trend changes slope and summarise it as an **average annual percentage
change (AAPC)**; compare a pre-shock and a during/post-shock window as a natural-experiment layer.

```r
library(segmented)
m  <- lm(log(rate) ~ year, data = d)                  # log-linear trend
jp <- segmented(m, seg.Z = ~year)                     # estimate joinpoint(s)
# APC per segment = 100*(exp(slope) - 1); AAPC = segment-length-weighted average of APCs
# pre/post split: fit two windows (e.g. 2010-2019 vs 2020-2023) and compare AAPCs, do not pool
```

The pre/post AAPC split is itself a robustness layer (two independent windows compared, not one
pooled trend). For a checkup cohort, the "shock" is a datable guideline/reimbursement/scanner-era
change; reslice existing follow-up around it.

## 5. Forecasting — age-period-cohort projection

Project a rate forward with a **Bayesian age-period-cohort (BAPC)** model (integrated nested
Laplace approximation), which yields predictive intervals natively.

```r
# install.packages("BAPC"); needs INLA (r-inla.org)
library(BAPC); library(INLA)
proj <- BAPC(APCList(cases, population, gf = 5),
             predict = list(npredict = 27, retro = TRUE))   # e.g. forecast to 2050 + back-test
```

- **Back-test**: withhold the last k years, forecast them, report calibration — do not ship a
  projection with no retrospective validation.
- A single predictor (SDI alone) or a single model is an ensemble caveat: state that no ensemble
  / no formal back-testing was done if it was not, rather than implying robustness.
- Alternatives: `demography`/`StMoMo` (Lee–Carter family), or a simple age-period GLM with a
  clearly stated extrapolation assumption.

## 6. Life-expectancy decomposition (Arriaga)

Partition a change in life expectancy into contributions by **age group** and, with cause-deleted
life tables, by **cause of death** — the standard framing for a mortality life-table paper.

```r
# DemoDecomp::stepwise_replacement or a direct Arriaga implementation on two life tables
library(DemoDecomp)
contrib <- stepwise_replacement(func = e0_from_mx, pars1 = mx_year1, pars2 = mx_year2)
# contrib sums to Δe0; aggregate by age band (and by cause using cause-specific mx)
```

---

## Reporting & reproducibility

- **GATHER** (`/check-reporting` `GATHER.md`) governs the estimate: define indicator/population/
  period (item 1), data sources and their biases (5–6), analysis detail with formulae (11),
  model evaluation and sensitivity (12–13), uncertainty methods and what was/was not accounted
  for (14), code access (15), and a machine-readable results file with a UI (17–18).
- Seed every RNG; emit the draw-level results, not only summaries. State the platform/version
  (GBD round, WHO Mortality Database vintage) and cite it via its data DOI (GHDx for GBD).
- Keep the causal claim honest: burden/attribution/decomposition/forecast are **descriptive or
  associational** unless an explicit causal design (a natural experiment with identification, an
  MR — see `mendelian_randomization.md`) is in place. Pair "adjustment covariate" with a
  non-causal disclaimer; do not call an adjustment covariate an instrument.
