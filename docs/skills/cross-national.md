<!-- AUTO-GENERATED from skills/cross-national/SKILL.md by scripts/gen_skill_docs.py. Do not edit by hand. -->

# cross-national

> End-to-end cross-national comparison study using KNHANES + NHANES + CHNS (or other parallel surveys). Variable harmonization, parallel weighted analysis, and comparison tables. Supports 2-country (KR+US) and 3-country (KR+US+CN) designs.

**Invoke:** `/cross-national` · **Tools:** Read, Write, Edit, Bash, Grep, Glob · **Model:** opus

## When to use

`cross-national` activates on requests such as: cross-national, 한미 비교, Korea US comparison, KNHANES NHANES, 양국 비교, binational, cross-country, 비교연구, 3국 비교, CHNS, 한미중.

## Quality Card

**Purpose** — Harmonize and analyze parallel national surveys (2- or 3-country) with correct complex-survey weighting.

**Safety boundaries**

- Variable harmonization is documented in an explicit mapping; survey weights are always applied.
- Numbers come from executed weighted analysis on real survey data.

**Known limitations**

- Cross-survey comparability is limited by instrument differences; residual non-comparability remains.
- No standalone demo; depends on a sound harmonization plan.

**Validation**

- `re-run weighted analysis per country and reconcile`
- `/self-review`

**Evidence** — `manual_workflow`

## Source

Canonical definition: [`skills/cross-national/SKILL.md`](../../skills/cross-national/SKILL.md)

---

*Part of [MedSci Skills](../../README.md) — Claude Code skills for the medical research lifecycle. This page is generated from the skill's `SKILL.md`; edit that file and re-run `scripts/gen_skill_docs.py`.*
