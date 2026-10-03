---
name: render-pdf-doc
description: Use when rendering a Markdown document (English or Korean) such as a proposal, IRB cover letter, handout or reference table to PDF via pandoc and xelatex, with auto-fitted table widths and CJK fonts. Not for manuscripts with a bibliography (/manage-refs) or Word forms.
metadata:
  triggers: "render PDF, PDF 렌더, korean PDF, 한글 PDF, anchor doc PDF, briefing PDF, proposal PDF, 연구계획서 PDF, 표 정렬 PDF, 표 폭 자동, tbl-colwidths, 학술 PDF"
---

# Render-PDF-Doc Skill

This skill handles layout only (CJK fonts, table column widths) with raw pandoc + xelatex — no
Quarto, whose `tbl-colwidths` has reported PDF regressions (issues 6089/9200). Not for: a
manuscript with a bibliography (`/manage-refs` `scripts/render_pandoc.sh`), an institutional .docx
form (`/fill-protocol`), the ICMJE COI form (`/fill-icmje-coi`), figures or PPTX (`/make-figures`,
`/present-paper`).

## Dependencies

Python 3 is required by the wrapper. FontTools is optional for the font-file
coverage check (`python3 -m pip install fonttools`).

```bash
# macOS
brew install pandoc
brew install --cask mactex-no-gui          # xelatex + xeCJK (~5 GB)

# Linux
sudo apt-get install pandoc texlive-xetex texlive-lang-cjk fonts-noto-cjk

# Windows (PowerShell) — run in Git Bash afterwards
winget install --id JohnMacFarlane.Pandoc
winget install --id MiKTeX.MiKTeX          # xelatex; installs missing LaTeX packages on demand
# No CJK font download needed: Malgun Gothic ships with Windows 7+ and is the default here.
```

Detection:
```bash
bash scripts/check_deps.sh
```

On Windows / Git Bash, MiKTeX's bin directory
(`%LOCALAPPDATA%\Programs\MiKTeX\miktex\bin\x64`) is often not on `PATH`; both `check_deps.sh`
and `render_pdf.sh` probe it. If `xelatex` still reads `[MISS]`, add that directory to `PATH`.

## Workflow

### Step 1 — Author markdown with frontmatter

```yaml
---
title: "Paper 2 Calibration Anchor — Q&A Grid"
author: "<Author Group>"
date: "2026-05-01"
mainfont: "Apple SD Gothic Neo"        # macOS default
CJKmainfont: "Apple SD Gothic Neo"
geometry: "margin=0.85in"
fontsize: 11pt
linestretch: 1.25
colorlinks: true
---
```

- Set both `mainfont` and `CJKmainfont`: without `CJKmainfont`, Hangul falls back to Times New
  Roman (broken glyphs or blanks). Use `Noto Sans CJK KR` on Linux/CI and `Malgun Gothic` on
  Windows; the render script auto-detects the per-OS default when the fields are absent.
- Read every number in a table from the source CSV or analysis output. Do not retype a number
  from prose or carry one forward from an earlier draft — a table correct in v3 is not evidence
  it is correct in v4.
- A circulation PDF carries no change history, internal version numbers (e.g. v3.2.2) or PI
  attribution: put them in a separate circulation file or a supplementary. Keep the received
  primary source (the `.docx` or `.eml` a co-author sent) unmodified as its own artifact — the
  PDF is a derivative, and the next round is diffed against the source. If that source was
  AI-drafted by a collaborator, re-derive every number, denominator and author-year in it from
  the underlying paper or analysis output before it reaches the PDF.

### Step 2 — Infer column widths

Never split pipe-table columns equally: a column holding only short labels then gets the same
width as the data columns, which cramps them. Size from content instead:

```bash
python3 scripts/infer_colwidths.py input.md > input.colwidths.md
```

For each pipe table it computes per-column display width = `max(len(header), max(len(cell)))`
(CJK = 2 cells, ASCII = 1) and rewrites the separator row with proportional dash counts. To set
widths by hand, write the separator dashes yourself and render without `--infer-colwidths`.

### Step 3 — Render

```bash
bash scripts/render_pdf.sh -i input.colwidths.md -o output.pdf
```

Or one-shot:
```bash
bash scripts/render_pdf.sh -i input.md -o output.pdf --infer-colwidths
```

Frontmatter wins over wrapper defaults, including `--font` / `--cjk-font`.
Missing fields use the wrapper or OS defaults. This also applies to `geometry`,
`fontsize`, `linestretch` and `colorlinks` (including `false`). Explicit pandoc
`-V` / `-M` arguments after `--` still override frontmatter; for example,
`-- -V fontsize=10pt`. The wrapper logs font **fallbacks**, not the final fonts.

The standard `article` class honours only `10pt`, `11pt` and `12pt` and silently
ignores any other size. When the effective `fontsize` is anything else and no
`documentclass` is set, the wrapper switches to KOMA-Script `scrartcl` (pandoc's
documented route), adds `classoption: fontsize=<size>` when you set no
`classoption` (KOMA reads a fractional size such as `8.5pt` only that way), and
logs the switch. Set `documentclass` yourself to override it.

### Step 3.5 — Scientific-symbol + CJK glyph scan (before render)

xelatex can finish successfully with missing glyphs. `render_pdf.sh` counts the
`Missing character` warnings pandoc relays: if there are any, it lists each glyph
(code point, count, font) and **exits 4** — the PDF is written but incomplete. It reads them from
pandoc's JSON `--log` (yours if you pass one after `--`), so a pass-through `--quiet` does not
hide them.
`--allow-missing-glyphs` prints the same list and exits 0. Academic markdown
routinely carries glyphs a default Latin font misses: transition arrows (→ ↑ ↓),
math operators (− ≤ ≥ ± √ ∪ × ≈ ≠), stats Greek (κ μ σ β), bullets/marks (• ★ ✓),
and CJK. Scan the source first so a silent drop is caught before it ships:

```bash
python3 scripts/scan_glyph_coverage.py input.md --strict
# real cmap check when you have the font file + fonttools:
python3 scripts/scan_glyph_coverage.py input.md --font "/path/to/body.otf" --strict
# TTC/OTC collections require the zero-based face index used by the renderer:
python3 scripts/scan_glyph_coverage.py input.md --font "/path/to/body.ttc" --font-index 0 --strict --json glyphs.json
```

Without `--font` it groups the risky glyphs by class (advisory); with `--font` + `fonttools` it
checks every non-ASCII character of the source that the font is asked to draw — not only the
five classes, so `°`, `µ`, `²`, `‰`, `∞` and `–` are covered too — and reports which are absent
from one face's preferred Unicode cmap (format characters such as a BOM or zero-width joiner, and
the no-break spaces and `…` that pandoc writes as ASCII TeX, are not looked up), never combining coverage across
collection faces — choose the face (index and PostScript name are in the report) that matches the
rendered font. A missing dependency, unreadable font, missing face selection or invalid index is
reported as `font_checked: false` with a reason in `font_check`; an empty `missing_in_font` list
then means **unverified**, not full coverage. Default mode exits 0; `--strict` exits 1 when risky
glyphs are unverified or missing (ASCII-only input still exits 0). The scan does not verify
shaping, fallback fonts, math fonts or final PDF glyphs.

If risky glyphs are present, make sure `mainfont`/`CJKmainfont` cover them — a CJK-capable font
such as *Apple SD Gothic Neo* / *Noto Sans CJK* usually covers arrows and Hangul but can still
miss the true-minus `−` U+2212 and `★`. **The DOCX is authoritative; the PDF is a convenience
copy** — never let a PDF render drop a glyph the document needs.

### Step 4 — Visual verify

Open the PDF and check:
- First-column labels stay on one line; data columns have enough width.
- No broken Korean glyphs (a Times New Roman fallback means `CJKmainfont` was not applied).
- No missing scientific symbols (arrows, −, ≤, ±, √) — the Step 3.5 scan flags candidates.
- No change history or internal version numbers exposed.

Read `references/known_pitfalls.md` when a render still looks wrong (em-dash overflow, smart
quotes under `CJKmainfont`, `|` inside a cell), and `references/pandoc_korean_cheatsheet.md` for
Korean frontmatter and font patterns.

## Templates

Starter markdown in `templates/` (English default; a Korean variant `*_ko.md` ships alongside
each), with slots marked `<!-- TODO: -->`:
- `anchor-doc.md` — Q&A grid
- `proposal-cover.md` — research-proposal cover page
- `briefing-handout.md` — meeting brief (1-page)
- `reference-table.md` — comparison-table format
