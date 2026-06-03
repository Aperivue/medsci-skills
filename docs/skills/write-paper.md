<!-- AUTO-GENERATED from skills/write-paper/SKILL.md by scripts/gen_skill_docs.py. Do not edit by hand. -->

# write-paper

> Full-pipeline medical/scientific paper writing. 8-phase IMRAD workflow from outline to submission-ready manuscript. Supports original articles, case reports, meta-analyses, AI validation studies, animal studies, and technical notes. Do NOT trigger for self-checking (use self-review instead).

**Invoke:** `/write-paper` · **Tools:** Read, Write, Edit, Bash, Grep, Glob · **Model:** inherit

## When to use

`write-paper` activates on requests such as: write paper, manuscript, draft paper, start writing, write methods, write results, write discussion, write introduction.

## Quality Card

**Purpose** — Draft a submission-ready IMRAD manuscript or section from approved project inputs (8-phase workflow).

**Safety boundaries**

- Never generates references from memory; citations come from search-lit and are checked by verify-refs.
- Never silently edits a frozen submission; branches to v_(N+1) instead.
- Numerical claims are audited against approved tables before submission (Step 7.3a).

**Known limitations**

- Reference integrity depends on verify-refs (PubMed/CrossRef); offline runs degrade to manual checking.
- Drafts the user's own manuscript only; not for self-critique (self-review), reviewer response (revise), or external review (peer-review).

**Validation**

- `/verify-refs --strict`
- `/self-review`

**Evidence** — `demo`

## Bundled resources

**References** (`skills/write-paper/references/`):

- `journal_profiles/` (54 files)
- `paper_types/` (9 files)
- `section_guides/` (7 files)
- `section_templates/` (1 file)

## Source

Canonical definition: [`skills/write-paper/SKILL.md`](../../skills/write-paper/SKILL.md)

---

*Part of [MedSci Skills](../../README.md) — Claude Code skills for the medical research lifecycle. This page is generated from the skill's `SKILL.md`; edit that file and re-run `scripts/gen_skill_docs.py`.*
