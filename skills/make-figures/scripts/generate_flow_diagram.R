#!/usr/bin/env Rscript
# generate_flow_diagram.R
# Monochrome outline flow diagrams (STROBE / CONSORT / PRISMA / STARD).
#
# Usage:
#   Rscript generate_flow_diagram.R \
#       --type {strobe|consort|prisma|stard} \
#       --config <path/to/counts.yaml> \
#       --out   <path/to/output_prefix>
#
# Output:
#   <prefix>.pdf            true vector PDF (journal submission)
#   <prefix>.png            ~300 dpi review copy (width 2400)
#   <prefix>_600.png        600 dpi RSNA/Eur Radiol line-art
#
# YAML schema (see references/exemplar_diagrams/<type>/example_input.yaml):
#   title: "Optional title"
#   rankdir: TB            # or LR
#   nodes:
#     - id: db
#       label: "Database (n = 1,000)"
#       highlight: true    # optional, draws thicker border
#       shape: note        # optional; overrides default "box"
#     - id: excl
#       label: "Excluded (n = 50)"
#       rank_same_with: db # optional; renders on same rank as <id>
#   edges:
#     - from: db
#       to:   cohort
#       style: solid       # or dashed
#       arrow: true        # false -> no arrowhead
#       constraint: true   # false -> layout ignores this edge
#
# Dependencies: DiagrammeR, DiagrammeRsvg, rsvg, yaml, librsvg (system).

suppressPackageStartupMessages({
  library(DiagrammeR); library(DiagrammeRsvg); library(rsvg); library(yaml)
})

# ---- CLI parsing ------------------------------------------------------------
parse_args <- function() {
  args <- commandArgs(trailingOnly = TRUE)
  out  <- list(type = NULL, config = NULL, out = NULL)
  i <- 1L
  while (i <= length(args)) {
    key <- args[[i]]; val <- args[[i + 1L]]
    if (key == "--type")   out$type   <- val
    if (key == "--config") out$config <- val
    if (key == "--out")    out$out    <- val
    i <- i + 2L
  }
  valid <- c("strobe", "consort", "prisma", "stard")
  if (is.null(out$type) || !(out$type %in% valid))
    stop("--type must be one of: ", paste(valid, collapse = ", "))
  if (is.null(out$config) || !file.exists(out$config))
    stop("--config file missing or not found: ", out$config)
  if (is.null(out$out)) stop("--out prefix required")
  out
}

# ---- DOT assembly -----------------------------------------------------------
STYLE_HEADER <- '  graph [layout=dot, rankdir=%s, fontname="Arial",
         splines=ortho, nodesep=0.45, ranksep=0.55]
  node  [shape=box, style="rounded,filled", fillcolor=white,
         color=black, fontname="Arial", fontsize=11, penwidth=1.2,
         margin="0.20,0.12"]
  edge  [color=black, arrowhead=normal, arrowsize=0.75, penwidth=1.0]'

escape_label <- function(txt) {
  # Convert \n in YAML-supplied string to DOT literal "\n" for line break.
  txt <- gsub('"', '\\\\"', txt, fixed = TRUE)
  gsub("\n", "\\n", txt, fixed = TRUE)
}

node_line <- function(node) {
  attrs <- c(sprintf('label="%s"', escape_label(node$label)))
  if (!is.null(node$shape))    attrs <- c(attrs, sprintf('shape=%s', node$shape))
  if (isTRUE(node$highlight))  attrs <- c(attrs, 'penwidth=1.8')
  if (!is.null(node$fontsize)) attrs <- c(attrs, sprintf('fontsize=%d', node$fontsize))
  sprintf("  %s [%s]", node$id, paste(attrs, collapse = ", "))
}

edge_line <- function(e) {
  attrs <- character()
  if (!is.null(e$style) && e$style != "solid")
    attrs <- c(attrs, sprintf("style=%s", e$style))
  if (isFALSE(e$arrow))       attrs <- c(attrs, "arrowhead=none")
  if (isFALSE(e$constraint))  attrs <- c(attrs, "constraint=false")
  suffix <- if (length(attrs)) sprintf(" [%s]", paste(attrs, collapse = ", ")) else ""
  sprintf("  %s -> %s%s", e$from, e$to, suffix)
}

rank_same_lines <- function(nodes) {
  pairs <- Filter(function(n) !is.null(n$rank_same_with), nodes)
  if (!length(pairs)) return(character())
  vapply(pairs, function(n)
         sprintf("  { rank=same; %s; %s }", n$rank_same_with, n$id),
         character(1))
}

build_dot <- function(cfg) {
  rankdir <- if (!is.null(cfg$rankdir)) cfg$rankdir else "TB"
  header  <- sprintf(STYLE_HEADER, rankdir)
  nodes   <- vapply(cfg$nodes, node_line, character(1))
  edges   <- vapply(cfg$edges, edge_line, character(1))
  ranks   <- rank_same_lines(cfg$nodes)
  paste(c("digraph flow {", header, nodes, edges, ranks, "}"), collapse = "\n")
}

# ---- Render -----------------------------------------------------------------
render <- function(dot, prefix) {
  svg <- export_svg(grViz(dot))
  raw <- charToRaw(svg)
  rsvg_pdf(raw, paste0(prefix, ".pdf"))
  rsvg_png(raw, paste0(prefix, ".png"),     width = 2400)
  rsvg_png(raw, paste0(prefix, "_600.png"), width = 4800)
  invisible(list(pdf = paste0(prefix, ".pdf"),
                 png = paste0(prefix, ".png"),
                 png600 = paste0(prefix, "_600.png")))
}

main <- function() {
  a <- parse_args()
  cfg <- yaml::read_yaml(a$config)
  # Type is informational for now (same style applies).
  # Future: load type-specific defaults from references/exemplar_diagrams/<type>/template.dot
  dot <- build_dot(cfg)
  out <- render(dot, a$out)
  cat(sprintf("[%s] rendered: %s + %s + %s\n",
              a$type, out$pdf, out$png, out$png600))
}

if (!interactive()) main()
