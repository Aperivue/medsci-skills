<!-- AUTO-GENERATED from skills/generate-codebook/SKILL.md by scripts/gen_skill_docs.py. Do not edit by hand. -->

# generate-codebook

> Use when a tabular dataset (CSV, Excel, Parquet, Stata, SAS) needs a data dictionary. Profiles every variable (type, levels, range, missingness) into codebook.md and codebook.json and flags coded values of unknown meaning as [NEEDS DICTIONARY] instead of guessing.

**Invoke:** `/generate-codebook` · **Model:** inherit

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
