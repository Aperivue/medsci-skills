<!-- AUTO-GENERATED from skills/orchestrate/SKILL.md by scripts/gen_skill_docs.py. Do not edit by hand. -->

# orchestrate

> General-purpose research orchestrator. Routes ambiguous or multi-step requests to the right skill(s) from the medsci-skills bundle. Use when the user describes a research goal without naming a specific skill, or when a task spans multiple skills.

**Invoke:** `/orchestrate` · **Tools:** Read, Write, Edit, Bash, Grep, Glob · **Model:** inherit

## When to use

`orchestrate` activates on requests such as: orchestrate, research help, what should I do next, where do I start, help me with my paper, run the pipeline, which skill, end-to-end, e2e.

## Quality Card

**Purpose** — Single entry point for the bundle: classify a request and route to the right skill, or chain skills for multi-step and end-to-end (--e2e) workflows.

**Safety boundaries**

- Never generates worker-skill outputs directly; routes to and invokes the owning skill.
- Does not bypass per-skill artifact validation in the chain.

**Known limitations**

- Routing is heuristic; an ambiguous request may need explicit skill selection.
- --e2e halts on missing expected outputs rather than proceeding with gaps.

**Validation**

- `python3 scripts/validate_skill_contracts.py`
- `python3 scripts/validate_project_contract.py`

**Evidence** — `demo`

## Bundled resources

**References** (`skills/orchestrate/references/`):

- `dialogue_nodes.md`
- `report_template.md`

## Source

Canonical definition: [`skills/orchestrate/SKILL.md`](../../skills/orchestrate/SKILL.md)

---

*Part of [MedSci Skills](../../README.md) — Claude Code skills for the medical research lifecycle. This page is generated from the skill's `SKILL.md`; edit that file and re-run `scripts/gen_skill_docs.py`.*
