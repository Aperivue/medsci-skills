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

## Credits

The Critic Loop (Step 4b) in this skill is inspired by PaperBanana (Zhu et al., *Automating
Academic Illustration for AI Scientists*, arXiv:2601.23265, 2025) and by prior self-refinement
research — Self-Refine (Madaan et al., 2023), Reflexion (Shinn et al., 2023), and Constitutional
AI (Anthropic, 2022). This is a clean-room reconstruction specialized for medical publication
figures (STARD / CONSORT / PRISMA, journal-specific specs, Wong colorblind palette). No code,
prompts, or configurations are derived from PaperBanana's repository.

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

**Optional flags:**
- `--study-type <type>`: One of: `diagnostic-accuracy`, `ai-validation`, `meta-analysis`, `dta-meta-analysis`, `observational-cohort`, `rct`. When set, auto-generate the full figure set from the Study-Type Figure Sets table below without prompting for individual figure types.
- `--data-dir <path>`: Directory containing analysis outputs (CSVs, `_analysis_outputs.md`). Default: current working directory.

Ask the user for:
1. **Figure type** (from the supported types below) — skipped when `--study-type` is provided
2. **Data source** (file path, DataFrame, or manual values)
3. **Target journal** (for dimension/font requirements)
4. **Panel layout** (single panel, multi-panel, or let you decide)
5. **Any special requests** (annotations, highlights, reference lines)
6. **Study type** (if not passed via `--study-type`): determines the required figure set

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

### Step 4b: Critic Loop (self-critique before final export)

Before Step 5 Export, run the automated Critic Loop. This is two stages —
deterministic quantitative checks via Python, then qualitative review by
Claude itself — and the combined output tells us whether to re-render or
hand off to the user.

**Stage 1: Quantitative checks (`critic_figure.py`)**

```bash
python ${CLAUDE_SKILL_DIR}/scripts/critic_figure.py \
    figures/fig1_stard.png \
    --type stard \
    --spec-min-dpi 600 \
    --spec-width-in 7.0 \
    --source-text figures/fig1_stard.txt \   # optional: expected strings for OCR coverage
    --out figures/fig1_stard.critique.json
```

This produces a JSON report covering:
- DPI and physical width vs. journal spec
- Dominant-color breakdown and out-of-Wong-palette fraction
- OCR-detected word count, minimum text height, and (if a source-text file
  was provided) source-word coverage

**Stage 2: Qualitative review (Claude session)**

1. Use the Read tool to load the generated PNG.
2. Read the corresponding rubric file:
   - Flow diagrams: `${CLAUDE_SKILL_DIR}/references/critic_rubrics/flow_diagram.md`
   - Data plots:    `${CLAUDE_SKILL_DIR}/references/critic_rubrics/data_plot.md`
3. If exemplars exist in `${CLAUDE_SKILL_DIR}/references/exemplar_diagrams/{type}/`,
   Read 1–3 of them plus their `_why.md` notes.
4. Score every rubric item as PASS / PARTIAL / FAIL with a one-line note,
   using the format at the bottom of the rubric file.
5. Emit a **"Required edits before next render"** list of concrete
   source-code changes (D2 node renames, count corrections, matplotlib
   parameter tweaks).

**Refinement loop**

- If all items are PASS → proceed to Step 5 Export with `critic_pass: yes`.
- If any item is FAIL → apply the required edits to the source (D2 file or
  matplotlib script), re-render, and re-run Stage 1 + Stage 2. Default
  maximum is **T=2 rounds**; the user may request up to T=3.
- If after the max rounds some items remain PARTIAL, proceed with
  `critic_pass: partial` and record the residual items in the manifest's
  `critic_notes` field.

Record the final state in `_figure_manifest.md` (see the manifest format
below) so downstream steps (`/write-paper` Phase 2 embedding and Phase 7
DOCX build) and future critic passes can see the history.

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

After generating all figures, create a structured manifest file at `figures/_figure_manifest.md`:

```markdown
# Figure Manifest
Generated: {YYYY-MM-DD}
Study type: {study type or "custom"}

| Figure | Path | Type | Tool | Critic | Rounds | Description |
|--------|------|------|------|--------|--------|-------------|
| Figure 1 | figures/fig1_stard_flow.svg | flow-diagram | D2 | yes | 2 | STARD participant flow diagram |
| Figure 2 | figures/fig2_roc.pdf | roc-curve | matplotlib | yes | 1 | ROC curves for Model A vs B |
| Figure 3 | figures/fig3_calibration.pdf | calibration | matplotlib | partial | 3 | Calibration plot; legend still crowded (see notes) |

## Critic notes
- Figure 3: after 3 rounds, legend placement remains crowded at the
  double-column width. Candidate remediations documented but not applied
  to avoid reducing data-point visibility.
```

**Manifest field definitions:**
- **Path**: Relative path from project root
- **Type**: One of: `flow-diagram`, `roc-curve`, `forest-plot`, `funnel-plot`, `calibration`, `km-curve`, `bland-altman`, `confusion-matrix`, `box-violin`, `bar-chart`, `heatmap`, `pipeline`, `visual-abstract`, `sroc-curve`, `other`
- **Tool**: Tool used to generate (`matplotlib`, `D2`, `python-pptx`, `seaborn`, etc.)
- **Critic**: `yes` (all rubric items PASS) / `partial` (some PARTIAL after max rounds) / `no` (never critiqued — avoid for submission figures) / `skip` (deliberately bypassed, e.g., panel figure assembled externally)
- **Rounds**: Number of Critic Loop rounds executed (0 if skipped)
- **Description**: One-line description suitable for figure legend context

A `## Critic notes` section at the bottom of the manifest records any
residual PARTIAL items and the rationale for accepting them.

This manifest is consumed by `/write-paper` Phase 2 (figure embedding) and Phase 7 (DOCX build). It **MUST** exist after figure generation completes. Verify the file is non-empty before finishing.

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
- To add one emphasis color (e.g., Wong blue `#0072B2` for a single highlighted box), edit `scripts/generate_flow_diagram.R` — do not inline hex colors in YAML.

**Legacy D2 fallback (only when R unavailable):**

```bash
d2 --layout elk --theme 0 --pad 20 flow.d2 /tmp/raw.png --scale 2
# Resize + 85% vertical compression via Pillow; then render PDF:
d2 --layout elk --theme 0 --pad 20 flow.d2 figures/fig1_flow.pdf
```

Use `font-size: 20-24`, `stroke: black`, `fill: white`. D2 PDF is vector; D2 PNG needs the resize step to match publication density.

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
| STROBE (cohort / cross-sectional) | **`scripts/generate_flow_diagram.R --type strobe`** | Single canonical tool; auto-layout; vector PDF + 300/600 dpi PNG |
| CONSORT (RCT) | **`scripts/generate_flow_diagram.R --type consort`** | Same pipeline; monochrome Arial default |
| PRISMA 2020 (SR/MA) | **`scripts/generate_flow_diagram.R --type prisma`** | Faithfully implements PRISMA 2020 structure; avoids PRISMA2020 R package's webshot-based raster PDF issue |
| STARD (DTA) | **`scripts/generate_flow_diagram.R --type stard`** | Same pipeline; supports 2x2 reference-standard split |
| Pipeline Diagram | **D2** (legacy) | Until pipeline-diagram support is added to the R script |

**R workflow for flow diagrams:** See the "R flow diagram recipe" above in the Flow diagram generation rule. Key points: YAML config → `Rscript scripts/generate_flow_diagram.R --type <t> --config <yaml> --out <prefix>` → PDF + 300/600 dpi PNG. Templates in `references/exemplar_diagrams/{strobe,consort,prisma,stard}/template_input.yaml`.

### Visual / Graphical Abstracts → python-pptx Template Generator

| Type | Recommended Tool |
|------|-----------------|
| Visual Abstract (any journal) | `generate_visual_abstract.py` with PPTX template |
| Visual element illustration | Study's own figures (preferred), or free libraries (Servier/NIAID) |
| Medical Illustration | See `${CLAUDE_SKILL_DIR}/references/medical_illustration_sources.md` |

See the Visual Abstract section above for the full workflow.

### Hybrid Workflow (recommended for publication)

```
Data plots:    matplotlib/seaborn → PDF + PNG (this skill)
Flow diagrams: generate_flow_diagram.R (DiagrammeR + rsvg) → PDF + 300/600 dpi PNG
Final assembly: pandoc or python-docx (auto-embedded in DOCX)
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

### Flow Diagrams (STROBE / CONSORT / PRISMA / STARD)

**Single canonical tool: `scripts/generate_flow_diagram.R`** (see the R flow diagram recipe above). Do not fall back to matplotlib for flow diagrams — manual coordinates break when text changes and patches distort in DOCX. D2 remains a documented legacy fallback only when R is unavailable.

Layout invariants:
- Rectangular boxes with rounded corners for stages; notes (`shape: note`) for exclusion side-boxes.
- Vertical top-down flow by default; horizontal only when the manuscript layout demands it.
- Every box label contains the count (e.g., `"Assessed for eligibility\n(n = 450)"`).
- Numbers are CSV-derived (numerical-safety) — author the YAML from an R/Python script that reads the upstream data, or cite the source file in a comment when a literal value is unavoidable.
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

## Anti-Hallucination

- **Never fabricate references.** All citations must be verified via `/search-lit` with confirmed DOI or PMID. Mark unverified references as `[UNVERIFIED - NEEDS MANUAL CHECK]`.
- **Never invent clinical definitions, diagnostic criteria, or guideline recommendations.** If uncertain, flag with `[VERIFY]` and ask the user.
- **Never fabricate numerical results** — compliance percentages, scores, effect sizes, or sample sizes must come from actual data or analysis output.
- If a reporting guideline item, journal policy, or clinical standard is uncertain, state the uncertainty rather than guessing.
