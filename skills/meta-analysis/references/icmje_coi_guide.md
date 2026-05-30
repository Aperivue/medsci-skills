# ICMJE COI Form Generation Guide

## Overview

Most journals (Springer/CVIR, Lancet, npj, etc.) require ICMJE Conflict of Interest
disclosure forms from all authors. This guide documents how to batch-generate pre-filled
forms using `python-docx`.

## Template Location

Use any existing blank ICMJE form as template. Suggested locations:
- A previously-used filled form from one of your manuscripts (under `<project>/submission/{journal}/icmje_forms/`).
- Download a blank from https://www.icmje.org/disclosure-of-interest/.

## ICMJE Form Structure (docx)

```
Table 0 (Header): 6 rows × 2 cols
  Row 0: Title ("ICMJE DISCLOSURE FORM")
  Row 1: Date
  Row 2: Author name        ← PRE-FILL THIS
  Row 3: Manuscript title    ← PRE-FILL THIS
  Row 4: Manuscript number   ← Leave blank or fill if known
  Row 5: Instructions text

Table 1 (Disclosures): 19 rows × 5 cols
  Row 0: Column headers
  Row 1: Time frame header (since initial planning)
  Row 2: Item 1 — Support for present manuscript
  Row 3: Time frame header (past 36 months)
  Rows 4-15: Items 2-13 (grants, royalties, consulting, etc.)
    → Col 3: Entity name (leave blank if no conflict)
    → Col 4: Specifications (leave blank if no conflict)
  Row 16: Empty
  Row 17: Certification header
  Row 18: Certification text  ← ADD "X" to certify
```

## Python Script: Batch Generate

```python
#!/usr/bin/env python3
"""Batch-generate ICMJE COI forms from a template."""
import shutil
from pathlib import Path
from docx import Document

def generate_coi_forms(
    template_path: str,
    output_dir: str,
    manuscript_title: str,
    authors: list[tuple[str, str]],  # [(name, email), ...]
    manuscript_number: str = "",
    date_str: str = "",
):
    """
    Generate one ICMJE COI form per author.
    
    KNOWN ISSUES (python-docx + ICMJE form):
    1. Merged cells: Table 0 Row 0 and Table 1 headers use merged cells.
       Writing to cell.text replaces ALL merged cell content.
       → Use cell.paragraphs[0].runs approach instead.
    2. Formatting loss: Direct cell.text assignment strips bold/italic.
       → Preserve runs and only modify run.text.
    3. XML namespace errors: Some ICMJE forms have custom XML.
       python-docx may warn about "lxml.etree.XMLSyntaxError".
       → These warnings are usually harmless; the output is still valid.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    
    for i, (name, email) in enumerate(authors, 1):
        # Copy template to preserve all formatting
        fname = f"ICMJE_COI_{i:02d}_{name.replace(' ', '_')}.docx"
        dst = out / fname
        shutil.copy2(template_path, dst)
        
        doc = Document(str(dst))
        t0 = doc.tables[0]
        
        # Pre-fill header fields
        # IMPORTANT: Access the cell, find existing text, append to it
        # Don't replace — some cells have label + value in same cell
        
        # Row 1: Date
        if date_str:
            _safe_append(t0.rows[1].cells[0], f" {date_str}")
        
        # Row 2: Author name
        _safe_append(t0.rows[2].cells[0], f" {name}")
        
        # Row 3: Manuscript title
        _safe_append(t0.rows[3].cells[0], f" {manuscript_title}")
        
        # Row 4: Manuscript number
        if manuscript_number:
            _safe_append(t0.rows[4].cells[0], f" {manuscript_number}")
        
        doc.save(str(dst))
        print(f"  Created: {fname}")
    
    print(f"\nGenerated {len(authors)} COI forms in {output_dir}")


def _safe_append(cell, text):
    """Append text to a cell without destroying existing formatting.
    
    This avoids the common python-docx pitfall where cell.text = "new"
    destroys all runs and formatting in merged cells.
    """
    if cell.paragraphs:
        p = cell.paragraphs[0]
        if p.runs:
            # Append to last run to preserve formatting
            p.runs[-1].text += text
        else:
            # No runs — add one
            run = p.add_run(text)
    else:
        cell.text = text


# === Example usage ===
if __name__ == "__main__":
    # Replace with the actual author roster for your manuscript.
    authors = [
        ("Author One", "author1@example.com"),
        ("Author Two", "author2@example.com"),
        ("Author Three", "author3@example.com"),
        # ...
    ]

    generate_coi_forms(
        template_path="path/to/blank_ICMJE_template.docx",
        output_dir="submission/{journal}/icmje_coi_forms/",
        manuscript_title="Your Manuscript Title Here",
        authors=authors,
        date_str="YYYY-MM-DD",
    )
```

## Common Pitfalls

### 1. Merged Cell Destruction
**Problem**: `cell.text = "new value"` on a merged cell deletes content in ALL merged cells.
**Fix**: Use `_safe_append()` or access `cell.paragraphs[0].runs[-1].text`.

### 2. XML/SQL-like Errors
**Problem**: `lxml.etree.XMLSyntaxError` when opening some ICMJE forms.
This happens because ICMJE's official template contains custom XML namespaces
that python-docx doesn't fully support.
**Fix**: These warnings are cosmetic. The output file is still valid Word doc.
If errors persist, use `shutil.copy2()` first, then open the copy.

### 3. Formatting Loss on Save
**Problem**: Bold/italic disappears after saving.
**Fix**: Never assign to `cell.text` directly. Always work through
`cell.paragraphs[0].runs` to preserve formatting.

### 4. Empty Cells for "No Conflict"
**Problem**: Some journals want explicit "None" vs empty cell.
**Fix**: Check journal-specific requirements. CVIR (Springer) accepts empty cells.

## Workflow for New Projects

1. Copy any existing ICMJE form as template (or download blank from icmje.org)
2. Update `authors` list with names and emails
3. Update `manuscript_title`
4. Run script → generates N individual docx files
5. Send to co-authors for review/signature
6. Collect signed forms before submission

## Author Email List (JSON format)

Store alongside COI forms for reference:
```json
[
  ["Author Name", "email@example.com"],
  ...
]
```
