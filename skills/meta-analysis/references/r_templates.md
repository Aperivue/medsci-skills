# R Code Templates for Meta-Analysis

## Required Packages

```r
# DTA meta-analysis
library(mada)      # bivariate model, SROC plot, paired forest plots
library(meta)      # general meta-analysis utilities, Deeks' test
library(metafor)   # advanced models

# Intervention meta-analysis
library(meta)
library(metafor)
```

## DTA Meta-Analysis

### Bivariate Model (Recommended)

```r
# data: one row per study with columns TP, FN, FP, TN
# Bivariate model (Reitsma et al.); with ANY zero cell, report the bivariate
# binomial GLMM as primary (analyze-stats dta_meta_analysis.R fits both)
fit <- reitsma(data, formula = cbind(tsens, tfpr) ~ 1, correction.control = "single")
summary(fit)               # rows "sensitivity" / "false pos. rate": back-transformed CIs
summary(SummaryPts(fit))   # LR+, LR-, DOR with CIs derived from the bivariate fit

# SROC curve with confidence and prediction regions (predict = FALSE by default)
plot(fit, sroclwd = 2, predict = TRUE, predlty = 2, main = "SROC Curve")
points(fpr(data), sens(data), pch = 2)

# Paired forest plots from the study-level data; mada:: because meta/metafor mask forest()
mada::forest(madad(data), type = "sens")
mada::forest(madad(data), type = "spec")
```

### Key Outputs for DTA

- Pooled sensitivity (95% CI)
- Pooled specificity (95% CI)
- Positive LR, negative LR and DOR with 95% CIs derived from the bivariate model (never pooled separately)
- SROC curve with confidence region and 95% prediction region (partial AUC over the observed FPR range, if an AUC is quoted)
- Heterogeneity: between-study SDs of logit(Se) and logit(FPR), their correlation, and the prediction region — not univariate I² for sensitivity and specificity (Cochrane DTA Handbook v1.0 ch.10 §10.4.3)
- Threshold effect: judged from the SROC plot and the bivariate correlation; a Spearman correlation is descriptive only

Rationale and citations: `phase6_statistical_synthesis.md` (DTA section).

### Publication Bias (DTA)

- Use Deeks' funnel plot asymmetry test (standard funnel plots are inappropriate for DTA), k ≥ 10:

```r
m_dor <- metabin(TP, TP + FN, FP, FP + TN, data = data, sm = "DOR")  # diseased first
metabias(m_dor, method.bias = "Deeks")
funnel(m_dor, yaxis = "ess")   # DOR against 1/sqrt(effective sample size)
```

## Intervention Meta-Analysis

### Random-Effects Model

```r
# Random-effects model (dat: ei/ni intervention, ec/nc control counts per study)
res <- metabin(ei, ni, ec, nc, data = dat, studlab = study, sm = "OR",
               method.tau = "REML",                        # PM if REML does not converge
               method.random.ci = "HK", adhoc.hakn.ci = "se",
               common = FALSE, random = TRUE, prediction = TRUE)
forest(res)
funnel(res)

# Heterogeneity
summary(res)  # I-squared, tau-squared, Q test, prediction interval

# Funnel asymmetry (k >= 10): Harbord or Peters for OR, not the original Egger
metabias(res, method.bias = "Harbord")

# Sensitivity analysis: leave-one-out
metainf(res, pooled = "random")
```

### Publication Bias (Intervention)

- Funnel plot + a test matched to the measure: OR → Harbord or Peters; RR → Peters; SMD → Pustejovsky; MD → Egger
- No test with fewer than 10 studies
- Asymmetry = small-study effects; publication bias is one possible cause, not the conclusion

## Subgroup / Meta-Regression

- Subgroup analysis for pre-specified covariates
- Meta-regression for continuous moderators
- Report interaction test p-value, not just within-subgroup p-values

## KM Curve Reconstruction (Guyot et al. 2012)

```r
library(IPDfromKM)
library(survival)

# Digitised curves: two columns, time and SURVIVAL probability, one file per arm.
# preprocess() expects survival; if the figure shows cumulative incidence,
# convert first (surv = 1 - cum).
ctrl <- read.csv("digitised_control.csv")
trt  <- read.csv("digitised_treatment.csv")

# Number-at-risk table under the figure
trisk      <- c(0, 6, 12, 18, 24, 30)
nrisk_ctrl <- c(51, 41, 30, 15, 7, 4)
nrisk_trt  <- c(50, 44, 36, 22, 12, 6)

# Reconstruct IPD per arm (maxy = 100 if the y-axis is in %);
# armID is only the label written to the `treat` column
ipd_ctrl <- getIPD(preprocess(ctrl, trisk, nrisk_ctrl, totalpts = 51, maxy = 1), armID = 0)$IPD
ipd_trt  <- getIPD(preprocess(trt,  trisk, nrisk_trt,  totalpts = 50, maxy = 1), armID = 1)$IPD
ipd <- rbind(ipd_ctrl, ipd_trt)          # columns: time, status, treat

# Meta-analysis input: the log hazard ratio and its SE
fit_cox  <- coxph(Surv(time, status) ~ treat, data = ipd)
log_hr   <- coef(fit_cox)[["treat"]]
se_loghr <- sqrt(vcov(fit_cox)[1, 1])    # pool with metagen(log_hr, se_loghr, sm = "HR")

# Single-arm outcome instead: the KM estimate and its SE at a pre-specified time
summary(survfit(Surv(time, status) ~ 1, data = ipd_ctrl), times = 24)
```

Key pitfalls:
- Never use `sum(status) / nrow(ipd)` as events/N: it ignores censoring and has no time
  horizon. A 2×2 table is valid only when every patient's status at the time point is known.
  Time-to-event outcomes are synthesised as HRs (Tierney et al. 2007, doi:10.1186/1745-6215-8-16)
- `getIPD()` returns a list; the reconstructed data are in `$IPD`
- `preprocess()` does NOT accept a `mateflag` parameter
- `armID` is an arbitrary group label (the package examples use 0 for control, 1 for treatment)
- Verify the reconstructed KM curve against the original figure, and the reconstructed HR
  against any HR the paper reports

## Pooled Proportion (Single-arm or combined)

```r
res_prop <- metaprop(event, n, data = dat,
                      studlab = study,
                      sm = "PLOGIT",          # logit transformation
                      method = "GLMM",         # exact binomial likelihood, no continuity correction
                      method.ci = "CP",        # Clopper-Pearson for individual studies
                      common = FALSE,
                      random = TRUE,
                      prediction = TRUE)

# Forest plot
forest(res_prop, xlim = c(0, 1),
       leftcols = c("studlab", "event", "n"),
       leftlabs = c("Study", "Events", "Total"))

# No Egger/funnel-asymmetry test for pooled proportions: the SE is a function of
# the proportion itself, so the test is uninterpretable (single_arm_proportion_ma.md §7)
```

## Sensitivity Analysis

- Leave-one-out analysis
- Excluding high RoB studies
- Excluding outliers (identified via influence diagnostics)
- Alternative model specifications
