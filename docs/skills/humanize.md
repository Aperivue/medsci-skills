<!-- AUTO-GENERATED from skills/humanize/SKILL.md by scripts/gen_skill_docs.py. Do not edit by hand. -->

# humanize

> Use when a manuscript or response-to-reviewers letter reads as AI-written. Scans for 27 AI writing patterns and rewrites flagged passages, preserving technical accuracy and bounding how much text changes. Not general copy-editing; that is /polish-language.

**Invoke:** `/humanize` · **Model:** inherit

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
- Patterns 1-18 are inherited from an external list; their thresholds are conventional, not measured on a medical corpus.

**Validation**

- `scripts/check_rewrite_fidelity.py --before <pre> --after <post> --strict`
- `scripts/check_sentence_variety.py --manuscript <file>`
- `/self-review`

**Evidence** — `manual_workflow`

## Bundled resources

**References** (`skills/humanize/references/`):

- `ai_patterns.md`

**Scripts** (`skills/humanize/scripts/`):

- `check_rewrite_fidelity.py`
- `check_sentence_variety.py`

## Source

Canonical definition: [`skills/humanize/SKILL.md`](../../skills/humanize/SKILL.md)

---

*Part of [MedSci Skills](../../README.md) — Claude Code skills for the medical research lifecycle. This page is generated from the skill's `SKILL.md`; edit that file and re-run `scripts/gen_skill_docs.py`.*
