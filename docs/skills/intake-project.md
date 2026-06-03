<!-- AUTO-GENERATED from skills/intake-project/SKILL.md by scripts/gen_skill_docs.py. Do not edit by hand. -->

# intake-project

> Intake and normalize a new radiology research project. Classifies project type, summarizes current state, identifies missing inputs, recommends next steps, and scaffolds lightweight project memory files.

**Invoke:** `/intake-project` · **Tools:** Read, Write, Edit, Bash, Grep, Glob · **Model:** inherit

## When to use

`intake-project` activates on requests such as: new project, intake project, project intake, classify project, organize project, what is this project.

## Quality Card

**Purpose** — Normalize a new or messy project into a classified, summarized starting point with scaffolded memory.

**Safety boundaries**

- Scaffolds new lightweight files; does not overwrite existing project artifacts.
- Flags missing inputs rather than inventing them.

**Known limitations**

- Classification is heuristic and may need correction on unusual projects.
- No standalone demo; a setup step, not an analysis.

**Validation**

- `review the scaffolded files and correct the classification if needed`

**Evidence** — `manual_workflow`

## Source

Canonical definition: [`skills/intake-project/SKILL.md`](../../skills/intake-project/SKILL.md)

---

*Part of [MedSci Skills](../../README.md) — Claude Code skills for the medical research lifecycle. This page is generated from the skill's `SKILL.md`; edit that file and re-run `scripts/gen_skill_docs.py`.*
