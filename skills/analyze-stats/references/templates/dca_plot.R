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
  output_prefix = "dca",
  # TRUE only to try the script on simulated data. A missing or misnamed input file
  # is an error, never a silent switch to simulated data.
  use_example_data = FALSE
)

# ══════════════════════════════════════════════════════════════════════════════
# EXAMPLE DATA — used only when CONFIG$use_example_data is TRUE
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
  if (isTRUE(config$use_example_data)) {
    cat("*** SIMULATED EXAMPLE DATA (use_example_data = TRUE) -- not a real analysis ***\n\n")
    return(example_data)
  }
  if (!file.exists(config$input_file)) {
    stop(sprintf("Input file '%s' not found (set CONFIG$input_file).", config$input_file))
  }
  df <- read.csv(config$input_file, stringsAsFactors = FALSE)
  cat(sprintf("Loaded: %s (N = %d)\n\n", config$input_file, nrow(df)))

  # Validate
  for (col in c(config$outcome_col, config$model_cols)) {
    if (!col %in% names(df)) {
      stop(sprintf("Column '%s' not found in %s", col, config$input_file))
    }
  }
  # DCA needs predicted probabilities. dca(as_probability = ...) would instead REFIT a
  # logistic model of the outcome on the column, i.e. recalibrate it on these data,
  # which hides exactly the miscalibration net benefit is meant to penalise.
  for (col in config$model_cols) {
    v <- df[[col]]
    if (any(v < 0 | v > 1, na.rm = TRUE)) {
      stop(sprintf(paste0("Column '%s' is not a probability (values outside 0-1). ",
                          "Convert the score with a model fitted on development data first."),
                   col))
    }
  }
  return(df)
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

# The model columns are already probabilities: no as_probability (see load_data)
dca_result <- dca(
  formula          = dca_formula,
  data             = df,
  thresholds       = seq(CONFIG$threshold_lo, CONFIG$threshold_hi, by = 0.01)
)

# ── Print net benefit at key thresholds ───────────────────────────────────────
cat("\nNet Benefit at Selected Thresholds:\n")
key_thresholds <- c(0.10, 0.20, 0.30, 0.40, 0.50)
# thresholds come from seq(); match with a tolerance, not %in%
at_key <- function(t) sapply(t, function(x) any(abs(x - key_thresholds) < 1e-9))

nb_summary <- dca_result$dca %>%
  filter(at_key(threshold)) %>%
  select(label, threshold, net_benefit) %>%
  tidyr::pivot_wider(names_from = label, values_from = net_benefit)

print(nb_summary, digits = 3)

# ── Standardized net benefit ──────────────────────────────────────────────────
# sNB = NB / p (p = event prevalence; the maximum achievable NB), so 1 = perfect.
p_event <- mean(df[[outcome_var]], na.rm = TRUE)
cat(sprintf("\nEvent prevalence: %.1f%%\n", p_event * 100))

# ── Net interventions avoided per 100 (vs treat-all) ─────────────────────────
# (NB_model - NB_treat_all) / (pt / (1 - pt)) * 100  (Vickers, Van Calster &
# Steyerberg 2016, doi:10.1136/bmj.i6), computed by dcurves itself
cat("\nNet Interventions Avoided per 100 Patients (vs treat-all):\n")
ia_summary <- dca_result %>%
  net_intervention_avoided(nper = 100) %>%
  as_tibble() %>%
  filter(at_key(threshold), !variable %in% c("all", "none")) %>%
  select(label, threshold, net_benefit, net_intervention_avoided)

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

# Rename model labels for display
dca_plot_data <- dca_result$dca %>%
  mutate(label = case_when(
    label %in% CONFIG$model_cols ~
      CONFIG$model_labels[match(label, CONFIG$model_cols)],
    TRUE ~ label
  ))

# Color map with renamed labels (dcurves labels its reference strategies
# "Treat All" / "Treat None")
color_map_renamed <- c(
  setNames(MODEL_COLORS[seq_along(CONFIG$model_labels)], CONFIG$model_labels),
  "Treat All"  = "#888888",
  "Treat None" = "#000000"
)

p_dca <- ggplot(dca_plot_data,
                aes(x = threshold, y = net_benefit,
                    color = label, linetype = label)) +
  geom_line(linewidth = 1.0, na.rm = TRUE) +
  scale_color_manual(values = color_map_renamed, name = NULL) +
  scale_linetype_manual(
    values = c(
      setNames(rep("solid", length(CONFIG$model_labels)), CONFIG$model_labels),
      "Treat All" = "dashed", "Treat None" = "dotted"
    ),
    name = NULL
  ) +
  scale_x_continuous(
    limits = c(CONFIG$threshold_lo, CONFIG$threshold_hi),
    labels = scales::percent_format(accuracy = 1)
  ) +
  # zoom (coord_cartesian) rather than scale limits, which would drop the
  # treat-all segments below the axis instead of clipping them
  coord_cartesian(ylim = c(-0.05, max(dca_result$dca$net_benefit, na.rm = TRUE) * 1.1)) +
  geom_hline(yintercept = 0, linetype = "solid", color = "#CCCCCC",
              linewidth = 0.5) +
  labs(
    x     = "Threshold probability",
    y     = "Net benefit",
    title = "Decision Curve Analysis"
  ) +
  # "sans" = Helvetica in PDF, Arial on Windows; the pdf() device has no "Arial"
  # font family and stops with "invalid font type"
  theme_classic(base_size = 9, base_family = "sans") +
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
  args <- list(outfile, plot = p_dca, width = 5.5, height = 4.0, bg = "white")
  if (ext == "png") args$dpi <- 300   # dpi = NULL is an error in ggsave
  do.call(ggsave, args)
  cat(sprintf("Saved: %s\n", outfile))
}

# ══════════════════════════════════════════════════════════════════════════════
# SAVE NUMERIC RESULTS
# ══════════════════════════════════════════════════════════════════════════════

results_file <- paste0(CONFIG$output_prefix, "_results.csv")
write.csv(as_tibble(net_intervention_avoided(dca_result, nper = 100)),
          results_file, row.names = FALSE)
cat(sprintf("Saved: %s\n", results_file))

# ── Session info ───────────────────────────────────────────────────────────────
cat("\n── Session Info ─────────────────────────────────────────────────────\n")
for (pkg in c("dcurves", "ggplot2", "dplyr")) {
  cat(sprintf("  %-12s %s\n", pkg, packageVersion(pkg)))
}
cat(sprintf("Date: %s\n", format(Sys.time())))
cat("DCA analysis complete.\n")
