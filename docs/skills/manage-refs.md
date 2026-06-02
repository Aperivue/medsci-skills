<!-- AUTO-GENERATED from skills/manage-refs/SKILL.md by scripts/gen_skill_docs.py. Do not edit by hand. -->

# manage-refs

> Cross-cutting reference manager for medical manuscripts. Single entry point for citation-key validation, journal-CSL pandoc rendering, manuscript ↔ DOCX cross-reference QC, marker conversion (``[N]`` ↔ ``[@key]``), and native Zotero CWYW field-code injection. Replaces the inline reference-handling that previously lived in ``/write-paper`` Phase 7.6 and is reused by ``/revise``, ``/peer-review``, ``/sync-submission``, and any skill that produces a journal submission. Audit-only verification stays in ``/verify-refs`` — this skill writes (renders, injects, converts); that skill only reads.

**Invoke:** `/manage-refs` · **Tools:** Read, Write, Edit, Bash, Grep, Glob · **Model:** inherit

## When to use

`manage-refs` activates on requests such as: manage-refs, references, citation, citation keys, pandoc citeproc, journal CSL, CSL swap, cascade rejection re-render, cross-reference QC, [@bibkey], Zotero CWYW, ADDIN ZOTERO_ITEM, marker conversion, [N] to [@key], reference manager, render manuscript, check_citation_keys, check_xref.

## Bundled resources

**References** (`skills/manage-refs/references/`):

- `check_xref_symptoms.md`

**Scripts** (`skills/manage-refs/scripts/`):

- `_vendor_citation_writer.py`
- `check_citation_keys.py`
- `check_xref.py`
- `inject_zotero_cwyw.py`
- `md_marker_convert.py`
- `pre_submission_gate.sh`
- `render_pandoc.sh`

## Source

Canonical definition: [`skills/manage-refs/SKILL.md`](../../skills/manage-refs/SKILL.md)

---

*Part of [MedSci Skills](../../README.md) — Claude Code skills for the medical research lifecycle. This page is generated from the skill's `SKILL.md`; edit that file and re-run `scripts/gen_skill_docs.py`.*
