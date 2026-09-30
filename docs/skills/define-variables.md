<!-- AUTO-GENERATED from skills/define-variables/SKILL.md by scripts/gen_skill_docs.py. Do not edit by hand. -->

# define-variables

> Use when exposure, outcome, covariate or eligibility definitions and cutoffs need a citable basis before the protocol. Reads the data dictionary first, then maps each variable to a guideline or published definition and the database columns in a citation-backed table.

**Invoke:** `/define-variables` · **Model:** inherit

## When to use

`define-variables` activates on requests such as: variable definition, phenotype definition, operationalization, cutoff justification, inclusion criteria, case definition, grouping criteria, literature-grounded definition, canonical definition, 변수 정의, 정의 근거.

## Quality Card

**Purpose** — Produce a literature-grounded, dictionary-cited operationalization table that prevents ad-hoc phenotype definitions.

**Safety boundaries**

- Every DB variable interpretation quotes the data dictionary verbatim (dictionary-first).
- Cutoffs cite a canonical literature source; unsupported definitions are flagged, not invented.

**Known limitations**

- Quality depends on a complete data dictionary; silent dictionary gaps block definitions.
- No standalone demo; output is reviewed against the dictionary and sources.

**Validation**

- `cross-check each row's dictionary citation against the source dictionary`

**Evidence** — `manual_workflow`

## Bundled resources

**References** (`skills/define-variables/references/`):

- `common_definitions.md`

**Templates** (`skills/define-variables/templates/`):

- `variable_operationalization.md`

## Source

Canonical definition: [`skills/define-variables/SKILL.md`](../../skills/define-variables/SKILL.md)

---

*Part of [MedSci Skills](../../README.md) — Claude Code skills for the medical research lifecycle. This page is generated from the skill's `SKILL.md`; edit that file and re-run `scripts/gen_skill_docs.py`.*
