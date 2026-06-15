<!-- AUTO-GENERATED from skills/render-pdf-doc/SKILL.md by scripts/gen_skill_docs.py. Do not edit by hand. -->

# render-pdf-doc

> Render academic Markdown documents (English or Korean) to publication-quality PDF via pandoc + xelatex. Targets non-bibliography artifacts: research proposals, IRB cover letters, briefing handouts, anchor docs (Q&A grids), and reference tables. Auto-infers pipe-table column widths from content (label column shrinks to fit, data columns share remaining width). CJK-aware font fallback for Korean text (Apple SD Gothic Neo on macOS, Noto Sans CJK KR on Linux). NOT for: manuscripts with bibliography (use /manage-refs render_pandoc.sh), Word form filling (/fill-protocol), figures (/make-figures).

**Invoke:** `/render-pdf-doc` · **Tools:** Read, Write, Edit, Bash, Grep, Glob · **Model:** inherit

## When to use

`render-pdf-doc` activates on requests such as: render PDF, PDF 렌더, korean PDF, 한글 PDF, anchor doc PDF, briefing PDF, proposal PDF, 연구계획서 PDF, 표 정렬 PDF, 표 폭 자동, tbl-colwidths, 학술 PDF.

## Quality Card

**Purpose** — Render a Markdown manuscript to a styled DOCX/PDF (tables, column widths, dependencies checked).

**Safety boundaries**

- Delegates bibliography rendering to manage-refs and figures/PPTX to make-figures/present-paper; does not modify citation keys.
- Does not hand-type CSV data into tables (numerical-safety).

**Known limitations**

- Output fidelity depends on installed render dependencies (checked by check_deps.sh).
- Institutional Word forms are out of scope (use fill-protocol).

**Validation**

- `bash scripts/check_deps.sh`
- `bash scripts/render_pdf.sh <manuscript.md>`
- `bash tests/test_glyph_coverage.sh`

**Evidence** — `bundled_script`

## Bundled resources

**References** (`skills/render-pdf-doc/references/`):

- `known_pitfalls.md`
- `pandoc_korean_cheatsheet.md`

**Scripts** (`skills/render-pdf-doc/scripts/`):

- `check_deps.sh`
- `infer_colwidths.py`
- `render_pdf.sh`
- `scan_glyph_coverage.py`

**Templates** (`skills/render-pdf-doc/templates/`):

- `anchor-doc.md`
- `anchor-doc_ko.md`
- `briefing-handout.md`
- `briefing-handout_ko.md`
- `proposal-cover.md`
- `proposal-cover_ko.md`
- `reference-table.md`
- `reference-table_ko.md`

## Source

Canonical definition: [`skills/render-pdf-doc/SKILL.md`](../../skills/render-pdf-doc/SKILL.md)

---

*Part of [MedSci Skills](../../README.md) — Claude Code skills for the medical research lifecycle. This page is generated from the skill's `SKILL.md`; edit that file and re-run `scripts/gen_skill_docs.py`.*
