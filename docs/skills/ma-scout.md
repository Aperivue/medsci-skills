<!-- AUTO-GENERATED from skills/ma-scout/SKILL.md by scripts/gen_skill_docs.py. Do not edit by hand. -->

# ma-scout

> Meta-analysis topic discovery and feasibility assessment. Professor-first (profile → gap) or Topic-first (question → gap → co-author). Pre-protocol phase from idea to ranked topic list.

**Invoke:** `/ma-scout` · **Tools:** Read, Write, Edit, Bash, Grep, Glob · **Model:** opus

## When to use

`ma-scout` activates on requests such as: ma-scout, MA 주제 찾기, professor MA, 메타분석 주제, MA gap, topic-first MA, 트렌드 MA, meta-analysis topic, 교수님 분석, 연구 분석.

## Quality Card

**Purpose** — Find feasible meta-analysis gaps (professor-first or topic-first) backed by literature evidence.

**Safety boundaries**

- Gap claims rest on real literature scans; candidate study counts are not fabricated.
- Advisory report; does not perform screening or synthesis.

**Known limitations**

- Feasibility is an estimate; the true includable pool is established only by meta-analysis screening.
- No standalone demo; topic selection needs domain judgement.

**Validation**

- `confirm feasibility by running meta-analysis screening on the shortlist`

**Evidence** — `manual_workflow`

## Bundled resources

**References** (`skills/ma-scout/references/`):

- `project_readme_template.md`

## Source

Canonical definition: [`skills/ma-scout/SKILL.md`](../../skills/ma-scout/SKILL.md)

---

*Part of [MedSci Skills](../../README.md) — Claude Code skills for the medical research lifecycle. This page is generated from the skill's `SKILL.md`; edit that file and re-run `scripts/gen_skill_docs.py`.*
