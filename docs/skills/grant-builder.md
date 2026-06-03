<!-- AUTO-GENERATED from skills/grant-builder/SKILL.md by scripts/gen_skill_docs.py. Do not edit by hand. -->

# grant-builder

> Grant and challenge proposal support for radiology and medical AI projects. Structures significance, innovation, approach, milestones, and consortium roles while keeping claims evidence-based and executable.

**Invoke:** `/grant-builder` · **Tools:** Read, Write, Edit, Bash, Grep, Glob · **Model:** inherit

## When to use

`grant-builder` activates on requests such as: grant, proposal, aims page, grant proposal, significance, innovation, approach, milestones, 산학과제, 산학협력, 과제계획서, 연구계획서, 연구비 신청, 첨부3.

## Quality Card

**Purpose** — Structure a fundable, executable proposal whose claims are evidence-based and whose milestones are realistic.

**Safety boundaries**

- Claims are tied to evidence the user supplies; preliminary data and citations are not invented.
- Milestones are scoped to be executable, not aspirational.

**Known limitations**

- Does not guarantee funding; tailoring to a specific reviewer panel is the user's responsibility.
- No standalone demo; content requires PI review.

**Validation**

- `/verify-refs --strict on any cited work`
- `/self-review for internal consistency`

**Evidence** — `manual_workflow`

## Source

Canonical definition: [`skills/grant-builder/SKILL.md`](../../skills/grant-builder/SKILL.md)

---

*Part of [MedSci Skills](../../README.md) — Claude Code skills for the medical research lifecycle. This page is generated from the skill's `SKILL.md`; edit that file and re-run `scripts/gen_skill_docs.py`.*
