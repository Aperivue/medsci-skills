---
name: make-figures
description: Generate publication-ready figures for medical research papers. Supports ROC curves, forest plots, CONSORT/STARD/PRISMA flow diagrams, calibration plots, Kaplan-Meier curves, Bland-Altman plots, confusion matrices, and pipeline diagrams. All figures meet journal specifications with proper dimensions, fonts, and colorblind-safe palettes.
triggers: figure, plot, graph, diagram, 그림, ROC curve, forest plot, flow diagram, CONSORT diagram, PRISMA flow, visualization, chart
tools: Read, Write, Edit, Bash, Grep, Glob
model: inherit
---

# Make-Figures Skill

You are helping a medical researcher generate publication-ready figures for medical research
manuscripts. Every figure must meet journal specifications for dimensions, resolution, fonts, and
color accessibility. Produce clean, data-focused visuals with no chartjunk.

## Communication Rules

- Communicate with the user in their preferred language.
- All figure text (labels, legends, annotations) must be in English.
- Medical terminology is always in English.

## Reference Files

- **Figure specifications**: `${CLAUDE_SKILL_DIR}/references/figure_specs.md`
- **Figure style**: `~/.claude/skills/analyze-stats/references/style/figure_style.mplstyle`
- **Project data**: See CLAUDE.md for data locations under `2_Data/`

Read `figure_specs.md` before generating any figure to confirm journal-specific requirements.

---

## Workflow

### Step 1: Specify

Ask the user for:
1. **Figure type** (from the supported types below)
2. **Data source** (file path, DataFrame, or manual values)
3. **Target journal** (for dimension/font requirements)
4. **Panel layout** (single panel, multi-panel, or let you decide)
5. **Any special requests** (annotations, highlights, reference lines)

If the user provides enough context, infer missing parameters and confirm before proceeding.

### Step 2: Configure

1. Load the figure style file:
   ```python
   import matplotlib.pyplot as plt
   import os
   plt.style.use(os.path.expanduser(
       '~/.claude/skills/analyze-stats/references/style/figure_style.mplstyle'))
   ```
2. Look up journal-specific dimensions from `${CLAUDE_SKILL_DIR}/references/figure_specs.md`.
3. Set the colorblind-safe palette (Wong palette by default).
4. Configure font sizes per element type (title, axis label, tick label, legend, annotation).

### Step 3: Generate

Create the figure using Python (matplotlib/seaborn as primary, with specialized libraries as needed).

**Script structure:**
```python
"""
Figure: {description}
Date: {YYYY-MM-DD}
Target: {journal}
Dimensions: {width} x {height} inches @ {DPI} DPI
"""
import numpy as np
import matplotlib.pyplot as plt
import os

plt.style.use(os.path.expanduser(
    '~/.claude/skills/analyze-stats/references/style/figure_style.mplstyle'))

# Wong colorblind-safe palette
WONG = ['#000000', '#E69F00', '#56B4E9', '#009E73',
        '#F0E442', '#0072B2', '#D55E00', '#CC79A7']

np.random.seed(42)
```

### Step 4: Review

Present the figure to the user and ask:
- Does the layout work?
- Are labels and annotations correct?
- Any adjustments to colors, sizing, or emphasis?

Iterate until the user approves.

### Step 5: Export

Save final outputs:
- **PDF** (vector format, preferred for journal submission)
- **PNG** (300 DPI raster, for review and presentation)
- **TIFF** (if the journal requires it, 300 DPI LZW compression)

Name files descriptively: `fig1_roc_curve.pdf`, `fig2_consort_flow.pdf`, etc.

---

## Supported Figure Types

| Type | Use Case | Key Library | Output |
|------|----------|-------------|--------|
| ROC Curve | Diagnostic accuracy | matplotlib, sklearn | Single/multi-model ROC with AUC |
| Forest Plot | Meta-analysis | matplotlib | Effect sizes with CIs, diamond summary |
| CONSORT Diagram | RCT flow | matplotlib (boxes+arrows) | Patient enrollment flow |
| STARD Diagram | Diagnostic study flow | matplotlib | Index test flow |
| PRISMA Flow | Systematic review | matplotlib | Search/screening/inclusion flow |
| Calibration Plot | Prediction model | matplotlib | Observed vs predicted with Hosmer-Lemeshow |
| KM Curve | Survival analysis | lifelines, matplotlib | With risk table, log-rank p |
| Bland-Altman | Agreement | matplotlib | With mean diff, +/-1.96 SD limits |
| Confusion Matrix | Classification | seaborn | Heatmap with percentages |
| Box/Violin Plot | Group comparison | seaborn | With individual data points |
| Pipeline Diagram | Methods figure | matplotlib (boxes+arrows) | Processing/workflow steps |
| Bar Chart | Categorical comparison | matplotlib | With error bars (CI or SD) |
| Heatmap | Correlation/agreement | seaborn | Color-coded matrix |

---

## Figure Type Templates

### ROC Curve

```python
from sklearn.metrics import roc_curve, auc

fig, ax = plt.subplots(figsize=(3.5, 3.5))
fpr, tpr, _ = roc_curve(y_true, y_score)
roc_auc = auc(fpr, tpr)
ax.plot(fpr, tpr, color=WONG[5], lw=1.5,
        label=f'Model (AUC = {roc_auc:.3f})')
ax.plot([0, 1], [0, 1], 'k--', lw=0.8, alpha=0.5)
ax.set(xlabel='1 - Specificity', ylabel='Sensitivity',
       xlim=[-0.02, 1.02], ylim=[-0.02, 1.02])
ax.legend(loc='lower right', frameon=False)
```

- For multiple models: use distinct Wong palette colors, include AUC + 95% CI in legend.
- For comparison: report DeLong p-value in annotation.

### Forest Plot

- Horizontal layout: effect sizes as squares (sized by weight), CIs as lines.
- Diamond at bottom for pooled estimate.
- Vertical dashed line at null effect (OR=1 or MD=0).
- Axis label: "Favours A | Favours B" or appropriate.
- Include heterogeneity stats (I-squared, p) below the diamond.

### Flow Diagrams (CONSORT / STARD / PRISMA)

- Use rectangular boxes with rounded corners for stages.
- Arrows connect stages vertically; side boxes for exclusions.
- Consistent box widths, centered text.
- Numbers must be included in each box (e.g., "Assessed for eligibility (n = 450)").
- Follow the official template layout from each guideline.
- Use matplotlib patches and FancyArrowPatch for clean rendering.

### Calibration Plot

- 45-degree reference line (perfect calibration).
- Grouped observed vs predicted with error bars.
- Report Hosmer-Lemeshow statistic and Brier score in annotation.
- Optional: histogram of predicted probabilities at the bottom.

### Kaplan-Meier Curve

- Step function with distinct colors per group.
- Censoring marks as small vertical ticks.
- Number-at-risk table below the plot (aligned with x-axis ticks).
- Log-rank p-value in annotation.
- Median survival with 95% CI if applicable.

### Bland-Altman Plot

- X-axis: mean of two measurements.
- Y-axis: difference between measurements.
- Horizontal lines: mean difference (solid), +/-1.96 SD (dashed).
- Annotate the mean diff and limits of agreement values.
- Optional: proportional bias check (regression line through points).

### Confusion Matrix

- Heatmap with both counts and percentages in each cell.
- Row-normalized percentages preferred (sensitivity per class).
- Clear axis labels: "Predicted" (x) and "Actual" (y).
- Use sequential colormap (Blues or Greens), not diverging.

### Box/Violin Plot

- Show individual data points (jittered) overlaid on box or violin.
- Mark median and mean distinctly.
- Statistical annotation brackets with significance stars.
- Stars: * p<0.05, ** p<0.01, *** p<0.001, ns for non-significant.

### Pipeline Diagram

- Horizontal or vertical flow of processing stages.
- Boxes: rounded rectangles with stage name and brief description.
- Arrows: labeled with data counts or transformation type.
- Color-code stages by category (data collection, processing, validation).
- Keep text minimal; use supplementary caption for details.

### Bar Chart

- Error bars: 95% CI (preferred) or SD, stated in caption.
- Individual data points overlaid if n < 30.
- Horizontal orientation for many categories.
- Sort by value (descending) unless order is meaningful.

### Heatmap

- Annotate cells with values.
- Use sequential colormap for correlation (coolwarm diverging if centered at zero).
- Mask diagonal for correlation matrices.
- Cluster rows/columns if appropriate.

---

## Style Rules

### Colors

**Wong colorblind-safe palette (default):**
```python
WONG = ['#000000', '#E69F00', '#56B4E9', '#009E73',
        '#F0E442', '#0072B2', '#D55E00', '#CC79A7']
```

**Sequential palettes (for heatmaps):**
- Positive values: `Blues` or `Greens`
- Diverging (centered at 0): `coolwarm` or `RdBu_r`
- Agreement matrices: `YlOrRd`

**Rules:**
- Never use red-green only distinctions.
- Use line style (solid, dashed, dotted) in addition to color for line plots.
- Use marker shape in addition to color for scatter plots.

### Typography

| Element | Font Size | Weight |
|---------|-----------|--------|
| Figure title (if any) | 10 pt | Bold |
| Axis label | 9 pt | Regular |
| Tick label | 8 pt | Regular |
| Legend text | 8 pt | Regular |
| Annotation | 8 pt | Regular |
| Panel label (A, B, C) | 12 pt | Bold |

- Font family: Arial or Helvetica (sans-serif).
- Panel labels: uppercase bold letter, top-left of each panel.

### Layout

- Minimize white space while maintaining readability.
- Align multi-panel figures on a grid.
- Consistent axis ranges across comparable panels.
- No figure titles in the plot itself (title goes in the caption below).

### Statistical Annotations

- Significance stars: * p<0.05, ** p<0.01, *** p<0.001
- Place above comparison brackets.
- Report exact p-value in the figure legend or caption, not in the plot.
- For AUC, correlation, or agreement: display in the legend with 95% CI.

---

## Journal Specifications

Default dimensions (override from `figure_specs.md` if journal-specific):

- **Single column**: 3.5 in (88 mm) width
- **1.5 column**: 5.0 in (127 mm) width
- **Double column**: 7.0 in (178 mm) width
- **Full page**: 7.0 x 9.5 in (178 x 241 mm)
- **DPI**: 300 minimum for halftone, 600 for line art
- **File formats**: PDF (vector, preferred) + PNG (300 DPI)
- **No chartjunk**: no 3D effects, no unnecessary gridlines, no decorative elements, no gradient fills

---

## Multi-Panel Figures

For composite figures with multiple panels:

```python
fig, axes = plt.subplots(nrows, ncols, figsize=(width, height))

# Label each panel
for ax, label in zip(axes.flat, 'ABCDEFGH'):
    ax.text(-0.15, 1.05, label, transform=ax.transAxes,
            fontsize=12, fontweight='bold', va='top')
```

Common layouts:
- 2-panel horizontal: `figsize=(7.0, 3.5)`, 1 row x 2 cols
- 2-panel vertical: `figsize=(3.5, 7.0)`, 2 rows x 1 col
- 2x2 grid: `figsize=(7.0, 7.0)`, 2 rows x 2 cols
- 3-panel: `figsize=(7.0, 3.0)`, 1 row x 3 cols

Use `plt.tight_layout()` or `fig.subplots_adjust()` for spacing.

---

## Caption Writing

After generating each figure, draft a caption following these rules:

1. **First sentence**: Describe what the figure shows (type + key finding).
2. **Subsequent sentences**: Define abbreviations, explain symbols, state sample sizes.
3. **Statistical details**: Note the test used and significance threshold.
4. **Format**: "Figure {N}. {Caption text}" -- no bold, no title case.

Example:
> Figure 1. Receiver operating characteristic curves comparing the diagnostic performance of
> the multi-agent pipeline (blue) and single-agent baseline (orange) for identifying incorrect
> Anki flashcard content. The area under the curve was 0.92 (95% CI: 0.89-0.95) for the
> multi-agent pipeline and 0.84 (95% CI: 0.80-0.88) for the single-agent baseline (DeLong
> test, p = 0.003). The dashed diagonal line represents chance performance.

---

## Skill Interactions

| When | Call | Purpose |
|------|------|---------|
| Need statistical values for plot | `/analyze-stats` | Get computed values (AUC, CI, p-values) |
| Flow diagram for manuscript | `/write-paper` Phase 2 | Coordinate with Tables & Figures plan |
| Caption review | `/write-paper` Phase 7 | Final polish pass |

---

## Error Handling

- If data is insufficient for the requested figure type, explain what is needed and ask the user.
- If a figure exceeds journal dimension limits, resize and report the adjustment.
- If text overlaps in the figure, try `tight_layout()`, reduce font size, or adjust spacing.
- Never fabricate data points. If sample data is needed for a template demo, explicitly label it as "example data."

## CLI Tools Available

ImageMagick, Ghostscript, FFmpeg are installed and can be used for post-processing:

```bash
# Figure DPI/format conversion for journal submission
magick input.png -density 300 -units PixelsPerInch output.tiff
magick input.png -resize 1200x -quality 95 output.jpg

# CMYK conversion (some print journals require this)
magick input.png -colorspace CMYK output.tiff

# Multi-panel figure assembly (A/B/C/D panels)
magick montage panelA.png panelB.png panelC.png panelD.png \
  -tile 2x2 -geometry +10+10 -density 300 combined.png

# Animated figure (GIF from frame sequence)
ffmpeg -framerate 2 -i frame_%03d.png -vf "scale=800:-1" output.gif

# Video from figure sequence (for supplementary materials)
ffmpeg -framerate 1 -i slide_%03d.png -c:v libx264 -pix_fmt yuv420p supplementary_video.mp4
```

## AI Image Generation

If a `generate_image.py` script is available in `${CLAUDE_SKILL_DIR}/scripts/`, it can be used
for AI-generated illustrations via the Gemini API:
```bash
python ${CLAUDE_SKILL_DIR}/scripts/generate_image.py \
  "prompt" --output output.png --aspect 16:9
```
Useful for graphical abstracts, procedural schematics, and pipeline diagrams.

## Language

- Code and figure text: English
- Communication with user: Match user's preferred language
- Medical terms: English only
