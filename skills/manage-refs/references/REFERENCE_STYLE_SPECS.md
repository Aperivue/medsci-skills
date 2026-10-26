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
| **jmir** | J Med Internet Res | **bracket `[1]`**, ranges with a **hyphen** `[2-13]` | **PMID or DOI** (either; not asserted) | **abbrev** | — (AMA 11th recommended) | preprints: **full posting date** | — | official JMIR CSL, not bundled; ✅ verified 2026-10-25 |

**Legend:** ✅ verified against author guide · ⚠ inherited from Zotero, not yet
confirmed against the journal's Instructions for Authors. Confirm and update the
row (and `check_csl_render.py::SPECS`) when you next submit to that journal.

`check_csl_render.py` checks the in-text format, DOI presence and journal abbreviation only. The
other columns (et-al, date, issue, hyphenated ranges) are not checked by any script; read the
rendered reference list against them.

## Known pitfalls (from JKMS submission, 2026-06-03)

1. **Journal abbreviation needs metadata.** CSL `container-title form="short"` only
   works if the `.bib` entry has a `shortjournal` (BibLaTeX) / `journalAbbreviation`
   (Zotero) field. Without it, the full name is printed regardless of CSL. Use
   `scripts/fill_journal_abbrev.py` to populate abbreviations from PubMed (NLM), then
   CrossRef for journals PubMed does not index; it names every CrossRef value, which is often
   ISO 4 with periods ("J. Stat. Soft.") rather than the NLM form ("J Stat Softw"), so check
   those against the NLM Catalog. In a Better BibTeX-managed bib, fill Zotero's "Journal Abbr"
   field instead: the next export overwrites the file.
2. **Title proper nouns.** pandoc/citeproc applies sentence-case to titles and will
   lowercase proper nouns (`Fleischner Society` → `fleischner society`) unless the
   title is double-braced `title = {{...}}`. Pull authoritative titles (with
   subtitle + proper-noun casing) from PubMed efetch ArticleTitle. Bracing the whole title also
   stops the sentence-casing a style asks for; to keep it, brace only the proper nouns
   (`{Bard}`, `{Advances in Neural Information Processing Systems}`).
3. **Name particles.** `de Torres`, `von Elm`, `de Bock` get demoted to
   `Torres JP de` unless braced `{de Torres}` in the family field. `demote-non-dropping-particle="never"`
   alone is insufficient because citeproc auto-splits lowercase particles: pandoc reads
   `von Elm, Erik` with `von` as a dropping particle, which a style prints after the initials.
4. **DOI hyperlinks survive surgical docx edits.** If you swap reference text in a
   Word file, a `<w:hyperlink>` carrying the DOI persists as a separate element
   (python-docx `p.runs` doesn't see it). Remove hyperlinks explicitly.

## Known pitfalls (JMIR house style, checked 2026-10-25)

5. **Preprint posting date.** A `@misc` arXiv entry renders its year only under the JMIR CSL,
   even with a full `date`. What printed the date (pandoc 3.9, JMIR CSL updated 2024-08-31):
   `@article` with `journal = {arXiv}`, `date = {2025-01-15}` and the arXiv DOI
   (`10.48550/arXiv.<id>`), rendering `arXiv 2025 Jan 15; doi: ...`.
6. **Citation ranges with a hyphen.** The CSL collapses `[2, 3, 4]` to `[2–4]` with an
   en dash. Adding the CSL term `citation-range-delimiter` changed nothing under pandoc 3.9, so a
   journal that wants `[2-4]` needs the rendered output post-processed. Change only the
   citation numbers: a range typed inside the citation (`[see 10–20 @key]`) is the author's text.
7. **URL printed twice.** `howpublished = {\url{...}}` together with `url = {...}` prints the
   address twice; keep `url` alone.

## Related
- `scripts/check_csl_render.py` — acceptance test
- `scripts/fill_journal_abbrev.py` — journal abbreviation injection (PubMed NLM, CrossRef fallback)
- `citation_styles/journal-of-korean-medical-science-strict.csl` — JKMS author-guide-faithful variant
