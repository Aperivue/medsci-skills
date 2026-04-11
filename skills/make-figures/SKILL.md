---
name: make-figures
description: Generate publication-ready figures and visual abstracts for medical research papers. Supports ROC curves, forest plots, CONSORT/STARD/PRISMA flow diagrams, calibration plots, Kaplan-Meier curves, Bland-Altman plots, confusion matrices, pipeline diagrams, and journal-specific visual/graphical abstracts (python-pptx template-based).
triggers: figure, plot, graph, diagram, ROC curve, forest plot, flow diagram, CONSORT diagram, PRISMA flow, visualization, chart, visual abstract, graphical abstract
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

## Data Privacy Check

Before reading any data file, check whether it might contain Protected Health Information (PHI):

1. If `*_deidentified.*` files exist in the working directory, use those preferentially.
2. If only raw CSV/Excel files exist (no `*_deidentified.*` counterpart), warn the user:
   > "이 데이터에 환자 식별정보(이름, 주민번호, 연락처 등)가 포함되어 있습니까?
   > 포함된 경우 `/deidentify` 스킬로 먼저 비식별화를 진행해주세요."
3. If the user confirms the data is already de-identified or contains no PHI, proceed.

## Reference Files

- **Figure specifications**: `${CLAUDE_SKILL_DIR}/references/figure_specs.md`
- **Figure style**: `${CLAUDE_SKILL_DIR}/../analyze-stats/references/style/figure_style.mplstyle` (or project's CLAUDE.md if available)
- **Project data**: See CLAUDE.md for data locations under `2_Data/`

Read `figure_specs.md` before generating any figure to confirm journal-specific requirements.

---

## AI-Generated Figure Warning

AI-generated illustrations (from Genspak, Canva AI, DALL-E, etc.) are immediately
recognizable to experienced reviewers and audiences. Telltale signs include:

- **Small decorative icons** that add no information
- **Overly uniform layouts** with templated grid patterns
- **Text too small** to read at print resolution
- **Generic medical clip-art style** that does not match the study specifics

**Rule**: AI tools may assist with figure drafting, but the final figure must not look
AI-generated. Always customize layouts, replace generic icons with study-specific visuals,
adjust text sizing, and verify that every visual element serves a purpose.

For important presentations and journal submissions, an AI-looking figure gives the
impression of low effort. When time permits, use Canva (for illustrations) or manual
PPT drawing (for anatomical sketches) to produce figures that show intentional design.

---

## DPI and Resolution Guide

| Output | Minimum DPI | Notes |
|--------|------------|-------|
| Journal halftone (photos, screenshots) | 300 | Standard for most journals |
| Journal line art (diagrams, graphs) | 600 | Required by Radiology, most Elsevier journals |
| Poster presentation | 150-200 | Lower is acceptable for large-format prints |
| Screen/web only | 72-150 | Not for print submission |

**Practical workflow for screen captures**:
- Use HyperSnap or similar tool with DPI pre-set to the journal requirement
- Compose the figure in PPT at high zoom → capture at target DPI → save as TIFF/PNG
- Verify final file dimensions match journal column width requirements

---

## Visual Abstract / Graphical Abstract

Many journals now require or strongly encourage visual abstracts. European Radiology made
graphical abstracts mandatory for all Original Articles from first revision (Jan 2025).
Submitting one voluntarily signals effort and can improve editorial impression.

### Journal Requirements

| Status | Example Journals |
|--------|-----------------|
| **Mandatory** | European Radiology (from 1st revision, all Original Articles) |
| **Encouraged** | Abdominal Radiology, JCO, Annals of Internal Medicine |
| **Voluntary** | Most other journals — improves social media visibility |

Check the target journal profile (`write-paper/references/journal_profiles/`) for specific
visual abstract requirements before starting.

### Workflow

1. **Check journal template.** Look for an official PPTX template in
   `${CLAUDE_SKILL_DIR}/references/visual_abstract_templates/{journal}.pptx`.
   If no journal-specific template exists, use `medsci_default.pptx`.
2. **Extract content from the manuscript:**
   - **Title:** Full article title
   - **Hypothesis/Question:** Derived from Key Point 1 or study objective (max 1 sentence)
   - **Methodology:** Brief flowchart or ≤3 bullets, <6 words each
   - **Visual element:** Study's own figure (ROC curve, flow diagram, representative image)
   - **Badges:** Patient cohort (N=...) | Modality/organ | Single/Multi-center
   - **Main finding:** Derived from Key Point 3 (<20 words)
   - **Citation:** Journal (year) Authors; DOI
3. **Select visual element** (priority order — no API needed for top options):
   1. Study's own figures (ROC, flow diagram, representative image) — **always preferred**
   2. Free illustration from Servier Medical Art or NIAID BioArt
      (see `${CLAUDE_SKILL_DIR}/references/medical_illustration_sources.md`)
   3. Manual drawing in PPT/Keynote/Figma
   4. AI generation via `generate_image.py --style medical` (only if GEMINI_API_KEY set)
4. **Generate using the script:**
   ```bash
   python ${CLAUDE_SKILL_DIR}/scripts/generate_visual_abstract.py \
     --template european_radiology \
     --title "Article Title" \
     --hypothesis "Research question" \
     --methods "Method 1|Method 2|Method 3" \
     --finding "Main finding statement" \
     --citation "Eur Radiol (2026) Author A et al; DOI:..." \
     --visual figures/fig1_roc_curve.png \
     --badges "N=450|CT chest|Multi-center" \
     --output figures/visual_abstract.pptx
   ```
5. **Review with user.** Open the PPTX to verify layout and content. Iterate.
6. **Export.** PPTX is the primary deliverable. For PNG: open in PowerPoint/Keynote → export,
   or use LibreOffice CLI (`soffice --headless --convert-to png`).

### Design Principles

- One page, landscape (16:9) or per journal template specification
- Three sections: Study question → Key method → Main result
- Use the study's actual figures rather than generic graphics
- Minimize text — let visuals carry the message
- Every visual element must serve a purpose (no decorative clip-art)

### Available Templates

| Template | File | Use When |
|----------|------|----------|
| European Radiology | `european_radiology.pptx` | Submitting to Eur Radiol |
| MedSci Default | `medsci_default.pptx` | Any journal without official template |

To add a new journal template: see `${CLAUDE_SKILL_DIR}/references/visual_abstract_templates/template_guide.md`.

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
   style_path = os.path.join(os.environ.get('CLAUDE_SKILL_DIR', '.'), '../analyze-stats/references/style/figure_style.mplstyle')
   if os.path.exists(style_path):
       plt.style.use(style_path)
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

style_path = os.path.join(os.environ.get('CLAUDE_SKILL_DIR', '.'), '../analyze-stats/references/style/figure_style.mplstyle')
if os.path.exists(style_path):
    plt.style.use(style_path)

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

### Step 6: Design QC Checklist

Before delivering the final figure, verify all items:

- [ ] **Font**: Sans-serif (Arial/Helvetica), minimum 7pt, axis labels ≥ 9pt
- [ ] **Color**: Wong/Okabe-Ito colorblind-safe palette used
- [ ] **Colorblind test**: Would the figure work for deuteranopia? (no red-green only distinctions)
- [ ] **Grayscale test**: Information preserved when printed in black & white
- [ ] **Alignment**: All elements on a consistent grid; panels aligned
- [ ] **Vector output**: PDF/SVG saved (not just PNG)
- [ ] **Resolution**: ≥ 300 DPI for raster elements, ≥ 600 DPI for line art
- [ ] **Journal specs**: Dimensions, font, and format match target journal requirements
- [ ] **No chartjunk**: No 3D effects, unnecessary gridlines, gradient fills, or decorative elements
- [ ] **Caption**: Drafted with key finding, abbreviations, statistical details, and sample size

---

## Study-Type Figure Sets

When the study type is known (from `/write-paper` Phase 0 or user specification), auto-detect and generate the complete required figure set without asking for each figure individually.

| Study Type (Guideline) | Required Figures |
|---|---|
| Diagnostic accuracy (STARD) | STARD flow diagram, ROC curve, confusion matrix, calibration plot |
| AI validation (TRIPOD+AI / CLAIM) | Flow diagram, ROC curve, confusion matrix, calibration plot, feature importance or SHAP, Grad-CAM (if imaging) |
| Meta-analysis (PRISMA) | PRISMA flow diagram, forest plot, funnel plot |
| DTA meta-analysis (PRISMA-DTA) | PRISMA flow diagram, paired forest plot (Se + Sp), SROC curve, Deeks funnel plot |
| Observational cohort (STROBE) | Flow diagram, Kaplan-Meier curves (if survival endpoint) |
| RCT (CONSORT) | CONSORT flow diagram, primary endpoint figure |

After generating all figures, print a manifest:
- List every output file with its path and one-line description
- Save the manifest to `figures/_figure_manifest.md`

**Flow diagram limitation:** STARD/CONSORT/PRISMA flow diagrams require D2, Mermaid, or manual tools. If these are unavailable, generate a text-based flow diagram in markdown and note that a graphical version should be created separately.

---

## Tool Selection Guide

Choose the right tool for each figure type. Using matplotlib for flow diagrams leads to
hard-coded coordinates that break when text changes — use auto-layout tools instead.

### Data Visualization → matplotlib/seaborn (this skill)

Best for figures where data drives the layout. This skill handles these directly:

| Type | Use Case | Key Library |
|------|----------|-------------|
| ROC Curve | Diagnostic accuracy | matplotlib, sklearn |
| Forest Plot | Meta-analysis | matplotlib |
| Calibration Plot | Prediction model | matplotlib |
| KM Curve | Survival analysis | lifelines, matplotlib |
| Bland-Altman | Agreement | matplotlib |
| Confusion Matrix | Classification | seaborn |
| Box/Violin Plot | Group comparison | seaborn |
| Bar Chart | Categorical comparison | matplotlib |
| Heatmap | Correlation/agreement | seaborn |

### Flow Diagrams → Dedicated Tools (NOT matplotlib)

Flow diagrams require auto-layout engines. Do NOT use matplotlib patches with manual coordinates
— this causes the "absolute coordinate hell" problem where changing one box breaks all
downstream positions.

| Type | Recommended Tool | Why |
|------|-----------------|-----|
| PRISMA Flow | **PRISMA 2020 Shiny App** (estech.shinyapps.io/prisma_flowdiagram/) | Enter numbers → auto-generate compliant diagram |
| CONSORT Diagram | **CONSORT2025 Shiny/R App** | Auto-generates CONSORT 2025 compliant flow |
| STARD Diagram | **D2** (`d2 --layout elk`) → SVG → Figma polish | Auto-layout with customizable styling |
| Pipeline Diagram | **D2** → SVG → optional Figma polish | Code-based + auto-layout + version control |

**D2 workflow for flow diagrams:**
```bash
# Install: brew install d2
# Render: d2 --layout elk --theme 0 diagram.d2 output.svg
# Then open SVG in Figma for final polish (grid alignment, font swap, color adjustment)
```

### Visual / Graphical Abstracts → python-pptx Template Generator

| Type | Recommended Tool |
|------|-----------------|
| Visual Abstract (any journal) | `generate_visual_abstract.py` with PPTX template |
| Visual element illustration | Study's own figures (preferred), or free libraries (Servier/NIAID) |
| Medical Illustration | See `${CLAUDE_SKILL_DIR}/references/medical_illustration_sources.md` |

See the Visual Abstract section above for the full workflow.

### Hybrid Workflow (recommended for publication)

```
Data plots: matplotlib → PDF (this skill)
Flow diagrams: D2 → SVG → Figma → PDF
Final assembly: Figma or Inkscape (multi-panel)
```

---

## Supported Figure Types (matplotlib/seaborn)

| Type | Use Case | Key Library | Output |
|------|----------|-------------|--------|
| ROC Curve | Diagnostic accuracy | matplotlib, sklearn | Single/multi-model ROC with AUC |
| Forest Plot | Meta-analysis | matplotlib | Effect sizes with CIs, diamond summary |
| Calibration Plot | Prediction model | matplotlib | Observed vs predicted with Hosmer-Lemeshow |
| KM Curve | Survival analysis | lifelines, matplotlib | With risk table, log-rank p |
| Bland-Altman | Agreement | matplotlib | With mean diff, +/-1.96 SD limits |
| Confusion Matrix | Classification | seaborn | Heatmap with percentages |
| Box/Violin Plot | Group comparison | seaborn | With individual data points |
| Pipeline Diagram | Methods figure | D2 (preferred) or matplotlib | Processing/workflow steps |
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

**Preferred approach: Use dedicated tools (see Tool Selection Guide above).**

If matplotlib is required (e.g., for consistency with other panels), follow these rules:
- Use rectangular boxes with rounded corners for stages.
- Arrows connect stages vertically; side boxes for exclusions.
- Consistent box widths, centered text.
- Numbers must be included in each box (e.g., "Assessed for eligibility (n = 450)").
- Follow the official template layout from each guideline.
- **Use relative positioning** — never hard-code absolute y-coordinates. Calculate each box
  position from the previous box's bottom edge plus a consistent gap constant.
- **Define gap constants** at the top of the script (e.g., `GAP_SMALL = 1.5`, `GAP_BRANCH = 2.2`).
- **Avoid magic number padding** in arrow endpoints — use named constants.

**D2 approach (recommended):**
```bash
d2 --layout elk --theme 0 flow.d2 output.svg
# Then: open SVG in Figma → grid-snap → font swap → export PDF
```

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

## AI Image Generation (Optional)

AI illustration is a **supplementary option**, not a requirement. Visual abstracts and figures
can be completed without any API key using study figures and free illustration libraries.

If `GEMINI_API_KEY` is set, the `generate_image.py` script can generate illustrations:
```bash
python ${CLAUDE_SKILL_DIR}/scripts/generate_image.py \
  "Clean medical illustration of a CT-guided lung biopsy procedure, \
   flat vector style, white background, no text" \
  --output output.png --aspect 16:9
```

Use for: procedural schematics, anatomical illustrations, pipeline diagrams.
Always review AI output against the AI-Generated Figure Warning section above.

If `GEMINI_API_KEY` is not set, guide the user to free illustration resources:
see `${CLAUDE_SKILL_DIR}/references/medical_illustration_sources.md`.

## Language

- Code and figure text: English
- Communication with user: Match user's preferred language
- Medical terms: English only
