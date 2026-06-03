<!-- AUTO-GENERATED from skills/replicate-study/SKILL.md by scripts/gen_skill_docs.py. Do not edit by hand. -->

# replicate-study

> Replicate an existing cohort study's methodology on a different database. Extracts study design from a source paper, maps variables to the target DB via harmonization table, generates analysis code, and produces a replication difference report.

**Invoke:** `/replicate-study` · **Tools:** Read, Write, Edit, Bash, Grep, Glob · **Model:** opus

## When to use

`replicate-study` activates on requests such as: replicate study, replicate paper, 논문 복제, 방법론 복제, reproduce study, replication, 다른 DB로, swap database, 데이터 교체.

## Quality Card

**Purpose** — Re-run a published study's method on a new DB and report exactly where target-DB constraints forced deviations.

**Safety boundaries**

- Method deviations forced by the target DB are documented in a difference report, not hidden.
- Results come from executed code on the target data.

**Known limitations**

- Perfect replication is rarely possible; residual method differences remain and are disclosed.
- No standalone demo; depends on a faithful variable mapping.

**Validation**

- `execute the replication code and review the difference report`
- `/self-review`

**Evidence** — `manual_workflow`

## Bundled resources

**References** (`skills/replicate-study/references/`):

- `harmonization_3country.csv`
- `harmonization_knhanes_nhanes.csv`
- `methodology_extraction_template.md`

## Source

Canonical definition: [`skills/replicate-study/SKILL.md`](../../skills/replicate-study/SKILL.md)

---

*Part of [MedSci Skills](../../README.md) — Claude Code skills for the medical research lifecycle. This page is generated from the skill's `SKILL.md`; edit that file and re-run `scripts/gen_skill_docs.py`.*
