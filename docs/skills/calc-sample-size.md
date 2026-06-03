<!-- AUTO-GENERATED from skills/calc-sample-size/SKILL.md by scripts/gen_skill_docs.py. Do not edit by hand. -->

# calc-sample-size

> Interactive sample size calculator for medical research. Decision-tree guided test selection, reproducible R/Python code, effect size interpretation, and IRB-ready justification text. Supports diagnostic accuracy, agreement, proportions, continuous outcomes, survival, ANOVA, logistic regression, and non-inferiority/equivalence designs.

**Invoke:** `/calc-sample-size` · **Tools:** Read, Write, Edit, Bash, Grep, Glob · **Model:** inherit

## When to use

`calc-sample-size` activates on requests such as: sample size, power analysis, power calculation, how many patients, how many subjects, IRB sample size.

## Quality Card

**Purpose** — Compute sample size / power with decision-tree test selection and reproducible R/Python code plus IRB-ready justification.

**Safety boundaries**

- Effect-size assumptions are justified and sourced, not fabricated; attrition/loss is accounted for.
- Any change to N updates both the justification and the protocol Methods (no silent change).

**Known limitations**

- Emits inline R/Python, not a packaged script; the user runs it.
- Output is only as valid as the assumed effect size and design.

**Validation**

- `re-run the emitted power code and confirm N matches the justification`

**Evidence** — `manual_workflow`

## Bundled resources

**References** (`skills/calc-sample-size/references/`):

- `formulas.md`
- `observational_cohort.md`

## Source

Canonical definition: [`skills/calc-sample-size/SKILL.md`](../../skills/calc-sample-size/SKILL.md)

---

*Part of [MedSci Skills](../../README.md) — Claude Code skills for the medical research lifecycle. This page is generated from the skill's `SKILL.md`; edit that file and re-run `scripts/gen_skill_docs.py`.*
