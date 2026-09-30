# Survival / Time-to-Event Guide

Estimating time-to-event outcomes and prognostic effects. The estimator is easy to
call; the ways these analyses fail review are (1) ignoring **competing risks** so a naive
1−KM **overestimates** the cumulative incidence, (2) reporting a **single time-averaged
hazard ratio** as the whole story when hazards are clearly non-proportional (with no
prespecified RMST or fixed-horizon estimand beside it), and (3) **estimand
drift** — quoting a subdistribution hazard for an etiologic claim or a cause-specific hazard
for an absolute-risk claim. This guide produces the right estimand; the operational caveats
(EPV gate, cluster-robust CIs, horizon, quantile estimands) are under **Operational rules**
and interval-censoring under **Interval-censored events**, both below.

---

## When to Use

- **Single event type, right-censored** → Kaplan–Meier (unadjusted) + Cox proportional-hazards
  (adjusted HR with 95% CI); the log-rank test for a KM group comparison.
- **≥2 competing event types** (recurrence + competing death, or cause-specific mortality) →
  cumulative incidence functions + **cause-specific Cox** or **Fine–Gray** — see below.
- **Prognostic model discrimination** → a C-index variant matched to the censoring + a
  time-dependent AUC at a clinical horizon (S6).
- NOT for: events detected only at scheduled visits → interval-censored methods (below);
  recurrent events per subject → a cluster-robust or frailty model (Operational rules, below);
  rater agreement → `analysis_guides/agreement_reliability.md`.

---

## Competing risks come first (this, not the HR, is the issue)

If a subject can experience an event that **precludes** the event of interest (death before
recurrence), treating the competing event as ordinary censoring is *informative* censoring:
the naive **1−KM overestimates** the cumulative incidence of the event of interest. Produce the
**cumulative incidence function (CIF)** with an Aalen–Johansen / Fine–Gray estimator instead.
This is the produce-side of probe **S3**.

```python
# lifelines: cumulative incidence for a competing-risks event of interest
from lifelines import AalenJohansenFitter, KaplanMeierFitter
import pandas as pd
df = pd.read_csv("survival.csv")   # time, event_type (0=censored, 1=interest, 2=competing)

ajf = AalenJohansenFitter()
ajf.fit(df["time"], df["event_type"], event_of_interest=1)
print(ajf.cumulative_density_.tail(1))          # correct CIF for cause 1

kmf = KaplanMeierFitter()                        # NAIVE (cause 2 censored) — overestimates
kmf.fit(df["time"], (df["event_type"] == 1).astype(int))
print("naive 1-KM:", float(1 - kmf.survival_function_.iloc[-1, 0]))
# the naive value will exceed the Aalen-Johansen CIF whenever the competing event is common.
```

**Which model for which question (S8 estimand):**

- **Cause-specific hazard** (a Cox model that censors the competing event) answers an
  **etiologic** question — "does X change the rate of recurrence among those still at risk?"
- **Fine–Gray subdistribution hazard** (`cmprsk::crr` / `survival::finegray` in R) answers a
  **prognostic / absolute-risk** question — "does X change the cumulative *incidence*?" Quote an
  sHR for an incidence claim and a cause-specific HR for an etiologic claim — not the reverse.

```r
library(survival)                       # Fine-Gray via a weighted Cox on the finegray split
fg  <- finegray(Surv(time, factor(event_type)) ~ ., data = d, etype = 1)
crr <- coxph(Surv(fgstart, fgstop, fgstatus) ~ x, weight = fgwt, data = fg)   # subdistribution HR
```

**Competing-risks operational rules:**

- **When**: mortality studies with multiple causes of death, cardiovascular events when non-CV
  death is frequent, any outcome where competing events are common (>5% of total events). State
  which competing events were defined.
- **R packages**: `cmprsk` (Fine–Gray, `cuminc()` CIF with Gray's test for group comparison),
  `tidycmprsk` (tidy interface), `survival` (cause-specific Cox).
- **Check the subdistribution-PH assumption** the same way as for Cox (a time-interaction term on
  the subdistribution scale, or scaled-residual analogues); a constant sHR is an assumption, not a
  given. Report the sHR (95% CI) with the cause-specific HR beside it, so the etiologic and
  prognostic readings are both visible; report both when the question is etiologic.
- Present **CIF plots, not 1−KM**, when competing risks exist.

---

## Proportional hazards, and RMST when it fails

A single Cox HR is a weighted time-average; if hazards are not proportional it averages a
changing effect, and whether that average is the quantity of interest is a design decision.
**Prespecify the estimand** — e.g. the HR *and* an RMST difference or survival difference at a
clinically fixed horizon τ — instead of switching estimands on the result of a PH test. The
Schoenfeld test depends on sample size: large cohorts "fail" for trivial departures, small ones
never do (Stensrud & Hernán 2020, doi:10.1001/jama.2020.1267). Use the scaled Schoenfeld
residual plots to *describe* how the effect changes over time.

```python
from lifelines import CoxPHFitter
cph = CoxPHFitter().fit(df, "time", "event")          # unpenalised MLE (the default)
cph.check_assumptions(df, show_plots=True)             # residual plots: describe, don't gate
```

```r
library(survRM2)
rmst2(time, status, arm, tau = 3)   # RMST difference at tau=3 years, valid under non-PH
```

`survival_analysis.py --rmst-t <tau>` prints each group's RMST and the difference with its 95% CI
(the estimator SE matches R `survival::survfit(..., rmean = tau)`).

---

## Follow-up and discrimination (S6)

- **Reverse Kaplan–Meier median follow-up** — the honest "how long were people followed"
  (median event time answers a different question). Compute it by **swapping the event
  indicator** (censored observations become the "events"); report it per cohort and per
  outcome, with the censoring date.

```python
kmf.fit(df["time"], 1 - df["event"])            # swap: censored -> event
print("reverse-KM median follow-up:", kmf.median_survival_time_)
```

- **C-index variant** — Harrell's C is biased under heavy or non-random censoring; report
  **Uno's IPCW C** (`survC1::Est.Cval` / `timeROC`) and a **time-dependent AUC at a clinical
  horizon** (2-/3-year) beside it, and state which variant and horizon (S6).

---

## Estimand provenance (S8)

State the survival estimand explicitly and hold it consistent across Abstract / Methods /
Results — event-free survival vs cause-specific cumulative incidence vs all-cause mortality,
and subject vs population level — with the evaluation horizon fixed in advance. Do not
re-designate the primary endpoint, model, or horizon after seeing results, and make every
derived statistic (an E-value, an sHR-vs-cause-specific contrast) trace to the *declared
primary* estimand. The self-review skill automates the registration ↔ manuscript and E-value
arithmetic checks (Phase 2.5f); see also `estimand-provenance-lock`.

---

## Operational rules

- **Events-per-variable (EPV) gate**: check `events / n_covariates >= 10` before fitting Cox
  (the mirror of the logistic EPV rule). If violated, reduce the covariates or use a Firth-
  penalised Cox with profile-likelihood CIs (R `coxphf`); do not report Wald CIs from a
  sparse-event model as if stable. Penalisation is never the default: a ridge penalty
  (`survival_analysis.py --penalizer`) shrinks every HR toward 1, so label such output as a
  penalised estimate.
- **Nested observation units (cluster-robust CI)**: when a subject contributes more than one
  analysed unit (multiple lesions, both eyes, repeated episodes), pass a subject id so the HR CIs
  use a robust cluster-sandwich variance (`coxph(..., cluster = id)` / `robust = TRUE` in R,
  `cluster_col=` in lifelines, e.g. `survival_analysis.py --cluster <id>`). Treating correlated
  rows as independent understates the standard errors and narrows the CI.
- **Non-proportional hazards → prespecified estimands, not a test-triggered switch.** State in
  the protocol/SAP which estimand is primary (HR, RMST difference at τ, survival difference at
  τ) and report the others alongside. If the scaled Schoenfeld residuals show the effect
  changing over time, describe it (a piecewise HR split at a clinically sensible cut, or a
  `tt()` time-transform) and state it explicitly; do not let a Schoenfeld P value decide which
  estimand becomes the headline (Stensrud & Hernán 2020, doi:10.1001/jama.2020.1267).
- **Horizon vs follow-up.** Do not read a KM or CIF estimate at a horizon beyond the data: if a
  reported time point (e.g., a 15-year cumulative incidence) exceeds the reverse-KM median
  follow-up, restrict the horizon to where the risk set is non-trivial or report the number at
  risk at that horizon.
- **Quantile estimands (warranty period, T25, etc.)** — time to a fixed cumulative incidence: use
  `quantile()` on the KM/`survfit` object and always emit the 95% CI (`quantile(km, conf.int =
  TRUE)`, or a log-transformed / bootstrap CI) with the events/n that define it. If the event rate
  stays below the target quantile, report "not reached" and consider Weibull parametric
  extrapolation (also with an interval).

---

## Interval-censored events

When exact event times are unknown (status changes detected at periodic visits — health-screening
cohorts, cancer-screening intervals, repeated biomarker assessments), the usual practice of dating
the event at the detection visit (the right end of the interval) makes every recorded event
time **later** than the true one, so standard KM **overestimates** event-free time (survival is
biased upward; Lindsey & Ryan 1998, doi:10.1002/(SICI)1097-0258(19980130)17:2<219::AID-SIM735>3.0.CO;2-O).

- **Auto-trigger**: if the event date is defined by a periodic visit or scheduled re-examination
  (the event is detected *at* a visit, not observed exactly), make an interval-censored model the
  **primary** analysis, or at minimum a mandatory pre-specified sensitivity analysis. Do not
  present a right-censored `coxph()` on visit-dated events as if the times were exact.
- **R packages**: `icenReg` (parametric/semi-parametric IC regression), `interval`
  (NPMLE/Turnbull), `survival` (`Surv` type `"interval2"`).
- **Turnbull estimator**: the non-parametric MLE for interval-censored data — the KM analogue that
  uses the interval between the last negative and the first positive observation.
- **Parametric IC models**: Weibull or log-logistic via `icenReg::ic_par()`; report shape/scale
  parameters and compare AIC across distributions.
- **Mid-point imputation** (event time = midpoint of last negative and first positive) is
  acceptable as a sensitivity analysis, NOT as the primary method.
- **Multistate / transition models** (e.g., `msm`) for repeated transitions: account for
  subject-level clustering with a subject random effect or a sandwich variance, and check
  time-homogeneity (constant transition intensities) before trusting a single rate.
- **Reporting**: state the interval-censored nature of the data in Methods; report standard KM
  (for comparability with prior literature) and the IC estimates (primary or sensitivity).

---

## Reporting

- KM curves **with a number-at-risk table**; median survival with 95% CI (or the reason it is
  not reached).
- Cox HR (95% CI) with the **PH check stated**; for competing risks, the CIF and whether the
  HR is cause-specific or subdistribution.
- Events and person-time per group; the **reverse-KM median follow-up**; EPV for the model.
- The estimand and horizon, stated once and consistent everywhere.

---

## Common failures (flag at review)

- **Competing risks ignored** — naive 1−KM (or a cause-specific model presented as absolute
  risk) overestimates incidence; report a CIF and name cause-specific vs subdistribution (S3/S8).
- **A single time-averaged HR as the only estimand when the effect clearly changes over time**
  — prespecify an RMST / fixed-horizon difference beside it and describe the time pattern.
- **Harrell's C under heavy censoring** with no Uno/IPCW variant and no horizon (S6).
- **Median *survival* reported as "follow-up"** instead of the reverse-KM follow-up.
- **Estimand drift** — a primary endpoint/model/horizon re-designated post-hoc, or a derived
  statistic quoted off a non-primary estimate (S8).

---

## Anti-Hallucination

- Never hand-type an HR, median, CIF, or CI — compute it from the time-to-event CSV with a
  seeded script, and carry each estimate together with its CI.
- Do not report a Cox HR without the proportional-hazards check the code actually ran.
- Under competing risks, do not quote a 1−KM cumulative incidence — report the Aalen–Johansen /
  Fine–Gray CIF the code produced.
