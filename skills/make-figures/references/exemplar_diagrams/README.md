# Exemplar Diagrams — Quality Anchors for the Critic Loop

This directory holds a small, hand-curated set of flow-diagram and figure
examples from published papers that we consider high-quality. The Critic
Loop references these as "visual structure first" anchors when reviewing
newly generated figures.

## Layout

```
exemplar_diagrams/
├── strobe/      # cohort / cross-sectional / case-control flow
├── stard/       # diagnostic-accuracy flow diagrams
├── consort/     # RCT participant flow
├── prisma/      # systematic review selection flow
├── pipeline/    # methods / algorithm flow diagrams
└── {other...}/  # future types (roc, forest, km, ...)
```

Each category directory can hold two kinds of files:

1. **Review anchors** (for the Critic Loop) — groups of three files per exemplar:
   - `{label}.png` — rendered figure cropped from a published paper (≥300 DPI)
   - `{label}.meta.yaml` — attribution metadata (source PDF, page, DOI, crop coords)
   - `{label}_why.md` — 50–100 word note on why this figure is a good anchor
2. **Generation templates** (for `generate_flow_diagram.R`) — one set per category:
   - `template_input.yaml` — minimal schema example showing all supported fields
   - `template_output.{pdf,png,_600.png}` — rendered reference output for the template
   - Render with `Rscript ../../scripts/generate_flow_diagram.R --type <type> --config <dir>/template_input.yaml --out <dir>/template_output`

## How to add a new exemplar

```bash
python skills/make-figures/scripts/extract_exemplar_from_pdf.py \
    --pdf "/path/to/paper.pdf" \
    --page 3 \
    --type stard \
    --label LastnameYEAR_STARD \
    --doi 10.1148/radiol.2017170371 \
    --crop 0.05,0.1,0.95,0.6
```

Then open the generated `{label}_why.md` and fill in the curator's note
(50–100 words on hierarchy, whitespace, typography, emphasis, color).

## Curator guidelines

- **Source quality** — prefer examples from Radiology, NEJM, Lancet, JAMA,
  European Radiology, BMJ, Cochrane Reviews. Lower-tier sources only when
  they show a specifically good design pattern.
- **One exemplar per design principle** — do not add five near-identical
  examples. Aim for 3–5 exemplars per category, each illustrating a
  different design strength.
- **Crop tightly** — remove surrounding caption and whitespace so the
  exemplar is purely the diagram.
- **No open-access conflict** — avoid exemplars from paywalled figures
  where fair-use for internal reference review is unclear. Prefer
  open-access or CC-licensed papers when possible.

## Attribution

Exemplars are used under fair-use for internal quality review only. They
are **not redistributed as part of generated figures** — the Critic Loop
uses them read-only as anchors for feedback. The `_meta.yaml` sidecar
records DOI and source for every exemplar.
