# Table: Survival / Time-to-Event (Cox) Results

## Reporting Guidelines
- **STROBE**: Observational time-to-event — HR with 95% CI, plus events, person-time, and follow-up.
- **TRIPOD**: Prognostic models — coefficients/HR with CI and a discrimination measure (C-index).

## Standard Structure

```
Table 3. Cox Proportional Hazards for [Outcome] (events = [E] / N = [N];
median follow-up [X.X] y [reverse Kaplan-Meier])

Variable            Events/N    IR*      Univariable          Multivariable
                                         HR (95% CI)  P       HR (95% CI)   P

Age, per 10 y         —         —        1.28 (1.11-1.47) <.001 1.21 (1.04-1.41) .01
Sex, male vs female  120/410   3.8      1.42 (1.02-1.98) .04   1.33 (0.94-1.88) .10
Stage III vs I-II    180/300   9.1      2.65 (1.88-3.74) <.001 2.31 (1.59-3.36) <.001
Biomarker ≥[cut]     ...        ...      ...                    ...

IR = incidence rate per 100 person-years; HR = hazard ratio; CI = confidence interval.
Reference categories: age <[x], female, Stage I-II, biomarker <[cut].
Model adjusted for [covariate set]. Proportional-hazards assumption assessed by
Schoenfeld residuals (global P = [.xx]). C-index [0.xx].
```

## Rules
- **Events and person-time, not just N**: show events per group and an incidence rate (or
  person-years); a HR without the event count is uninterpretable and hides a sparse-data model.
- **Median follow-up via reverse Kaplan-Meier** (not the mean of observed times), reported in
  the title or a row; report median survival with 95% CI where estimable.
- **Reference category** always stated (set factor levels explicitly so the model matches the
  footnote); **clinically meaningful units** for continuous ("per 10 y", not "per 1 y");
  **effect measure = HR** (Cox), and match the design.
- **Median survival** with 95% CI where estimable; report **"not reached"** when the event rate
  stays below 50% — never substitute the maximum observed follow-up or leave a blank.
- **Univariable AND multivariable** (or justify omission); state the variable-selection rule
  and any forced confounders in a footnote.
- **Proportional-hazards assumption**: report that Schoenfeld residuals were checked. If
  **violated**, do not present a single time-averaged HR — report a piecewise/time-stratified
  HR or an **RMST difference at a fixed horizon**, and say so.
- **EPV / sparse strata**: with events/covariates < 10, flag instability (Firth/penalized Cox,
  profile-likelihood CIs); for any stratum-specific HR with < 10 events, add a sparse-stratum
  caveat with its reference contrast and event count.
- **Nested units** (multiple lesions/both eyes/repeated episodes): note cluster-robust
  (sandwich) variance was used so CIs are not artificially narrow.
- **Interval-censored** (event detected at scheduled visits, not observed exactly): note the
  interval-censored model; do not present a right-censored Cox as if times were exact.
- **Censoring**: state how censoring was defined and the competing-risk handling (cause-specific
  vs subdistribution) when competing events exist.

## gtsummary / R Code
```r
library(survival); library(gtsummary); library(dplyr)

# Set reference levels explicitly so the model matches the table footnote
d <- d %>% mutate(
  sex   = relevel(factor(sex), ref = "female"),
  stage = relevel(factor(stage), ref = "I-II")
)

# Median follow-up (reverse KM): event indicator flipped
fu <- survfit(Surv(time, 1 - status) ~ 1, data = d)  # report median of `fu`

# Univariable
uv <- tbl_uvregression(
  d[, c("time","status","age","sex","stage","biomarker")],
  method = coxph, y = Surv(time, status),
  exponentiate = TRUE
)

# Multivariable + PH check
fit <- coxph(Surv(time, status) ~ age + sex + stage + biomarker, data = d)
cox.zph(fit)                       # Schoenfeld global + per-term; if violated, see Rules
mv <- tbl_regression(fit, exponentiate = TRUE) %>% add_global_p() %>% bold_p(t = 0.05)

tbl_merge(list(uv, mv), tab_spanner = c("Univariable", "Multivariable"))
# concordance(fit)$concordance   # C-index for the footnote

# Nested units (multiple lesions/both eyes/repeated episodes): cluster-robust variance
# fit_r <- coxph(Surv(time, status) ~ age + sex + stage + cluster(id), data = d, robust = TRUE)
```
