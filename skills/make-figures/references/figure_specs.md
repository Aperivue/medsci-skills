# Figure Specifications Reference

## Journal Dimension Requirements

| Journal | Single Column | 1.5 Column | Double Column | Full Page | Max Height |
|---------|--------------|------------|---------------|-----------|------------|
| AJR | 3.3 in (84 mm) | 5.0 in (127 mm) | 6.83 in (174 mm) | 6.83 x 9.19 in | 9.19 in |
| Radiology | 3.37 in (85.6 mm) | 5.04 in (128 mm) | 6.83 in (173.5 mm) | 6.83 x 9.19 in | 9.19 in |
| Radiology: AI | 3.37 in (85.6 mm) | 5.04 in (128 mm) | 6.83 in (173.5 mm) | 6.83 x 9.19 in | 9.19 in |
| European Radiology | 3.35 in (85 mm) | -- | 6.85 in (174 mm) | 6.85 x 9.13 in | 9.13 in |
| KJR | 3.27 in (83 mm) | -- | 6.89 in (175 mm) | 6.89 x 9.21 in | 9.21 in |
| **Default** | **3.5 in (88 mm)** | **5.0 in (127 mm)** | **7.0 in (178 mm)** | **7.0 x 9.5 in** | **9.5 in** |

### Notes

- Dimensions are the maximum printable area; figures should not exceed these.
- When in doubt, use single-column width (3.5 in) for simple plots and double-column (7.0 in) for complex or multi-panel figures.
- Height is flexible but should not exceed the max height listed above.

---

## DPI Requirements

| Content Type | Minimum DPI | Recommended DPI | Notes |
|-------------|-------------|-----------------|-------|
| Line art (diagrams, flow charts) | 600 | 1200 | Vector PDF preferred |
| Halftone (photographs, medical images) | 300 | 300 | TIFF or PNG |
| Combination (line art + halftone) | 600 | 600 | |
| Color figures | 300 | 300 | |
| Review/presentation | 150 | 300 | PNG acceptable |

---

## File Format Requirements by Journal

| Journal | Preferred Format | Accepted Formats | Notes |
|---------|-----------------|------------------|-------|
| AJR | TIFF | TIFF, EPS, PDF, JPEG | TIFF LZW compression; JPEG only for photos |
| Radiology | TIFF | TIFF, EPS, PDF, PNG | EPS for vector; TIFF for raster |
| Radiology: AI | PDF | PDF, TIFF, EPS, PNG | PDF preferred for vector graphics |
| European Radiology | TIFF | TIFF, EPS, PDF | EPS or PDF for line art |
| KJR | TIFF | TIFF, JPEG, PPT | PPT accepted but not recommended |
| **Default** | **PDF + PNG** | PDF (vector), PNG (raster) | Always produce both |

---

## Color Palettes

### Wong Colorblind-Safe Palette (Default)

| Index | Name | Hex | Use |
|-------|------|-----|-----|
| 0 | Black | `#000000` | Text, axes, reference lines |
| 1 | Orange | `#E69F00` | Primary category 1 |
| 2 | Sky Blue | `#56B4E9` | Primary category 2 |
| 3 | Bluish Green | `#009E73` | Primary category 3 |
| 4 | Yellow | `#F0E442` | Highlight (use sparingly) |
| 5 | Blue | `#0072B2` | Primary model/group |
| 6 | Vermillion | `#D55E00` | Secondary model/group |
| 7 | Reddish Purple | `#CC79A7` | Tertiary model/group |

```python
WONG = ['#000000', '#E69F00', '#56B4E9', '#009E73',
        '#F0E442', '#0072B2', '#D55E00', '#CC79A7']
```

### Sequential Palettes (Heatmaps)

| Use Case | Matplotlib Colormap | Direction |
|----------|-------------------|-----------|
| Positive values only | `Blues`, `Greens`, `Oranges` | Light to dark |
| Diverging (centered at 0) | `coolwarm`, `RdBu_r` | Negative=blue, positive=red |
| Correlation matrix | `coolwarm` | -1 to +1 centered |
| Agreement matrix | `YlOrRd` | Low=yellow, high=red |
| Confusion matrix | `Blues` | Low=white, high=blue |
| p-value heatmap | `Reds_r` | Significant=dark |

### Rules

- Never rely on color alone; combine with line style, marker shape, or hatching.
- Test figures in grayscale to ensure readability.
- Avoid pure red (#FF0000) and pure green (#00FF00) adjacent to each other.

---

## Font Size Table

| Element | Size (pt) | Weight | Font Family |
|---------|-----------|--------|-------------|
| Figure title (rare, prefer caption) | 10 | Bold | Arial / Helvetica |
| Axis label | 9 | Regular | Arial / Helvetica |
| Tick label | 8 | Regular | Arial / Helvetica |
| Legend text | 8 | Regular | Arial / Helvetica |
| Annotation text | 8 | Regular | Arial / Helvetica |
| Panel label (A, B, C) | 12 | Bold | Arial / Helvetica |
| Inset text | 7 | Regular | Arial / Helvetica |
| Table text (in figure) | 7-8 | Regular | Arial / Helvetica |

### Rules

- Minimum readable size after print: 6 pt.
- All text in figures must be embedded (not rasterized) for vector formats.
- Use `plt.rcParams['font.family'] = 'sans-serif'` and `plt.rcParams['font.sans-serif'] = ['Arial', 'Helvetica']`.

---

## Common Figure Layouts

### Single Panel

```
+-----------+
|           |
|   Plot    |
|           |
+-----------+
```
- Width: single column (3.5 in) or double column (7.0 in)
- Height: proportional, typically 1:1 or 4:3 aspect ratio
- Use: ROC curve, calibration plot, KM curve, Bland-Altman

### 2-Panel Horizontal

```
+-----+-----+
|  A  |  B  |
+-----+-----+
```
- Width: double column (7.0 in), each panel ~3.3 in
- Height: 3.0-3.5 in
- Use: comparing two related plots (e.g., ROC for two endpoints)

### 2-Panel Vertical

```
+-----+
|  A  |
+-----+
|  B  |
+-----+
```
- Width: single column (3.5 in)
- Height: 6.0-7.0 in
- Use: same variable, different conditions (e.g., training vs test set)

### 2x2 Grid

```
+-----+-----+
|  A  |  B  |
+-----+-----+
|  C  |  D  |
+-----+-----+
```
- Width: double column (7.0 in), each panel ~3.3 in
- Height: 6.0-7.0 in
- Use: four related analyses (e.g., subgroup comparisons)

### 3-Panel Horizontal

```
+---+---+---+
| A | B | C |
+---+---+---+
```
- Width: double column (7.0 in), each panel ~2.1 in
- Height: 2.5-3.0 in
- Use: three conditions or progressive stages

### Unequal Panels (GridSpec)

```
+---------+----+
|         | B  |
|    A    +----+
|         | C  |
+---------+----+
```
- Use `matplotlib.gridspec.GridSpec` for custom layouts
- Use: main result (A) with supporting details (B, C)

---

## Caption Writing Guidelines

### Structure

1. **Sentence 1**: What the figure shows -- figure type and key finding.
2. **Sentences 2-3**: Define symbols, abbreviations, colors, and line styles.
3. **Sentence 3-4**: State sample sizes, statistical tests, significance levels.
4. **Final sentence**: Interpretation aid (if not self-evident from the plot).

### Format

```
Figure {N}. {Description starting with capital letter, ending with period.}
```

- No bold title. No title case (except proper nouns and abbreviations).
- Use sentence case throughout.
- Spell out abbreviations on first use in the caption.

### Multi-Panel Captions

```
Figure {N}. {Overall description.} (A) {Panel A description.} (B) {Panel B description.}
```

### Examples

**ROC Curve:**
> Figure 2. Receiver operating characteristic curves for the multi-agent validation pipeline. The area under the curve was 0.92 (95% CI: 0.89-0.95) for the full pipeline and 0.84 (95% CI: 0.80-0.88) for the single-agent baseline (DeLong test, p = 0.003). The dashed diagonal line represents chance performance (AUC = 0.5). AUC = area under the curve, CI = confidence interval.

**Flow Diagram:**
> Figure 1. Study flow diagram following the Standards for Reporting Diagnostic Accuracy Studies (STARD) 2015 guidelines. Numbers in each box represent the count of Anki flashcards at each stage of the validation pipeline.

**Multi-Panel:**
> Figure 3. Agreement analysis between human reviewers and the multi-agent pipeline. (A) Bland-Altman plot showing the difference in quality scores between reviewer 1 and the pipeline against their mean. Horizontal dashed lines indicate the mean difference and 95% limits of agreement. (B) Scatter plot of reviewer 1 versus pipeline scores with the line of identity (dashed).

---

## Figure Numbering Conventions

- Number figures sequentially as they appear in the text (Figure 1, Figure 2, ...).
- Supplemental figures: Figure S1, Figure S2, ...
- Reference every figure at least once in the main text.
- Place figures after first mention (or at end, per journal preference).
- Do not include a figure title inside the plot area; use the caption below instead.

---

## Flow Diagram Tool Selection (STROBE / CONSORT / PRISMA / STARD)

All reporting-guideline flow diagrams use a single canonical pipeline: `scripts/generate_flow_diagram.R` (DiagrammeR DOT → DiagrammeRsvg → rsvg).

### Why this stack

| Requirement | Requirement detail | DiagrammeR + rsvg |
|---|---|---|
| Vector PDF (editable, journal-grade) | Radiology/NEJM/Eur Radiol require EPS/AI/PDF | **True vector via `rsvg_pdf()`** |
| 300 / 600 / 1200 dpi PNG | RSNA line-art = 1200 dpi; Eur Radiol = 300–1000 | **Arbitrary DPI via `rsvg_png(width=...)`** |
| Arial font embedded | AMA/RSNA style | `fontname="Arial"` enforced in DOT header |
| Single-color monochrome outline | BMJ/Annals IM convention; Eugene's preference | `color=black, fillcolor=white, style=filled` |
| Auto-overlap resolution | Labels change size; manual coords fail | Graphviz `dot` hierarchical engine |
| 4 reporting guidelines in one tool | Avoid stack sprawl | Generic DOT template switch |

### Why not the obvious alternatives

| Rejected tool | Reason |
|---|---|
| matplotlib `FancyBboxPatch` (manual coords) | Overlap on label change; DOCX embed distortion. Root cause of CK-5 Figure 1 rework (2026-04-20). |
| D2 + post-processing | Weak Arial enforcement; PNG needs 85% vertical compression hack; font-size must be manually set 20–24. Retained as legacy fallback only. |
| R `consort` v1.2.2 | CONSORT/STROBE only; STARD/PRISMA not covered; box style parameters not officially exposed (requires gpar override). |
| R `PRISMA2020` v1.1.1 | `PRISMA_save()` uses webshot → PDF rasterized; no DPI parameter. Not suitable for journal submission. |
| Mermaid / PlantUML | Font control weak; hard to enforce Arial + monochrome outline. |

### PRISMA 2020 compliance

The generic DOT template in `generate_flow_diagram.R` implements the PRISMA 2020 structure (two identification streams, duplicates-removed box, title/abstract screening, full-text retrieval, full-text assessment, final inclusion) and can reproduce the official template shape. When a journal explicitly requires use of the PRISMA2020 R package or Shiny app for provenance, run that tool separately; the DiagrammeR pipeline is the default for all other submissions.

### File outputs

Every render emits three files at the same prefix:

```
<prefix>.pdf        true vector (journal submission, figure_manifest primary)
<prefix>.png        300 dpi (2400 px wide; review copy, DOCX embed)
<prefix>_600.png    600 dpi (4800 px wide; RSNA/Eur Radiol line-art)
```

### System dependency

`brew install librsvg` (macOS; one-time). On Linux: `apt-get install librsvg2-bin`.
