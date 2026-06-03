<!-- AUTO-GENERATED from skills/design-study/SKILL.md by scripts/gen_skill_docs.py. Do not edit by hand. -->

# design-study

> Study design and validity review for radiology and medical AI research. Identifies analysis unit, cohort logic, leakage risks, comparator design, validation strategy, and reporting guideline fit before drafting or submission.

**Invoke:** `/design-study` · **Tools:** Read, Write, Edit, Bash, Grep, Glob · **Model:** inherit

## When to use

`design-study` activates on requests such as: study design, leakage check, cohort design, analysis plan, validation strategy, comparator design, bias check.

## Quality Card

**Purpose** — Surface design and validity risks (leakage, analysis unit, comparator, validation strategy) before a study is built or written.

**Safety boundaries**

- Advisory only: writes decision notes, not analysis or manuscript artifacts.
- Names validity threats explicitly rather than rubber-stamping a design.

**Known limitations**

- A review reduces but cannot eliminate design risk; it is not a guarantee of validity.
- No standalone demo; recommendations require researcher judgement.

**Validation**

- `carry findings into write-protocol Methods and re-check with /self-review`

**Evidence** — `manual_workflow`

## Source

Canonical definition: [`skills/design-study/SKILL.md`](../../skills/design-study/SKILL.md)

---

*Part of [MedSci Skills](../../README.md) — Claude Code skills for the medical research lifecycle. This page is generated from the skill's `SKILL.md`; edit that file and re-run `scripts/gen_skill_docs.py`.*
