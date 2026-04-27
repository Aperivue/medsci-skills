# Visual Abstract Template Guide

How `generate_visual_abstract.py` maps content to PPTX template shapes.

## Matching Rules

The script iterates through all shapes on slide index 0 and matches by **text content**
(case-insensitive substring match). Each shape is filled exactly once.

| Content Field | Match Pattern (in shape.text) | CLI Flag |
|---|---|---|
| Article title | `ArticleTitle` | `--title` |
| Hypothesis / research question | `Hypothesis` or `Question` | `--hypothesis` |
| Methodology | `Methodology` or `flowchart` or `bullet` | `--methods` |
| Visual element (image) | `Visual element` or `Image` or `Illustration` | `--visual` |
| Main finding | `Main finding` or `relevance` | `--finding` |
| Citation | `Eur Radiol` or `DOI` or `Author` | `--citation` |
| Patient cohort badge | `Patient` or `cohort` | `--badges` (1st) |
| Modality badge | `Modality` or `organ` | `--badges` (2nd) |
| Center type badge | `Single` or `Multi-center` or `center` | `--badges` (3rd) |

## European Radiology Template

**Source:** EURA-GA-Jan2025.pptx (January 2025)
**File:** `european_radiology.pptx`
**Use slide:** Index 0 (slide 1 = blank template; slide 2 = filled example)

### Shape Map (Slide 1)

| Shape # | Name | Content Field | Position |
|---------|------|---------------|----------|
| 0 | Title 1 | Article title | Top, full width |
| 5 | Abgerundetes Rechteck 7 | Hypothesis/Question | Below title, full width |
| 3 | Abgerundetes Rechteck 7 | Methodology | Left panel, below hypothesis |
| 4 | Abgerundetes Rechteck 7 | Visual element (image) | Right panel, large area |
| 7 | Abgerundetes Rechteck 7 | Patient cohort badge | Left, below methodology |
| 8 | Abgerundetes Rechteck 7 | Modality / organ badge | Center-left, below methodology |
| 9 | Abgerundetes Rechteck 7 | Single / Multi-center badge | Center, below methodology |
| 6 | Abgerundetes Rechteck 7 | Main finding | Bottom area, full width |
| 2 | Abgerundetes Rechteck 2 | Citation line | Bottom bar |
| 1 | Content Placeholder 4 | (Logo area — leave empty or add journal logo) |

### Notes

- All shape names in the EUR template are generic German ("Abgerundetes Rechteck" = rounded
  rectangle). The script identifies shapes by their **text content**, not by name.
- The Visual element shape (Shape 4) should have its text cleared and an image inserted.
  The script places the image within the shape's bounding box, maintaining aspect ratio.
- Badge shapes (7, 8, 9) have small icon images in the EUR example slides — the script
  replaces text only. Icons can be added manually in PowerPoint after generation.

## MedSci Default Template

**File:** `medsci_default.pptx`
**Use slide:** Index 0

A journal-neutral template following the same structure as European Radiology but without
journal-specific branding. Uses neutral colors (dark gray accent, white background).

### Shape Map

Same field mapping as EUR, with these differences:
- No journal logo placeholder
- Neutral accent color (#404040 dark gray)
- Slightly wider visual element area

## Adding a New Journal Template

1. Obtain the journal's official visual abstract template (PPTX or PPT format).
2. Copy to `visual_abstract_templates/{journal_name}.pptx`.
3. Ensure the template slide has placeholder text matching the patterns in the
   Matching Rules table above. If not, either:
   - Manually edit the template to add matching placeholder text, OR
   - Add custom matching rules to `generate_visual_abstract.py`
4. Add a section to this guide documenting the shape map.
5. Update the journal profile in `write-paper/references/journal_profiles/` with
   the visual abstract requirement status and template name.

## JACC Central Illustration Template

`jacc_central_illustration.pptx` — for JACC family journals (`--type central-illustration`).

Built reproducibly via `scripts/build_jacc_template.py` to match the official JACC submission PPTX layout (verified against doi:10.1016/j.jacc.2019.10.035 Figures 1–4).

### Layout (10 × 7.5 in slide)

| Slot | Type | Position (left, top) | Size (W × H) | Placeholder text | Filled by `--type central-illustration` |
|---|---|---|---|---|---|
| 1 | TEXT_BOX | (0.4, 5.3) | 9.4 × 0.5 in | `ARTICLECITATION` | `--citation` |
| 2 | RECTANGLE → image | (3.0, 0.8) | 4.0 × 4.2 in | `VISUALELEMENT` | `--visual` (PNG/TIFF, ≥600 DPI) |
| 3 | TEXT_BOX | (0.4, 7.0) | 4.1 × 0.5 in | `FOOTERNOTE` | optional, usually empty |
| 4 | RECTANGLE | (7.3, 6.7) | 2.7 × 0.8 in | `JACCLOGO` | leave for editorial |

### Why a separate template

The JACC editorial team applies the red outer border and the blue "CENTRAL ILLUSTRATION:" header bar after acceptance. Author submissions must contain only:
- The content figure (slot 2)
- The citation line (slot 1)

Pre-rendering JACC house elements (red border, blue header) is incorrect — JACC will replace them anyway, and pre-rendered versions clash with the family branding.

### Validation rules

The CI mode in `generate_visual_abstract.py` validates structural simplicity per Fuster-Mann 2019:
- ≤ 3 visual zones in the content figure (`--ci-zones`)
- ≤ 30 total label words (`--ci-label-words`)
- ≤ 4 numerical highlights (`--ci-numerical-points`)
- No methodology terms in `--ci-raw-text` (CI ≠ Visual Abstract)

Override with `--ci-allow {zones|words|numerical|methods}` only when justified.

### Future cardiology templates

For Circulation, EHJ, JAHA, or other journals with similar CI requirements, copy this template and rename. The Fuster-Mann 5 rules and CI mode validation apply unchanged; only the slide dimensions and citation footer pattern may need adjustment.
