<!-- AUTO-GENERATED from skills/make-figures/SKILL.md by scripts/gen_skill_docs.py. Do not edit by hand. -->

# make-figures

> Generate publication-ready figures and visual abstracts for medical research papers. Supports ROC curves, forest plots, CONSORT/STARD/PRISMA flow diagrams, calibration plots, Kaplan-Meier curves, Bland-Altman plots, confusion matrices, pipeline diagrams, and journal-specific visual/graphical abstracts (python-pptx template-based).

**Invoke:** `/make-figures` · **Tools:** Read, Write, Edit, Bash, Grep, Glob · **Model:** inherit

## When to use

`make-figures` activates on requests such as: figure, plot, graph, diagram, ROC curve, forest plot, flow diagram, CONSORT diagram, PRISMA flow, visualization, chart, visual abstract, graphical abstract, key message, figure design, figure planning, effective figure, cognitive load.

## Quality Card

**Purpose** — Generate publication-ready figures and visual/graphical abstracts (ROC, forest, CONSORT/STARD/PRISMA flow, KM, Bland-Altman, etc.).

**Safety boundaries**

- Figure numbers are not fabricated; flow diagrams are built from real source counts.
- Honors journal AI-image policies; no AI images for prohibited targets.

**Known limitations**

- Figure correctness depends on correct input data/counts supplied by upstream skills.
- PPTX visual abstracts need the Mac-compatibility check before sharing.

**Validation**

- `Rscript scripts/generate_flow_diagram.R`
- `python3 scripts/validate_pptx_mac_compat.py <file>`

**Evidence** — `demo`

## Bundled resources

**References** (`skills/make-figures/references/`):

- `critic_rubrics/` (2 files)
- `design_principles.md`
- `exemplar_diagrams/` (53 files)
- `figure_specs.md`
- `flow_diagram_lessons.md`
- `jacc_central_illustration_principles.md`
- `medical_illustration_sources.md`
- `pipeline_concepts_medical_ai.md`
- `reporting_guideline_figure_map.md`
- `visual_abstract_templates/` (4 files)

**Scripts** (`skills/make-figures/scripts/`):

- `build_jacc_template.py`
- `build_prisma2020_template.py`
- `build_strobe_template.py`
- `critic_figure.py`
- `derive_figure_legend_counts.py`
- `extract_exemplar_from_pdf.py`
- `fetch_official_templates.sh`
- `fill_prisma_template.py`
- `generate_flow_diagram.R`
- `generate_image.py`
- `generate_visual_abstract.py`
- `validate_pptx_mac_compat.py`

**Templates** (`skills/make-figures/templates/`):

- `official/` (10 files)

## Source

Canonical definition: [`skills/make-figures/SKILL.md`](../../skills/make-figures/SKILL.md)

---

*Part of [MedSci Skills](../../README.md) — Claude Code skills for the medical research lifecycle. This page is generated from the skill's `SKILL.md`; edit that file and re-run `scripts/gen_skill_docs.py`.*
