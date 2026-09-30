<!-- AUTO-GENERATED from skills/batch-cohort/SKILL.md by scripts/gen_skill_docs.py. Do not edit by hand. -->

# batch-cohort

> Use when one validated cohort analysis must be repeated across many exposure/outcome pairs. Generates one R/Python script per combination from a single methodology template, changing only the variables, and aggregates the results into a summary matrix.

**Invoke:** `/batch-cohort` · **Model:** opus

## When to use

`batch-cohort` activates on requests such as: batch cohort, batch analysis, 대량 분석, 변수 교체, variable swap, mass production, 80명 팀, batch generate, 일괄 코드 생성, exposure outcome matrix, combinatorial analysis.

## Quality Card

**Purpose** — Scale one validated method across many variable combinations, swapping only exposure/outcome, never the method.

**Safety boundaries**

- The methodology is held constant across all generated scripts; deviations are disclosed.
- Generated scripts run on real data; no results are pre-filled.

**Known limitations**

- Inherits the source template's assumptions; a flawed template propagates.
- No standalone demo; outputs are code to be executed and reviewed.

**Validation**

- `execute each generated script and reconcile the summary matrix`
- `/self-review`

**Evidence** — `manual_workflow`

## Bundled resources

**References** (`skills/batch-cohort/references/`):

- `base_template_knhanes.R`
- `batch_template_generator.R`
- `variable_coding_registry.md`

## Source

Canonical definition: [`skills/batch-cohort/SKILL.md`](../../skills/batch-cohort/SKILL.md)

---

*Part of [MedSci Skills](../../README.md) — Claude Code skills for the medical research lifecycle. This page is generated from the skill's `SKILL.md`; edit that file and re-run `scripts/gen_skill_docs.py`.*
