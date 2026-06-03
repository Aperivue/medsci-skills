<!-- AUTO-GENERATED from skills/manage-project/SKILL.md by scripts/gen_skill_docs.py. Do not edit by hand. -->

# manage-project

> Research project management for medical manuscripts. Scaffold project structure, track writing progress across phases, maintain project memory files, generate submission checklists and backwards timelines. Commands: init, status, sync-memory, checklist, timeline.

**Invoke:** `/manage-project` · **Tools:** Read, Write, Edit, Bash, Grep, Glob · **Model:** inherit

## When to use

`manage-project` activates on requests such as: manage project, project init, project status, submission checklist, project scaffold, create project, new paper project.

## Quality Card

**Purpose** — Track and scaffold a manuscript project across phases with checklists and timelines from real project state.

**Safety boundaries**

- Reads/writes project state and scaffolding; never edits canonical manuscript artifacts.
- Status and timelines reflect actual project files, not invented progress.

**Known limitations**

- Timelines are planning aids, not commitments; depend on user-maintained state.
- No standalone demo; an orchestration/tracking utility.

**Validation**

- `reconcile reported phase against the project's SSOT/artifacts`

**Evidence** — `manual_workflow`

## Bundled resources

**References** (`skills/manage-project/references/`):

- `pre_submission_checklist.md`
- `project_state_template.json`
- `scaffold_templates.md`
- `status_output_format.md`
- `timeline_example.md`

**Templates** (`skills/manage-project/templates/`):

- `SSOT.yaml.template`

## Source

Canonical definition: [`skills/manage-project/SKILL.md`](../../skills/manage-project/SKILL.md)

---

*Part of [MedSci Skills](../../README.md) — Claude Code skills for the medical research lifecycle. This page is generated from the skill's `SKILL.md`; edit that file and re-run `scripts/gen_skill_docs.py`.*
