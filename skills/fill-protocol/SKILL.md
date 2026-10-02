---
name: fill-protocol
description: Use when an institutional Word form (.doc/.docx IRB protocol, ethics application, grant template) must be filled without breaking its styles, tables, fonts or page layout. Renders content drafted by /write-protocol into the template; CJK-aware.
metadata:
  triggers: "fill protocol, fill template, fill IRB form, IRB template, ethics template, grant template, 양식 채우기, 연구계획서 작성, 신청서 작성, 정부 양식, 병원 양식, 워드 템플릿"
---

# Fill-Protocol Skill

## Core Principles (Do Not Violate)

1. **Open the existing template — never create from scratch.** Use `Document(template_path)`, not
   `Document()`: rebuilding loses the header logo, custom margins, footer placeholders and page
   numbering. Replace cell/paragraph text in place; never a single `cell.text = "value"`
   assignment, which erases run-level styles (bold, color, eastAsia font).
2. **Convert .doc → .docx via LibreOffice headless** before any editing. `pandoc -f doc` is not
   supported; `textutil` corrupts table structure (merged cells dropped).
3. **Match cells by left-label text**, not row/column coordinates such as `table.cell(2, 1)`.
   Templates evolve and coordinate matching breaks silently.
4. **Apply `cantSplit` to every filled row** so a row never breaks across pages.
5. **For CJK languages, set the `eastAsia` font attribute**, not just `run.font.name`, or
   Hangul/Kanji/Hanzi render in fallback fonts.
6. **Validate** every fill operation: resolve every `[MISS]` line and every `WARN:` line
   (`[TABLE-MISS]`, `[SECTION-MISS]`, `[SECTION-UNBOUNDED]`, `[RAW-NEWLINE]`) before the filled
   form is submitted.

## Dependencies

Python packages `docxtpl python-docx pyyaml` are always required. LibreOffice is needed only for a
legacy `.doc` template (~700 MB on macOS). The bundled `setup.sh` detects what is missing:

```bash
bash ${CLAUDE_SKILL_DIR}/setup.sh check     # report what's installed (read-only)
bash ${CLAUDE_SKILL_DIR}/setup.sh install   # install missing pieces (asks before each)
```

When invoking this skill on behalf of a user:

1. **Skip LibreOffice entirely** if the template is already `.docx`.
2. **Before calling `doc_to_docx.py`**, run `setup.sh check`. If LibreOffice is missing, **ask the
   user** before installing, because the cask is ~700 MB.
3. **Never** pass `--yes` to `setup.sh install` unless the user has explicitly authorized
   unattended installation in this session, because it installs without prompting.
4. If the user declines, ask them to convert the `.doc` manually (Word/LibreOffice/Pages → Save
   As → .docx) and re-run with the converted file.

## Workflow

### Step 1 — Convert legacy .doc to .docx (if needed)

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/doc_to_docx.py path/to/template.doc path/to/template.docx
```

### Step 2 — Inspect the template structure

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/inspect_template.py path/to/template.docx
```

It lists every table, every cell (coordinates and content preview) and every top-level paragraph.
Take the exact labels for the YAML from this output.

### Step 3 — Author a content YAML

Start from `${CLAUDE_SKILL_DIR}/examples/example_irb_template.yaml`. Three fill modes; all keys are
optional.

```yaml
protections:
  korean_font: "맑은 고딕"   # CJK font (set to "Noto Sans CJK KR", "SimSun",
                              # "MS Mincho", etc. for other locales)
  cant_split: true            # Apply <w:cantSplit/> to every filled row

  # Readability options (defaults shown)
  blank_between_paragraphs: true            # Enter between \n\n chunks
  blank_around_section_header: true         # Enter above/below filled sections
  blank_around_all_section_headers: false   # opt-in; also touches untouched sections
  normalize_page_breaks: true               # empty page-break paragraphs -> pageBreakBefore

# Mode 1 — table key/value (left-label cell → right value cell)
table_kv:
  "Study Title": "Multi-center prospective validation of ..."
  "Principal Investigator": "Last, First (Department)"
  "연구 목적": "본 연구는 ..."

# Mode 2 — section replacement (find numbered header, replace until next header)
section_replace:
  "1. Background":
    "Hepatocellular carcinoma is the third leading cause of ..."
  "4. 연구 배경 및 이론적 근거":
    "..."

# Mode 3 — single paragraph in-place text replacement
paragraph_replace:
  "Title:":
    "Title: Multi-center prospective validation of ..."
```

Read `${CLAUDE_SKILL_DIR}/references/best_practices.md` (Readability knobs) before changing any
readability option from its default.

Content rules: put a reference in only with a `/search-lit`-confirmed DOI or PMID, otherwise mark
it `[UNVERIFIED - NEEDS MANUAL CHECK]`; mark any unconfirmed clinical definition, diagnostic
criterion or guideline claim `[VERIFY]` and ask the user.

### Step 4 — Run the fill

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/fill_form.py \
  --template path/to/template.docx \
  --content  content.yaml \
  --output   path/to/filled.docx
```

The CLI prints `[OK]` / `[MISS]` for every fill operation, a summary, then any `WARN:` lines.
Investigate every `[MISS]` and `WARN:` before submitting (Principle 6).

Every value under `table_kv`, `section_replace` and `paragraph_replace` is written exactly as
typed (`012345`, `12:30`, `1.10`, `No` stay text). An empty value or a list/mapping value stops the
run with exit 2 and names the label; write `''` to blank a field on purpose. A `section_replace`
on a header with no later numbered header replaces only the first paragraph after it and keeps
the rest (`[SECTION-UNBOUNDED]`), so a trailing signature/date block is never deleted.

### Step 5 — Visual verification

```bash
soffice --headless --convert-to pdf path/to/filled.docx
```

Open the PDF and confirm: page count is sensible, no table row was split across pages, no font fell
back to Times New Roman, all required fields are populated.

Read `${CLAUDE_SKILL_DIR}/references/best_practices.md` when a label or section header does not
match, the template has no numbered section headers (`stop_pattern` via the Python API), a cell
needs multi-line content, or cells are merged.

## Known Limitations

- **HWP / HWPX input is not handled directly** — convert it to `.docx` first.
- **Merged cells**: filling a label cell that participates in a vertical merge may overwrite the
  merged region's content. Test on a copy first.
- **Embedded form fields** (Word content controls): not supported; plain paragraph and table cell
  content only.
- **Right-to-left scripts** (Arabic, Hebrew): untested.
