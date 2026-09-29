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

- **HWP / HWPX input**: chain with `hwp-pipeline` first (HWP → HWPX → DOCX)
- **PDF form filling**: use the `pdf` skill or a dedicated PDF-form library
- **Free-form research writing**: use `write-paper` or `write-protocol`
- **Slides / presentations**: use `present-paper`
- **Templates with Word "content controls"** (interactive form fields): not
  yet supported by this skill
