# R Code Templates for Meta-Analysis

## Required Packages

```r
# DTA meta-analysis
library(mada)      # bivariate model, forest/SROC plots
library(meta)      # general meta-analysis utilities
library(metafor)   # advanced models

# Intervention meta-analysis
library(meta)
library(metafor)
```

## DTA Meta-Analysis

### Bivariate Model (Recommended)

```r
# Bivariate model (Reitsma et al.)
fit <- reitsma(data, formula = cbind(tsens, tfpr) ~ 1)
summary(fit)

# SROC curve with confidence and prediction regions
plot(fit, sroclwd = 2, main = "SROC Curve")

# Forest plot (paired: sensitivity + specificity)
forest(fit, type = "sens")
forest(fit, type = "spec")
```

### Key Outputs for DTA

- Pooled sensitivity (95% CI)
- Pooled specificity (95% CI)
- Pooled positive LR, negative LR
- Pooled DOR
- SROC curve with AUC, confidence region, prediction region
- Heterogeneity: I-squared for sensitivity and specificity separately
- Threshold effect: Spearman correlation between sensitivity and FPR

### Publication Bias (DTA)

- Use Deeks' funnel plot asymmetry test (standard funnel plots are inappropriate for DTA)

## Intervention Meta-Analysis

### Random-Effects Model

```r
# Random-effects model
res <- metagen(TE, seTE, data = dat, studlab = study,
               method.tau = "REML", sm = "OR")
forest(res)
funnel(res)

# Heterogeneity
summary(res)  # I-squared, tau-squared, Q test

# Publication bias
metabias(res, method.bias = "Egger")

# Sensitivity analysis: leave-one-out
metainf(res, pooled = "random")
```

### Publication Bias (Intervention)

- Funnel plot + Egger's or Peters' test
- Note: Tests underpowered for <10 studies

## Subgroup / Meta-Regression

- Subgroup analysis for pre-specified covariates
- Meta-regression for continuous moderators
- Report interaction test p-value, not just within-subgroup p-values

## KM Curve Reconstruction (Guyot et al. 2012)

```r
library(IPDfromKM)

# Read digitised KM curve (time, cumulative event rate)
dat <- read.csv("digitised_curve.csv")

# Number-at-risk from figure
trisk <- c(0, 6, 12, 18, 24, 30)  # time points
nrisk <- c(51, 41, 30, 15, 7, 4)  # at-risk counts
totalpts <- 51

# Reconstruct IPD
preproc <- preprocess(dat, trisk, nrisk, totalpts, maxy = 1)
ipd <- getIPD(preproc, armID = 1)  # armID = 1 (NOT 0)

# Count events for meta-analysis input
events <- sum(ipd$status == 1)
total <- nrow(ipd)
cat(sprintf("Events: %d / %d\n", events, total))
```

Key pitfalls:
- `preprocess()` does NOT accept a `mateflag` parameter
- `armID` starts at 1, not 0
- Verify reconstructed KM visually against original figure

## Pooled Proportion (Single-arm or combined)

```r
res_prop <- metaprop(event, n, data = dat,
                      studlab = study,
                      sm = "PLOGIT",          # logit transformation
                      method.tau = "ML",       # maximum likelihood
                      method.ci = "CP",        # Clopper-Pearson for individual studies
                      common = FALSE,
                      random = TRUE)

# Forest plot
forest(res_prop, xlim = c(0, 1),
       leftcols = c("studlab", "event", "n"),
       leftlabs = c("Study", "Events", "Total"))

# Egger's test (k >= 10)
metabias(res_prop, method.bias = "Egger")
```

## Sensitivity Analysis

- Leave-one-out analysis
- Excluding high RoB studies
- Excluding outliers (identified via influence diagnostics)
- Alternative model specifications
