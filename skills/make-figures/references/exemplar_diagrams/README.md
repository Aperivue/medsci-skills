# Exemplar Diagrams — Quality Anchors for the Critic Loop

Visual anchors the Critic Loop reads before judging a newly generated figure: *what does a
well-composed one actually look like?*

## What is here — and what is deliberately not

| | |
|---|---|
| **`{type}/template_output*.png`** | Diagrams **this skill renders itself** (`scripts/generate_flow_diagram.R` + the `template_input.yaml` beside them). Ours. Safe to ship. |
| **`{label}_why.md`** | **The teaching content.** 50–100 words on *why* an exemplar works — hierarchy, whitespace, typography, emphasis, colour. Written by us. This is what the Critic Loop actually learns from. |
| ~~`{label}.png` cropped from a published paper~~ | **Removed 2026-07-14 — see below.** |

## Why the paper figures are gone

This directory held ten PNGs **cropped from published papers**. The old README said so plainly, and
promised each carried a `.meta.yaml` recording *"source PDF, page, DOI, crop coords"*, and that the
sidecar *"records DOI and source for every exemplar."*

**It did not.** The files recorded `label`, `figure_type` and `dpi`. No source. No DOI. No licence.
Eight of the eighteen images had no metadata at all. The safeguard the README described had never
been implemented.

The old README also argued fair use, on the grounds that the exemplars are *"not redistributed as
part of generated figures"* — the Critic Loop only looks at them. That is true, and it is not the
question. **They were redistributed as part of the package**: this repository is **MIT-licensed** and
ships on npm and as a classroom ZIP that every user downloads. MIT tells the world it may *"use,
copy, modify, merge, publish, distribute, sublicense, and sell"* what is inside. We were granting
those rights over other people's figures — without knowing whose, without a licence, without credit.

Some were probably open-access and freely reusable with attribution. We cannot say which, because
the provenance was never recorded, and **a permission you cannot demonstrate is not a permission.**

The `_why.md` notes stay. They are ours, and they are where the value was: a paragraph explaining
*why* a two-tone palette survives greyscale teaches more than the picture it was written about.

**A figure you may legally read is not a figure you may legally ship.** That distinction is the whole
reason for this file.

## Bringing your own visual anchors

The Critic Loop reads whatever exemplars it finds here.

1. Drop them into `{type}/` **on your own machine.** They stay local; nothing here is uploaded
   anywhere, and a local file you never commit is never redistributed.
2. Give each one a sidecar:

   ```yaml
   label: "pipeline_11"
   figure_type: "pipeline"
   source: "Author et al., Journal Name, 2025"
   doi: "10.1234/example"
   license: "CC-BY-4.0"        # must be true, and must permit redistribution
   ```

3. If you want to **contribute** an exemplar back to the project, the licence has to permit
   redistribution — CC-BY, CC0, or your own work. `scripts/check_bundled_media_license.py` enforces
   that in CI: an image that ships without a declared, redistributable licence fails the build.

## Layout

```
exemplar_diagrams/
├── strobe/      # cohort / cross-sectional / case-control flow
├── stard/       # diagnostic-accuracy flow
├── consort/     # RCT participant flow
├── prisma/      # systematic-review selection flow
├── pipeline/    # methods / algorithm flow   (design notes only)
└── other/       #                            (design notes only)
```

Each type directory holds `template_input.yaml` (the config the R script consumes),
`template_output*.png` (what it renders), and any `_why.md` design notes.

Render one yourself:

```bash
Rscript ../../scripts/generate_flow_diagram.R \
  --type prisma --config prisma/template_input.yaml --out prisma/template_output
```
