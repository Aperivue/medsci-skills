---
name: make-figures
description: Use when a paper needs publication-ready figures or a visual abstract. Makes ROC, forest, calibration, Kaplan-Meier and Bland-Altman plots, CONSORT/STARD/PRISMA flow diagrams, confusion matrices, pipeline diagrams and journal visual abstracts, checking the journal's AI-image policy first.
metadata:
  triggers: "figure, plot, graph, diagram, ROC curve, forest plot, flow diagram, CONSORT diagram, PRISMA flow, visualization, chart, visual abstract, graphical abstract, key message, figure design, figure planning, effective figure, cognitive load"
---

# Make-Figures Skill

## Data Privacy Check

Before reading any data file, check whether it might contain Protected Health Information (PHI):

1. If `*_deidentified.*` files exist in the working directory, use those preferentially.
2. If only raw CSV/Excel files exist (no `*_deidentified.*` counterpart), ask the user, in their
   language, whether the data contains patient identifiers (names, national ID / RRN, contact
   details, etc.) and, if so, to de-identify it first with the `/deidentify` skill.
3. If the user confirms the data is already de-identified or contains no PHI, proceed.

## Reference Files

- **Figure specifications**: `${CLAUDE_SKILL_DIR}/references/figure_specs.md` — read it before
  generating any figure (journal dimensions, DPI, file formats, palettes, font sizes, panel
  layouts, caption format).
- **Figure style**: `${CLAUDE_SKILL_DIR}/../analyze-stats/references/style/figure_style.mplstyle`

---

## Journal AI-Image Policies (CRITICAL — check BEFORE generation)

| Journal family | Policy on AI-generated images | Disclosure required |
|---|---|---|
| **JACC family (incl. JACC: Asia, JACC Imaging, JACC EP, JACC BTS)** | **Prohibited without prior Editor-in-Chief permission** ([JACC pathway, PMC10167500](https://pmc.ncbi.nlm.nih.gov/articles/PMC10167500/)) | Cover-letter pre-submission inquiry + ICMJE-style declaration |
| NEJM | AI image generation prohibited | N/A |
| Radiology / Radiology AI | Allowed with disclosure | Manuscript disclosure block |
| Nature family | Allowed with disclosure + license check | Methods + figure legend |
| Lancet family | Disclosure required, generation discouraged | Manuscript disclosure |
| Default (target unknown) | Treat as prohibited until confirmed | N/A |

**Hard rule**: For JACC, NEJM, or any "unknown" target journal, **never** use Gemini / DALL-E / Midjourney / Stable Diffusion / Nano Banana to create images that will appear in figures, Central Illustrations, or graphical abstracts. AI text-editing of the manuscript prose remains acceptable subject to standard disclosure.

### Default workflow when AI images are not allowed

1. **SMART Servier Medical Art** — https://smart.servier.com/, CC BY 4.0, free, 3,000+ vector medical icons (anatomy, organs, ethnicity-specific human figures, drugs, devices). Commercial / journal use allowed. **Required attribution** (1 line in figure legend OR methods):
   > Anatomical icons modified from SMART Servier Medical Art (CC BY 4.0).
2. **NIAID BioArt** (https://bioart.niaid.nih.gov) — public domain (US Govt), microbiology / immunology / lab-tech focus.
3. **BioRender** (https://www.biorender.com) — institutional license usually required; use the exported "Publication-ready" PNG/TIFF and cite per BioRender publication policy.
4. For "diseased" variants not directly available (e.g., calcified vessel from a clean vessel): reuse the healthy asset and overlay disease markers via matplotlib `scatter` / `Circle` / `PathPatch`. Keeps the entire pipeline non-AI and reproducible.

Even when AI images are allowed, experienced reviewers recognise AI-generated illustrations (small decorative icons that add no information, overly uniform layouts, generic clip-art style). For high-impact submissions, prefer Servier / BioArt / BioRender + matplotlib overlays over AI.

### Asset directory convention

```
manuscript/figures/_assets_servier/      # CC BY 4.0 source PNGs
manuscript/figures/_assets_servier/CITATION.md   # source URL + download date per asset
manuscript/figures/_assets_data/         # data-driven raster (R / matplotlib heat maps, KM, etc.)
manuscript/figures/_legacy/              # archived prior versions
```

Composition scripts should load only from `_assets_servier/` and `_assets_data/`. If a script imports from `_assets_ai/`, treat it as a policy violation for JACC/NEJM/unknown targets.

### AI Image Generation (Optional)

AI illustration is a supplementary option: every figure and visual abstract can be completed without an API key. If `GEMINI_API_KEY` is set, `generate_image.py` can generate illustrations (procedural schematics, anatomical illustrations), subject to the policy table and hard rule above:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/generate_image.py \
  "Clean medical illustration of a CT-guided lung biopsy procedure, \
   flat vector style, white background, no text" \
  --output output.png --aspect 16:9
```

If `GEMINI_API_KEY` is not set, use `${CLAUDE_SKILL_DIR}/references/medical_illustration_sources.md`.

---

## Visual Abstract / Graphical Abstract

European Radiology made graphical abstracts mandatory for all Original Articles from first revision
(Jan 2025); other journals encourage or accept them (status list in `template_guide.md`). Check the
target journal profile (`write-paper/references/journal_profiles/`) for its visual abstract
requirements before starting.

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
3. **Select visual element** (priority order):
   1. Study's own figures (ROC, flow diagram, representative image) — **always preferred**
   2. Free illustration from Servier Medical Art or NIAID BioArt
      (see `${CLAUDE_SKILL_DIR}/references/medical_illustration_sources.md`)
   3. Manual drawing in PPT/Keynote/Figma
   4. AI generation via `generate_image.py --style medical` (only if GEMINI_API_KEY set)
4. **Generate using the script:**
   ```bash
   python ${CLAUDE_SKILL_DIR}/scripts/generate_visual_abstract.py \
     --template medsci_default \
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

Design: one page, landscape (16:9) or per the journal template; three sections (study question →
key method → main result); the study's actual figures rather than generic graphics; minimal text;
no decorative clip-art.

### Available Templates

| Template | File | Use When |
|----------|------|----------|
| MedSci Default | `medsci_default.pptx` | Any journal without an official template |
| JACC Central Illustration | `jacc_central_illustration.pptx` | JACC family journals (use `--type central-illustration`) |

**Using a journal's own template.** We do not redistribute journals' templates (e.g., European
Radiology's `EURA-GA-Jan2025.pptx`): download it and pass its absolute path:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/generate_visual_abstract.py \
  --template /absolute/path/to/EURA-GA-Jan2025.pptx  ...
```

`--template` takes an absolute path to any `.pptx`. The script locates the fields by their text
content rather than by shape name, so a journal's own template works unmodified. If the path does
not exist it falls back to `medsci_default.pptx`.

To add a new journal template: see `${CLAUDE_SKILL_DIR}/references/visual_abstract_templates/template_guide.md`.

---

## Central Illustration vs Visual Abstract

JACC family journals (JACC, JACC: Asia, JACC: Cardiovascular Imaging, JACC: Heart Failure, JACC: CardioOncology, JACC: Clinical Electrophysiology, JACC: Basic to Translational Science) require a Central Illustration (CI) with every Original Article. A CI is **not** a Visual Abstract: it conveys one key finding and contains no methods. Before making one, read `${CLAUDE_SKILL_DIR}/references/jacc_central_illustration_principles.md` (CI vs VA table, the five Fuster-Mann rules, layout and validation thresholds).

### CI mode invocation

```bash
python ${CLAUDE_SKILL_DIR}/scripts/generate_visual_abstract.py \
  --type central-illustration \
  --visual figures/central_illustration_v2.png \
  --citation "FirstAuthor Last et al. Journal Name 2026; vol(issue):pages." \
  --output submission/jacc_asia/central_illustration.pptx \
  --ci-zones 3 --ci-label-words 22 --ci-numerical-points 2 \
  --ci-raw-text "warranty drops to 3 years in age 45+ with cardiometabolic burden; MASLD HR 1.77"
```

CI mode validates before rendering and rejects (exit 2) if any of: zones > 3, label words > 30, numerical points > 4, or methodology terms (cohort flow / inclusion criteria / exclusion criteria / study design / enrollment / randomized / sample size / CONSORT / PRISMA / STARD) appear in `--ci-raw-text`. Override individual rules with `--ci-allow {zones|words|numerical|methods}` only when you have a defensible reason. Submit only the content figure + citation: JACC editorial applies the red border and blue "CENTRAL ILLUSTRATION:" header after acceptance.

---

## Workflow

Any reference in a caption, legend or illustration needs a DOI or PMID confirmed via `/search-lit`;
mark one you cannot confirm `[UNVERIFIED - NEEDS MANUAL CHECK]`. Mark an unconfirmed clinical
definition, criterion or guideline claim `[VERIFY]` and ask — the submission gates block on both.

### Step 1: Specify

**Before specifying figure type, read `${CLAUDE_SKILL_DIR}/references/design_principles.md`** —
identify (1) the one-sentence key message, (2) audience and reading-time budget, and
(3) whether a figure is the right vehicle (vs a small table or in-line text). Skip only when the
figure is mandated by a reporting guideline (e.g., PRISMA / CONSORT flow), and even then apply the
cognitive-load checklist.

**For reporting-guideline figures**, also load
`${CLAUDE_SKILL_DIR}/references/reporting_guideline_figure_map.md` — which guideline mandates which
figures and whether this skill ships an official template (✅), generic flow only (⚠️), or needs
manual production (❌). Critical for AI-extension guidelines (CONSORT-AI, STARD-AI, TRIPOD+AI,
CLAIM 2024, DECIDE-AI).

**For medical AI / engineering pipeline figures** (DICOM workflow, annotation pipeline, federated
learning topology, model architecture), also load
`${CLAUDE_SKILL_DIR}/references/pipeline_concepts_medical_ai.md` — canonical layouts, required
annotations, and tool selection per type.

**Optional flags:**
- `--study-type <type>`: One of: `diagnostic-accuracy`, `ai-validation`, `meta-analysis`, `dta-meta-analysis`, `observational-cohort`, `rct`, `case-report`. When set, auto-generate the full figure set from the Study-Type Figure Sets table below without prompting for individual figure types.
- `--data-dir <path>`: Directory containing analysis outputs (CSVs, `_analysis_outputs.md`). Default: current working directory.

Ask the user for (infer what the context already gives, and confirm before proceeding):
1. **Figure type** — skipped when `--study-type` is provided
2. **Data source** (file path, DataFrame, or manual values)
3. **Target journal** (for dimension/font requirements)
4. **Panel layout** (single panel, multi-panel, or let you decide)
5. **Any special requests** (annotations, highlights, reference lines)
6. **Study type** (if not passed via `--study-type`): determines the required figure set

### Step 2: Configure

1. Load the figure style file (skeleton below).
2. Look up journal-specific dimensions in `${CLAUDE_SKILL_DIR}/references/figure_specs.md`.
3. Set the colorblind-safe palette (Wong palette by default).
4. Set font sizes per element type (title, axis label, tick label, legend, annotation) from `figure_specs.md`.

### Step 3: Generate

Use Python (matplotlib/seaborn, with specialized libraries as needed). Compose each data plot from
its anatomy model in `${CLAUDE_SKILL_DIR}/references/exemplar_plots/` (index in its `README.md`);
for box/violin, bar and heatmap figures follow the per-type conventions in `figure_specs.md`. Flow
diagrams never use matplotlib — see the Tool Selection Guide.

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

Never fabricate data points. If sample data is needed for a template demo, label it "example data".
When a figure is produced by a data-driven `.py`/`.R` script (ROC, forest, KM, calibration, heat
maps), lint that script before finalizing with the `/analyze-stats` code-quality gate
(`check_generated_code.py {script} --strict`): it catches a missing plotting seed for any
bootstrapped CI band, a hardcoded absolute data path, or a hand-typed data literal that should have
been read from the analysis CSV.

### Step 4: Review

Present the figure to the user (layout, labels and annotations, colors/sizing/emphasis) and iterate
until the user approves.

### Step 4b: Critic Loop (self-critique before final export)

Before Step 5 Export, run two stages — deterministic quantitative checks, then your own
qualitative review — to decide whether to re-render or hand off to the user.

**Stage 1: Quantitative checks (`critic_figure.py`)**

```bash
python ${CLAUDE_SKILL_DIR}/scripts/critic_figure.py \
    figures/fig1_stard.png \
    --type stard \
    --spec-min-dpi 600 \
    --spec-width-in 7.0 \
    --source-text figures/fig1_stard.txt \
    --out figures/fig1_stard.critique.json
```

`--source-text` is optional (expected strings for OCR coverage). The JSON report covers DPI and
physical width vs. the journal spec, the dominant-color breakdown and out-of-Wong-palette fraction,
and OCR word count, minimum text height, and source-word coverage.

**Stage 2: Qualitative review**

1. Use the Read tool to load the generated PNG.
2. Read the corresponding rubric file (sections A–G in each):
   - Flow diagrams: `${CLAUDE_SKILL_DIR}/references/critic_rubrics/flow_diagram.md`
   - Data plots: `${CLAUDE_SKILL_DIR}/references/critic_rubrics/data_plot.md`
   - For PRISMA / CONSORT / STARD / STROBE, also read
     `${CLAUDE_SKILL_DIR}/references/flow_diagram_lessons.md` (official-template fidelity, PDF
     export via VML fallback, docx XML escape, sequential placeholder mapping, frozen-version sync
     with the manuscript).
   - For AI-extension guidelines or pipeline figures, also check against the
     `reporting_guideline_figure_map.md` row / `pipeline_concepts_medical_ai.md` loaded in Step 1.
3. Read the `_why.md` design notes in `${CLAUDE_SKILL_DIR}/references/exemplar_diagrams/{type}/`
   — hierarchy, whitespace, typography, emphasis, colour. **They are the anchors.** Where a rendered
   exemplar is bundled (`template_output*.png`), Read 1–2 of those too. Figures cropped from
   published papers are not shipped (see that directory's README); a user's own local exemplars can
   be used instead. For a non-flow data plot, read the matching anatomy model in
   `${CLAUDE_SKILL_DIR}/references/exemplar_plots/` (e.g., `forest_plot.md`).
4. Score every rubric item as PASS / PARTIAL / FAIL with a one-line note,
   using the format at the bottom of the rubric file.
5. Emit a **"Required edits before next render"** list of concrete
   source-code changes (node/label renames, count corrections, matplotlib
   parameter tweaks).

**Refinement loop**

- If all items are PASS → proceed to Step 5 Export with `critic_pass: yes`.
- If any item is FAIL → apply the required edits to the source (flow-diagram config/R script or
  matplotlib script), re-render, and re-run Stage 1 + Stage 2. Default
  maximum is **T=2 rounds**; the user may request up to T=3.
- If after the max rounds some items remain PARTIAL, proceed with
  `critic_pass: partial` and record the residual items in the manifest's
  `critic_notes` field.

Record the final state in `_figure_manifest.md` (see Study-Type Figure Sets) so downstream steps
(`/write-paper` Phase 2 embedding and Phase 7 DOCX build) and future critic passes can see the
history.

### Step 5: Export

Save final outputs to `analysis/figures/` (`analysis/figures/*.pdf`, `analysis/figures/*.png`):
- **PDF** (vector format, preferred for journal submission)
- **PNG** (300 DPI raster, for review and presentation)
- **TIFF** (if the journal requires it, 300 DPI LZW compression) — produce it with
  `export_portal_tiff.py`, not a raw `magick ... output.tiff`: that keeps the alpha channel
  (transparent regions print **black** on many production pipelines) and stays uncompressed (a
  600-dpi RGBA TIFF blows past a portal's 25 MB cap). The script white-flattens RGBA→RGB,
  LZW-compresses, and **verifies the result is pixel-identical** to that flatten. Use it when a
  portal accepts only `.tiff`/`.jpeg`/`.eps` (Springer Nature SNAPP) or caps figure size (JACC: Asia):
  ```bash
  python3 scripts/export_portal_tiff.py --in figure.png --out figure.tiff --max-mb 25
  # exit 1 if still over the cap
  ```

Name files descriptively: `fig1_roc_curve.pdf`, `fig2_consort_flow.pdf`, etc.

**For PPTX outputs (visual abstract, central illustration, or any deck the figure
will live in)**: run the Mac-compatibility validator before delivery. PowerPoint
Mac silently drops TIFF, renders `<a:sp3d>` 3-D bevels as red outlines that PDF
export does not show, and refuses to open files whose `app.xml` slide count
disagrees with the actual slide XML files.

```bash
python ${CLAUDE_SKILL_DIR}/scripts/validate_pptx_mac_compat.py \
    figures/visual_abstract.pptx \
    --json figures/visual_abstract.mac_compat.json \
    --strict
```

Exit code 1 means at least one FAIL — fix per the `fix:` field in the JSON
report and re-render the PPTX before delivery. Exit code 0 with WARN is
acceptable. Skip this step when the figure is PNG/PDF only (no PPTX).

### Step 6: Design QC Checklist

Before delivering the final figure, verify all items:

- [ ] **Font**: Sans-serif (Arial/Helvetica), minimum 7pt, axis labels ≥ 9pt
- [ ] **Color**: Wong/Okabe-Ito colorblind-safe palette used
- [ ] **Colorblind test**: Works for deuteranopia (no red-green only distinctions)
- [ ] **Grayscale test**: Information preserved when printed in black & white
- [ ] **Alignment**: All elements on a consistent grid; panels aligned
- [ ] **Vector output**: PDF/SVG saved (not just PNG)
- [ ] **Resolution**: ≥ 300 DPI for raster elements, ≥ 600 DPI for line art
- [ ] **Journal specs**: Dimensions, font, and format match the target journal (if a figure exceeds a limit, resize it and report the adjustment)
- [ ] **No chartjunk**: No 3D effects, unnecessary gridlines, gradient fills, or decorative elements
- [ ] **Caption**: Drafted per `figure_specs.md` (Caption Writing Guidelines) with key finding, abbreviations, statistical details, and sample size

---

## Study-Type Figure Sets

When the study type is known (from `/write-paper` Phase 0 or user specification), generate the complete required figure set without asking for each figure individually.

| Study Type (Guideline) | Required Figures |
|---|---|
| Diagnostic accuracy (STARD) | STARD flow diagram, ROC curve, confusion matrix, calibration plot |
| AI validation (TRIPOD+AI / CLAIM) | Flow diagram, ROC curve, confusion matrix, calibration plot, feature importance or SHAP, Grad-CAM (if imaging) |
| Meta-analysis (PRISMA) | PRISMA flow diagram, forest plot, funnel plot |
| DTA meta-analysis (PRISMA-DTA) | PRISMA flow diagram, paired forest plot (Se + Sp), SROC curve, Deeks funnel plot |
| Observational cohort (STROBE) | Flow diagram, Kaplan-Meier curves (if survival endpoint) |
| RCT (CONSORT) | CONSORT flow diagram, primary endpoint figure |
| Case report / series (CARE) | Clinical timeline figure (`exemplar_plots/clinical_timeline.md`), annotated multimodality imaging panel when visually load-bearing (`exemplar_plots/imaging_panel.md`); for a series, an all-cases summary table |
| Oncology treatment study (CONSORT RCT or single-arm phase II; REMARK for biomarker subsets) | CONSORT or cohort flow diagram, Kaplan-Meier PFS/OS with number-at-risk table (`exemplar_plots/km_curve.md`), waterfall plot of best response (`exemplar_plots/waterfall_plot.md`), swimmer plot for durability (`exemplar_plots/swimmer_plot.md`), spider plot when response kinetics matter (`exemplar_plots/spider_plot.md`), cumulative incidence instead of 1 - KM when competing risks are present (`exemplar_plots/cumulative_incidence.md`) |

**The manifest is mandatory.** After generating all figures, write
`analysis/figures/_figure_manifest.md` — one row per figure (`Figure | Path | Type | Tool | Critic |
Rounds | Description`) plus a `## Critic notes` section recording any residual PARTIAL items and
why they were accepted. It is consumed by `/write-paper` Phase 2 (figure embedding) and Phase 7
(DOCX build); verify it exists and is non-empty before finishing. Read
`${CLAUDE_SKILL_DIR}/references/figure_manifest.md` when writing it (format and field definitions).

## Tool Selection Guide

```
Data plots:    matplotlib/seaborn → PDF + PNG (this skill)
Flow diagrams: generate_flow_diagram.R (DiagrammeR + rsvg) → PDF + 300/600 dpi PNG
Final assembly: pandoc or python-docx (auto-embedded in DOCX)
```

### Flow Diagrams → Dedicated Tools (NOT matplotlib)

STARD / CONSORT / PRISMA / STROBE flow diagrams **MUST** use the standardized R pipeline
`scripts/generate_flow_diagram.R` (DiagrammeR + Graphviz dot + rsvg) — the single canonical tool
for all four. Do **NOT** use matplotlib `FancyBboxPatch` (manual coordinates break when text
changes, and patches distort when embedded in DOCX). Do **NOT** use D2 for new flow diagrams (weak
font control, overlap needs manual post-processing); D2 is a legacy fallback only when R is
unavailable.

| Type | Recommended Tool | Why |
|------|-----------------|-----|
| STROBE (cohort / cross-sectional) | **`scripts/generate_flow_diagram.R --type strobe`** | Single canonical tool; auto-layout; vector PDF + 300/600 dpi PNG |
| CONSORT (RCT) | **`scripts/generate_flow_diagram.R --type consort`** | Same pipeline; monochrome Arial default |
| PRISMA 2020 (SR/MA) | **`scripts/generate_flow_diagram.R --type prisma`** | Faithfully implements PRISMA 2020 structure; avoids PRISMA2020 R package's webshot-based raster PDF issue |
| STARD (DTA) | **`scripts/generate_flow_diagram.R --type stard`** | Same pipeline; supports 2x2 reference-standard split |
| Pipeline Diagram | **D2** (legacy) | Until pipeline-diagram support is added to the R script |

YAML config → `Rscript scripts/generate_flow_diagram.R --type <t> --config <yaml> --out <prefix>` →
PDF + 300/600 dpi PNG. Templates in `references/exemplar_diagrams/{strobe,consort,prisma,stard}/template_input.yaml`.
Read `${CLAUDE_SKILL_DIR}/references/flow_diagram_recipe.md` when generating a flow diagram (YAML
schema, fixed style, per-project `create_figure1.R` pattern, D2 fallback); a ROC curve or forest
plot needs none of it.

Every box label contains its count (e.g., `"Assessed for eligibility\n(n = 450)"`). Numbers in
labels must be CSV-derived — author the YAML from an R/Python script that reads the upstream data —
or hand-written only when the value lives in a commit-tracked data artifact (cite the source file
in a comment).

**Caption ↔ flow-SSOT reconciliation (before Step 5 Export).** The flow-diagram config is the
single source of truth for participant counts; a hand-written Figure 1 caption drifts from it when
the cohort is re-locked but the caption is not ("caption says n = 1,284 analytic, diagram box says
n = 998"). Re-derive the caption counts from the flow config and reconcile:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/derive_figure_legend_counts.py \
  --flow-config figures/figure1_strobe_graphviz.yaml \
  --manuscript manuscript/index.qmd \
  --out qc/figure_legend_counts.json --strict
```

Any `n = N` in the caption that is not a box count in the flow config is a `MISMATCH` (stale
caption) — update the caption from the config, never the reverse. The reconciler is stdlib-only and
parses the config as text, so it works regardless of the flow tool.

### Official Reporting Guideline Templates → `templates/official/`

When a journal requires the canonical, statement-issued template (rather than the auto-laid-out R
version), use the bundled official files in
`templates/official/{prisma2020,consort2010,stard2015,spirit2013}/`.

| Guideline | What ships | When to use |
|-----------|-----------|-------------|
| PRISMA 2020 | Locally built `.pptx` (4 variants) + `fill_prisma_template.py` | Reviewer asks for the official PRISMA 2020 layout, or you want editable PowerPoint instead of an R-rendered PDF. |
| STROBE (cohort) | Parametric `.pptx` builder `build_strobe_template.py` (YAML config) | Cohort/case-control Figure 1 when co-authors want PowerPoint they can hand-edit. Optional left-side phase column: omit `stages:` for the plain STROBE convention; include it for the PRISMA-style Identification/Screening/Inclusion/Analysis column. Pair with `generate_flow_diagram.R --type strobe` for the vector PDF/TIFF submission file. |
| CONSORT 2025 | Official `.docx` flow diagram + checklist | RCT submissions to journals that mandate the consort-spirit.org template. |
| STARD 2015 | Official `.pdf` flow diagram + `.docx` checklist | Diagnostic accuracy studies; flow diagram is fixed PDF, checklist is editable. |
| SPIRIT 2025 | Official `.docx` participant timeline + checklist | Trial protocols. |

Refresh / fill workflow:

```bash
# Refresh from canonical sources (CC-BY 4.0 / public-statement licenses)
bash ${CLAUDE_SKILL_DIR}/scripts/fetch_official_templates.sh

# Build PRISMA 2020 .pptx (one-time; site blocks programmatic .docx fetch)
python3 ${CLAUDE_SKILL_DIR}/scripts/build_prisma2020_template.py \
    --variant new \
    --out ${CLAUDE_SKILL_DIR}/templates/official/prisma2020/PRISMA_2020_flow_new_v1.pptx

# Fill counts — positional 10-tuple matching most SR/MA workflows:
#   n_db, n_dup, n_screened, n_screen_excluded,
#   n_sought, n_assessed, n_excl_r1, n_excl_r2, n_excl_r3, n_studies
python3 ${CLAUDE_SKILL_DIR}/scripts/fill_prisma_template.py \
    --template ${CLAUDE_SKILL_DIR}/templates/official/prisma2020/PRISMA_2020_flow_new_v1.pptx \
    --counts "315,122,186,7,111,204,102,84,3,15" \
    --out fig1_prisma_filled.pptx

# Or use full JSON mapping for studies with non-standard PRISMA splits
python3 ${CLAUDE_SKILL_DIR}/scripts/fill_prisma_template.py \
    --template ${CLAUDE_SKILL_DIR}/templates/official/prisma2020/PRISMA_2020_flow_new_v1.pptx \
    --counts-file my_counts.json \
    --out fig1_prisma_filled.pptx

# STROBE — parametric single-script builder (cohort study; spine structure varies per study).
# YAML schema: stages, spine (id/stage/text), exclusions (after/text). Consecutive same-stage
# rows share one phase label automatically.
python3 ${CLAUDE_SKILL_DIR}/scripts/build_strobe_template.py \
    --config figures/figure1_strobe.yaml \
    --out    figures/figure1_strobe.pptx
```

The STROBE builder checks that the exclusion cascade closes: for every link that declares an
exclusion, the spine box count minus the exclusions after it must equal the next spine box
(`A - Σ(exclusions after A) == B`). It warns loudly on any imbalance and, with `--strict-cascade`,
refuses to build — catching figure arithmetic drift (a dropped exclusion leaving the figure short of
the analytic N) that text and prose gates miss. Run `scripts/_strobe_cascade.py --config
figure1_strobe.yaml --strict` to check a config without rebuilding the diagram.

For STROBE the canonical KJR/Radiology/BMJ submission flow is:

1. Render the vector submission file via the auto-fitting Graphviz path:
   `Rscript ${CLAUDE_SKILL_DIR}/scripts/generate_flow_diagram.R --type strobe --config figures/figure1_strobe_graphviz.yaml --out figures/figure1`
2. Build the editable PowerPoint companion via `build_strobe_template.py` so co-authors and senior reviewers can adjust prose/positioning before sign-off.
3. Re-export the final PPTX to PDF/TIFF only after co-author edits are integrated.

See `templates/official/NOTES.md` for licenses, attribution, and refresh notes.

---

## Style Rules

Palettes, font sizes, panel layouts, and caption format are in `figure_specs.md`. In addition:

- All figure text (labels, legends, annotations) is in English; medical terminology is always English.
- Never use red-green only distinctions. Use line style (solid, dashed, dotted) in addition to color
  for line plots, and marker shape in addition to color for scatter plots.
- Panel labels: uppercase bold letter (12 pt), top-left of each panel.
- No figure titles in the plot itself (the title goes in the caption).
- Align multi-panel figures on a grid, with consistent axis ranges across comparable panels.
- Significance stars (* p<0.05, ** p<0.01, *** p<0.001) go above comparison brackets; report the
  exact p-value in the figure legend or caption, not in the plot.
- For AUC, correlation, or agreement: display in the legend with 95% CI.

## Skill Interactions

| When | Call | Purpose |
|------|------|---------|
| Need statistical values for plot | `/analyze-stats` | Get computed values (AUC, CI, p-values) |
| Flow diagram for manuscript | `/write-paper` Phase 2 | Coordinate with Tables & Figures plan |
| Caption review | `/write-paper` Phase 7 | Final polish pass |
