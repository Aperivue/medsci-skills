<!-- AUTO-GENERATED from skills/lit-sync/SKILL.md by scripts/gen_skill_docs.py. Do not edit by hand. -->

# lit-sync

> Use when references in a .bib file (often from /search-lit) should land in Zotero and Obsidian. Syncs them to the Zotero library, writes Obsidian literature notes and extracts cross-cutting concept notes once enough accumulate. A folder of PDFs is /obsidian-paper-vault.

**Invoke:** `/lit-sync` · **Model:** inherit

## When to use

`lit-sync` activates on requests such as: lit-sync, 문헌 동기화, 레퍼런스 정리, 개념 노트 추출, lit sync, Zotero 동기화, reference sync, 참고문헌 옵시디언.

## Quality Card

**Purpose** — Sync verified references from .bib into Zotero and Obsidian literature notes, extracting cross-cutting concept notes when enough literature accumulates.

**Safety boundaries**

- Bibliographic metadata is never fabricated; only Better BibTeX may write refs.bib.
- Existing literature notes are not overwritten.

**Known limitations**

- Depends on a connected Zotero MCP + Better BibTeX auto-export; degrades to manual without them.
- No standalone demo; effects are in the user's Zotero/Obsidian.

**Validation**

- `confirm refs.bib mtime refreshed via Better BibTeX`
- `zotero_find_duplicates after sync`
- `bash skills/lit-sync/tests/citekey_provenance_challenge.sh`
- `bash skills/lit-sync/tests/citekey_provenance_challenge_selftest.sh`

**Evidence** — `manual_workflow`

## Bundled resources

**References** (`skills/lit-sync/references/`):

- `bbt_lookup.md`
- `concept_note_template.md`
- `fulltext_report.md`
- `locale/` (1 file)

**Scripts** (`skills/lit-sync/scripts/`):

- `check_citekey_provenance.py`

## Source

Canonical definition: [`skills/lit-sync/SKILL.md`](../../skills/lit-sync/SKILL.md)

---

*Part of [MedSci Skills](../../README.md) — Claude Code skills for the medical research lifecycle. This page is generated from the skill's `SKILL.md`; edit that file and re-run `scripts/gen_skill_docs.py`.*
