<!-- AUTO-GENERATED from skills/manage-refs/SKILL.md by scripts/gen_skill_docs.py. Do not edit by hand. -->

# manage-refs

> Use when references must be written, rendered or converted. Checks [@key] citation keys, renders the reference list with a journal CSL via pandoc, converts [N] markers, injects Zotero Word field codes and runs manuscript-DOCX cross-reference QC. Read-only auditing is /verify-refs.

**Invoke:** `/manage-refs` · **Tools:** Read, Write, Edit, Bash, Grep, Glob · **Model:** inherit

## When to use

`manage-refs` activates on requests such as: manage-refs, references, citation, citation keys, pandoc citeproc, journal CSL, CSL swap, cascade rejection re-render, cross-reference QC, [@bibkey], Zotero CWYW, ADDIN ZOTERO_ITEM, marker conversion, [N] to [@key], reference manager, render manuscript, check_citation_keys, check_xref.

## Quality Card

**Purpose** — Manage the reference lifecycle: citekey validation, CSL rendering (pandoc citeproc), Zotero CWYW injection, marker conversion, and cross-reference QC.

**Safety boundaries**

- References are never hand-typed; only Better BibTeX / citeproc / CWYW produce the list.
- Citekeys are validated against the .bib; unmapped markers are not guessed; CWYW docx is not regex-patched.

**Known limitations**

- Pandoc/Zotero must be installed; rendering is deterministic but environment-dependent.
- Phase 3 CWYW field safety depends on a correct Zotero library.

**Validation**

- `python3 scripts/check_citation_keys.py manuscript.md refs.bib`
- `bash tests/test_bib_title_markup.sh`
- `python3 scripts/check_xref.py --md manuscript.md --docx out.docx --strict`

**Evidence** — `bundled_script`

## Bundled resources

**References** (`skills/manage-refs/references/`):

- `REFERENCE_STYLE_SPECS.md`
- `check_xref_symptoms.md`

**Scripts** (`skills/manage-refs/scripts/`):

- `_vendor_citation_writer.py`
- `check_bib_title_markup.py`
- `check_citation_keys.py`
- `check_citation_keys_challenge/` (4 files)
- `check_csl_render.py`
- `check_reference_duplication.py`
- `check_xref.py`
- `fill_journal_abbrev.py`
- `inject_zotero_cwyw.py`
- `md_marker_convert.py`
- `pre_submission_gate.sh`
- `render_pandoc.sh`
- `strip_source_metadata.lua`

## Source

Canonical definition: [`skills/manage-refs/SKILL.md`](../../skills/manage-refs/SKILL.md)

---

*Part of [MedSci Skills](../../README.md) — Claude Code skills for the medical research lifecycle. This page is generated from the skill's `SKILL.md`; edit that file and re-run `scripts/gen_skill_docs.py`.*
