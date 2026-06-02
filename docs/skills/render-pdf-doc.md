<!-- AUTO-GENERATED from skills/render-pdf-doc/SKILL.md by scripts/gen_skill_docs.py. Do not edit by hand. -->

# render-pdf-doc

> Render Korean academic Markdown documents to publication-quality PDF via pandoc + xelatex. Targets non-bibliography artifacts: research proposals, IRB cover letters, briefing handouts, anchor docs (Q&A grids), and reference tables. Auto-infers pipe-table column widths from content (label column shrinks to fit, data columns share remaining width). CJK font fallback (Apple SD Gothic Neo on macOS, Noto Sans CJK KR on Linux). NOT for: manuscripts with bibliography (use /manage-refs render_pandoc.sh), Word form filling (/fill-protocol), figures (/make-figures).

**Invoke:** `/render-pdf-doc` · **Tools:** Read, Write, Edit, Bash, Grep, Glob · **Model:** inherit

## When to use

`render-pdf-doc` activates on requests such as: render PDF, PDF 렌더, korean PDF, 한글 PDF, anchor doc PDF, briefing PDF, proposal PDF, 연구계획서 PDF, 표 정렬 PDF, 표 폭 자동, tbl-colwidths, 학술 PDF.

## Bundled resources

**References** (`skills/render-pdf-doc/references/`):

- `known_pitfalls.md`
- `pandoc_korean_cheatsheet.md`

**Scripts** (`skills/render-pdf-doc/scripts/`):

- `check_deps.sh`
- `infer_colwidths.py`
- `render_pdf.sh`

**Templates** (`skills/render-pdf-doc/templates/`):

- `anchor-doc.md`
- `briefing-handout.md`
- `proposal-cover.md`
- `reference-table.md`

## Source

Canonical definition: [`skills/render-pdf-doc/SKILL.md`](../../skills/render-pdf-doc/SKILL.md)

---

*Part of [MedSci Skills](../../README.md) — Claude Code skills for the medical research lifecycle. This page is generated from the skill's `SKILL.md`; edit that file and re-run `scripts/gen_skill_docs.py`.*
