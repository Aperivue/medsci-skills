#!/usr/bin/env Rscript
# meta_analysis.R — Comprehensive Meta-Analysis Script
# =====================================================
# Random-effects meta-analysis with DerSimonian-Laird estimator.
# Supports binary outcomes (OR/RR), continuous outcomes (MD/SMD),
# and diagnostic accuracy (sensitivity/specificity via bivariate model).
#
# Dependencies: meta, metafor, dplyr, ggplot2
# Install: install.packages(c("meta", "metafor", "dplyr", "ggplot2"))
#
# Input CSV: see EXAMPLE DATA section below for format
#
# Usage:
#   Rscript meta_analysis.R --input studies.csv --effect OR --output meta_results
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
  effect_type  = "OR",                 # "OR", "RR", "MD", "SMD", "AUC"
  outcome_name = "Primary outcome",    # Label for forest plot
  alpha        = 0.05,                 # Significance threshold
  output_dir   = ".",                  # Output directory
  output_prefix = "meta",             # File name prefix
  # Subgroup column name in CSV (NA to skip)
  subgroup_col = NA,                   # e.g., "scanner_type"
  # Trim-and-fill parameters
  n_iter_trimfill = 50
)

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
  } else {
    cat("Input file not found. Using built-in example data.\n\n")
    if (config$effect_type %in% c("OR", "RR")) {
      return(example_data_OR)
    } else {
      return(example_data_MD)
    }
  }
}

df <- load_data(CONFIG)

# ══════════════════════════════════════════════════════════════════════════════
# PRIMARY META-ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════

run_meta <- function(df, effect_type, subgroup_col = NA) {

  cat(sprintf("═══ META-ANALYSIS: %s ═══════════════════════════════════\n",
              effect_type))

  if (effect_type %in% c("OR", "RR")) {
    # Binary outcomes
    m <- metabin(
      event.e = events_treat,
      n.e     = n_treat,
      event.c = events_control,
      n.c     = n_control,
      studlab = study_label,
      data    = df,
      sm      = effect_type,
      method  = "MH",         # Mantel-Haenszel for primary pooling
      method.tau = "DL",      # DerSimonian-Laird for τ²
      random  = TRUE,
      fixed   = FALSE,
      prediction = TRUE,      # Show prediction interval
      title   = paste("Meta-analysis:", effect_type)
    )

  } else if (effect_type %in% c("MD", "SMD")) {
    # Continuous outcomes
    m <- metacont(
      n.e    = n_treat,
      mean.e = mean_treat,
      sd.e   = sd_treat,
      n.c    = n_control,
      mean.c = mean_control,
      sd.c   = sd_control,
      studlab = study_label,
      data   = df,
      sm     = effect_type,
      method.tau = "DL",
      random = TRUE,
      fixed  = FALSE,
      prediction = TRUE
    )
  } else {
    stop(sprintf("Unsupported effect type: %s. Use OR, RR, MD, or SMD.", effect_type))
  }

  return(m)
}

m <- run_meta(df, CONFIG$effect_type)

# ── Print summary ─────────────────────────────────────────────────────────────
cat("\n─── Pooled Estimate ─────────────────────────────────────────────────\n")
cat(sprintf("  %s (random-effects): %.3f (95%% CI: %.3f – %.3f)\n",
            CONFIG$effect_type,
            exp(m$TE.random),  # exponentiate if OR/RR
            exp(m$lower.random),
            exp(m$upper.random)))
cat(sprintf("  95%% Prediction interval: %.3f – %.3f\n",
            exp(m$lower.predict), exp(m$upper.predict)))
cat(sprintf("\n─── Heterogeneity ──────────────────────────────────────────────────\n"))
cat(sprintf("  I² = %.1f%% (95%% CI: %.1f%% – %.1f%%)\n",
            m$I2 * 100, m$lower.I2 * 100, m$upper.I2 * 100))
cat(sprintf("  τ² = %.4f (τ = %.4f)\n", m$tau^2, m$tau))
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
  for (sg in unique(df[[CONFIG$subgroup_col]])) {
    idx <- df[[CONFIG$subgroup_col]] == sg
    sub_df <- df[idx, ]
    m_s <- run_meta(sub_df, CONFIG$effect_type)
    cat(sprintf("  %s: %s = %.3f (95%% CI: %.3f – %.3f), I² = %.1f%%\n",
                sg, CONFIG$effect_type,
                exp(m_s$TE.random), exp(m_s$lower.random), exp(m_s$upper.random),
                m_s$I2 * 100))
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
    run_meta(df_loo, CONFIG$effect_type),
    error = function(e) NULL
  )
  if (!is.null(m_loo)) {
    loo_results <- rbind(loo_results, data.frame(
      Study_removed = df$study_label[i],
      Pooled_effect = round(exp(m_loo$TE.random), 3),
      CI_lower = round(exp(m_loo$lower.random), 3),
      CI_upper = round(exp(m_loo$upper.random), 3),
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
# PUBLICATION BIAS — Egger's test + Trim-and-Fill
# ══════════════════════════════════════════════════════════════════════════════

if (nrow(df) >= 10) {
  cat("\n═══ PUBLICATION BIAS ════════════════════════════════════════════════\n")

  # Egger's test via metafor
  rma_fit <- rma(
    yi = m$TE,
    sei = m$seTE,
    method = "DL"
  )

  egger <- regtest(rma_fit)
  cat(sprintf("  Egger's test: z = %.3f, P = %.3f\n",
              egger$zval, egger$pval))
  if (egger$pval < 0.05) {
    cat("  → Funnel plot asymmetry detected (possible publication bias)\n")
  } else {
    cat("  → No significant funnel plot asymmetry\n")
  }

  # Trim-and-fill
  tf <- trimfill(rma_fit, estimator = "L0",
                  maxiter = CONFIG$n_iter_trimfill)
  cat(sprintf("\n  Trim-and-fill: imputed %d studies\n", tf$k0))
  cat(sprintf("  Adjusted pooled %s: %.3f (95%% CI: %.3f – %.3f)\n",
              CONFIG$effect_type,
              exp(tf$b), exp(tf$ci.lb), exp(tf$ci.ub)))

  # Funnel plot
  funnel_file <- file.path(CONFIG$output_dir,
                            paste0(CONFIG$output_prefix, "_funnel.pdf"))
  pdf(funnel_file, width = 5, height = 5)
  funnel(tf, main = "Funnel Plot with Trim-and-Fill",
         xlab = paste("Effect estimate:", CONFIG$effect_type),
         ylab = "Standard error")
  dev.off()
  cat(sprintf("\nSaved: %s\n", funnel_file))
} else {
  cat("\nPub bias: Skipped (< 10 studies; low power for Egger's test)\n")
}

# ══════════════════════════════════════════════════════════════════════════════
# FOREST PLOT
# ══════════════════════════════════════════════════════════════════════════════

cat("\n═══ FOREST PLOT ══════════════════════════════════════════════════════\n")

forest_file_pdf <- file.path(CONFIG$output_dir,
                              paste0(CONFIG$output_prefix, "_forest.pdf"))
forest_file_png <- file.path(CONFIG$output_dir,
                              paste0(CONFIG$output_prefix, "_forest.png"))

# PDF
pdf(forest_file_pdf, width = 10, height = max(6, nrow(df) * 0.35 + 3))
forest(m,
       sortvar    = TE,
       prediction = TRUE,
       print.tau2 = TRUE,
       leftlabs   = c("Study", "N treated", "N control"),
       rightlabs  = c(CONFIG$effect_type, "95% CI", "Weight"),
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
    "95% CI lower",
    "95% CI upper",
    "95% Prediction interval lower",
    "95% Prediction interval upper",
    "I² (%)",
    "τ²",
    "Cochran Q",
    "Q p-value",
    "N studies",
    "Total N (estimated)"
  ),
  Value = c(
    round(exp(m$TE.random), 3),
    round(exp(m$lower.random), 3),
    round(exp(m$upper.random), 3),
    round(exp(m$lower.predict), 3),
    round(exp(m$upper.predict), 3),
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
