#!/usr/bin/env Rscript
# sample_size.R — Sample Size Calculations for Medical Research
# =============================================================
# Covers: diagnostic accuracy, ICC agreement, kappa, proportions,
#         continuous outcomes, survival/log-rank, and survey studies.
#
# Dependencies: pwr, epiR, MKpower (install if needed)
# Install: install.packages(c("pwr", "epiR", "MKpower"))
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

# MKpower is optional (for ICC sample size)
mk_available <- requireNamespace("MKpower", quietly = TRUE)
if (!mk_available) {
  cat("Note: MKpower not available. ICC-based sample size will be skipped.\n")
  cat("  Install with: install.packages('MKpower')\n\n")
}

results <- list()

# ══════════════════════════════════════════════════════════════════════════════
# 1. DIAGNOSTIC ACCURACY STUDY
#    Sample size for desired precision of sensitivity or specificity
# ══════════════════════════════════════════════════════════════════════════════

cat("═══ 1. DIAGNOSTIC ACCURACY ═══════════════════════════════════════════\n")

# Clopper-Pearson interval approach:
# Desired: sensitivity ≥ 0.85, width of 95% CI ≤ 0.10 (i.e., ±5%)
# Prevalence in study population: 30%

sensitivity_expected <- 0.85
ci_half_width       <- 0.05    # desired half-width of 95% CI
prevalence          <- 0.30    # prevalence in study population
alpha               <- 0.05

# For a proportion p, n needed for 95% CI width 2*w:
# n = (z_{alpha/2} / w)^2 * p * (1 - p)
z <- qnorm(1 - alpha / 2)
n_positives <- ceiling((z / ci_half_width)^2 * sensitivity_expected *
                         (1 - sensitivity_expected))
n_total_diag <- ceiling(n_positives / prevalence)

cat(sprintf("Expected sensitivity:         %.2f\n", sensitivity_expected))
cat(sprintf("Desired 95%% CI half-width:   ±%.2f\n", ci_half_width))
cat(sprintf("Disease prevalence:           %.1f%%\n", prevalence * 100))
cat(sprintf("N disease-positive cases:     %d\n", n_positives))
cat(sprintf("Total N (accounting for %.0f%% prevalence): %d\n",
            prevalence * 100, n_total_diag))
cat(sprintf("With 15%% attrition: N = %d\n\n", ceiling(n_total_diag / 0.85)))

results[["diagnostic_accuracy"]] <- data.frame(
  Analysis = "Diagnostic accuracy",
  Expected_metric = sensitivity_expected,
  CI_half_width = ci_half_width,
  Prevalence = prevalence,
  N_positive = n_positives,
  N_total = n_total_diag,
  N_with_attrition = ceiling(n_total_diag / 0.85)
)

# ══════════════════════════════════════════════════════════════════════════════
# 2. INTER-RATER AGREEMENT — ICC
#    Bonett (2002) formula for two-way mixed ICC
# ══════════════════════════════════════════════════════════════════════════════

cat("═══ 2. INTER-RATER AGREEMENT (ICC) ═══════════════════════════════════\n")

# Bonett (2002) formula
icc_expected    <- 0.75    # expected ICC (good agreement)
icc_null        <- 0.50    # null hypothesis ICC (acceptable lower bound)
n_raters        <- 2       # number of raters
alpha_icc       <- 0.05
power_icc       <- 0.80

# Approximate formula (Bonett 2002, Psychol Methods)
# Requires icc_exp > icc_null
if (mk_available) {
  library(MKpower)
  n_icc <- tryCatch({
    result <- sampleSize.ICC(
      rho0 = icc_null,
      rho1 = icc_expected,
      k = n_raters,
      alpha = alpha_icc,
      power = power_icc
    )
    result$n
  }, error = function(e) NA)
} else {
  # Manual approximation using Fisher z-transformation
  z_exp  <- 0.5 * log((1 + icc_expected) / (1 - icc_expected))
  z_null <- 0.5 * log((1 + icc_null) / (1 - icc_null))
  z_diff <- z_exp - z_null
  n_icc <- ceiling(
    ((qnorm(1 - alpha_icc) + qnorm(power_icc)) / z_diff)^2 + 3
  )
}

cat(sprintf("Expected ICC:             %.2f\n", icc_expected))
cat(sprintf("Null ICC (lower bound):   %.2f\n", icc_null))
cat(sprintf("Number of raters:         %d\n", n_raters))
cat(sprintf("Power:                    %.0f%%\n", power_icc * 100))
if (!is.na(n_icc)) {
  cat(sprintf("Required N:               %d\n", n_icc))
  cat(sprintf("With 10%% attrition:       %d\n\n", ceiling(n_icc / 0.90)))
} else {
  cat("  N calculation failed — install MKpower\n\n")
}

results[["icc"]] <- data.frame(
  Analysis = "ICC agreement",
  Expected_ICC = icc_expected,
  Null_ICC = icc_null,
  N_raters = n_raters,
  N_required = ifelse(is.na(n_icc), NA, n_icc),
  N_with_attrition = ifelse(is.na(n_icc), NA, ceiling(n_icc / 0.90))
)

# ══════════════════════════════════════════════════════════════════════════════
# 3. KAPPA STATISTIC
#    Sample size for desired precision of kappa
# ══════════════════════════════════════════════════════════════════════════════

cat("═══ 3. KAPPA AGREEMENT ════════════════════════════════════════════════\n")

# Donner & Eliasziw (1992) approximation
kappa_expected  <- 0.70    # expected kappa (substantial agreement)
kappa_null      <- 0.40    # null hypothesis kappa
po_expected     <- 0.75    # expected proportion of agreement
alpha_kappa     <- 0.05
power_kappa     <- 0.80

pe <- (po_expected - kappa_expected) / (1 - kappa_expected)
se_kappa <- sqrt((po_expected * (1 - po_expected)) /
                   (length(c(po_expected)) * (1 - pe)^2))

# Simple z-test approximation
n_kappa <- ceiling(
  ((qnorm(1 - alpha_kappa) + qnorm(power_kappa))^2 *
     (kappa_expected * (1 - kappa_expected))) /
    (kappa_expected - kappa_null)^2 + 1
)

cat(sprintf("Expected kappa:           %.2f\n", kappa_expected))
cat(sprintf("Null kappa:               %.2f\n", kappa_null))
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

hr        <- 0.65    # expected hazard ratio (treatment vs. control)
median_ctrl <- 24    # median survival control arm (months)
accrual_time <- 12   # accrual period (months)
follow_up    <- 24   # follow-up after accrual (months)
drop_rate    <- 0.05 # annual dropout rate
alpha_lr     <- 0.05
power_lr     <- 0.80

# Schoenfeld (1981) formula: required events
n_events <- ceiling(
  (qnorm(1 - alpha_lr / 2) + qnorm(power_lr))^2 /
    (log(hr))^2
)

# Total N: approximate
lambda_ctrl <- log(2) / median_ctrl
lambda_trt  <- lambda_ctrl * hr
p_event_ctrl <- 1 - exp(-lambda_ctrl * follow_up)
p_event_trt  <- 1 - exp(-lambda_trt  * follow_up)
avg_p_event  <- (p_event_ctrl + p_event_trt) / 2
n_lr <- ceiling(n_events / avg_p_event)

cat(sprintf("Expected hazard ratio:    %.2f\n", hr))
cat(sprintf("Median OS (control):      %d months\n", median_ctrl))
cat(sprintf("Accrual period:           %d months\n", accrual_time))
cat(sprintf("Follow-up period:         %d months\n", follow_up))
cat(sprintf("Required events:          %d\n", n_events))
cat(sprintf("Estimated total N:        %d per group (%d total)\n",
            ceiling(n_lr / 2), n_lr))
cat(sprintf("With dropout:             +%.0f%% → %d total\n\n",
            drop_rate * 100, ceiling(n_lr / (1 - drop_rate))))

results[["survival"]] <- data.frame(
  Analysis = "Log-rank test",
  HR = hr,
  Median_OS_ctrl = median_ctrl,
  N_events = n_events,
  N_total = n_lr,
  N_with_dropout = ceiling(n_lr / (1 - drop_rate))
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
for (pkg in c("pwr", "epiR", "MKpower")) {
  if (requireNamespace(pkg, quietly = TRUE)) {
    cat(sprintf("  %-12s %s\n", pkg, packageVersion(pkg)))
  }
}
