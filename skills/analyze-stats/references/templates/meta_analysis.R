#!/usr/bin/env Rscript
# meta_analysis.R — Comprehensive Meta-Analysis Script
# =====================================================
# Random-effects pairwise meta-analysis: REML estimator of tau^2 (Paule-Mandel
# if REML fails to converge), Hartung-Knapp CI with the ad hoc variance
# correction, t-based prediction interval.
# Supports binary outcomes (OR/RR) and continuous outcomes (MD/SMD).
# Diagnostic accuracy (Se/Sp) is NOT handled here: use dta_meta_analysis.R.
# Rare binary events (pooled rate < 1% or zero-event arms) need the rare-event
# branch (Peto / MH without correction / GLMM), not this inverse-variance pool.
#
# Dependencies: meta, metafor, dplyr, ggplot2
# Install: install.packages(c("meta", "metafor", "dplyr", "ggplot2"))
#
# Input CSV: see EXAMPLE DATA section below for format
#
# Usage:
#   Rscript meta_analysis.R --input studies.csv --effect OR --output meta_results
#   Optional: --subgroup <column>
#   Or source() interactively — edit parameters in CONFIGURATION section

set.seed(42)
suppressPackageStartupMessages({
  library(meta)
  library(metafor)
  library(dplyr)
  library(ggplot2)
})

cat(sprintf("meta_analysis.R | Date: %s | R: %s\n",
            format(Sys.Date()), R.version$version.string))
cat(sprintf("meta: %s | metafor: %s\n\n",
            packageVersion("meta"), packageVersion("metafor")))

# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION — Modify these for your analysis
# ══════════════════════════════════════════════════════════════════════════════

CONFIG <- list(
  input_file   = "studies.csv",        # Path to study data CSV
  effect_type  = "OR",                 # "OR", "RR", "MD", "SMD"
  outcome_name = "Primary outcome",    # Label for forest plot
  alpha        = 0.05,                 # Significance threshold
  output_dir   = ".",                  # Output directory
  output_prefix = "meta",             # File name prefix
  # Subgroup column name in CSV (NA to skip)
  subgroup_col = NA                    # e.g., "scanner_type"
)

# Command-line flags override CONFIG (see Usage above)
cli_args <- commandArgs(trailingOnly = TRUE)
cli_value <- function(flag) {
  i <- match(flag, cli_args)
  if (is.na(i) || i == length(cli_args)) NULL else cli_args[i + 1]
}
input_given <- !is.null(cli_value("--input"))
if (input_given)                     CONFIG$input_file    <- cli_value("--input")
if (!is.null(cli_value("--effect")))   CONFIG$effect_type   <- toupper(cli_value("--effect"))
if (!is.null(cli_value("--output")))   CONFIG$output_prefix <- cli_value("--output")
if (!is.null(cli_value("--subgroup"))) CONFIG$subgroup_col  <- cli_value("--subgroup")

if (!CONFIG$effect_type %in% c("OR", "RR", "MD", "SMD")) {
  stop(sprintf("Unsupported effect type: %s. Use OR, RR, MD, or SMD.", CONFIG$effect_type))
}

# Ratio measures are pooled on the log scale and back-transformed;
# differences (MD/SMD) are pooled and reported on their natural scale.
is_ratio <- CONFIG$effect_type %in% c("OR", "RR")
bt <- if (is_ratio) exp else identity

# ══════════════════════════════════════════════════════════════════════════════
# EXAMPLE DATA — Replace with real data or load from CSV
# ══════════════════════════════════════════════════════════════════════════════

example_data_OR <- data.frame(
  study_label    = c("Kim 2019", "Park 2020", "Lee 2021",
                     "Chen 2022", "Wang 2023", "Smith 2023"),
  events_treat   = c(28, 45, 19, 67, 52, 31),   # Events in treatment arm
  n_treat        = c(120, 180, 85, 240, 200, 130),
  events_control = c(42, 62, 28, 89, 75, 44),   # Events in control arm
  n_control      = c(118, 175, 87, 235, 195, 128),
  subgroup       = c("A", "A", "A", "B", "B", "B")
)

example_data_MD <- data.frame(
  study_label = c("Study A", "Study B", "Study C", "Study D"),
  mean_treat  = c(24.3, 21.5, 26.1, 22.8),
  sd_treat    = c(6.2, 5.8, 7.1, 5.5),
  n_treat     = c(85, 120, 60, 95),
  mean_control = c(28.1, 26.0, 30.5, 27.2),
  sd_control  = c(6.5, 6.0, 7.3, 5.8),
  n_control   = c(83, 118, 58, 92),
  subgroup    = c("X", "X", "Y", "Y")
)

# ══════════════════════════════════════════════════════════════════════════════
# LOAD DATA
# ══════════════════════════════════════════════════════════════════════════════

load_data <- function(config) {
  if (file.exists(config$input_file)) {
    df <- read.csv(config$input_file, stringsAsFactors = FALSE)
    cat(sprintf("Loaded: %s (%d studies)\n\n", config$input_file, nrow(df)))
    return(df)
  }
  if (input_given) stop(sprintf("Input file not found: %s", config$input_file))
  cat("Input file not found. Using built-in EXAMPLE data — these are not your studies.\n\n")
  if (config$effect_type %in% c("OR", "RR")) example_data_OR else example_data_MD
}

df <- load_data(CONFIG)

# ══════════════════════════════════════════════════════════════════════════════
# PRIMARY META-ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════

fit_meta <- function(df, effect_type, method.tau) {
  # Random-effects weights are inverse-variance in every branch. The HK CI uses
  # the ad hoc variance correction (adhoc.hakn.ci = "se"): without it, HK can
  # give a CI narrower than the common-effect CI when tau^2 is estimated as 0.
  if (effect_type %in% c("OR", "RR")) {
    metabin(
      event.e = events_treat, n.e = n_treat,
      event.c = events_control, n.c = n_control,
      studlab = study_label, data = df,
      sm = effect_type,
      method = "Inverse",
      method.tau = method.tau,
      method.random.ci = "HK", adhoc.hakn.ci = "se",
      common = FALSE, random = TRUE,
      prediction = TRUE,
      title = paste("Meta-analysis:", effect_type)
    )
  } else {
    metacont(
      n.e = n_treat, mean.e = mean_treat, sd.e = sd_treat,
      n.c = n_control, mean.c = mean_control, sd.c = sd_control,
      studlab = study_label, data = df,
      sm = effect_type,
      method.tau = method.tau,
      method.random.ci = "HK", adhoc.hakn.ci = "se",
      common = FALSE, random = TRUE,
      prediction = TRUE
    )
  }
}

run_meta <- function(df, effect_type, verbose = TRUE) {
  if (verbose) {
    cat(sprintf("═══ META-ANALYSIS: %s ═══════════════════════════════════\n",
                effect_type))
  }
  # REML is the default tau^2 estimator (Cochrane Handbook v6.5 §10.10.4.4);
  # Paule-Mandel always has a solution, so it is the fallback, not DL.
  tryCatch(
    fit_meta(df, effect_type, "REML"),
    error = function(e) {
      cat(sprintf("  REML did not converge (%s); using Paule-Mandel.\n", conditionMessage(e)))
      fit_meta(df, effect_type, "PM")
    }
  )
}

m <- run_meta(df, CONFIG$effect_type)

if (is_ratio) {
  total_events <- sum(df$events_treat + df$events_control)
  total_n      <- sum(df$n_treat + df$n_control)
  if (any(c(df$events_treat, df$events_control) == 0) || total_events / total_n < 0.01) {
    cat("  WARNING: zero-event arm(s) or pooled event rate < 1%. Inverse-variance pooling\n",
        "          with a 0.5 correction is the wrong tool for rare events: use Peto,\n",
        "          MH without a zero-cell correction, or a GLMM (meta-analysis skill,\n",
        "          phase6_statistical_synthesis.md, 'Rare Events').\n", sep = "")
  }
}

# ── Print summary ─────────────────────────────────────────────────────────────
cat("\n─── Pooled Estimate ─────────────────────────────────────────────────\n")
cat(sprintf("  %s (random-effects, %s, HK CI): %.3f (95%% CI: %.3f – %.3f)\n",
            CONFIG$effect_type, m$method.tau,
            bt(m$TE.random), bt(m$lower.random), bt(m$upper.random)))
cat(sprintf("  95%% Prediction interval: %.3f – %.3f\n",
            bt(m$lower.predict), bt(m$upper.predict)))
m_classic <- update(m, method.random.ci = "classic")
cat(sprintf("  Sensitivity analysis, Wald-type (classic) CI: %.3f – %.3f\n",
            bt(m_classic$lower.random), bt(m_classic$upper.random)))
cat(sprintf("\n─── Heterogeneity ──────────────────────────────────────────────────\n"))
cat(sprintf("  I² = %.1f%% (95%% CI: %.1f%% – %.1f%%)\n",
            m$I2 * 100, m$lower.I2 * 100, m$upper.I2 * 100))
cat(sprintf("  τ² = %.4f (τ = %.4f), estimator: %s\n", m$tau^2, m$tau, m$method.tau))
cat(sprintf("  Cochran Q = %.2f, df = %d, P = %.3f\n",
            m$Q, m$df.Q, m$pval.Q))

# ══════════════════════════════════════════════════════════════════════════════
# SUBGROUP ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════

if (!is.na(CONFIG$subgroup_col) && CONFIG$subgroup_col %in% names(df)) {
  cat(sprintf("\n═══ SUBGROUP ANALYSIS: %s ════════════════════════════════\n",
              CONFIG$subgroup_col))

  m_sub <- update(m, subgroup = df[[CONFIG$subgroup_col]])

  cat("  Subgroup estimates:\n")
  for (j in seq_along(m_sub$subgroup.levels)) {
    cat(sprintf("  %s (k = %d): %s = %.3f (95%% CI: %.3f – %.3f), I² = %.1f%%\n",
                m_sub$subgroup.levels[j], m_sub$k.w[j], CONFIG$effect_type,
                bt(m_sub$TE.random.w[j]), bt(m_sub$lower.random.w[j]),
                bt(m_sub$upper.random.w[j]), m_sub$I2.w[j] * 100))
  }

  # Test for subgroup interaction
  cat(sprintf("\n  Test for subgroup differences:\n"))
  cat(sprintf("  Q_between = %.2f, df = %d, P = %.3f\n",
              m_sub$Q.b.random, m_sub$df.Q.b, m_sub$pval.Q.b.random))
  if (m_sub$pval.Q.b.random < 0.05) {
    cat("  → Significant subgroup heterogeneity detected.\n")
  } else {
    cat("  → No significant subgroup heterogeneity.\n")
  }
}

# ══════════════════════════════════════════════════════════════════════════════
# SENSITIVITY ANALYSIS — Leave-one-out
# ══════════════════════════════════════════════════════════════════════════════

cat("\n═══ SENSITIVITY ANALYSIS: Leave-one-out ══════════════════════════════\n")

loo_results <- data.frame(
  Study_removed = character(),
  Pooled_effect = numeric(),
  CI_lower = numeric(),
  CI_upper = numeric(),
  I2 = numeric(),
  stringsAsFactors = FALSE
)

for (i in 1:nrow(df)) {
  df_loo <- df[-i, ]
  m_loo <- tryCatch(
    run_meta(df_loo, CONFIG$effect_type, verbose = FALSE),
    error = function(e) NULL
  )
  if (!is.null(m_loo)) {
    loo_results <- rbind(loo_results, data.frame(
      Study_removed = df$study_label[i],
      Pooled_effect = round(bt(m_loo$TE.random), 3),
      CI_lower = round(bt(m_loo$lower.random), 3),
      CI_upper = round(bt(m_loo$upper.random), 3),
      I2 = round(m_loo$I2 * 100, 1)
    ))
  }
}

cat("  Leave-one-out estimates:\n")
print(loo_results, row.names = FALSE)

loo_file <- file.path(CONFIG$output_dir,
                       paste0(CONFIG$output_prefix, "_leave_one_out.csv"))
write.csv(loo_results, loo_file, row.names = FALSE)
cat(sprintf("\nSaved: %s\n", loo_file))

# ══════════════════════════════════════════════════════════════════════════════
# SMALL-STUDY EFFECTS — funnel asymmetry test + trim-and-fill sensitivity
# ══════════════════════════════════════════════════════════════════════════════

# The original Egger test is not recommended for OR or SMD because the effect
# and its SE are artefactually correlated (Cochrane Handbook v6.5 ch.13).
bias_method <- switch(CONFIG$effect_type,
                      OR  = "Harbord",      # Harbord et al. 2006
                      RR  = "Peters",       # regression on 1/N, not on the SE
                      SMD = "Pustejovsky",  # Pustejovsky & Rodgers 2019
                      MD  = "Egger")

# k counts the studies actually pooled: studies with no events (or only events)
# in both arms are excluded from an OR/RR pool, so m$k can be < nrow(df).
if (m$k >= 10) {
  cat("\n═══ SMALL-STUDY EFFECTS ═════════════════════════════════════════════\n")

  pb <- metabias(m, method.bias = bias_method, k.min = 10)
  if (is.null(pb$pval)) {
    # metabias() returns no test when fewer than k.min studies are usable
    cat(sprintf("  %s test not computed by metabias() (too few usable studies)\n", bias_method))
  } else {
    cat(sprintf("  %s test for funnel plot asymmetry: t = %.3f, df = %d, P = %.3f\n",
                bias_method, pb$statistic, pb$df, pb$pval))
    if (pb$pval < CONFIG$alpha) {
      cat("  → Funnel plot asymmetry (small-study effects) detected; publication bias is\n",
          "    only one possible cause (heterogeneity, chance, and poorer small-study\n",
          "    quality are others).\n", sep = "")
    } else {
      cat("  → No evidence of funnel plot asymmetry (low power; not proof of no bias).\n")
    }
  }

  # Trim-and-fill is a sensitivity analysis, not a bias-corrected estimate
  # (Peters et al. 2007, doi:10.1002/sim.2889).
  tf <- trimfill(m)
  cat(sprintf("\n  Trim-and-fill (sensitivity analysis only): %d studies imputed\n", tf$k0))
  cat(sprintf("  %s with imputed studies: %.3f (95%% CI: %.3f – %.3f)\n",
              CONFIG$effect_type,
              bt(tf$TE.random), bt(tf$lower.random), bt(tf$upper.random)))

  # Funnel plot
  funnel_file <- file.path(CONFIG$output_dir,
                            paste0(CONFIG$output_prefix, "_funnel.pdf"))
  pdf(funnel_file, width = 5, height = 5)
  funnel(m, type = "contour", studlab = FALSE)
  title(main = "Contour-enhanced funnel plot")
  dev.off()
  cat(sprintf("\nSaved: %s\n", funnel_file))
} else {
  cat(sprintf("\nSmall-study effects: not tested (k = %d studies pooled < 10; tests have too little power)\n",
              m$k))
}

# ══════════════════════════════════════════════════════════════════════════════
# FOREST PLOT
# ══════════════════════════════════════════════════════════════════════════════

cat("\n═══ FOREST PLOT ══════════════════════════════════════════════════════\n")

forest_file_pdf <- file.path(CONFIG$output_dir,
                              paste0(CONFIG$output_prefix, "_forest.pdf"))
forest_file_png <- file.path(CONFIG$output_dir,
                              paste0(CONFIG$output_prefix, "_forest.png"))

# PDF (default meta column labels match the columns shown for each outcome type)
pdf(forest_file_pdf, width = 10, height = max(6, nrow(df) * 0.35 + 3))
forest(m,
       sortvar    = TE,
       prediction = TRUE,
       print.tau2 = TRUE,
       col.diamond = "#D55E00",
       col.predict = "#009E73",
       fontsize   = 10,
       smlab      = paste("Random-effects", CONFIG$effect_type))
dev.off()
cat(sprintf("Saved: %s\n", forest_file_pdf))

# PNG (300 DPI)
png(forest_file_png, width = 10, height = max(6, nrow(df) * 0.35 + 3),
    units = "in", res = 300)
forest(m,
       sortvar    = TE,
       prediction = TRUE,
       print.tau2 = TRUE,
       col.diamond = "#D55E00",
       col.predict = "#009E73",
       fontsize   = 9)
dev.off()
cat(sprintf("Saved: %s\n", forest_file_png))

# ══════════════════════════════════════════════════════════════════════════════
# RESULTS SUMMARY CSV
# ══════════════════════════════════════════════════════════════════════════════

summary_df <- data.frame(
  Metric = c(
    paste("Pooled", CONFIG$effect_type, "(random-effects)"),
    "95% CI lower (Hartung-Knapp, ad hoc corrected)",
    "95% CI upper (Hartung-Knapp, ad hoc corrected)",
    "95% CI lower (classic, sensitivity)",
    "95% CI upper (classic, sensitivity)",
    "95% Prediction interval lower",
    "95% Prediction interval upper",
    "I² (%)",
    paste0("τ² (", m$method.tau, ")"),
    "Cochran Q",
    "Q p-value",
    "N studies",
    "Total N (estimated)"
  ),
  Value = c(
    round(bt(m$TE.random), 3),
    round(bt(m$lower.random), 3),
    round(bt(m$upper.random), 3),
    round(bt(m_classic$lower.random), 3),
    round(bt(m_classic$upper.random), 3),
    round(bt(m$lower.predict), 3),
    round(bt(m$upper.predict), 3),
    round(m$I2 * 100, 1),
    round(m$tau^2, 4),
    round(m$Q, 2),
    round(m$pval.Q, 3),
    m$k,
    sum(df$n_treat + df$n_control, na.rm = TRUE)
  )
)

results_file <- file.path(CONFIG$output_dir,
                           paste0(CONFIG$output_prefix, "_summary.csv"))
write.csv(summary_df, results_file, row.names = FALSE)
cat(sprintf("Saved: %s\n", results_file))

# ── Session info ───────────────────────────────────────────────────────────────
cat("\n── Session Info ─────────────────────────────────────────────────────\n")
cat(sprintf("R: %s\n", R.version$version.string))
cat(sprintf("Date: %s\n", format(Sys.time())))
for (pkg in c("meta", "metafor", "dplyr", "ggplot2")) {
  if (requireNamespace(pkg, quietly = TRUE)) {
    cat(sprintf("  %-12s %s\n", pkg, packageVersion(pkg)))
  }
}
cat("\nMeta-analysis complete.\n")
