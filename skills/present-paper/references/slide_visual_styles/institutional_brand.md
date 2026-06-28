# Slide Visual Style — Institutional Brand (fill the user's template)

Use when the venue or employer **requires a branded master** — a university, hospital,
or society `.pptx` / `.potx` with a fixed logo, color theme, and slide layouts. Here you
do **not** design a deck; you **fill** the supplied template, preserving its master,
theme, and logo placement. This is SKILL.md **Mode C** and follows *patch-over-rebuild*
(`~/.claude/rules/pptx-mac-compatibility.md` §2): never regenerate from scratch — that
destroys the institution's master/layout/theme.

> **Triggered from**: SKILL.md Step 0b when the user answers "yes, I have a template".
> Most institutions publish these (e.g. UT Southwestern, IU School of Medicine, WashU
> Medicine, Columbia CUIMC brand centers). The user supplies the file.

## Workflow

### 1. Inspect the template
```bash
python3 scripts/inspect_pptx_template.py /path/to/institution_template.potx
```
This lists every **slide layout** with its index, name, and **placeholders** (idx, type,
name, size). It also reports the theme fonts and the first few theme colors so you can
match body slides to the institution's palette. Read it before writing any content.

### 2. Map content to layouts (do not invent layouts)
- Choose the template's existing layouts: usually a **Title**, a **Title + Content**
  (or **Title Only**), a **Section Header**, and a **Closing/Thank-you**.
- Map each outline slide to one layout. Put the slide title in the title placeholder and
  body bullets in the body/content placeholder by **placeholder index** (from the
  inspector), so the institution's fonts, sizes, and logo are inherited automatically.
- For figures/tables, add them inside the content area; match the figure caption font to
  the template body (do not import the Nature/Lancet tokens).

### 3. Fill via python-pptx (placeholder-targeted)
```python
from pptx import Presentation
prs = Presentation("institution_template.potx")   # .potx opens like .pptx
LAYOUT = {l.name: i for i, l in enumerate(prs.slide_layouts)}

def add(layout_idx, title, body_lines):
    s = prs.slides.add_slide(prs.slide_layouts[layout_idx])
    ph = {p.placeholder_format.idx: p for p in s.placeholders}
    ph[0].text = title                       # title placeholder (idx from inspector)
    body = ph[1].text_frame                   # body/content placeholder
    body.clear()
    for i, line in enumerate(body_lines):
        p = body.paragraphs[0] if i == 0 else body.add_paragraph()
        p.text = line                         # inherits the template's bullet style
    return s
```
- **Target placeholders by idx** (from the inspector), not by adding free text boxes —
  free boxes lose the institution's typography.
- Let the template's theme carry color/font. Add an accent only if the template defines
  one; otherwise leave the institutional defaults.
- Delete any example/sample slides shipped in the template that you are not using, then
  sync `docProps/app.xml` (`~/.claude/rules/pptx-mac-compatibility.md` §5–5.1).

### 4. Speaker notes
Inject notes the same way as for generated decks (`scripts/inject_speaker_notes.py`) —
notes are independent of the visual template.

### 5. Verify (do not break the brand)
- Open in **Mac PowerPoint**: no repair dialog, logo present on every slide, fonts intact.
- `unzip -l filled.pptx | grep ppt/media` — the institution's logo/media is still
  embedded.
- Confirm you added slides via `add_slide(layout)`, not by rebuilding the presentation
  object — a from-scratch `Presentation()` would drop the master.

## When the template has no usable body layout
Some templates ship only a title + a blank layout. Then mirror the institution's theme
(read its theme colors/fonts from the inspector) into the generic builder
(`references/generate_pptx_templates.py`) as the design tokens, so new slides *look* like
the brand even though they are generated. Keep the logo by copying the title layout's
logo picture onto generated slides, or by using the template's blank layout (which
usually still carries the master logo).

## Cross-references
- `scripts/inspect_pptx_template.py` — layout/placeholder/theme inspector
- `~/.claude/rules/pptx-mac-compatibility.md` §2 (patch-over-rebuild), §5–5.1 (app.xml)
- `references/presentation_design_guidelines.md` — content rules still apply inside the brand
- SKILL.md "Mode C: Fill an institutional template"
