# Flow diagrams (STARD / CONSORT / PRISMA / STROBE) — the R recipe

Load-on-demand companion to `/make-figures`. SKILL.md states the mandatory rule (the
standardized R pipeline, never matplotlib `FancyBboxPatch`, never D2 for new diagrams);
this file is the recipe: the YAML schema, the fixed style, the per-project
`create_figure1.R` pattern, and the legacy D2 fallback.

Read it when you are actually generating a reporting-guideline flow diagram. A figure set
with no flow diagram (a ROC curve, a forest plot, a calibration plot) needs none of it.

**Flow diagram generation rule:** STARD/CONSORT/PRISMA/STROBE flow diagrams **MUST** use the standardized R pipeline `scripts/generate_flow_diagram.R` (DiagrammeR + Graphviz dot + rsvg). This is the single canonical tool for all four reporting-guideline flow diagrams. Do NOT use matplotlib `FancyBboxPatch` (manual coordinates break when text changes, and patches distort when embedded in DOCX). Do NOT use D2 for new flow diagrams (font control is weak, overlap requires manual post-processing). The legacy D2 recipe remains documented below as a fallback only when R is unavailable.

**R flow diagram recipe (mandatory for all flow diagrams):**

The pipeline reads a YAML config describing nodes/edges and produces: a true vector PDF (journal submission), a 300 dpi PNG (review copy), and a 600 dpi PNG (RSNA/Eur Radiol line-art). Default style is single-color black outline with white fill in Arial, overriding D2's colored defaults and matplotlib's manual coordinates.

```bash
# 1. One-time system dependency:
brew install librsvg
Rscript -e 'install.packages(c("DiagrammeR","DiagrammeRsvg","rsvg","yaml"))'

# 2. Author a YAML config. Templates for each type live at
#    references/exemplar_diagrams/{strobe,consort,prisma,stard}/template_input.yaml
# 3. Render:
Rscript ${CLAUDE_SKILL_DIR}/scripts/generate_flow_diagram.R \
    --type   {strobe|consort|prisma|stard} \
    --config path/to/counts.yaml \
    --out    figures/figure1_flow
# Outputs: figure1_flow.pdf, figure1_flow.png (300 dpi), figure1_flow_600.png
```

**YAML schema highlights:**
- `rankdir: TB` (top-down, default) or `LR` (left-to-right).
- `nodes:` list with `id`, `label` (use literal `\n` for line breaks, real Unicode `–`, `≤`, `−`, `•`).
- Optional per-node: `highlight: true` (thicker border), `shape: note` (side boxes), `rank_same_with: <other_id>` (place on same horizontal rank).
- `edges:` list with `from`, `to`, optional `style: dashed`, `arrow: false` (no arrowhead), `constraint: false` (edge ignored by layout engine — use for exclusion side-links).
- Numbers in labels **MUST** be CSV-derived in an upstream R script that emits the YAML, or hand-written only when the value lives in a commit-tracked data artifact. Follow numerical-safety rules.

**Style is fixed (do not override in the YAML):**
- Monochrome: all boxes `color=black, fillcolor=white, fontname="Arial"`.
- Penwidth 1.2 default, 1.8 for highlighted cohort box.
- Arrow style: black solid, arrowsize 0.75. Dashed without arrowhead for exclusion side-links.
- Bullet alignment in multi-item labels: Graphviz `\l` (left-align), never `\n` (center). Each `\l` applies to text preceding it.
- **No HTML-like labels** (`label=<...>` with `<B>`, `<I>`, `&#8226;`). Plain quoted labels with `\l` bullets produce tighter, more readable structure than HTML ragged wrapping. Do not reintroduce without explicit approval.
- To add one emphasis color (e.g., Wong blue `#0072B2` for a single highlighted box), edit `scripts/generate_flow_diagram.R` — do not inline hex colors in YAML.

**Per-project `create_figure1.R` pattern (preferred for complex flows):**

When the flow has derived counts, `stopifnot()` reconciliation, multi-rank `{rank=same; ... }` constraints, or exclusion side-cars that the generic YAML dispatcher cannot express cleanly, write a per-project `create_figure1.R` directly (same DiagrammeR + DiagrammeRsvg + rsvg stack, sprintf'd `dot` string). This is the dominant pattern when the generic YAML dispatcher cannot capture the flow:

- STROBE cohort: `<project>/manuscript/figures/create_figure1.R`
- STARD: `<project>/Analysis/figures/create_figure1.R` or `<project>/figures/v2_monochrome/create_figure1.R`
- PRISMA / PRISMA-DTA: `<project>/5_Figures/create_figure1.R` or `<project>/analysis/create_figure1.R`
- CONSORT-edu (naturalistic allocation): `<project>/figures/v2_monochrome/create_figure1.R`

Copy the `STYLE_HEADER` (graph/node/edge attrs) verbatim from any exemplar; then customise nodes, edges, and `{rank=same}` blocks. Use `read.csv()` for cohort counts when possible; if hardcoded, every number must have a source comment referencing manuscript line / CSV cell / screening log row.

**Legacy D2 fallback (only when R unavailable):**

```bash
d2 --layout elk --theme 0 --pad 20 flow.d2 /tmp/raw.png --scale 2
# Resize + 85% vertical compression via Pillow; then render PDF:
d2 --layout elk --theme 0 --pad 20 flow.d2 figures/fig1_flow.pdf
```

Use `font-size: 20-24`, `stroke: black`, `fill: white`. D2 PDF is vector; D2 PNG needs the resize step to match publication density.

---
