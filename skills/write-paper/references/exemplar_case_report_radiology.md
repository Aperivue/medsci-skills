# Radiology case-report anatomy — when the image is the case

A structure model for **imaging-led case reports** (diagnostic radiology, nuclear medicine, and
interventional radiology), complementing `exemplar_case_report.md` and `paper_types/case_report.md`.
Load it when the teaching point is an imaging finding, a cross-modality discordance, an incidental
finding, a structured-reporting decision, or an image-guided procedure/complication. Synthetic
anatomy model: required moves, failure modes, cross-checks — not prose to copy.

## What makes a radiology case report different

The contribution is the **image and how it was read**, so the discipline lives in the imaging
description, not just the clinical narrative. Three rules govern the whole report:

1. **Per-modality, in clinical order.** Describe each modality the way it was acquired and read —
   for each: **technique → findings → impression**, kept separate. Walk modalities in the order they
   were obtained (e.g., radiograph → ultrasound → CT → MRI → PET/CT → histopathology), not lumped.
2. **Reproducible technique.** State the parameters another reader would need: sequence/phase,
   field strength, contrast agent + dose + injection rate, CT kV/keV-reconstruction/CTDIvol, PET
   tracer dose + uptake time + fasting, transducer frequency. For interventional cases, name devices
   with sizes/gauge and the step sequence.
3. **Findings vs impression.** Report the observation ("circumferential aortic wall thickening,
   iodine X mg/mL") separately from the interpretation ("favoring active vascular inflammation").

## Structured reporting lexicons

When a standardized system applies, **use the category and state what it means** — a bare "BI-RADS 4"
is weaker than "BI-RADS 4b (moderate suspicion, ~10–50% malignancy risk)."

- Breast — **BI-RADS** (give the sub-category and risk band)
- Liver — **LI-RADS**; Prostate — **PI-RADS**; Thyroid — **TI-RADS**; Lung nodule — **Lung-RADS**;
  Adnexal — **O-RADS**; incidental findings — the relevant ACR Incidental Findings/white-paper
  guidance.
- If no system applies, describe with the standard descriptors of that modality (margin, echotexture,
  signal on each sequence, enhancement kinetics/curve type, attenuation).

## Quantitative anchors (and their honesty)

- Give the **measurement with method and units**: lesion size + location (e.g., o'clock + distance
  from nipple/skin), SUVmax, iodine concentration (mg/mL) with the ROI placement rule, time–signal
  intensity curve type, degree of stenosis / peak systolic velocity.
- When a value has **no validated threshold**, say so and label it exploratory; optionally give
  institutional comparison values. Do not present a number as diagnostic when no cutoff exists.

## Multimodality correlation and discordance

- When modalities **disagree**, make the discordance the explicit teaching point and state how it was
  resolved (the decisive modality, or histopathology/IHC). Example pattern: ultrasound suspicious vs
  MRI benign kinetic curve → resolved by core-needle biopsy.
- **Modality-completeness self-critique**: if a standard modality was not performed, name it as a
  limitation (e.g., "mammography was not obtained, precluding complete radiologic correlation") and
  say why (compliance, availability, pain).

## Subtype: interventional radiology (procedure / complication)

- **Reproducible procedure log**: access, devices with sizes (needle gauge, wire, balloon, catheter,
  coil/embolic, ablation probe + protocol), imaging guidance, and the step sequence.
- **Complication recognition and management in context**: state latency (e.g., a delayed post-procedural bleed),
  the recognition trigger, and the diagnostic-then-therapeutic pathway (angiography → embolization),
  with pre/post outcome. Quantify (blood loss, transfusion, preserved organ function) and give the
  background complication rate.

## Subtype: incidental finding

- Frame imaging as a **problem-solving / staging** tool and describe how the incidental lesion was
  characterized (the discriminating CT/US/MR features), the **functional-imaging pitfall** if relevant
  (FDG-avid benign mimic; FDG-occult malignancy), and the **reporting action** — what should be
  explicitly stated in the report to prevent mis-staging or over-treatment.

## Image and figure discipline (do this before submission)

- **De-identify every image at the DICOM level**: remove burned-in annotations, accession numbers,
  dates, institution banners, and faces; confirm panels carry no identifiers.
- **Write real alt text** for each figure (not a placeholder) — modality, plane, and the labeled
  finding; pair complex cases with `make-figures` `exemplar_plots/imaging_panel.md`.
- **Disclose device/vendor relationships**: advanced-technique or device cases (spectral/photon-counting
  CT, ablation systems) must state vendor research agreements, employment, or speaker arrangements.

## Common failure modes

- **Modality soup** — findings from several modalities merged into one paragraph instead of
  technique → findings → impression per modality.
- **Bare structured category** — "BI-RADS 4" / "PI-RADS 4" with no sub-category or risk meaning.
- **Unreproducible technique** — no sequence/phase, contrast, dose, or device specifics.
- **Number without a threshold** — a quantitative value presented as diagnostic when no validated
  cutoff exists.
- **Placeholder alt text / identifiable images** — the most common reviewer/production stop for an
  imaging case report.
- **Undisclosed device/vendor COI** in an advanced-technique case.
- **Overclaiming from n=1** — a feasibility or detection case framed as performance/effectiveness.
