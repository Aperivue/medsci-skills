# Survival / Time-to-Event Guide

Estimating time-to-event outcomes and prognostic effects. The estimator is easy to
call; the ways these analyses fail review are (1) ignoring **competing risks** so a naive
1−KM **overestimates** the cumulative incidence, (2) reporting a **single time-averaged
hazard ratio** when the proportional-hazards assumption is violated, and (3) **estimand
drift** — quoting a subdistribution hazard for an etiologic claim or a cause-specific hazard
for an absolute-risk claim. This guide produces the right estimand; the operational caveats
(EPV gate, cluster-robust CIs, interval-censoring) live in the SKILL.md `### Survival
Analysis` section.

---

## When to Use

- **Single event type, right-censored** → Kaplan–Meier (unadjusted) + Cox proportional-hazards
  (adjusted HR with 95% CI); the log-rank test for a KM group comparison.
- **≥2 competing event types** (recurrence + competing death, or cause-specific mortality) →
  cumulative incidence functions + **cause-specific Cox** or **Fine–Gray** — see below.
- **Prognostic model discrimination** → a C-index variant matched to the censoring + a
  time-dependent AUC at a clinical horizon (S6).
- NOT for: events detected only at scheduled visits → interval-censored methods (SKILL.md);
  recurrent events per subject → a cluster-robust or frailty model (SKILL.md cluster rule);
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

---

## Proportional hazards, and RMST when it fails

A single Cox HR is a time-average; if PH is violated it averages a changing effect. Test PH,
and when it fails report a **restricted mean survival time (RMST) difference** at a fixed
horizon (an estimand that stays interpretable under non-PH) rather than one HR.

```python
from lifelines import CoxPHFitter
cph = CoxPHFitter().fit(df, "time", "event")
cph.check_assumptions(df, p_value_threshold=0.05)   # Schoenfeld; significant -> PH violated
```

```r
library(survRM2)
rmst2(time, status, arm, tau = 3)   # RMST difference at tau=3 years, valid under non-PH
```

Do not report a single time-averaged HR alongside a significant Schoenfeld test without also
giving a piecewise/time-stratified HR or an RMST difference (SKILL.md PH-violation rule).

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
- **A single time-averaged HR under a violated PH assumption** — needs a piecewise HR or RMST.
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
