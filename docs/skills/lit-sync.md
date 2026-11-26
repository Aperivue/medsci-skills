<!-- AUTO-GENERATED from skills/lit-sync/SKILL.md by scripts/gen_skill_docs.py. Do not edit by hand. -->

# lit-sync

> Use when references (a .bib from /search-lit, a DOI/PMID list or a PDF folder) should land in Zotero and keep the manuscript refs.bib current. Adds items without duplicates, files them into the project collection and sets up the Better BibTeX auto-export. Obsidian notes are /obsidian-paper-vault.

**Invoke:** `/lit-sync`

## When to use

`lit-sync` activates on requests such as: lit-sync, 문헌 동기화, 레퍼런스 정리, lit sync, Zotero 동기화, Zotero에 등록, PDF 폴더 Zotero, reference sync, refs.bib 갱신.

## Quality Card

**Purpose** — Add verified references (.bib, DOI/PMID list or PDF folder) to Zotero without duplicates and keep refs.bib current through Better BibTeX; audit vault citekeys against the library.

**Safety boundaries**

- Bibliographic metadata is never fabricated; only Better BibTeX may write refs.bib.
- Writes no Obsidian notes (that is /obsidian-paper-vault); PDFs from a folder are added only after the user reviews a dry-run list.

**Known limitations**

- Depends on a connected Zotero MCP + Better BibTeX auto-export; degrades to manual without them.
- No standalone demo; effects are in the user's Zotero library.

**Validation**

- `confirm refs.bib mtime refreshed via Better BibTeX`
- `zotero_find_duplicates after sync`
- `bash skills/lit-sync/tests/citekey_provenance_challenge.sh`
- `bash skills/lit-sync/tests/citekey_provenance_challenge_selftest.sh`

**Evidence** — `manual_workflow`

## Bundled resources

**References** (`skills/lit-sync/references/`):

- `bbt_autoexport.md`
- `bbt_lookup.md`
- `fulltext_report.md`
- `pdf_folder_ingest.md`
- `zotero_mcp_tools.md`

**Scripts** (`skills/lit-sync/scripts/`):

- `check_citekey_provenance.py`

## Source

Canonical definition: [`skills/lit-sync/SKILL.md`](../../skills/lit-sync/SKILL.md)

---

*Part of [MedSci Skills](../../README.md) — Claude Code skills for the medical research lifecycle. This page is generated from the skill's `SKILL.md`; edit that file and re-run `scripts/gen_skill_docs.py`.*
