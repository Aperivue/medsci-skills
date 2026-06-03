<!-- AUTO-GENERATED from skills/humanize/SKILL.md by scripts/gen_skill_docs.py. Do not edit by hand. -->

# humanize

> Detect and remove AI writing patterns from academic manuscripts and response-to-reviewers letters. Scans for 24 common AI-generated text patterns and rewrites flagged passages to sound naturally human-written while preserving technical accuracy.

**Invoke:** `/humanize` · **Tools:** Read, Write, Edit, Grep, Glob · **Model:** inherit

## When to use

`humanize` activates on requests such as: humanize, AI patterns, AI 문체, remove AI writing, make it sound natural, 자연스럽게, de-AI.

## Quality Card

**Purpose** — Rewrite flagged passages to read as naturally human-written without changing facts, numbers, or citations.

**Safety boundaries**

- Edits style only; never alters numeric values, citations, or scientific meaning.
- Preserves the manuscript's technical claims while removing AI tells.

**Known limitations**

- Pattern detection is heuristic; subtle tells may remain and need a human pass.
- No standalone demo; judgement is required on borderline phrasings.

**Validation**

- `diff against the source to confirm only style changed`
- `/self-review`

**Evidence** — `manual_workflow`

## Bundled resources

**References** (`skills/humanize/references/`):

- `ai_patterns.md`

## Source

Canonical definition: [`skills/humanize/SKILL.md`](../../skills/humanize/SKILL.md)

---

*Part of [MedSci Skills](../../README.md) — Claude Code skills for the medical research lifecycle. This page is generated from the skill's `SKILL.md`; edit that file and re-run `scripts/gen_skill_docs.py`.*
