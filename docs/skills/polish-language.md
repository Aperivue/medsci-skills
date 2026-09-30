<!-- AUTO-GENERATED from skills/polish-language/SKILL.md by scripts/gen_skill_docs.py. Do not edit by hand. -->

# polish-language

> Use when a manuscript needs a copy-edit for consistency and non-native English clarity. Flags abbreviation, US/UK spelling, en-dash range, P/p, hyphenation, number-style and unit-spacing issues, then polishes style only. AI-tell removal is /humanize.

**Invoke:** `/polish-language` · **Tools:** Read, Write, Edit, Grep, Glob, Bash · **Model:** inherit

## When to use

`polish-language` activates on requests such as: polish language, copy-edit, consistency check, ESL, non-native English, house style, abbreviation consistency, en-dash, US UK spelling, proofread manuscript, 일관성 검사, 교정.

## Quality Card

**Purpose** — Standardize house-style consistency and improve non-native clarity without changing facts, numbers, or citations.

**Safety boundaries**

- Edits style only; never alters numeric values, p-values, units, citations, or scientific meaning.
- Linter findings remain advisory and need contextual review; no edit without user approval.

**Known limitations**

- Spelling/hyphenation families are a fixed list; uncommon variants may be missed.
- Small-number and abbreviation heuristics can flag intended author choices — triage with the user.

**Validation**

- `python3 scripts/lint_consistency.py <manuscript.md>`
- `bash scripts/lint_challenge/verify.sh  # deterministic, network-free`
- `python3 tests/test_consistency_controls.py`
- `python3 scripts/lint_figure_locale.py --manuscript <manuscript.md> --figures-dir <figures/>`
- `bash scripts/lint_figure_locale_challenge/verify.sh  # deterministic, network-free`

**Evidence** — `bundled_script`

## Bundled resources

**Scripts** (`skills/polish-language/scripts/`):

- `lint_challenge/` (6 files)
- `lint_consistency.py`
- `lint_figure_locale.py`
- `lint_figure_locale_challenge/` (2 files)

## Source

Canonical definition: [`skills/polish-language/SKILL.md`](../../skills/polish-language/SKILL.md)

---

*Part of [MedSci Skills](../../README.md) — Claude Code skills for the medical research lifecycle. This page is generated from the skill's `SKILL.md`; edit that file and re-run `scripts/gen_skill_docs.py`.*
