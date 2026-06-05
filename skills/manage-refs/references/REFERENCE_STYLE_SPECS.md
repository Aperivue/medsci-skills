# Journal Reference-Style Specs (CSL acceptance criteria)

Zotero-sourced CSL files are **not** auto-validated against each journal's author
guide. A dependent (stub) CSL inherits its parent's format, which can differ from
what the journal requires. This table is the **acceptance criteria** for
`scripts/check_csl_render.py` — run it BEFORE submission so format mismatches are
caught at build time, not in the portal proof PDF.

## How to use

```bash
# Validate a CSL against a journal spec before rendering the manuscript:
python scripts/check_csl_render.py --csl citation_styles/<file>.csl \
    --bib refs.bib --journal <key>
# Exits non-zero on mismatch (in-text format / DOI / abbreviation).
```

If a journal's stub CSL fails (parent format ≠ author guide), create a
`-strict` variant (see `journal-of-korean-medical-science-strict.csl`) and use it
for the pandoc render while keeping the original for Zotero CWYW.

## Spec table

| key | Journal | in-text | DOI | journal name | et-al | date | issue | CSL status |
|-----|---------|---------|-----|--------------|-------|------|-------|-----------|
| **jkms** | J Korean Med Sci | **superscript** | **none** | **NLM abbrev** | ≤6 then et al | **year only** | include `(n)` | stub→**use `-strict`** ✅ verified 2026-06-03 |
| radiology | Radiology (RSNA) | paren `(1)` | yes | abbrev | — | — | — | full; ⚠ VERIFY vs author guide |
| ajr | Am J Roentgenol | superscript | none | abbrev | — | — | — | full; ⚠ VERIFY |
| kjr | Korean J Radiol | superscript | none | abbrev | — | — | — | full; ⚠ VERIFY |
| eur-radiol | European Radiology | bracket `[1]` | yes | full ok | — | — | — | stub→springer-basic; ⚠ VERIFY |
| cvir | Cardiovasc Intervent Radiol | bracket `[1]` | yes | full ok | — | — | — | stub→springer-vancouver; ⚠ VERIFY |

**Legend:** ✅ verified against author guide · ⚠ inherited from Zotero, not yet
confirmed against the journal's Instructions for Authors. Confirm and update the
row (and `check_csl_render.py::SPECS`) when you next submit to that journal.

## Known pitfalls (from JKMS submission, 2026-06-03)

1. **Journal abbreviation needs metadata.** CSL `container-title form="short"` only
   works if the `.bib` entry has a `shortjournal` (BibLaTeX) / `journalAbbreviation`
   (Zotero) field. Without it, the full name is printed regardless of CSL. Use
   `scripts/fill_journal_abbrev.py` to populate NLM abbreviations from PubMed.
2. **Title proper nouns.** pandoc/citeproc applies sentence-case to titles and will
   lowercase proper nouns (`Fleischner Society` → `fleischner society`) unless the
   title is double-braced `title = {{...}}`. Pull authoritative titles (with
   subtitle + proper-noun casing) from PubMed efetch ArticleTitle.
3. **Name particles.** `de Torres`, `von Elm`, `de Bock` get demoted to
   `Torres JP de` unless braced `{de Torres}` in the family field. `demote-non-dropping-particle="never"`
   alone is insufficient because citeproc auto-splits lowercase particles.
4. **DOI hyperlinks survive surgical docx edits.** If you swap reference text in a
   Word file, a `<w:hyperlink>` carrying the DOI persists as a separate element
   (python-docx `p.runs` doesn't see it). Remove hyperlinks explicitly. See
   `~/.claude/rules/submission-portal-verification.md` §1.

## Related
- `scripts/check_csl_render.py` — acceptance test
- `scripts/fill_journal_abbrev.py` — NLM abbreviation injection
- `citation_styles/journal-of-korean-medical-science-strict.csl` — JKMS author-guide-faithful variant
- `~/.claude/rules/manuscript-references.md` — hybrid pandoc/Zotero workflow
