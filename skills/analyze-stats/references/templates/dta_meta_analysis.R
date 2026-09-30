#!/usr/bin/env Rscript
# dta_meta_analysis.R — Diagnostic Test Accuracy Meta-Analysis
# ==============================================================
# Bivariate random-effects model (Reitsma) for DTA studies.
# Produces SROC curve with confidence and prediction regions, paired forest
# plots, pooled accuracy measures, summary LR/DOR derived from the bivariate
# fit, between-study variance components, and Deeks' funnel plot test.
# With any zero cell, also fits the bivariate binomial GLMM (exact binomial
# likelihood), which should then be reported as the primary analysis.
#
# Requires: mada (>=0.5.11), meta (>=7.0-0), metafor (>=4.0-0);
#           lme4 for the binomial GLMM (only needed when a cell is zero)
# Install: install.packages(c("mada", "meta", "metafor", "lme4"))
#
# Alternative: If mada is unavailable, bivariate model can be fitted
# with metafor::rma.mv() using a bivariate random-effects structure.
#
# Input CSV columns: study_label, TP, FP, FN, TN
#   Optional: subgroup, threshold
#
# Usage:
#   Rscript dta_meta_analysis.R --input dta_studies.csv --output dta_results
#   Or source() interactively -- edit CONFIG section below

set.seed(42)
suppressPackageStartupMessages({
  library(mada)
  library(meta)
  library(metafor)
})

cat(sprintf("dta_meta_analysis.R | Date: %s | R: %s\n",
            format(Sys.Date()), R.version$version.string))
cat(sprintf("mada: %s | meta: %s | metafor: %s\n\n",
            packageVersion("mada"), packageVersion("meta"), packageVersion("metafor")))

# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════

CONFIG <- list(
  input_file    = "dta_studies.csv",
  output_dir    = ".",
  output_prefix = "dta_meta",
  alpha         = 0.05,
  # Subgroup column name in CSV (NA to skip)
  subgroup_col  = NA
)

# Command-line flags override CONFIG (see Usage above)
cli_args <- commandArgs(trailingOnly = TRUE)
cli_value <- function(flag) {
  i <- match(flag, cli_args)
  if (is.na(i) || i == length(cli_args)) NULL else cli_args[i + 1]
}
input_given <- !is.null(cli_value("--input"))
if (input_given)                     CONFIG$input_file    <- cli_value("--input")
if (!is.null(cli_value("--output"))) CONFIG$output_prefix <- cli_value("--output")

# ══════════════════════════════════════════════════════════════════════════════
# EXAMPLE DATA — Replace with real data or load from CSV
# ══════════════════════════════════════════════════════════════════════════════

example_data <- data.frame(
  study_label = c("Kim 2019", "Park 2020", "Lee 2021",
                  "Chen 2022", "Wang 2023", "Smith 2023",
                  "Jones 2024", "Zhang 2024"),
  TP = c(85, 120, 45, 95, 78, 60, 110, 55),
  FP = c(12, 18,  8, 15, 10,  9,  14,  7),
  FN = c( 5,  8,  3,  7,  4,  5,   6,  3),
  TN = c(98, 154, 44, 83, 108, 76, 170, 35),
  subgroup = c("A", "A", "A", "A", "B", "B", "B", "B")
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
  example_data
}

df <- load_data(CONFIG)
has_zero <- any(df[, c("TP", "FP", "FN", "TN")] == 0)

# ══════════════════════════════════════════════════════════════════════════════
# BIVARIATE MODEL (Reitsma)
# ══════════════════════════════════════════════════════════════════════════════

cat("═══ BIVARIATE MODEL (Reitsma) ══════════════════════════════════════════\n")

# Normal approximation to the binomial within-study likelihood. mada's default
# zero-cell handling adds 0.5 to every cell of EVERY study once any study has a
# zero; "single" confines the correction to the studies that need it.
fit_reitsma <- function(d) {
  reitsma(d, formula = cbind(tsens, tfpr) ~ 1, correction.control = "single")
}
fit <- fit_reitsma(df)
s <- summary(fit)
print(s)

# Pooled estimates: summary(fit) already carries the back-transformed rows
co <- s$coefficients
sens_est <- co["sensitivity", "Estimate"]
sens_lo  <- co["sensitivity", "95%ci.lb"]
sens_hi  <- co["sensitivity", "95%ci.ub"]
spec_est <- 1 - co["false pos. rate", "Estimate"]
spec_lo  <- 1 - co["false pos. rate", "95%ci.ub"]
spec_hi  <- 1 - co["false pos. rate", "95%ci.lb"]

cat("\n─── Pooled Estimates ─────────────────────────────────────────────────\n")
cat(sprintf("  Pooled Sensitivity: %.3f (95%% CI: %.3f – %.3f)\n", sens_est, sens_lo, sens_hi))
cat(sprintf("  Pooled Specificity: %.3f (95%% CI: %.3f – %.3f)\n", spec_est, spec_lo, spec_hi))

# ── Summary LR and DOR, derived from the bivariate fit ───────────────────────
# Never pool LRs or DORs separately (Zwinderman & Bossuyt 2008).
# SummaryPts() samples from the fitted model; set.seed() above fixes the draw.
pts <- summary(SummaryPts(fit))
lr_pos <- pts["posLR", ]; lr_neg <- pts["negLR", ]; dor <- pts["DOR", ]

cat(sprintf("  Positive LR: %.2f (95%% CI: %.2f – %.2f)\n", lr_pos["Median"], lr_pos["2.5%"], lr_pos["97.5%"]))
cat(sprintf("  Negative LR: %.3f (95%% CI: %.3f – %.3f)\n", lr_neg["Median"], lr_neg["2.5%"], lr_neg["97.5%"]))
cat(sprintf("  Diagnostic OR: %.1f (95%% CI: %.1f – %.1f)\n", dor["Median"], dor["2.5%"], dor["97.5%"]))

# ══════════════════════════════════════════════════════════════════════════════
# ZERO CELLS — bivariate binomial GLMM (exact within-study likelihood)
# ══════════════════════════════════════════════════════════════════════════════

glmm <- NULL
if (has_zero) {
  cat("\n═══ ZERO CELLS: BIVARIATE BINOMIAL GLMM ═══════════════════════════════\n")
  cat("  At least one 2x2 cell is zero. The normal approximation with a 0.5\n",
      "  correction biases Se/Sp towards 0.5; report this GLMM as the primary\n",
      "  analysis and the Reitsma fit as a sensitivity analysis (Chu & Cole 2006).\n", sep = "")
  if (requireNamespace("lme4", quietly = TRUE)) {
    k <- nrow(df)
    long <- rbind(
      data.frame(study = seq_len(k), se = 1, sp = 0, true = df$TP, n = df$TP + df$FN),
      data.frame(study = seq_len(k), se = 0, sp = 1, true = df$TN, n = df$TN + df$FP)
    )
    g <- lme4::glmer(cbind(true, n - true) ~ 0 + se + sp + (0 + se + sp | study),
                     data = long, family = binomial,
                     control = lme4::glmerControl(optimizer = "bobyqa"))
    b <- lme4::fixef(g); v <- sqrt(diag(as.matrix(vcov(g))))
    glmm <- list(
      sens = plogis(b["se"] + c(0, -1.96, 1.96) * v["se"]),
      spec = plogis(b["sp"] + c(0, -1.96, 1.96) * v["sp"])
    )
    cat(sprintf("  GLMM Sensitivity: %.3f (95%% CI: %.3f – %.3f)\n", glmm$sens[1], glmm$sens[2], glmm$sens[3]))
    cat(sprintf("  GLMM Specificity: %.3f (95%% CI: %.3f – %.3f)\n", glmm$spec[1], glmm$spec[2], glmm$spec[3]))
    print(lme4::VarCorr(g))
    if (lme4::isSingular(g)) {
      cat("  Note: singular fit (a variance or the correlation is at its boundary).\n")
    }
  } else {
    cat("  Package lme4 is not installed: install.packages(\"lme4\") and re-run.\n")
  }
}

# ══════════════════════════════════════════════════════════════════════════════
# HETEROGENEITY AND THRESHOLD EFFECT
# ══════════════════════════════════════════════════════════════════════════════

cat("\n═══ HETEROGENEITY (bivariate variance components) ═══════════════════════\n")

# Univariate I² for Se and Sp is not the DTA heterogeneity summary: it ignores
# threshold effects. Report the between-study SDs (logit scale), their
# correlation, and the 95% prediction region on the SROC plot
# (Cochrane DTA Handbook v1.0 ch.10 §10.4.3).
tau_sens <- sqrt(fit$Psi[1, 1])
tau_fpr  <- sqrt(fit$Psi[2, 2])
rho      <- fit$Psi[1, 2] / (tau_sens * tau_fpr)

cat(sprintf("  Between-study SD, logit(Se):  %.3f\n", tau_sens))
cat(sprintf("  Between-study SD, logit(FPR): %.3f\n", tau_fpr))
cat(sprintf("  Correlation logit(Se)-logit(FPR): %.3f\n", rho))
if (abs(rho) > 0.99 || min(tau_sens, tau_fpr) < 0.05) {
  cat("  → Boundary estimate (|correlation| ≈ 1 or an SD ≈ 0): the variance\n",
      "    components are not identifiable from these data. Do not interpret the\n",
      "    correlation as a threshold effect; say so in the Results.\n", sep = "")
}

# A positive Se-FPR correlation is what a threshold effect produces, but it is
# not proof of one, and a non-significant Spearman test on few studies is not
# proof of its absence. If positivity thresholds differ across studies, present
# the SROC curve (with its prediction region) as the summary.
logit_sens <- qlogis((df$TP + 0.5) / (df$TP + df$FN + 1))
logit_fpr  <- qlogis((df$FP + 0.5) / (df$FP + df$TN + 1))
sp_test <- suppressWarnings(cor.test(logit_sens, logit_fpr, method = "spearman"))
cat(sprintf("  Spearman rho (descriptive only): %.3f, P = %.3f\n",
            sp_test$estimate, sp_test$p.value))

# ══════════════════════════════════════════════════════════════════════════════
# SROC CURVE
# ══════════════════════════════════════════════════════════════════════════════

cat("\n═══ SROC CURVE ══════════════════════════════════════════════════════════\n")

auc <- s$AUC
cat(sprintf("  SROC AUC: %.3f; partial AUC over the observed FPR range: %.3f\n",
            auc$AUC, auc$pAUC))

draw_sroc <- function() {
  plot(fit, sroclwd = 2, predict = TRUE, predlty = 2,
       main = "SROC Curve (Bivariate Model)")
  points(fpr(df), sens(df), pch = 2, cex = 0.8)
  legend("bottomright",
         c("SROC curve", "Summary point", "95% confidence region",
           "95% prediction region", "Studies"),
         lty = c(1, NA, 1, 2, NA), lwd = c(2, NA, 1, 1, NA),
         pch = c(NA, 1, NA, NA, 2), bty = "n")
}

sroc_file <- file.path(CONFIG$output_dir,
                        paste0(CONFIG$output_prefix, "_sroc.pdf"))
pdf(sroc_file, width = 7, height = 7)
draw_sroc()
dev.off()
cat(sprintf("Saved: %s\n", sroc_file))

# PNG version
sroc_png <- file.path(CONFIG$output_dir,
                       paste0(CONFIG$output_prefix, "_sroc.png"))
png(sroc_png, width = 7, height = 7, units = "in", res = 300)
draw_sroc()
dev.off()
cat(sprintf("Saved: %s\n", sroc_png))

# ══════════════════════════════════════════════════════════════════════════════
# PAIRED FOREST PLOTS
# ══════════════════════════════════════════════════════════════════════════════

cat("\n═══ FOREST PLOTS ═══════════════════════════════════════════════════════\n")

# Paired forest plots are drawn from the study-level descriptives (madad),
# not from the reitsma fit, which has no forest method. Call mada::forest
# explicitly: metafor and meta, attached after mada, mask the generic.
dd <- madad(df, correction.control = "single")

# Sensitivity forest plot
forest_sens_file <- file.path(CONFIG$output_dir,
                               paste0(CONFIG$output_prefix, "_forest_sens.pdf"))
pdf(forest_sens_file, width = 10, height = max(5, nrow(df) * 0.4 + 2))
mada::forest(dd, type = "sens", snames = df$study_label,
       main = "Forest Plot: Sensitivity", xlab = "Sensitivity")
dev.off()
cat(sprintf("Saved: %s\n", forest_sens_file))

# Specificity forest plot
forest_spec_file <- file.path(CONFIG$output_dir,
                               paste0(CONFIG$output_prefix, "_forest_spec.pdf"))
pdf(forest_spec_file, width = 10, height = max(5, nrow(df) * 0.4 + 2))
mada::forest(dd, type = "spec", snames = df$study_label,
       main = "Forest Plot: Specificity", xlab = "Specificity")
dev.off()
cat(sprintf("Saved: %s\n", forest_spec_file))

# ══════════════════════════════════════════════════════════════════════════════
# PUBLICATION BIAS — Deeks' Funnel Plot Asymmetry Test
# ══════════════════════════════════════════════════════════════════════════════

cat("\n═══ PUBLICATION BIAS (Deeks' Funnel Plot) ═════════════════════════════\n")

deeks_p <- NA
if (nrow(df) >= 10) {
  # Deeks et al. 2005: lnDOR regressed on 1/sqrt(ESS), weighted by ESS, where
  # ESS = 4*n1*n2/(n1+n2) with n1/n2 = diseased/non-diseased counts.
  # metabin(sm = "DOR") takes the diseased as the first group.
  m_dor <- metabin(event.e = TP, n.e = TP + FN, event.c = FP, n.c = FP + TN,
                   studlab = study_label, data = df, sm = "DOR")
  deeks_file <- file.path(CONFIG$output_dir,
                           paste0(CONFIG$output_prefix, "_deeks_funnel.pdf"))
  deeks <- metabias(m_dor, method.bias = "Deeks", k.min = 10)
  deeks_p <- deeks$pval

  # Deeks' funnel plot: DOR (log scale) against 1/sqrt(ESS), with the fitted
  # regression line lnDOR = intercept + slope / sqrt(ESS)
  pdf(deeks_file, width = 6, height = 6)
  funnel(m_dor, yaxis = "ess", common = FALSE, random = FALSE,
         main = "Deeks' Funnel Plot Asymmetry Test")
  inv_sqrt_ess <- 1 / sqrt(4 * m_dor$n.e * m_dor$n.c / (m_dor$n.e + m_dor$n.c))
  yy <- seq(0, max(inv_sqrt_ess), length.out = 50)
  lines(exp(deeks$intercept + deeks$estimate["bias"] * yy), yy, lty = 2)
  mtext(sprintf("Deeks' test P = %.3f", deeks_p), side = 3, line = 0.3, cex = 0.9)
  dev.off()
  cat(sprintf("Saved: %s\n", deeks_file))

  cat(sprintf("  Deeks' test: t = %.3f, df = %d, P = %.3f\n",
              deeks$statistic, deeks$df, deeks_p))
  if (deeks_p < CONFIG$alpha) {
    cat("  → Funnel plot asymmetry detected; study size may relate to accuracy for\n",
        "    reasons other than publication bias.\n", sep = "")
  } else {
    cat("  → No evidence of asymmetry (the test has low power under heterogeneity)\n")
  }
} else {
  cat("  Skipped: < 10 studies (Deeks' test underpowered)\n")
}

# ══════════════════════════════════════════════════════════════════════════════
# SENSITIVITY ANALYSIS — Leave-one-out
# ══════════════════════════════════════════════════════════════════════════════

cat("\n═══ SENSITIVITY ANALYSIS: Leave-one-out ══════════════════════════════\n")

loo_results <- data.frame(
  Study_removed    = character(),
  Pooled_Sens      = numeric(),
  Pooled_Spec      = numeric(),
  stringsAsFactors = FALSE
)

for (i in 1:nrow(df)) {
  df_loo <- df[-i, ]
  fit_loo <- tryCatch(fit_reitsma(df_loo), error = function(e) NULL)
  if (!is.null(fit_loo)) {
    co_loo <- summary(fit_loo)$coefficients
    loo_results <- rbind(loo_results, data.frame(
      Study_removed = df$study_label[i],
      Pooled_Sens   = round(co_loo["sensitivity", "Estimate"], 3),
      Pooled_Spec   = round(1 - co_loo["false pos. rate", "Estimate"], 3)
    ))
  }
}

print(loo_results, row.names = FALSE)

loo_file <- file.path(CONFIG$output_dir,
                       paste0(CONFIG$output_prefix, "_leave_one_out.csv"))
write.csv(loo_results, loo_file, row.names = FALSE)
cat(sprintf("\nSaved: %s\n", loo_file))

# ══════════════════════════════════════════════════════════════════════════════
# DUAL APPROACH: Comparative + Single-Arm Pooled Proportion
# ══════════════════════════════════════════════════════════════════════════════
#
# When studies report both comparative (test A vs B) and single-arm data,
# use dual approach:
#   1. metabin() for comparative studies (OR/RR with Hartung-Knapp CI)
#   2. metaprop() for single-arm pooled proportion (logit GLMM)
#
# Reference: Lin 2025 (PMID:41419890), Su 2026 (PMID:41653198)
#
# Uncomment and adapt the section below when you have comparative data:
#
# ── Comparative meta-analysis (non-rare events) ────────────────────────────
# m_comp <- metabin(
#   event.e = events_test, n.e = n_test,
#   event.c = events_ref,  n.c = n_ref,
#   studlab = study_label, data = df_comp,
#   sm = "OR",
#   method = "Inverse",
#   method.tau = "REML",     # PM if REML does not converge
#   method.random.ci = "HK", # Hartung-Knapp CI ...
#   adhoc.hakn.ci = "se",    # ... never narrower than the classic CI
#   common = FALSE,          # NOT fixed (deprecated)
#   random = TRUE            # NOT comb.random (deprecated)
# )
# Rare events (pooled rate < 1% or zero-event arms): Peto, MH without a
# correction, or method = "GLMM" instead; see the meta-analysis skill.
#
# ── Single-arm pooled proportion ───────────────────────────────────────────
# m_prop <- metaprop(
#   event = events, n = total,
#   studlab = study_label, data = df_single,
#   sm = "PLOGIT",           # logit transformation
#   method = "GLMM",         # exact binomial likelihood; no continuity correction
#   method.ci = "CP",        # Clopper-Pearson CI for the individual studies
#   common = FALSE,
#   random = TRUE,
#   prediction = TRUE
# )

# ══════════════════════════════════════════════════════════════════════════════
# RESULTS SUMMARY
# ══════════════════════════════════════════════════════════════════════════════

summary_df <- data.frame(
  Metric = c(
    "Pooled Sensitivity",
    "Sensitivity 95% CI lower",
    "Sensitivity 95% CI upper",
    "Pooled Specificity",
    "Specificity 95% CI lower",
    "Specificity 95% CI upper",
    "Positive LR", "Positive LR 95% CI lower", "Positive LR 95% CI upper",
    "Negative LR", "Negative LR 95% CI lower", "Negative LR 95% CI upper",
    "Diagnostic OR", "Diagnostic OR 95% CI lower", "Diagnostic OR 95% CI upper",
    "Between-study SD logit(Se)",
    "Between-study SD logit(FPR)",
    "Correlation logit(Se)-logit(FPR)",
    "SROC partial AUC (observed FPR range)",
    "Deeks' test P (NA if k < 10)",
    "Any zero cell (1 = yes; report GLMM as primary)",
    "N studies"
  ),
  Value = c(
    round(sens_est, 3),
    round(sens_lo, 3),
    round(sens_hi, 3),
    round(spec_est, 3),
    round(spec_lo, 3),
    round(spec_hi, 3),
    round(lr_pos[c("Median", "2.5%", "97.5%")], 2),
    round(lr_neg[c("Median", "2.5%", "97.5%")], 3),
    round(dor[c("Median", "2.5%", "97.5%")], 1),
    round(tau_sens, 3),
    round(tau_fpr, 3),
    round(rho, 3),
    round(auc$pAUC, 3),
    round(deeks_p, 3),
    as.integer(has_zero),
    nrow(df)
  )
)
if (!is.null(glmm)) {
  summary_df <- rbind(summary_df, data.frame(
    Metric = c("GLMM Sensitivity", "GLMM Sensitivity 95% CI lower", "GLMM Sensitivity 95% CI upper",
               "GLMM Specificity", "GLMM Specificity 95% CI lower", "GLMM Specificity 95% CI upper"),
    Value = round(c(glmm$sens, glmm$spec), 3)
  ))
}

results_file <- file.path(CONFIG$output_dir,
                           paste0(CONFIG$output_prefix, "_summary.csv"))
write.csv(summary_df, results_file, row.names = FALSE)
cat(sprintf("\nSaved: %s\n", results_file))

# ── Session info ───────────────────────────────────────────────────────────────
cat("\n── Session Info ─────────────────────────────────────────────────────\n")
cat(sprintf("R: %s\n", R.version$version.string))
cat(sprintf("Date: %s\n", format(Sys.time())))
for (pkg in c("mada", "meta", "metafor", "lme4")) {
  if (requireNamespace(pkg, quietly = TRUE)) {
    cat(sprintf("  %-12s %s\n", pkg, packageVersion(pkg)))
  }
}
cat("\nDTA meta-analysis complete.\n")
