# Medical Illustration Sources

Reference for finding medical illustrations for visual abstracts, graphical abstracts, and
manuscript figures. Consult this file when a standalone illustration (not a data plot) is needed.

## Priority Order

1. **Study's own figures** — ROC curve, flow diagram, representative images from the study.
   Always preferred. No licensing issues. Most relevant to the paper.
2. **Free illustration libraries** — Download and insert into the visual abstract template.
3. **Manual drawing** — Simple shapes in Figma, PowerPoint, or Keynote.
4. **AI generation** — Only if GEMINI_API_KEY is available. Use `generate_image.py --style medical`.

---

## Free Resources (CC BY or Public Domain)

### Servier Medical Art (SMART)

- **URL:** https://smart.servier.com/
- **License:** CC BY 4.0 (attribution required)
- **Assets:** 3000+ medical illustrations
- **Categories:** Anatomy (11 systems), cellular biology, medical specialties, equipment
- **Format:** PowerPoint (editable vectors), PNG
- **Best for:** Organ systems, cells, molecules, medical devices, surgical instruments
- **Attribution:** "Illustrations adapted from Servier Medical Art (https://smart.servier.com/),
  licensed under CC BY 4.0"
- **Access:** Browse categories on website. No API. Download slide sets per category.

### NIAID Visual & Medical Arts (BioArt)

- **URL:** https://bioart.niaid.nih.gov/
- **License:** Public domain (US Government work — no attribution legally required, but recommended)
- **Assets:** 2000+ illustrations
- **Categories:** Viruses, bacteria, parasites, anatomy, cells, lab equipment, animals
- **Format:** SVG, PNG, TIFF (high resolution)
- **Best for:** Infectious disease, pathogens, immune cells, laboratory scenes
- **Access:** Browse/search on website. No API.

### BioIcons

- **URL:** https://bioicons.com/
- **License:** Various CC licenses (check per icon)
- **Format:** SVG
- **Best for:** Schematic diagrams, pathway illustrations, icons for flow diagrams

### Reactome Icon Library

- **URL:** https://reactome.org/icon-lib
- **License:** CC BY 4.0
- **Format:** SVG, PNG
- **Best for:** Molecular pathways, biochemistry, cell signaling

---

## Paid Resources

### BioRender

- **URL:** https://biorender.com/
- **License:** Subscription (academic plans available, ~$99/year student)
- **Best for:** Professional graphical abstracts, pathway diagrams, figure panels
- **Note:** Industry standard. Output must include BioRender watermark on free tier.
  Academic publications require paid license for copyright clearance.

### Medi-Sketch

- **URL:** https://www.medi-sketch.com/
- **License:** Per-illustration purchase
- **Best for:** High-quality Korean medical illustrations, graphical abstract commissions
- **Note:** Korean marketplace connecting researchers with professional medical illustrators

---

## Keyword → Source Mapping

| Need | Recommended Source |
|------|--------------------|
| Organ anatomy (heart, lung, brain, kidney) | Servier Medical Art |
| Cell biology (membrane, organelles, DNA) | Servier Medical Art |
| Infectious agents (virus, bacteria) | NIAID BioArt |
| Lab equipment (microscope, pipette, scanner) | NIAID BioArt or Servier |
| CT/MRI scanner illustration | Servier Medical Art |
| Molecular pathway | Reactome or BioRender |
| Schematic flow icons | BioIcons |
| Custom professional illustration | Medi-Sketch or BioRender |

---

## Usage Notes

- **Editable vectors preferred.** Servier provides PowerPoint files with ungroupable vector shapes.
  Extract individual elements and recolor to match your visual abstract palette.
- **Resolution check.** Ensure downloaded PNGs are ≥300 DPI for print. SVGs scale infinitely.
- **Consistency.** Within one visual abstract, use illustrations from the same source to maintain
  visual coherence (mixing Servier flat style with NIAID 3D renders looks inconsistent).
- **AI generation warning.** See the AI-Generated Figure Warning section in SKILL.md.
  AI-generated medical illustrations are recognizable to reviewers. Use sparingly and customize.
