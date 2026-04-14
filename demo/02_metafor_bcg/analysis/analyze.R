#!/usr/bin/env Rscript
# ============================================================
# MedSci Skills Demo 2: BCG Vaccine Meta-Analysis
# E2E Pipeline Step 1 — analyze-stats (R metafor)
#
# Dataset: metafor::dat.bcg (13 RCTs of BCG vaccine for TB prevention)
# Reference: Colditz et al. (1994) JAMA
#
# Pipeline: Load → effect sizes → RE model → forest → funnel →
#           heterogeneity → subgroup → meta-regression → sensitivity →
#           publication bias
#
# Usage: Rscript analyze.R
# ============================================================

cat("=", rep("=", 59), "\n", sep = "")
cat("MedSci Skills Demo 2: BCG Vaccine Meta-Analysis\n")
cat("=", rep("=", 59), "\n", sep = "")

# === REPRODUCIBILITY HEADER ===
set.seed(42)
cat("Date:", format(Sys.Date()), "\n")
cat("R:", R.version.string, "\n")

library(metafor)
library(meta)

cat("metafor:", as.character(packageVersion("metafor")), "\n")
cat("meta:", as.character(packageVersion("meta")), "\n\n")

# === LOAD DATA ===
data(dat.bcg)
cat("Loaded: dat.bcg —", nrow(dat.bcg), "studies\n")
cat("Years:", min(dat.bcg$year), "-", max(dat.bcg$year), "\n")
cat("Total participants (treatment):", sum(dat.bcg$tpos + dat.bcg$tneg), "\n")
cat("Total participants (control):", sum(dat.bcg$cpos + dat.bcg$cneg), "\n\n")

# === COMPUTE EFFECT SIZES ===
dat <- escalc(measure = "RR", ai = tpos, bi = tneg, ci = cpos, di = cneg,
              data = dat.bcg, append = TRUE)

# ============================================================
# PART A: RANDOM-EFFECTS MODEL (REML)
# ============================================================
cat("\n", rep("=", 60), "\n", sep = "")
cat("PART A: Random-Effects Model (REML)\n")
cat(rep("=", 60), "\n", sep = "")

res <- rma(yi, vi, data = dat, method = "REML")
print(summary(res))

pooled_rr <- exp(coef(res))
pooled_ci_lb <- exp(res$ci.lb)
pooled_ci_ub <- exp(res$ci.ub)
cat(sprintf("\nPooled RR = %.3f (95%% CI: %.3f - %.3f)\n", pooled_rr, pooled_ci_lb, pooled_ci_ub))
cat(sprintf("Risk reduction: %.1f%% (95%% CI: %.1f%% - %.1f%%)\n",
            (1 - pooled_rr) * 100,
            (1 - pooled_ci_ub) * 100,
            (1 - pooled_ci_lb) * 100))

# ============================================================
# PART B: HETEROGENEITY
# ============================================================
cat("\n", rep("=", 60), "\n", sep = "")
cat("PART B: Heterogeneity Assessment\n")
cat(rep("=", 60), "\n", sep = "")

cat(sprintf("Q = %.2f (df = %d, p %s)\n", res$QE, res$k - 1,
            ifelse(res$QEp < 0.001, "< 0.001", sprintf("= %.3f", res$QEp))))
cat(sprintf("I² = %.1f%%\n", res$I2))
cat(sprintf("tau² = %.4f (SE = %.4f)\n", res$tau2, res$se.tau2))

pred <- predict(res)
cat(sprintf("Prediction interval (RR): %.3f - %.3f\n", exp(pred$pi.lb), exp(pred$pi.ub)))

# ============================================================
# PART C: FOREST PLOT
# ============================================================
cat("\n", rep("=", 60), "\n", sep = "")
cat("PART C: Forest Plot\n")
cat(rep("=", 60), "\n", sep = "")

for (ext in c("pdf", "png")) {
  if (ext == "pdf") {
    pdf("figures/forest_plot.pdf", width = 10, height = 7)
  } else {
    png("figures/forest_plot.png", width = 10, height = 7, units = "in", res = 300)
  }
  forest(res, slab = paste0(dat$author, " (", dat$year, ")"),
         atransf = exp,
         header = c("Study", "Risk Ratio [95% CI]"),
         xlab = "Risk Ratio (log scale)",
         mlab = sprintf("RE Model (I² = %.1f%%, p %s)",
                        res$I2,
                        ifelse(res$QEp < 0.001, "< 0.001", sprintf("= %.3f", res$QEp))),
         cex = 0.85, efac = 0.8)
  dev.off()
}
cat("Saved: figures/forest_plot.{pdf,png}\n")

# ============================================================
# PART D: FUNNEL PLOT + PUBLICATION BIAS
# ============================================================
cat("\n", rep("=", 60), "\n", sep = "")
cat("PART D: Funnel Plot + Publication Bias\n")
cat(rep("=", 60), "\n", sep = "")

for (ext in c("pdf", "png")) {
  if (ext == "pdf") {
    pdf("figures/funnel_plot.pdf", width = 7, height = 6)
  } else {
    png("figures/funnel_plot.png", width = 7, height = 6, units = "in", res = 300)
  }
  funnel(res, xlab = "Log Risk Ratio", main = "Funnel Plot — BCG Vaccine Efficacy")
  dev.off()
}
cat("Saved: figures/funnel_plot.{pdf,png}\n")

cat("\n--- Egger's Test ---\n")
egger <- regtest(res, model = "lm")
print(egger)

cat("\n--- Begg's Rank Test ---\n")
begg <- ranktest(res)
print(begg)

cat("\n--- Trim-and-Fill ---\n")
tf <- trimfill(res)
print(tf)
cat(sprintf("Imputed: %d studies, Adjusted RR: %.3f (95%% CI: %.3f - %.3f)\n",
            tf$k0, exp(coef(tf)), exp(tf$ci.lb), exp(tf$ci.ub)))

for (ext in c("pdf", "png")) {
  if (ext == "pdf") {
    pdf("figures/funnel_trimfill.pdf", width = 7, height = 6)
  } else {
    png("figures/funnel_trimfill.png", width = 7, height = 6, units = "in", res = 300)
  }
  funnel(tf, xlab = "Log Risk Ratio",
         main = "Funnel Plot with Trim-and-Fill Imputation")
  dev.off()
}
cat("Saved: figures/funnel_trimfill.{pdf,png}\n")

# ============================================================
# PART E: SUBGROUP ANALYSIS
# ============================================================
cat("\n", rep("=", 60), "\n", sep = "")
cat("PART E: Subgroup Analysis (Allocation Method)\n")
cat(rep("=", 60), "\n", sep = "")

res_alloc <- rma(yi, vi, data = dat, mods = ~ alloc, method = "REML")
print(summary(res_alloc))

for (a in unique(dat$alloc)) {
  sub <- rma(yi, vi, data = dat, subset = (alloc == a), method = "REML")
  cat(sprintf("%s (k=%d): RR = %.3f (95%% CI: %.3f - %.3f), I² = %.1f%%\n",
              a, sub$k, exp(coef(sub)), exp(sub$ci.lb), exp(sub$ci.ub), sub$I2))
}

# ============================================================
# PART F: META-REGRESSION
# ============================================================
cat("\n", rep("=", 60), "\n", sep = "")
cat("PART F: Meta-Regression (Absolute Latitude)\n")
cat(rep("=", 60), "\n", sep = "")

res_lat <- rma(yi, vi, mods = ~ ablat, data = dat, method = "REML")
print(summary(res_lat))
cat(sprintf("R² = %.1f%%\n", res_lat$R2))

for (ext in c("pdf", "png")) {
  if (ext == "pdf") {
    pdf("figures/bubble_plot.pdf", width = 7, height = 6)
  } else {
    png("figures/bubble_plot.png", width = 7, height = 6, units = "in", res = 300)
  }
  regplot(res_lat, xlab = "Absolute Latitude", ylab = "Log Risk Ratio",
          main = "Meta-Regression: Vaccine Efficacy vs. Latitude",
          atransf = exp, pi = TRUE, legend = TRUE)
  dev.off()
}
cat("Saved: figures/bubble_plot.{pdf,png}\n")

# ============================================================
# PART G: SENSITIVITY (Leave-One-Out)
# ============================================================
cat("\n", rep("=", 60), "\n", sep = "")
cat("PART G: Sensitivity Analysis\n")
cat(rep("=", 60), "\n", sep = "")

loo <- leave1out(res)
loo_df <- data.frame(
  Study = paste0(dat$author, " (", dat$year, ")"),
  RR = round(exp(loo$estimate), 3),
  CI_lower = round(exp(loo$ci.lb), 3),
  CI_upper = round(exp(loo$ci.ub), 3),
  I2 = round(loo$I2, 1),
  stringsAsFactors = FALSE
)
print(loo_df)

ext_res <- rstudent(res)
influential <- which(abs(ext_res$z) > 2)
if (length(influential) > 0) {
  cat("\nInfluential studies (|rstudent| > 2):\n")
  for (i in influential) {
    cat(sprintf("  %s (%d): rstudent = %.3f\n", dat$author[i], dat$year[i], ext_res$z[i]))
  }
} else {
  cat("\nNo studies with |rstudent| > 2.\n")
}

# ============================================================
# PART H: OUTPUT TABLES
# ============================================================
cat("\n", rep("=", 60), "\n", sep = "")
cat("PART H: Output Tables\n")
cat(rep("=", 60), "\n", sep = "")

# Per-study results
study_results <- data.frame(
  Study = paste0(dat$author, " (", dat$year, ")"),
  RR = round(exp(dat$yi), 3),
  CI_lower = round(exp(dat$yi - 1.96 * sqrt(dat$vi)), 3),
  CI_upper = round(exp(dat$yi + 1.96 * sqrt(dat$vi)), 3),
  Weight = round(weights(res), 1),
  Latitude = dat$ablat,
  Allocation = dat$alloc,
  stringsAsFactors = FALSE
)
write.csv(study_results, "tables/study_results.csv", row.names = FALSE)
cat("Saved: tables/study_results.csv\n")

# Summary table
alloc_types <- unique(dat$alloc)
summary_rows <- list()
summary_rows[[1]] <- list(Analysis = "Overall (REML)", k = res$k,
                          RR = round(pooled_rr, 3),
                          CI_lower = round(pooled_ci_lb, 3),
                          CI_upper = round(pooled_ci_ub, 3),
                          I2 = round(res$I2, 1), tau2 = round(res$tau2, 4))
for (a in alloc_types) {
  sub <- rma(yi, vi, data = dat, subset = (alloc == a), method = "REML")
  summary_rows[[length(summary_rows) + 1]] <- list(
    Analysis = paste0("Subgroup: ", a), k = sub$k,
    RR = round(exp(coef(sub)), 3),
    CI_lower = round(exp(sub$ci.lb), 3),
    CI_upper = round(exp(sub$ci.ub), 3),
    I2 = round(sub$I2, 1), tau2 = round(sub$tau2, 4))
}
summary_rows[[length(summary_rows) + 1]] <- list(
  Analysis = "Trim-and-fill adjusted", k = tf$k,
  RR = round(exp(coef(tf)), 3),
  CI_lower = round(exp(tf$ci.lb), 3),
  CI_upper = round(exp(tf$ci.ub), 3),
  I2 = round(tf$I2, 1), tau2 = round(tf$tau2, 4))

summary_table <- do.call(rbind, lapply(summary_rows, as.data.frame))
write.csv(summary_table, "tables/summary_table.csv", row.names = FALSE)
cat("Saved: tables/summary_table.csv\n")

# Meta-regression table
metareg_table <- data.frame(
  Covariate = c("Intercept", "Absolute latitude"),
  Estimate = round(coef(res_lat), 4),
  SE = round(res_lat$se, 4),
  z = round(res_lat$zval, 3),
  p = ifelse(res_lat$pval < 0.001, "<0.001", round(res_lat$pval, 3)),
  stringsAsFactors = FALSE
)
write.csv(metareg_table, "tables/metaregression_table.csv", row.names = FALSE)
cat("Saved: tables/metaregression_table.csv\n")

# Leave-one-out table
write.csv(loo_df, "tables/leave_one_out.csv", row.names = FALSE)
cat("Saved: tables/leave_one_out.csv\n")

# ============================================================
# ANALYSIS OUTPUTS MANIFEST
# ============================================================
manifest <- paste0(
  "# Analysis Outputs — Demo 2: BCG Vaccine Meta-Analysis\n",
  "Generated: ", Sys.Date(), "\n",
  "Study type: Meta-analysis (intervention, 13 RCTs)\n",
  "Effect measure: Risk Ratio (log-transformed)\n",
  "Model: Random-effects (REML)\n\n",
  "## Key Results\n",
  sprintf("- Pooled RR: %.3f (95%% CI: %.3f-%.3f)\n", pooled_rr, pooled_ci_lb, pooled_ci_ub),
  sprintf("- I²: %.1f%%, tau²: %.4f\n", res$I2, res$tau2),
  sprintf("- Meta-regression R² (latitude): %.1f%%\n", res_lat$R2),
  sprintf("- Egger's test p = %.3f\n", egger$pval),
  sprintf("- Trim-and-fill: %d imputed, adjusted RR = %.3f\n\n", tf$k0, exp(coef(tf))),
  "## Tables\n",
  "- `tables/study_results.csv` — Per-study RR with 95% CI and weights\n",
  "- `tables/summary_table.csv` — Pooled estimates (overall, subgroup, trim-and-fill)\n",
  "- `tables/metaregression_table.csv` — Meta-regression coefficients\n",
  "- `tables/leave_one_out.csv` — Leave-one-out sensitivity analysis\n\n",
  "## Figures\n",
  "- `figures/forest_plot.{pdf,png}` — Forest plot (13 studies, REML)\n",
  "- `figures/funnel_plot.{pdf,png}` — Funnel plot\n",
  "- `figures/funnel_trimfill.{pdf,png}` — Funnel plot with trim-and-fill\n",
  "- `figures/bubble_plot.{pdf,png}` — Meta-regression bubble plot (latitude)\n\n",
  "## Data\n",
  "- `data/bcg_raw.csv` — Original dataset (metafor::dat.bcg)\n"
)
writeLines(manifest, "_analysis_outputs.md")
cat("Saved: _analysis_outputs.md\n")

cat("\n", rep("=", 60), "\n", sep = "")
cat("ANALYSIS COMPLETE\n")
cat(rep("=", 60), "\n", sep = "")
