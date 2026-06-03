<!-- AUTO-GENERATED from skills/find-journal/SKILL.md by scripts/gen_skill_docs.py. Do not edit by hand. -->

# find-journal

> Journal recommendation engine for medical manuscripts. 2-pass matching against a curated public profile library plus any user-local private profiles, enriched with detailed write-paper profiles for top-5 output. Returns ranked recommendations with scope fit rationale, AI disclosure policy, and homepage links. No cached IF/APC data — users verify current metrics at journal sites.

**Invoke:** `/find-journal` · **Tools:** Read, Write, Edit, Grep, Glob · **Model:** inherit

## When to use

`find-journal` activates on requests such as: find journal, recommend journal, where to submit, which journal, journal selection, target journal, journal match.

## Quality Card

**Purpose** — Rank candidate journals by scope fit from the curated profile library, with AI-disclosure policy and homepage links.

**Safety boundaries**

- No cached impact-factor/APC values are asserted; users verify current metrics at journal sites.
- Recommendations are drawn from the curated profile library, not invented venues.

**Known limitations**

- Coverage is limited to profiled journals; an unprofiled fit may be missed (add via add-journal).
- Scope-fit ranking is advisory, not an acceptance prediction.

**Validation**

- `verify shortlisted journals' current scope and metrics at their official sites`

**Evidence** — `manual_workflow`

## Bundled resources

**References** (`skills/find-journal/references/`):

- `journal_profiles/` (67 files)

## Source

Canonical definition: [`skills/find-journal/SKILL.md`](../../skills/find-journal/SKILL.md)

---

*Part of [MedSci Skills](../../README.md) — Claude Code skills for the medical research lifecycle. This page is generated from the skill's `SKILL.md`; edit that file and re-run `scripts/gen_skill_docs.py`.*
