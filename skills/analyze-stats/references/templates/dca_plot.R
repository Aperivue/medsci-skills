#!/usr/bin/env Rscript
# dca_plot.R — Decision Curve Analysis
# =====================================
# Generates DCA plots showing net benefit vs threshold probability.
# Compares models against treat-all and treat-none strategies.
#
# Dependencies: dcurves, ggplot2, dplyr
# Install: install.packages(c("dcurves", "ggplot2", "dplyr"))
#
# Input: Data frame with binary outcome + one or more prediction scores
#
# Usage:
#   Rscript dca_plot.R --input predictions.csv --outcome event \
#     --models model1_prob model2_prob --output dca_results

set.seed(42)
suppressPackageStartupMessages({
  library(dcurves)
  library(ggplot2)
  library(dplyr)
})

cat(sprintf("dca_plot.R | Date: %s | R: %s\n",
            format(Sys.Date()), R.version$version.string))
cat(sprintf("dcurves: %s | ggplot2: %s\n\n",
            packageVersion("dcurves"), packageVersion("ggplot2")))

# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION — Edit for your analysis
# ══════════════════════════════════════════════════════════════════════════════

CONFIG <- list(
  input_file    = "predictions.csv",   # CSV with outcome and model probabilities
  outcome_col   = "event",             # Binary outcome column (0/1)
  model_cols    = c("model1", "model2"), # Probability score columns
  model_labels  = c("AI Model", "Radiologist Score"), # Labels for legend
  threshold_lo  = 0.05,               # Lower threshold for DCA
  threshold_hi  = 0.50,               # Upper threshold for DCA
  output_prefix = "dca"
)

# ══════════════════════════════════════════════════════════════════════════════
# EXAMPLE DATA — Replace with real data
# ══════════════════════════════════════════════════════════════════════════════

set.seed(42)
n <- 400
example_data <- data.frame(
  event   = rbinom(n, 1, prob = 0.25),
  model1  = plogis(rnorm(n, mean = 0.8, sd = 1.2)),
  model2  = plogis(rnorm(n, mean = 0.3, sd = 1.0))
)
# Add some correlation between outcome and predictions
example_data$model1 <- plogis(
  qlogis(example_data$model1) + example_data$event * 1.5
)
example_data$model2 <- plogis(
  qlogis(example_data$model2) + example_data$event * 1.0
)

# ══════════════════════════════════════════════════════════════════════════════
# LOAD DATA
# ══════════════════════════════════════════════════════════════════════════════

load_data <- function(config) {
  if (file.exists(config$input_file)) {
    df <- read.csv(config$input_file, stringsAsFactors = FALSE)
    cat(sprintf("Loaded: %s (N = %d)\n\n", config$input_file, nrow(df)))

    # Validate
    for (col in c(config$outcome_col, config$model_cols)) {
      if (!col %in% names(df)) {
        stop(sprintf("Column '%s' not found in %s", col, config$input_file))
      }
    }
    return(df)
  } else {
    cat("Input file not found. Using built-in example data.\n\n")
    return(example_data)
  }
}

df <- load_data(CONFIG)

# Rename columns for dcurves
outcome_var <- CONFIG$outcome_col
model_cols  <- CONFIG$model_cols

# ══════════════════════════════════════════════════════════════════════════════
# RUN DCA
# ══════════════════════════════════════════════════════════════════════════════

cat("═══ DECISION CURVE ANALYSIS ════════════════════════════════════════════\n")

# Build formula dynamically
formula_str <- paste(outcome_var, "~",
                     paste(model_cols, collapse = " + "))
dca_formula <- as.formula(formula_str)

dca_result <- dca(
  formula          = dca_formula,
  data             = df,
  thresholds       = seq(CONFIG$threshold_lo, CONFIG$threshold_hi, by = 0.01),
  as_probability   = model_cols  # our columns are already probabilities
)

# ── Print net benefit at key thresholds ───────────────────────────────────────
cat("\nNet Benefit at Selected Thresholds:\n")
key_thresholds <- c(0.10, 0.20, 0.30, 0.40, 0.50)

nb_summary <- dca_result$dca %>%
  filter(threshold %in% key_thresholds) %>%
  select(label, threshold, net_benefit) %>%
  tidyr::pivot_wider(names_from = label, values_from = net_benefit)

print(nb_summary, digits = 3)

# ── Standardized net benefit ──────────────────────────────────────────────────
# NB_std = (NB_model - NB_treat-all) / (p / (1 - p))
# where p = event prevalence

p_event <- mean(df[[outcome_var]], na.rm = TRUE)
cat(sprintf("\nEvent prevalence: %.1f%%\n", p_event * 100))

# ── Interventions avoided per 100 ────────────────────────────────────────────
cat("\nInterventions Avoided per 100 Patients (vs treat-all):\n")
ia_summary <- dca_result$dca %>%
  filter(threshold %in% key_thresholds, !label %in% c("All", "None")) %>%
  mutate(
    nb_all = dca_result$dca$net_benefit[
      dca_result$dca$label == "All" &
        dca_result$dca$threshold %in% threshold
    ][match(threshold, key_thresholds)],
    ia_per_100 = (nb_all - net_benefit) / (threshold / (1 - threshold)) * 100
  ) %>%
  select(label, threshold, net_benefit, ia_per_100)

print(ia_summary, digits = 2)

# ══════════════════════════════════════════════════════════════════════════════
# PLOT — Standard DCA plot
# ══════════════════════════════════════════════════════════════════════════════

# Wong colorblind-safe palette
MODEL_COLORS <- c(
  "#0072B2",  # blue — model 1
  "#D55E00",  # vermillion — model 2
  "#009E73",  # green — model 3 (if present)
  "#E69F00"   # orange — model 4 (if present)
)

# Build label-color mapping (exclude "All" and "None" built-ins)
model_labels_full <- c(CONFIG$model_labels)
color_map <- c(
  setNames(MODEL_COLORS[seq_along(CONFIG$model_cols)], CONFIG$model_cols),
  "All"  = "#888888",
  "None" = "#000000"
)

# Rename model labels for display
dca_plot_data <- dca_result$dca %>%
  mutate(label = case_when(
    label %in% CONFIG$model_cols ~
      CONFIG$model_labels[match(label, CONFIG$model_cols)],
    TRUE ~ label
  ))

# Color map with renamed labels
color_map_renamed <- c(
  setNames(MODEL_COLORS[seq_along(CONFIG$model_labels)], CONFIG$model_labels),
  "All"  = "#888888",
  "None" = "#000000"
)

p_dca <- ggplot(dca_plot_data,
                aes(x = threshold, y = net_benefit,
                    color = label, linetype = label)) +
  geom_line(linewidth = 1.0, na.rm = TRUE) +
  scale_color_manual(values = color_map_renamed, name = NULL) +
  scale_linetype_manual(
    values = c(
      setNames(rep("solid", length(CONFIG$model_labels)), CONFIG$model_labels),
      "All" = "dashed", "None" = "dotted"
    ),
    name = NULL
  ) +
  scale_x_continuous(
    limits = c(CONFIG$threshold_lo, CONFIG$threshold_hi),
    labels = scales::percent_format(accuracy = 1)
  ) +
  scale_y_continuous(
    limits = c(
      -0.05,
      max(dca_result$dca$net_benefit, na.rm = TRUE) * 1.1
    )
  ) +
  geom_hline(yintercept = 0, linetype = "solid", color = "#CCCCCC",
              linewidth = 0.5) +
  labs(
    x     = "Threshold probability",
    y     = "Net benefit",
    title = "Decision Curve Analysis"
  ) +
  theme_classic(base_size = 9, base_family = "Arial") +
  theme(
    legend.position   = "bottom",
    legend.text       = element_text(size = 8),
    axis.title        = element_text(size = 9),
    axis.text         = element_text(size = 8),
    plot.title        = element_text(size = 10, face = "bold"),
    panel.grid.major.y = element_line(color = "#EEEEEE", linewidth = 0.4)
  )

# Save
for (ext in c("pdf", "png")) {
  outfile <- paste0(CONFIG$output_prefix, "_dca.", ext)
  dpi <- if (ext == "png") 300 else NULL
  ggsave(outfile, plot = p_dca, width = 5.5, height = 4.0,
         dpi = dpi, bg = "white")
  cat(sprintf("Saved: %s\n", outfile))
}

# ══════════════════════════════════════════════════════════════════════════════
# SAVE NUMERIC RESULTS
# ══════════════════════════════════════════════════════════════════════════════

results_file <- paste0(CONFIG$output_prefix, "_results.csv")
write.csv(dca_result$dca, results_file, row.names = FALSE)
cat(sprintf("Saved: %s\n", results_file))

# ── Session info ───────────────────────────────────────────────────────────────
cat("\n── Session Info ─────────────────────────────────────────────────────\n")
for (pkg in c("dcurves", "ggplot2", "dplyr")) {
  cat(sprintf("  %-12s %s\n", pkg, packageVersion(pkg)))
}
cat(sprintf("Date: %s\n", format(Sys.time())))
cat("DCA analysis complete.\n")
