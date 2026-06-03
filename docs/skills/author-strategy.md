<!-- AUTO-GENERATED from skills/author-strategy/SKILL.md by scripts/gen_skill_docs.py. Do not edit by hand. -->

# author-strategy

> PubMed author profile analysis. Author name → PubMed fetch → study type classification → visualization → strategy report.

**Invoke:** `/author-strategy` · **Tools:** Read, Write, Edit, Bash, Glob, Grep · **Model:** inherit

## When to use

`author-strategy` activates on requests such as: author-strategy, 저자 분석, publication analysis, 다작 분석, 연구 전략 분석, author profile, reverse engineer strategy.

## Quality Card

**Purpose** — Summarize an author's PubMed publication profile and surface strategy options from the actual record.

**Safety boundaries**

- Records are fetched from PubMed, not recalled from memory; author disambiguation is explicit.
- Reports describe the public record only; no private or speculative attribution.

**Known limitations**

- Name collisions on PubMed can blur profiles; disambiguation is best-effort.
- No standalone demo; output is an advisory report.

**Validation**

- `manual review of the fetched record against PubMed`

**Evidence** — `manual_workflow`

## Source

Canonical definition: [`skills/author-strategy/SKILL.md`](../../skills/author-strategy/SKILL.md)

---

*Part of [MedSci Skills](../../README.md) — Claude Code skills for the medical research lifecycle. This page is generated from the skill's `SKILL.md`; edit that file and re-run `scripts/gen_skill_docs.py`.*
