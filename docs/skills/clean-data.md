<!-- AUTO-GENERATED from skills/clean-data/SKILL.md by scripts/gen_skill_docs.py. Do not edit by hand. -->

# clean-data

> Interactive data profiling and cleaning assistant for medical research. Three-stage workflow (profile, flag, code-generate) with user approval gates at each step. Handles missing values, outliers, duplicates, and type mismatches in CSV/Excel clinical data. Does NOT auto-clean — all decisions require researcher confirmation.

**Invoke:** `/clean-data` · **Tools:** Read, Write, Edit, Bash, Grep, Glob · **Model:** inherit

## When to use

`clean-data` activates on requests such as: clean data, data cleaning, data preprocessing, data profiling, missing values, outliers, check my data, data quality.

## Quality Card

**Purpose** — Profile, flag, and code-generate cleaning steps for clinical tabular data, with a researcher approval gate at every stage.

**Safety boundaries**

- Never auto-cleans; every decision (missing values, outliers, dups, types) requires user confirmation.
- All transforms are emitted as reviewable code, not applied silently.

**Known limitations**

- Heuristic flags need clinical judgement; the skill does not decide what is a true outlier.
- No standalone demo; correctness depends on user approvals.

**Validation**

- `re-run the emitted cleaning code and re-profile`
- `/version-dataset for a manifest`

**Evidence** — `manual_workflow`

## Bundled resources

**References** (`skills/clean-data/references/`):

- `cleaning_patterns.md`
- `profiling_template.py`

**Scripts** (`skills/clean-data/scripts/`):

- `check_structural_zero.py`

## Source

Canonical definition: [`skills/clean-data/SKILL.md`](../../skills/clean-data/SKILL.md)

---

*Part of [MedSci Skills](../../README.md) — Claude Code skills for the medical research lifecycle. This page is generated from the skill's `SKILL.md`; edit that file and re-run `scripts/gen_skill_docs.py`.*
