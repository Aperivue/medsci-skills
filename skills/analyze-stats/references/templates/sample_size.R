#!/usr/bin/env Rscript
# sample_size.R — Sample Size Calculations for Medical Research
# =============================================================
# Covers: diagnostic accuracy, ICC agreement, kappa, proportions,
#         continuous outcomes, and survival/log-rank.
# Each section's example reproduces the package value noted beside it; the
# formulas and their checks are documented in calc-sample-size references/formulas.md.
#
# Dependencies: pwr, epiR (install if needed)
# Install: install.packages(c("pwr", "epiR"))
#
# Usage:
#   Rscript sample_size.R
#   Or source("sample_size.R") interactively
#
# Outputs:
#   Console: formatted results
#   CSV: sample_size_results.csv

set.seed(42)
cat(sprintf("sample_size.R | Date: %s | R: %s\n\n",
            format(Sys.Date()), R.version$version.string))

# ── Load packages ─────────────────────────────────────────────────────────────
pkgs <- c("pwr", "epiR")
for (pkg in pkgs) {
  if (!requireNamespace(pkg, quietly = TRUE)) {
    cat(sprintf("Installing %s...\n", pkg))
    install.packages(pkg, repos = "https://cran.r-project.org")
  }
  suppressPackageStartupMessages(library(pkg, character.only = TRUE))
}

results <- list()

# ══════════════════════════════════════════════════════════════════════════════
# 1. DIAGNOSTIC ACCURACY STUDY
#    Sample size for desired precision of sensitivity or specificity
# ══════════════════════════════════════════════════════════════════════════════

cat("═══ 1. DIAGNOSTIC ACCURACY ═══════════════════════════════════════════\n")

# Buderer (1996), Wald interval: sensitivity is estimated in the diseased,
# specificity in the non-diseased; N is the larger of the two requirements.
# Check: Se 0.85, Sp 0.90, prevalence 0.30, half-width 0.05 -> 654
#        (epiR::epi.ssdxsesp(test = 0.85, type = "se", Py = 0.3, epsilon = 0.05,
#         error = "absolute") -> 654; test = 0.90, type = "sp" -> 198)

sensitivity_expected <- 0.85
specificity_expected <- 0.90
ci_half_width       <- 0.05    # desired half-width of 95% CI
prevalence          <- 0.30    # prevalence in study population
alpha               <- 0.05

z <- qnorm(1 - alpha / 2)
n_for_se <- ceiling(z^2 * sensitivity_expected * (1 - sensitivity_expected) /
                      (ci_half_width^2 * prevalence))
n_for_sp <- ceiling(z^2 * specificity_expected * (1 - specificity_expected) /
                      (ci_half_width^2 * (1 - prevalence)))
n_total_diag <- max(n_for_se, n_for_sp)
n_positives <- ceiling(n_total_diag * prevalence)

cat(sprintf("Expected sensitivity / specificity: %.2f / %.2f\n",
            sensitivity_expected, specificity_expected))
cat(sprintf("Desired 95%% CI half-width:   ±%.2f\n", ci_half_width))
cat(sprintf("Disease prevalence:           %.1f%%\n", prevalence * 100))
cat(sprintf("N for sensitivity:            %d\n", n_for_se))
cat(sprintf("N for specificity:            %d\n", n_for_sp))
cat(sprintf("Total N (larger of the two):  %d (%d expected disease-positive)\n",
            n_total_diag, n_positives))
cat(sprintf("With 15%% attrition: N = %d\n\n", ceiling(n_total_diag / 0.85)))

results[["diagnostic_accuracy"]] <- data.frame(
  Analysis = "Diagnostic accuracy",
  Expected_metric = sensitivity_expected,
  Expected_specificity = specificity_expected,
  CI_half_width = ci_half_width,
  Prevalence = prevalence,
  N_positive = n_positives,
  N_total = n_total_diag,
  N_with_attrition = ceiling(n_total_diag / 0.85)
)

# ══════════════════════════════════════════════════════════════════════════════
# 2. INTER-RATER AGREEMENT — ICC
#    Walter, Eliasziw & Donner (1998) test of ICC against a null value
# ══════════════════════════════════════════════════════════════════════════════

cat("═══ 2. INTER-RATER AGREEMENT (ICC) ═══════════════════════════════════\n")

# Walter, Eliasziw & Donner (1998): test H0: ICC <= icc_null (one-sided), k ratings/subject.
# Check: 0.75 vs 0.50, k = 2 -> 36; k = 3 -> 24
#        (ICC.Sample.Size::calculateIccSampleSize(p = 0.75, p0 = 0.5, k = 2, tails = 1))
# For a CI-width (precision) aim use Bonett (2002) instead: presize::prec_icc().
icc_expected    <- 0.75    # expected ICC (good agreement)
icc_null        <- 0.50    # null hypothesis ICC (acceptable lower bound)
n_raters        <- 2       # number of raters
alpha_icc       <- 0.05
power_icc       <- 0.80

C0 <- (1 + n_raters * icc_null / (1 - icc_null)) /
  (1 + n_raters * icc_expected / (1 - icc_expected))
n_icc <- ceiling(1 + 2 * n_raters * (qnorm(1 - alpha_icc) + qnorm(power_icc))^2 /
                   ((n_raters - 1) * log(C0)^2))

cat(sprintf("Expected ICC:             %.2f\n", icc_expected))
cat(sprintf("Null ICC (lower bound):   %.2f\n", icc_null))
cat(sprintf("Number of raters:         %d\n", n_raters))
cat(sprintf("Power:                    %.0f%%\n", power_icc * 100))
cat(sprintf("Required N:               %d\n", n_icc))
cat(sprintf("With 10%% attrition:       %d\n\n", ceiling(n_icc / 0.90)))

results[["icc"]] <- data.frame(
  Analysis = "ICC agreement",
  Expected_ICC = icc_expected,
  Null_ICC = icc_null,
  N_raters = n_raters,
  N_required = n_icc,
  N_with_attrition = ceiling(n_icc / 0.90)
)

# ══════════════════════════════════════════════════════════════════════════════
# 3. KAPPA STATISTIC
#    Sample size to test kappa against a null value
# ══════════════════════════════════════════════════════════════════════════════

cat("═══ 3. KAPPA AGREEMENT ════════════════════════════════════════════════\n")

# Donner & Eliasziw (1992) goodness-of-fit, two raters, binary rating.
# The variance of kappa depends on the trait prevalence, so N does too.
# Check: 0.70 vs 0.40, prevalence 0.50 -> 74; prevalence 0.20 -> 107
#        (kappaSize::PowerBinary(kappa0 = 0.4, kappa1 = 0.7, props = 0.5, raters = 2));
# 3-6 raters or 3-5 categories: use kappaSize directly.
kappa_expected  <- 0.70    # expected kappa (substantial agreement)
kappa_null      <- 0.40    # null hypothesis kappa
prevalence_k    <- 0.50    # proportion of subjects with the trait
alpha_kappa     <- 0.05    # two-sided
power_kappa     <- 0.80

cell_probs <- function(k, p) {
  q <- 1 - p
  c(q^2 + k * p * q, 2 * (1 - k) * p * q, p^2 + k * p * q)
}
p_alt  <- cell_probs(kappa_expected, prevalence_k)
p_null <- cell_probs(kappa_null, prevalence_k)
chi2_k <- sum((p_alt - p_null)^2 / p_null)
n_kappa <- ceiling((qnorm(1 - alpha_kappa / 2) + qnorm(power_kappa))^2 / chi2_k)

cat(sprintf("Expected kappa:           %.2f\n", kappa_expected))
cat(sprintf("Null kappa:               %.2f\n", kappa_null))
cat(sprintf("Trait prevalence:         %.2f\n", prevalence_k))
cat(sprintf("Required N:               %d\n", n_kappa))
cat(sprintf("With 10%% attrition:       %d\n\n", ceiling(n_kappa / 0.90)))

results[["kappa"]] <- data.frame(
  Analysis = "Kappa agreement",
  Expected_kappa = kappa_expected,
  Null_kappa = kappa_null,
  N_required = n_kappa,
  N_with_attrition = ceiling(n_kappa / 0.90)
)

# ══════════════════════════════════════════════════════════════════════════════
# 4. TWO-PROPORTION COMPARISON (UNPAIRED)
#    Chi-square or Fisher's exact test
# ══════════════════════════════════════════════════════════════════════════════

cat("═══ 4. TWO-PROPORTION COMPARISON (UNPAIRED) ══════════════════════════\n")

p1 <- 0.70    # proportion in Group 1 (e.g., AI detection rate)
p2 <- 0.55    # proportion in Group 2 (e.g., conventional detection rate)
power_prop <- 0.80
alpha_prop <- 0.05

h <- ES.h(p1, p2)  # Cohen's h effect size
result_prop <- pwr.2p.test(h = h, sig.level = alpha_prop, power = power_prop)
n_prop <- ceiling(result_prop$n)

cat(sprintf("Group 1 proportion:       %.2f\n", p1))
cat(sprintf("Group 2 proportion:       %.2f\n", p2))
cat(sprintf("Cohen's h:                %.3f\n", h))
cat(sprintf("N per group:              %d\n", n_prop))
cat(sprintf("Total N:                  %d\n", n_prop * 2))
cat(sprintf("With 15%% attrition:       %d per group (%d total)\n\n",
            ceiling(n_prop / 0.85), ceiling(n_prop / 0.85) * 2))

results[["two_proportions"]] <- data.frame(
  Analysis = "Two proportions (unpaired)",
  P1 = p1, P2 = p2,
  Cohen_h = round(h, 3),
  N_per_group = n_prop,
  N_total = n_prop * 2,
  N_with_attrition = ceiling(n_prop / 0.85) * 2
)

# ══════════════════════════════════════════════════════════════════════════════
# 5. PAIRED PROPORTIONS (McNEMAR TEST)
#    For paired binary outcomes (e.g., two readers, pre-post)
# ══════════════════════════════════════════════════════════════════════════════

cat("═══ 5. PAIRED PROPORTIONS (McNEMAR) ══════════════════════════════════\n")

# Discordant proportions (only these matter for McNemar)
p01 <- 0.10    # P(Method A negative, Method B positive)
p10 <- 0.25    # P(Method A positive, Method B negative)
alpha_mc <- 0.05
power_mc <- 0.80

# Sample size for McNemar test
n_mc <- ceiling(
  (qnorm(1 - alpha_mc / 2) * sqrt(p01 + p10) +
     qnorm(power_mc) * sqrt(p01 + p10 - (p10 - p01)^2))^2 /
    (p10 - p01)^2
)

cat(sprintf("p01 (A-, B+):             %.2f\n", p01))
cat(sprintf("p10 (A+, B-):             %.2f\n", p10))
cat(sprintf("Required N (pairs):       %d\n", n_mc))
cat(sprintf("With 10%% attrition:       %d\n\n", ceiling(n_mc / 0.90)))

results[["mcnemar"]] <- data.frame(
  Analysis = "McNemar (paired proportions)",
  p01 = p01, p10 = p10,
  N_pairs = n_mc,
  N_with_attrition = ceiling(n_mc / 0.90)
)

# ══════════════════════════════════════════════════════════════════════════════
# 6. CONTINUOUS OUTCOME — INDEPENDENT SAMPLES t-TEST
# ══════════════════════════════════════════════════════════════════════════════

cat("═══ 6. CONTINUOUS OUTCOME (INDEPENDENT t-TEST) ═══════════════════════\n")

mean_diff <- 5.0    # expected mean difference
pooled_sd <- 10.0   # pooled SD (from literature or pilot)
d_cohen   <- mean_diff / pooled_sd  # Cohen's d
alpha_t   <- 0.05
power_t   <- 0.80

result_t <- pwr.t.test(d = d_cohen, sig.level = alpha_t,
                        power = power_t, type = "two.sample")
n_t <- ceiling(result_t$n)

cat(sprintf("Expected mean difference: %.1f\n", mean_diff))
cat(sprintf("Pooled SD:                %.1f\n", pooled_sd))
cat(sprintf("Cohen's d:                %.3f\n", d_cohen))
cat(sprintf("N per group:              %d\n", n_t))
cat(sprintf("Total N:                  %d\n", n_t * 2))
cat(sprintf("With 15%% attrition:       %d per group\n\n", ceiling(n_t / 0.85)))

results[["t_test"]] <- data.frame(
  Analysis = "Independent t-test",
  Mean_diff = mean_diff, Pooled_SD = pooled_sd,
  Cohen_d = round(d_cohen, 3),
  N_per_group = n_t,
  N_total = n_t * 2,
  N_with_attrition = ceiling(n_t / 0.85) * 2
)

# ══════════════════════════════════════════════════════════════════════════════
# 7. SURVIVAL ANALYSIS — LOG-RANK TEST
# ══════════════════════════════════════════════════════════════════════════════

cat("═══ 7. SURVIVAL ANALYSIS (LOG-RANK TEST) ═════════════════════════════\n")

# Schoenfeld (1983) events, with the allocation term p(1 - p); patients from the
# event probability under uniform accrual, exponential survival and exponential dropout.
# Check: HR 0.65, 1:1 -> 170 events (gsDesign::nEvents(hr = 0.65, alpha = 0.05,
#        beta = 0.2, sided = 2) = 169.18); N 356 (gsDesign::nSurv(lambdaC = log(2)/24,
#        hr = 0.65, eta = -log(0.95)/12, R = 12, T = 36, minfup = 24, method = "Schoenfeld")
#        n = 355.40 -> 178 per arm)
hr        <- 0.65    # expected hazard ratio (treatment vs. control)
p_alloc   <- 0.5     # proportion randomised to treatment
median_ctrl <- 24    # median survival control arm (months)
accrual_time <- 12   # accrual period (months)
follow_up    <- 24   # minimum follow-up after accrual (months)
drop_rate    <- 0.05 # proportion lost to follow-up per year
alpha_lr     <- 0.05
power_lr     <- 0.80

d_raw <- (qnorm(1 - alpha_lr / 2) + qnorm(power_lr))^2 /
  (p_alloc * (1 - p_alloc) * log(hr)^2)
n_events <- ceiling(d_raw)

lambda_ctrl <- log(2) / median_ctrl
lambda_trt  <- lambda_ctrl * hr
eta <- -log(1 - drop_rate) / 12          # monthly dropout hazard
total_time <- accrual_time + follow_up
p_event <- function(lambda) {
  a <- lambda + eta
  lambda / a * (1 - (exp(-a * follow_up) - exp(-a * total_time)) / (a * accrual_time))
}
p_bar <- p_alloc * p_event(lambda_trt) + (1 - p_alloc) * p_event(lambda_ctrl)
n_trt  <- ceiling(p_alloc * d_raw / p_bar)
n_ctrl <- ceiling((1 - p_alloc) * d_raw / p_bar)
n_lr <- n_trt + n_ctrl

cat(sprintf("Expected hazard ratio:    %.2f\n", hr))
cat(sprintf("Median OS (control):      %d months\n", median_ctrl))
cat(sprintf("Accrual period:           %d months\n", accrual_time))
cat(sprintf("Minimum follow-up:        %d months\n", follow_up))
cat(sprintf("Dropout:                  %.0f%% per year (inside P(event))\n", drop_rate * 100))
cat(sprintf("Required events:          %d\n", n_events))
cat(sprintf("P(event) averaged:        %.4f\n", p_bar))
cat(sprintf("Total N:                  %d (%d treatment + %d control)\n\n",
            n_lr, n_trt, n_ctrl))

results[["survival"]] <- data.frame(
  Analysis = "Log-rank test",
  HR = hr,
  Median_OS_ctrl = median_ctrl,
  N_events = n_events,
  N_total = n_lr,
  N_with_dropout = n_lr   # dropout is already inside P(event)
)

# ══════════════════════════════════════════════════════════════════════════════
# SUMMARY TABLE
# ══════════════════════════════════════════════════════════════════════════════

cat("\n═══ SUMMARY ═══════════════════════════════════════════════════════════\n")
cat(sprintf("  %-35s %6s %6s\n", "Analysis", "N min", "N+attrition"))
cat(rep("─", 55), "\n", sep="")

for (nm in names(results)) {
  r <- results[[nm]]
  n_min <- ifelse("N_total" %in% names(r), r$N_total,
                  ifelse("N_pairs" %in% names(r), r$N_pairs,
                         ifelse("N_required" %in% names(r), r$N_required,
                                r$N_positives)))
  n_att <- ifelse("N_with_attrition" %in% names(r), r$N_with_attrition,
                  ifelse("N_with_dropout" %in% names(r), r$N_with_dropout, NA))
  cat(sprintf("  %-35s %6s %6s\n",
              substr(r$Analysis, 1, 35),
              ifelse(is.na(n_min), "—", n_min),
              ifelse(is.na(n_att), "—", n_att)))
}

cat("\n")
cat(sprintf("Note: All calculations use α = 0.05 (two-tailed), power = 80%%\n"))
cat(sprintf("      unless otherwise specified above.\n"))

# ── Save CSV ──────────────────────────────────────────────────────────────────
all_results <- do.call(rbind.fill_safe <- function(x) {
  all_cols <- unique(unlist(lapply(x, names)))
  do.call(rbind, lapply(x, function(d) {
    missing_cols <- setdiff(all_cols, names(d))
    d[missing_cols] <- NA
    d[all_cols]
  }))
}, list(results))

# Simple bind_rows equivalent
result_list <- lapply(results, function(r) {
  data.frame(lapply(r, as.character), stringsAsFactors = FALSE)
})
result_df <- do.call(function(...) {
  all_cols <- unique(unlist(lapply(list(...), names)))
  rows <- lapply(list(...), function(d) {
    for (col in setdiff(all_cols, names(d))) d[[col]] <- NA
    d[all_cols]
  })
  do.call(rbind, rows)
}, result_list)

write.csv(result_df, "sample_size_results.csv", row.names = FALSE)
cat("\nSaved: sample_size_results.csv\n")

# ── Session info ──────────────────────────────────────────────────────────────
cat("\n── Session Info ─────────────────────────────────────────────────────\n")
cat(sprintf("R: %s\n", R.version$version.string))
cat(sprintf("Date: %s\n", format(Sys.time())))
for (pkg in c("pwr", "epiR")) {
  if (requireNamespace(pkg, quietly = TRUE)) {
    cat(sprintf("  %-12s %s\n", pkg, packageVersion(pkg)))
  }
}
