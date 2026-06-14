<!-- AUTO-GENERATED from skills/polish-language/SKILL.md by scripts/gen_skill_docs.py. Do not edit by hand. -->

# polish-language

> Academic English consistency linting and non-native (ESL) language polish for medical manuscripts. Deterministically flags abbreviation define-once violations, US/UK spelling drift, hyphen-vs-en-dash numeric ranges, P/p case, hyphenation variants, small-number style, and value/unit spacing, then guides a style-only clarity pass that never alters numbers, citations, or scientific meaning. Distinct from humanize (AI-tell removal) and check-reporting (guideline items).

**Invoke:** `/polish-language` · **Tools:** Read, Write, Edit, Grep, Glob, Bash · **Model:** inherit

## When to use

`polish-language` activates on requests such as: polish language, copy-edit, consistency check, ESL, non-native English, house style, abbreviation consistency, en-dash, US UK spelling, proofread manuscript, 일관성 검사, 교정.

## Quality Card

**Purpose** — Standardize house-style consistency and improve non-native clarity without changing facts, numbers, or citations.

**Safety boundaries**

- Edits style only; never alters numeric values, p-values, units, citations, or scientific meaning.
- Deterministic linter is the authority for mechanical issues; no edit without user approval.

**Known limitations**

- Spelling/hyphenation families are a fixed list; uncommon variants may be missed.
- Small-number and abbreviation heuristics can flag intended author choices — triage with the user.

**Validation**

- `python3 scripts/lint_consistency.py <manuscript.md>`
- `bash scripts/lint_challenge/verify.sh  # deterministic, network-free`

**Evidence** — `bundled_script`

## Bundled resources

**Scripts** (`skills/polish-language/scripts/`):

- `lint_challenge/` (4 files)
- `lint_consistency.py`

## Source

Canonical definition: [`skills/polish-language/SKILL.md`](../../skills/polish-language/SKILL.md)

---

*Part of [MedSci Skills](../../README.md) — Claude Code skills for the medical research lifecycle. This page is generated from the skill's `SKILL.md`; edit that file and re-run `scripts/gen_skill_docs.py`.*
