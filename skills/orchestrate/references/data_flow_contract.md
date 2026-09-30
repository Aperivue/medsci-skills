# Data Flow Contract

What each routed skill reads and writes. Load when chaining skills and you need a skill's input or
output files; the Standard Pipeline in SKILL.md already names the files for its own seven steps.

| Skill | Reads | Writes |
|-------|-------|--------|
| deidentify | raw data with PHI (CSV/Excel) | `*_deidentified.*`, `mapping.json`, `audit_log.csv` |
| fulltext-retrieval | DOI list (CSV/text) | `pdfs/*.pdf`, retrieval report |
| analyze-stats | raw data (CSV/Excel) | analysis/tables/*.csv, analysis/figures/*, `analysis/_analysis_outputs.md` |
| make-figures | `analysis/_analysis_outputs.md`, data files | analysis/figures/*.pdf, analysis/figures/*.png, `analysis/figures/_figure_manifest.md` |
| write-paper | analysis/figures/, analysis/tables/, manifests, journal profile | manuscript/manuscript.md, manuscript/title_page.md (DOCX rendering is delegated to manage-refs) |
| check-reporting | manuscript/manuscript.md | qc/reporting_checklist.md |
| verify-refs | manuscript/manuscript.md or a bib input | qc/reference_audit.json (sole writer; see `/verify-refs` §Output Contract) |
| self-review | manuscript/manuscript.md | qc/self_review.md (with JSON block) |
| lit-sync | Zotero collection (live), `manuscript/_src/refs.bib` (Better BibTeX auto-export) | `manuscript/_src/refs.bib` (refreshed), `references/zotero_collection.json`, Obsidian literature notes (sole writer of refs.bib) |
| manage-refs | manuscript/manuscript.md, manuscript/_src/refs.bib, n_to_zotero_key map (optional) | manuscript/manuscript_final.docx (or _cwyw.docx), qc/xref_audit.json (sole writer) |
| render-pdf-doc | non-bib markdown (proposal/briefing/anchor doc/IRB cover) | PDF (same dir, same stem) |
| fill-protocol | content markdown + institutional Word template (.doc/.docx) | filled `*.docx` preserving original styles, table layouts, fonts, geometry |
| fill-icmje-coi | author roster (JSON), seed `coi_disclosure.docx` (synthetic shipped) | per-author `coi_disclosure_{author}.docx` (Date, Name, Manuscript Title replaced) |
| sync-submission | manuscript/, qc/ artifacts, journal profile | submission/{journal}/manifest.md, drift report |
| peer-review | external manuscript (.docx/.pdf), journal scope | review draft (review.md) following the medical imaging peer-review guideline |
