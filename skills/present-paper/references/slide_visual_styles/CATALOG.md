# Slide Visual Styles — Catalog

A visual style is a **design-token set** (palette + typography + layout grid + slide-type
recipes) that any of the five presentation contexts in
`references/medical_presentation_templates.md` can call. Pick one in **Phase 0** (the
skill offers this menu after collecting inputs; see SKILL.md "Step 0b — Template & visual
style selection"). All styles obey `references/presentation_design_guidelines.md`
(24-pt floor, ≤3 colors, CVD-safe, redrawn tables) and the Mac-compatibility checklist.

## Available styles

| Style | File | Best for | Background | Primary / accent | Feel |
|-------|------|----------|------------|------------------|------|
| **Nature / Lancet** | `nature_lancet.md` | Journal club, conference talk, academic lecture (default for medical academic decks) | White | Navy `#1B2A4E` / coral `#B83E3A` | Editorial-academic, restrained |
| **Clinical Blue** | `clinical_blue.md` | Grand rounds, tumor board, hospital/CME, guideline talks | White / very light blue | Navy-teal `#0B3D62` / teal `#0E7C9B` | Calm, clinical, trustworthy, CVD-safe |
| **Editorial Mono** | `editorial_mono.md` | Single-message keynote, opinion/perspective, big-result reveals | White | Near-black `#111111` / one accent (red or blue) | High-contrast, oversized type, magazine |
| **Dark Modern** | `dark_modern.md` | Tech/AI talks, product/method launches, low-light auditoria | Deep slate `#0E1116` | Off-white `#E8EAED` / electric accent | Sharp, contemporary, "colors pop" |
| **Institutional Brand** | `institutional_brand.md` | When the venue/employer requires a branded master (university, hospital, society) | From the supplied `.potx`/`.pptx` | From the template theme | Matches the institution; you fill, not redesign |

> **Default**: if the user expresses no preference and the deck is a medical academic
> talk, use **Nature / Lancet** (`~/.claude/rules/academic-lecture-style.md`).

## How styles are applied

- **Nature / Lancet** has a dedicated reference builder
  (`templates/build_pptx_nature_lancet.py`).
- **Clinical Blue / Editorial Mono / Dark Modern** reuse the generic template library
  (`references/generate_pptx_templates.py`): swap the design tokens (palette + fonts +
  bullet markers) to the values in that style's spec. The coordinate zones, slide-type
  functions, and Mac-compat helpers are shared.
- **Institutional Brand** is *not* a from-scratch build — it is **patch-over-rebuild**
  into the user's template (SKILL.md "Mode C"). Inspect the template with
  `scripts/inspect_pptx_template.py`, map content into the existing layouts/placeholders,
  and preserve the master, theme, and logo.

## Adding a new style

1. Copy `nature_lancet.md` as the section skeleton (Color palette → Typography → Layout
   grid → Slide types → Figure handling → Notes density → Mac checklist).
2. Keep to **≤ 3 colors** and the 24-pt floor; verify the palette is CVD-safe or uses
   redundant encoding (`presentation_design_guidelines.md` §4).
3. Add a row to the table above and a one-line preview to SKILL.md Step 0b.
4. English only (locale inventory); no PII; reference in-skill files by relative path.
