# theme_publication.R
# Publication-ready ggplot2 theme for medical research figures
# Standards: Arial 8-10pt, 300 DPI, colorblind-safe (Wong 2011) palette
#
# Usage:
#   source("theme_publication.R")
#   ggplot(data, aes(x, y)) + geom_point() + theme_publication()

# ── Wong (2011) colorblind-safe palette (8 colors) ──────────────────────────
WONG_COLORS <- c(
  "#E69F00",  # orange
  "#56B4E9",  # sky blue
  "#009E73",  # bluish green
  "#F0E442",  # yellow
  "#0072B2",  # blue
  "#D55E00",  # vermillion
  "#CC79A7",  # reddish purple
  "#000000"   # black
)

# Primary 2-color pair (high contrast, colorblind-safe)
WONG_2 <- c("#0072B2", "#D55E00")  # blue + vermillion

# ── Publication theme ────────────────────────────────────────────────────────
theme_publication <- function(base_size = 9,
                               base_family = "Arial",
                               border = TRUE) {
  require(ggplot2)
  require(ggthemes)

  t <- theme_foundation(base_size = base_size, base_family = base_family) +
    theme(
      # Panel
      panel.background  = element_rect(fill = "white", colour = NA),
      panel.grid.major  = element_line(colour = "grey85", linewidth = 0.3),
      panel.grid.minor  = element_blank(),
      panel.border      = if (border) element_rect(colour = "black", fill = NA,
                                                    linewidth = 0.5)
                          else element_blank(),

      # Axes
      axis.line         = if (!border) element_line(colour = "black",
                                                     linewidth = 0.5)
                          else element_blank(),
      axis.text         = element_text(size = base_size - 1, colour = "black"),
      axis.title        = element_text(size = base_size, face = "plain",
                                       colour = "black"),
      axis.ticks        = element_line(colour = "black", linewidth = 0.3),
      axis.ticks.length = unit(2, "pt"),

      # Legend
      legend.background = element_rect(fill = "white", colour = NA),
      legend.key        = element_rect(fill = "white", colour = NA),
      legend.key.size   = unit(0.9, "lines"),
      legend.text       = element_text(size = base_size - 1),
      legend.title      = element_text(size = base_size - 1, face = "bold"),
      legend.margin     = margin(2, 2, 2, 2),
      legend.position   = "bottom",

      # Strip (facet labels)
      strip.background  = element_rect(fill = "grey92", colour = "black",
                                       linewidth = 0.4),
      strip.text        = element_text(size = base_size - 1, face = "bold"),

      # Plot labels
      plot.title        = element_text(size = base_size + 1, face = "bold",
                                       hjust = 0),
      plot.subtitle     = element_text(size = base_size, colour = "grey30",
                                       hjust = 0),
      plot.caption      = element_text(size = base_size - 2, colour = "grey50",
                                       hjust = 1),
      plot.margin       = margin(4, 4, 4, 4, "pt"),

      # Complete theme
      complete = TRUE
    )

  return(t)
}

# ── Color scales ─────────────────────────────────────────────────────────────
scale_colour_wong <- function(...) {
  scale_colour_manual(values = WONG_COLORS, ...)
}

scale_fill_wong <- function(...) {
  scale_fill_manual(values = WONG_COLORS, ...)
}

# ── Figure dimension helpers ─────────────────────────────────────────────────
# Single column: 3.5 inches wide
# Double column: 7.0 inches wide
# Height: typically 2.5–4 inches

save_figure <- function(plot, filename, width = 7.0, height = 3.5,
                        dpi = 300, device = c("pdf", "png")) {
  require(ggplot2)

  device <- match.arg(device, several.ok = TRUE)
  base_name <- tools::file_path_sans_ext(filename)

  for (dev in device) {
    out_file <- paste0(base_name, ".", dev)
    ggsave(out_file, plot = plot, width = width, height = height,
           dpi = dpi, device = dev, bg = "white")
    message("Saved: ", out_file)
  }

  invisible(plot)
}

# ── Reproducibility helper ───────────────────────────────────────────────────
print_session_info <- function() {
  cat("─── Reproducibility Info ───────────────────────────────────────\n")
  cat("Date:", format(Sys.time(), "%Y-%m-%d %H:%M:%S"), "\n")
  cat("R version:", R.version$version.string, "\n")
  pkgs <- c("ggplot2", "ggthemes", "dplyr", "tidyr")
  for (pkg in pkgs) {
    if (requireNamespace(pkg, quietly = TRUE)) {
      cat(sprintf("  %-12s %s\n", pkg,
                  as.character(packageVersion(pkg))))
    }
  }
  cat("────────────────────────────────────────────────────────────────\n")
}

# ── Example usage (run interactively) ────────────────────────────────────────
if (FALSE) {
  library(ggplot2)
  library(ggthemes)

  # Basic scatter plot with theme
  p <- ggplot(mtcars, aes(x = wt, y = mpg, colour = factor(cyl))) +
    geom_point(size = 2) +
    scale_colour_wong() +
    labs(title = "Example Plot",
         x = "Weight (1000 lbs)",
         y = "Miles per Gallon",
         colour = "Cylinders") +
    theme_publication()

  # Save in both formats
  save_figure(p, "example_figure", width = 7.0, height = 3.5,
              device = c("pdf", "png"))

  print_session_info()
}
