---
name: render-pdf-doc
description: >
  Render academic Markdown documents (English or Korean) to publication-quality PDF via pandoc + xelatex.
  Targets non-bibliography artifacts: research proposals, IRB cover letters, briefing
  handouts, anchor docs (Q&A grids), and reference tables. Auto-infers pipe-table column
  widths from content (label column shrinks to fit, data columns share remaining width).
  CJK-aware font fallback for Korean text (Apple SD Gothic Neo on macOS, Noto Sans CJK KR on Linux).
  NOT for: manuscripts with bibliography (use /manage-refs render_pandoc.sh), Word form
  filling (/fill-protocol), figures (/make-figures).
triggers: render PDF, PDF 렌더, korean PDF, 한글 PDF, anchor doc PDF, briefing PDF, proposal PDF, 연구계획서 PDF, 표 정렬 PDF, 표 폭 자동, tbl-colwidths, 학술 PDF
tools: Read, Write, Edit, Bash, Grep, Glob
model: inherit
---

# Render-PDF-Doc Skill

Markdown + frontmatter → publication-quality academic PDF (English or Korean).

## Why This Skill Exists

In real circulation cycles for academic PDFs, two recurring failure patterns appear:
1. v1 drafts: change-history, version numbers, and PI attribution leak into the attached PDF, confusing the first recipient.
2. v2 drafts: pandoc pipe-table dash ratios are misjudged, narrowing the first column and forcing label wrapping that hurts readability.

Manual fixes work but the same pattern recurs across proposals, briefings, IRB covers, exemption applications. This skill focuses on **layout** (CJK fonts + table column widths). Bibliography and CSL are handled by `/manage-refs`.

## Boundary (separation from other skills)

| Task | Skill |
|---|---|
| Manuscript + bibliography → DOCX/PDF | `/manage-refs scripts/render_pandoc.sh` (CSL + .bib) |
| Filling an institutional .docx form | `/fill-protocol` |
| ICMJE COI form | `/fill-icmje-coi` |
| Figure / PPTX | `/make-figures`, `/present-paper` |
| **This skill**: non-bib academic markdown → PDF (proposal, briefing, anchor doc, IRB cover) | `/render-pdf-doc` |

## Core Principles

1. **Pipe table column widths must be inferred from content.** No equal splitting. Size the first column (label) to the longest label, and distribute the remaining width content-proportionally across the data columns.
2. **Set the CJK font explicitly** — `mainfont` + `CJKmainfont`. The default fallback is OS-detected.
3. **For circulation PDFs, remove change history / version numbers / PI attribution** (or split them into a supplementary). Use the frontmatter `redact_internal: true` option.
4. **No Quarto dependency** — raw pandoc + xelatex. Quarto's `tbl-colwidths` has reported PDF regressions (issues 6089/9200).

## Dependencies

```bash
# Required
brew install pandoc                                                   # macOS
brew install --cask mactex-no-gui          # xelatex + xeCJK (~5 GB)

# Linux
sudo apt-get install pandoc texlive-xetex texlive-lang-cjk fonts-noto-cjk
```

Detection:
```bash
bash scripts/check_deps.sh
```

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

For Linux/CI, use `Noto Sans CJK KR` instead. The render script auto-detects.

### Step 2 — Infer column widths

```bash
python scripts/infer_colwidths.py input.md > input.colwidths.md
```

The script:
1. Finds every pipe table block.
2. For each column, computes display width = `max(len(header), max(len(cell)))` (CJK = 2 cells, ASCII = 1).
3. Generates dash-row separator with proportional dash counts.
4. Writes a new file with separator rows replaced.

Override per-table via attribute: `{tbl-colwidths="[20,40,40]"}` after caption — passes through unchanged.

### Step 3 — Render

```bash
bash scripts/render_pdf.sh -i input.colwidths.md -o output.pdf
```

Or one-shot:
```bash
bash scripts/render_pdf.sh -i input.md -o output.pdf --infer-colwidths
```

### Step 3.5 — Scientific-symbol + CJK glyph scan (before render)

xelatex **silently drops** any character the chosen font does not cover — the PDF
renders with the glyph simply missing, no error or warning. Academic markdown
routinely carries glyphs a default Latin font misses: transition arrows (→ ↑ ↓),
math operators (− ≤ ≥ ± √ ∪ × ≈ ≠), stats Greek (κ μ σ β), bullets/marks (• ★ ✓),
and CJK. Scan the source first so a silent drop is caught before it ships:

```bash
python3 scripts/scan_glyph_coverage.py input.md --strict
# real cmap check when you have the font file + fonttools:
python3 scripts/scan_glyph_coverage.py input.md --font "/path/to/body.otf" --strict
```

It groups the risky glyphs by class (advisory), or — with `--font` + `fonttools`
— reports which are genuinely absent from the font's cmap. If risky glyphs are
present, ensure `mainfont`/`CJKmainfont` cover them (a CJK-capable font such as
*Apple SD Gothic Neo* / *Noto Sans CJK* usually covers arrows + Hangul but can
still miss the true-minus `−` U+2212 and `★`). **The DOCX is authoritative; the
PDF is a convenience copy** — never let a PDF render drop a glyph the document
needs.

### Step 4 — Visual verify

Open the PDF. Check:
- The first-column labels do not wrap and stay on a single line
- Data columns have sufficient width
- No broken Korean glyphs (a Times New Roman fallback means CJKmainfont was not applied)
- No missing scientific symbols (arrows, −, ≤, ±, √) — the Step 3.5 scan flags candidates
- No change history / internal version numbers exposed

## Templates

Starter markdown in `templates/` (English default; a Korean variant `*_ko.md` ships alongside each):
- `anchor-doc.md` — Q&A grid
- `proposal-cover.md` — research-proposal cover page
- `briefing-handout.md` — meeting brief (1-page)
- `reference-table.md` — comparison-table format

Each template marks slots with a `<!-- TODO: -->` marker.

## Anti-Patterns

| Anti-pattern | Consequence |
|---|---|
| Equal dash split (`\|---\|---\|---\|`) | A column with only a short label gets the same width → cramped data columns |
| `CJKmainfont` not set | Hangul falls back to Times New Roman (broken Latin glyphs or blanks) |
| Change history / version (e.g. v3.2.2) / PI attribution exposed in a circulation PDF | Confuses the first recipient; leaks internal information |
| Quarto `tbl-colwidths` for PDF | PDF regression in Quarto 1.4+ — trust HTML only |

## Files

- `scripts/render_pdf.sh` — pandoc + xelatex wrapper, OS font detection
- `scripts/infer_colwidths.py` — auto-generates pipe-table separator dash ratios
- `scripts/check_deps.sh` — checks for pandoc / xelatex / CJK font
- `templates/` — 4 starters (English) + their `*_ko.md` Korean variants
- `references/pandoc_korean_cheatsheet.md` — collection of frontmatter patterns (Korean-PDF reference)
- `references/known_pitfalls.md` — em-dash line breaks, smart quotes, etc. (Korean-PDF reference)

## Anti-Hallucination

- Numerical content in tables: apply `~/.claude/rules/numerical-safety.md`. Read from CSV.
- References: use `/manage-refs` separately — this skill does not handle bib.
- When producing a circulation PDF, apply `~/.claude/rules/senior-mentor-circulation.md` (preserve the primary source) + `~/.claude/rules/ai-drafted-document-policy.md`.
