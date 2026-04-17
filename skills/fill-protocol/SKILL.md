---
name: fill-protocol
description: >
  Fill institutional Word form templates (.doc/.docx) for IRB protocols, ethics
  applications, grant proposals, and other structured research documents while
  preserving the original styles, table layouts, fonts, and page geometry. Pairs
  with write-protocol — write-protocol drafts the scientific content, fill-protocol
  renders it into the institutional template. Korean-aware (CJK eastAsia font
  enforcement, table cantSplit) but works for any language template.
triggers: fill protocol, fill template, fill IRB form, IRB template, ethics template, grant template, 양식 채우기, 연구계획서 작성, 신청서 작성, 정부 양식, 병원 양식, 워드 템플릿
tools: Read, Write, Edit, Bash, Grep, Glob
model: inherit
---

# Fill-Protocol Skill

You are helping a researcher populate an institutional Word form (IRB protocol,
ethics application, grant proposal, etc.) without breaking the original document
formatting. This skill is the formatting counterpart to `write-protocol`: where
`write-protocol` drafts content, `fill-protocol` lays that content into the
institutional template.

## Why This Skill Exists

Recreating institutional forms from scratch with `python-docx` reliably destroys
table layouts, page breaks, and font consistency. The only safe approach is to
**open the existing template** and replace cell/paragraph text in place. This
skill enforces that pattern.

## Core Principles (Do Not Violate)

1. **Open the existing template — never create from scratch.** Use
   `Document(template_path)`, not `Document()`.
2. **Convert .doc → .docx via LibreOffice headless** before any editing.
   `pandoc -f doc` is not supported; `textutil` corrupts table structure.
3. **Match cells by left-label text**, not row/column coordinates. Templates
   evolve and coordinate matching breaks silently.
4. **Apply `cantSplit` to every filled row** so a row never breaks across pages.
5. **For CJK languages, set the `eastAsia` font attribute**, not just
   `run.font.name`. Hangul/Kanji/Hanzi will render in fallback fonts otherwise.
6. **Validate** every fill operation: report unmatched labels, count empty cells,
   and surface mismatches before saving.

## Dependencies

If the template is already `.docx`, **LibreOffice is not required** — only the
three Python packages below. LibreOffice is needed only when the template is a
legacy `.doc` and must be converted first.

```bash
# Python libraries (always required)
pip install --user docxtpl python-docx pyyaml

# LibreOffice (only for legacy .doc input; ~700 MB on macOS)
brew install --cask libreoffice              # macOS
sudo apt-get install -y libreoffice           # Debian/Ubuntu
sudo dnf install -y libreoffice               # Fedora
sudo pacman -S --needed libreoffice-fresh     # Arch
```

### Bundled setup script

The skill ships a `setup.sh` that detects what is missing and installs only
those parts, with a confirmation prompt before each step:

```bash
bash setup.sh check     # report what's installed (read-only)
bash setup.sh install   # install missing pieces (asks before each)
```

### Auto-install behavior (for Claude as the caller)

When invoking this skill on behalf of a user:

1. **Before calling `doc_to_docx.py`**, run `bash setup.sh check`. If
   LibreOffice is missing, **ask the user** before installing — the cask is
   ~700 MB and proceeding silently is unfriendly.
2. **Skip LibreOffice entirely** if the template is already `.docx`. Only
   surface the install prompt when a `.doc` is encountered.
3. **Never** pass `--yes` to `setup.sh install` unless the user has explicitly
   authorized unattended installation in this session.
4. If the user declines installation, fall back to asking them to convert
   the `.doc` manually (open in Word/LibreOffice/Pages → Save As → .docx) and
   then re-run with the converted file.

## Workflow

### Step 1 — Convert legacy .doc to .docx (if needed)

```bash
python scripts/doc_to_docx.py path/to/template.doc path/to/template.docx
```

### Step 2 — Inspect the template structure

```bash
python scripts/inspect_template.py path/to/template.docx
```

This lists every table, every cell (with row/column coordinates and content
preview), and every top-level paragraph. Use this output to identify the labels
you will match against in your YAML content file.

### Step 3 — Author a content YAML

The YAML supports three fill modes. All keys are optional.

```yaml
protections:
  korean_font: "맑은 고딕"   # CJK font (set to "Noto Sans CJK KR", "SimSun",
                              # "MS Mincho", etc. for other locales)
  cant_split: true            # Apply <w:cantSplit/> to every filled row

  # Readability options (see "Readability" section below for full semantics)
  blank_between_paragraphs: true            # default true — Enter between \n\n chunks
  blank_around_section_header: true         # default true — Enter above/below filled sections
  blank_around_all_section_headers: false   # default false — opt-in; also touches untouched sections

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

### Readability — three blank-line knobs

All blank paragraphs inserted by these options use a forced single-line height
(`<w:spacing w:line="240" w:before="0" w:after="0"/>`) so the gap is exactly
one body-text line — never inflates the document's apparent line spacing.

| Option | Default | What it does | When to flip |
|---|---|---|---|
| `blank_between_paragraphs` | `true` | Inserts a blank line between every `\n\n`-split chunk inside `section_replace` | Disable only for forms where every line must be packed tight |
| `blank_around_section_header` | `true` | Wraps each header that you `section_replace` with a blank above and a blank below | Disable when the template style already adds visual gaps via `space_before/after` |
| `blank_around_all_section_headers` | `false` | After all fills, scans every numbered header (`\d+\.\s+`) — including ones you didn't replace — and adds blank lines around them | Enable when uniform readability matters more than form fidelity. **Default off because IRB / public-document submissions favor template fidelity over visual consistency** (page count stability, boilerplate untouched, reviewer-expected layout) |

The third option exists because `section_replace` only touches sections you
list in the YAML. If a template has 18 numbered sections and you only fill 12,
the other 6 stay tight against their content — visually inconsistent. Turn the
opt-in on for documents where you'd rather the consistency than the fidelity.

### Step 4 — Run the fill

```bash
python scripts/fill_form.py \
  --template path/to/template.docx \
  --content  content.yaml \
  --output   path/to/filled.docx
```

The CLI prints `[OK]` / `[MISS]` for every fill operation and a summary at the
end. Investigate any `[MISS]` before submitting.

### Step 5 — Visual verification

```bash
soffice --headless --convert-to pdf path/to/filled.docx
```

Open the PDF and visually confirm: page count is sensible, no table row was
split across pages, no font fell back to Times New Roman, all required fields
are populated.

## Python API

```python
from fill_form import FormFiller

filler = FormFiller("template.docx", korean_font="맑은 고딕")

# Fill table cells
filler.fill_table_kv("Study Title", "...")
filler.fill_table_kv("연구 목적", "...")

# Replace section content (header to next header)
filler.replace_paragraphs_after("4. Background", new_content)

# Replace a single paragraph
filler.replace_paragraph_matching("Title:", "Title: ...")

# Validate and save
warnings = filler.validate()
for w in warnings:
    print(w)
filler.save("filled.docx")
```

## Anti-Patterns (Do Not Do)

| Anti-pattern | Consequence |
|---|---|
| `Document()` then rebuild table | Loss of header logo, custom margins, footer placeholders, and page numbering |
| `pandoc -f doc -t docx` | "Unknown input format doc" — pandoc does not parse .doc |
| `textutil -convert docx` | Table cell merging is dropped or corrupted |
| `cell.text = "value"` (single assignment) | Run-level styles (bold, color, eastAsia font) are erased |
| Coordinate-based matching `table.cell(2, 1)` | Silent breakage when the template adds or reorders rows |
| `run.font.name` alone for Hangul | Hangul characters render in the default Western font |

## Companion Skills

- `write-protocol` — drafts the scientific content (Background, Study Design,
  Sample Size, Statistical Plan) that `fill-protocol` then renders into the form
- `hwp-pipeline` — converts Korean Hangul .hwp / .hwpx files; chain it before
  `fill-protocol` when the institutional form is distributed in HWP format
- `check-reporting` — validates that the filled protocol satisfies CONSORT /
  STARD / TRIPOD / CLAIM checklists before submission
- `calc-sample-size` — produces the sample size text that `fill-protocol` slots
  into the corresponding section

## Files

- `scripts/doc_to_docx.py` — LibreOffice headless wrapper for .doc → .docx
- `scripts/inspect_template.py` — reports tables, cells, and paragraphs
- `scripts/fill_form.py` — the `FormFiller` library and CLI entry point
- `examples/` — worked examples for IRB, ethics waiver, and grant templates
- `references/best_practices.md` — formatting notes (cantSplit, eastAsia,
  multi-line cell text)

## Known Limitations

- **HWP / HWPX input is not handled directly** — chain with `hwp-pipeline` to
  convert HWP → HWPX → DOCX first.
- **Merged cells**: filling a label cell that participates in a vertical merge
  may overwrite the merged region's content. Test on a copy first.
- **Embedded form fields** (Word's content controls): not yet supported. Plain
  paragraph and table cell content only.
- **Right-to-left scripts** (Arabic, Hebrew): untested.
