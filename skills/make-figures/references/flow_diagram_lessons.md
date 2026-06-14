# Flow Diagram Production — Hard-Earned Lessons

> **Triggered from**: SKILL.md Step 4b (Critic Loop). Read this file when
> generating PRISMA / CONSORT / STARD / STROBE diagrams, especially before a
> circulation round with senior co-authors.
>
> **Source**: Distilled from a multi-revision meta-analysis project where
> Figure 1 (PRISMA flow) went through four major iterations before clearing
> a senior reviewer round. Each lesson maps to a concrete failure mode.

Flow diagrams look simple but consume disproportionate revision time. The
underlying causes are rarely "wrong numbers" — they are template fidelity,
PDF export fidelity, and version drift between the diagram and the
manuscript. The five lessons below address each in turn.

---

## Lesson 1: Use the official template once a senior reviewer is in the loop

**Failure mode**: Custom Graphviz / DiagrammeR layout offers more freedom
(left-aligned bullets via `\l`, `penwidth=1.8` highlights on the analytic
cohort, free positioning of side-boxes). Senior systematic-review reviewers,
however, expect the **PRISMA 2020 standard layout** as published by the
PRISMA Statement group. A custom layout reads as "the authors did not follow
the guideline," even when every count is correct.

**Resolution**:

- Prototype freely with Graphviz / DiagrammeR for early drafts.
- **Switch to an official template before circulation.** The R package
  `PRISMA2020` (Haddaway et al.) renders the canonical layout from a CSV.
  Equivalent canonical templates exist for CONSORT 2010, STARD 2015, and
  STROBE.
- If the official template lacks a feature you need (e.g., a third
  exclusion sub-branch), prefer to fold the detail into the existing slots
  rather than restructure.

**Cross-link**: `critic_rubrics/flow_diagram.md` — "Official template
fidelity" check.

---

## Lesson 2: PDF export — the VML fallback breaks under headless converters

**Failure mode**: The official PRISMA 2020 docx contains VML (Vector Markup
Language) fallback pairs that older Word versions render. When converted to
PDF via headless LibreOffice (`soffice --headless --convert-to pdf`), the
phase labels can shift by several pixels, columns misalign, and on some
systems text reflows out of its box. The PDF looks "almost right" — the
kind of bug that survives a quick visual scan.

**Resolution by platform**:

| Platform | Approach | Notes |
|---|---|---|
| **macOS** | AppleScript driving Microsoft Word for Mac | Deterministic native render; can be invoked headlessly via `osascript`. |
| **Windows** | PowerShell / VBScript COM driving Word | `Word.Application` object → `.SaveAs2` with `wdFormatPDF`. |
| **Linux / CI** | Office Online Server (paid), or commit a pre-rendered PDF produced on macOS / Windows | Headless LibreOffice is **not** safe for VML-heavy templates. |
| Any platform (fallback) | Open in desktop Word → "Save As PDF" manually | Slow but always correct; document the manual step in the manifest. |

**Verify visually**: After export, open the PDF and the source docx
side-by-side. Compare phase-label positions, column widths, and the Y
position of every numeric box. If anything has shifted, do not submit that
PDF.

---

## Lesson 3: docx XML editing requires entity escape

**Failure mode**: A docx file is a ZIP archive containing
`word/document.xml`. Programmatic placeholder substitution (e.g., replacing
`{{n_screened}}` with `1,234` plus a comment, or `{{study_title}}` with a
title containing `&`) by raw `str.replace` produces invalid XML. Word then
shows "We're sorry, we can't open the file because there's a problem with
the contents." dialog on next open, or — worse — opens with a "repair"
prompt that silently drops content.

**Resolution**:

- Use an entity-escaping helper before injecting any user-provided string.
  Python: `xml.sax.saxutils.escape(value)`. JavaScript: `he.encode` or a
  small regex (`& → &amp;`, `< → &lt;`, `> → &gt;`).
- High-risk fields:
  - Study titles containing `&` (`Smith & Jones, 2020`).
  - Range strings containing `<` or `>` (`age <5 years`, `loss >50%`).
  - Author lists with apostrophes (`O'Brien`).
- After substitution, validate with `python -c "import zipfile,
  xml.etree.ElementTree as E;
  E.fromstring(zipfile.ZipFile('out.docx').read('word/document.xml'))"`.
  An exception means the docx is broken.

---

## Lesson 4: VML fallback templates need sequential placeholder maps

**Failure mode**: The official PRISMA 2020 docx duplicates each numeric box
as a `<w:t>` pair: a primary text element plus a VML fallback. Branch
ordering in XML DOM does **not** match rendering order — the "Other"
identification branch and the "Database" branch are interleaved in the
document, and the VML fallbacks appear elsewhere again. A naive
"replace each placeholder with the next number" loop misaligns most boxes.

**Resolution**:

1. Dump every `<w:t>` in document order with a script
   (`python -c "from docx import Document; ..."` or direct XML walk).
2. Annotate each `<w:t>` with column / branch / role
   (`identification.databases.records_n`, `identification.databases.records_n.fallback`).
3. Build a static `VALUES` list with one entry per `<w:t>` slot, **with a
   comment per slot** documenting what it represents.
4. Validate by filling all slots with a sentinel value (e.g., `999`) and
   visually checking that all 60+ boxes show `999` in the rendered PDF
   before re-running with real data.

This sentinel-render is cheap (one extra `999` pass) and catches mapping
errors before they propagate into a circulation round.

---

## Lesson 5: Freeze figure versions alongside manuscript versions

**Failure mode**: A reviewer asks about Figure 1 in revision round 2, but
the figure file in `manuscript/figures/figure_1.pdf` was edited in place
between rounds. The version visible in v3 of the manuscript no longer
exists, and tracing what changed requires diffing PDFs (lossy and slow).

**Resolution**:

- Treat figures as part of the manuscript artifact — they freeze with each
  manuscript version under the **`v_N` rule** (manuscript-versioning
  protocol).
- Maintain `figures/v{N}/` directories. Each contains the source script
  (`generate_figure_1.R`), the input data CSV, and the rendered docx + PDF
  pair.
- An `INDEX.md` at `figures/INDEX.md` maps figure version ↔ manuscript
  version, e.g.:
  ```
  | Manuscript | Figure 1 | Figure 2 | Figure 3 |
  |---|---|---|---|
  | v3 (circulated 2025-09-01) | figures/v3/figure_1.pdf | figures/v3/figure_2.pdf | figures/v2/figure_3.pdf |
  | v4 (submitted 2025-10-15)  | figures/v4/figure_1.pdf | figures/v3/figure_2.pdf | figures/v3/figure_3.pdf |
  ```
- **Never edit `figures/v3/*.pdf` after circulation.** Branch to
  `figures/v4/` and rebuild.

---

## Lesson 6: Any flowchart-shaped figure uses the monochrome Graphviz convention — not colorful boxes-and-arrows

**Failure mode**: A study-design / reader-flow / pipeline schematic (i.e. NOT a
reporting-guideline flow) gets hand-built in matplotlib (or slides) with filled
color boxes, accent palettes, and manually positioned text. It reads as
"AI-generated", text is poorly aligned inside the boxes (matplotlib anchors text
by point, not to the box geometry, so multi-line bodies overflow the border), and
it does not match the journal house style of the group's accepted papers.

**Resolution** — treat *every* flowchart-shaped figure (CONSORT/PRISMA/STARD/STROBE
**and** study-design, reader-flow, cohort-assembly, MRMC/reader-study, generation-
pipeline schematics) as the same object and render it with `scripts/generate_flow_diagram.R`
(DiagrammeR → Graphviz `dot`). The house convention, already encoded in that
script's `STYLE_HEADER`, is the journal standard:

- `fillcolor=white, color=black` (white fill, **black outline only — no color**)
- `fontname="Arial"`, `fontsize` 10–11
- `shape=box, style="rounded,filled"`, `penwidth=1.2` (emphasis boxes `penwidth=1.8`)
- `splines=ortho` (right-angle edges), `nodesep`/`ranksep` ≈ 0.4–0.55
- left-aligned sub-lists with `\l` and `•` (`•`); side panels / exclusions via
  `{ rank=same; main; side }` and an invisible edge to anchor them
- Graphviz lays text out *relative to the node box*, so alignment and centering are
  automatic — this is why it beats hand-positioned matplotlib/slide boxes.

Reconcile every count to the manuscript with `stopifnot()` assertions in the script
header (e.g. `stopifnot(N_auth + N_v16 + N_v12 == N_pool)`); leave data-dependent
counts as a single find-replaceable token (e.g. `[N_COMPLETED]`) filled at data lock.

**Do not** reach for matplotlib/PowerPoint/AI-image tools for a box-and-arrow figure.
matplotlib is for *data* figures (ROC, forest, calibration, KM); Graphviz is for
*flow/structure* figures. Mixing them produces the colorful, misaligned look this
lesson exists to prevent.

> Motivation: a reader-study Figure 1 was first built in colorful matplotlib and
> rejected by the author as "too AI-looking, text not aligned in the boxes." Rebuilt
> with `generate_flow_diagram.R` in the monochrome house style — matching the same
> style used across the group's accepted meta-analysis, cohort, and reader-study flow
> figures — it passed immediately.

---

## When to use which approach

| Stage | Tool | Output | Risk if you skip |
|---|---|---|---|
| Early draft | DiagrammeR + Graphviz custom | PNG, fast iteration | None — flexibility wins here |
| Internal QC | R `PRISMA2020` package or equivalent | Official-template PNG / PDF | Custom layout will be flagged in circulation |
| Circulation | Filled official-template docx + native-Word PDF (macOS AppleScript / Windows COM) | Frozen docx + PDF pair | Headless export drift; reviewer notices misaligned labels |
| Submission | `figures/v_N/` frozen pair | Immutable docx + PDF | Edit-in-place breaks the manuscript-figure version map |

---

## Quick cross-references

- `critic_rubrics/flow_diagram.md` — extended critic checklist (rounds T=1…3)
- `design_principles.md` — communication-first design strategies
- `figure_specs.md` — journal-specific dimensions and DPI
- `exemplar_diagrams/{prisma,consort,stard,strobe}/` — reference layouts
