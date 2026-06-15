# Exemplar anatomy — annotated multimodality imaging panel (case report / series)

A worked **anatomy model** for the composite imaging figure that carries a radiology case report or
series — the figure where the diagnosis lives. This is a synthetic teaching model describing what the
panel must show, not a layout to copy. Use it when the teaching point is an imaging finding, a
cross-modality discordance, or a treatment response. Complements `clinical_timeline.md` (which carries
chronology); this file carries the **images themselves**.

## Elements

- **Panel grid with explicit labels** — one sub-panel per modality, sequence, or timepoint (e.g.,
  mammography / ultrasound / FDG PET-CT; or T2 / FLAIR / DWI / post-contrast). Letter each sub-panel
  (A, B, C…) and state the modality/sequence and plane in the caption, not only the image.
- **Arrow or marker to the key finding** in every sub-panel — the reader must see what to look at.
  An unannotated image is a decoration, not evidence.
- **Quantitative labels where a number is the point** — lesion size, SUVmax, BI-RADS/standardized
  category, signal characteristics, degree of stenosis. These anchor the description in the text.
- **Same-lesion correspondence across panels** — when showing discordance (e.g., visible on one
  modality, occult on another) or response (pre- vs post-treatment), keep the same lesion/orientation
  so the comparison is read at a glance; mark the same anatomical landmark in each.
- **Modality-appropriate orientation and scale** — laterality labels (L/R), a scale where size is
  load-bearing, and consistent windowing across compared panels.
- **Histopathology/immunostain sub-panel when origin hinges on it** — stain name and magnification in
  the caption (e.g., the EBER/IHC panel that settles a mimic).
- **Caption that states de-identification and defines every abbreviation/scale** used in the labels.

## Discipline (what the figure must not do)

- **Do not expose identifiers** — strip dates, accession numbers, institution banners, patient
  initials, faces, and embedded DICOM overlays before export.
- **Do not show unannotated images** — every sub-panel needs an arrow/label tying it to a finding
  named in the case presentation.
- **Do not imply causality or response without correspondence** — a "before/after" pair must be the
  same lesion/plane; mismatched views overstate the change.
- **Do not omit the quantitative anchor** when the teaching point is a number (an "occult on PET"
  claim needs the SUVmax; a "stenosis" needs the degree or velocity).
- **Do not overcrowd** — split into more sub-panels rather than stacking arrows on one image.

## Common omission

- **Cross-modality / cross-timepoint correspondence** and the **quantitative label**. A case whose
  lesson is discordance or response fails if the panels are not the same lesion or the decisive number
  is missing. Cross-reference `write-paper/references/exemplar_case_report.md` (diagnostic-assessment
  and adverse-event/mimic subtypes), `clinical_timeline.md` for the chronology figure, and the CARE
  checklist in `/check-reporting`.
