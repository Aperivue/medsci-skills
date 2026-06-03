<!-- AUTO-GENERATED from skills/generate-codebook/SKILL.md by scripts/gen_skill_docs.py. Do not edit by hand. -->

# generate-codebook

> Generate a citable data dictionary / codebook from a tabular dataset (CSV/TSV/Excel/Parquet/Stata/SAS). Profiles every variable — role, type, units placeholder, level frequencies, range/quantiles, missingness — and emits codebook.md + codebook.json. Flags coded variables whose level meanings are unknown as [NEEDS DICTIONARY] rather than guessing them, feeding /define-variables and the dictionary-first workflow.

**Invoke:** `/generate-codebook` · **Tools:** Read, Write, Edit, Bash, Grep, Glob · **Model:** inherit

## When to use

`generate-codebook` activates on requests such as: generate codebook, data dictionary, codebook, profile variables, variable dictionary, describe dataset, what variables, column dictionary, build codebook.

## Quality Card

**Purpose** — Derive a structured codebook (variables, types, ranges, missingness) directly from a dataset.

**Safety boundaries**

- Descriptive statistics are computed from the data by the bundled script, not asserted.
- Variable semantics not present in the data are left blank for the researcher, not invented.

**Known limitations**

- Computes structure and distributions; does not supply clinical meaning of variables.
- Free-text/semantic descriptions require researcher input.

**Validation**

- `python3 scripts/generate_codebook.py <dataset>`

**Evidence** — `bundled_script`

## Bundled resources

**References** (`skills/generate-codebook/references/`):

- `codebook_schema.md`

**Scripts** (`skills/generate-codebook/scripts/`):

- `generate_codebook.py`

## Source

Canonical definition: [`skills/generate-codebook/SKILL.md`](../../skills/generate-codebook/SKILL.md)

---

*Part of [MedSci Skills](../../README.md) — Claude Code skills for the medical research lifecycle. This page is generated from the skill's `SKILL.md`; edit that file and re-run `scripts/gen_skill_docs.py`.*
