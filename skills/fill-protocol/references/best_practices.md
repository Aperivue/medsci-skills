# fill-protocol — Best Practices Reference

## CJK Font Setting (mandatory for Korean / Japanese / Chinese)

`run.font.name = "맑은 고딕"` alone does **not** apply to Hangul characters in
docx output. Word and LibreOffice route CJK glyphs through the `eastAsia`
font slot, which lives in `<w:rPr><w:rFonts w:eastAsia="..."/>`. The skill
sets all four font slots (`ascii`, `hAnsi`, `cs`, `eastAsia`) to the same
font name to guarantee consistent rendering.

### Recommended fonts by platform

| Platform | CJK font that always exists |
|---|---|
| Windows | 맑은 고딕 (Malgun Gothic) |
| macOS | Apple SD Gothic Neo |
| Linux | Noto Sans CJK KR |

If the document will be opened on multiple platforms, embed the font in the
.docx (Word: File → Options → Save → Embed fonts in the file) or stick to
fonts that exist everywhere (Noto family).

## Table Row Page-Break Prevention (`cantSplit`)

Korean institutional IRB tables routinely have multi-line cells (e.g.
inclusion/exclusion criteria with 5–10 items). Without `cantSplit`, a row
can break across pages and the label cell ends up orphaned on the previous
page.

The XML insertion looks like:

```xml
<w:tr>
  <w:trPr>
    <w:cantSplit/>           <!-- this line is added by the skill -->
  </w:trPr>
  ...
</w:tr>
```

The skill applies this automatically to every row that gets filled.
You can also pre-set this in Word: select the row → Layout → Properties →
Row → uncheck "Allow row to break across pages".

## Multi-line Cell Content

YAML `|` (literal block) and `>` (folded block) both produce strings with
embedded newlines. `fill-protocol` splits on `\n` and writes each line as a
separate paragraph in the cell, cloning the first paragraph's `pPr` so
indentation, line spacing, and alignment are preserved.

```yaml
"Inclusion Criteria": |
  All of the following:
  1. Age ≥ 19 years
  2. Confirmed diagnosis ...
  3. Imaging within 30 days
```

If you want bullets (•) instead of numbers, type them literally in the
YAML — Word formatting is preserved at the run level, but list numbering
markers are not auto-generated.

## Label Matching

The skill normalizes whitespace (including newlines) before comparing
cell content to the YAML key. So a cell labeled

```
연구대상자
정보
```

matches the YAML key `"연구대상자 정보"` (with a space). Confirm exact
labels via `inspect_template.py` — institutional templates often have
trailing spaces, half-width vs. full-width parentheses, or zero-width
characters that are invisible in Word but break exact-match.

## Section Header Matching

`section_replace` finds a paragraph whose text equals the YAML key, then
replaces every paragraph from there until the next paragraph that starts
with `\d+\.\s+` (e.g. "1. ", "12. "). This is robust across templates
that re-number sections, but assumes numbered headers. For non-numbered
templates, pass `stop_pattern` to `replace_paragraphs_after()` directly
in Python.

## Readability Knobs

All four options live under `protections:` in the content YAML. Every blank paragraph they insert
uses a forced single-line height (`<w:spacing w:line="240" w:before="0" w:after="0"/>`), so the gap
is exactly one body-text line and never inflates the document's apparent line spacing.

| Option | Default | What it does | When to flip |
|---|---|---|---|
| `blank_between_paragraphs` | `true` | Inserts a blank line between every `\n\n`-split chunk inside `section_replace` | Disable only for forms where every line must be packed tight |
| `blank_around_section_header` | `true` | Wraps each header that you `section_replace` with a blank above and a blank below | Disable when the template style already adds visual gaps via `space_before/after` |
| `blank_around_all_section_headers` | `false` | After all fills, scans every numbered header (`\d+\.\s+`) — including ones you didn't replace — and adds blank lines around them | Enable when uniform readability matters more than form fidelity. **Default off because IRB / public-document submissions favor template fidelity over visual consistency** (page count stability, boilerplate untouched, reviewer-expected layout) |
| `normalize_page_breaks` | `true` | On save, converts dangling empty paragraphs whose sole content is `<w:br w:type="page"/>` into a `<w:pageBreakBefore/>` attribute on the next content paragraph. Prevents visible blank pages when the preceding content (e.g. an abstract table) grows or shrinks and pushes the empty paragraph onto a page of its own, causing the break to land one page later. | Disable only if your template intentionally relies on the empty-paragraph-as-separator pattern for spacing |

The third option exists because `section_replace` only touches sections you list in the YAML. If a
template has 18 numbered sections and you only fill 12, the other 6 stay tight against their
content — visually inconsistent. Turn the opt-in on for documents where you'd rather the
consistency than the fidelity.

## Python API

Use the library directly (with `${CLAUDE_SKILL_DIR}/scripts` on `sys.path`) when the YAML modes are
not enough — e.g., `stop_pattern` for templates without numbered section headers.

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

## Merged Cells

`python-docx` returns the same `_Cell` object for cells that participate
in a merge (horizontal or vertical). Filling such a cell once propagates
the content. The skill detects this via `id(cell._tc)` and skips
duplicates within a row, so vertical-merge label cells won't be filled
multiple times.

## Validation Before Submission

Always run the visual check:

```bash
soffice --headless --convert-to pdf filled.docx
```

Look for:

1. Page count is roughly equal to the original template (±20% is normal,
   ±50% suggests content overflow or section deletion).
2. No empty cells in mandatory fields.
3. Footer / page number formatting unchanged.
4. CJK characters rendering correctly (not boxes, not Times New Roman
   substitution).
5. Tables not broken across pages mid-row.

## When This Skill Is Not the Right Tool

- **HWP / HWPX input**: convert to `.docx` first
- **PDF form filling**: use the `pdf` skill or a dedicated PDF-form library
- **Free-form research writing**: use `write-paper` or `write-protocol`
- **Slides / presentations**: use `present-paper`
- **Templates with Word "content controls"** (interactive form fields): not
  yet supported by this skill
