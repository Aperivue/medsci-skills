<!-- AUTO-GENERATED from skills/author-strategy/SKILL.md by scripts/gen_skill_docs.py. Do not edit by hand. -->

# author-strategy

> PubMed author profile analysis. Author name → PubMed fetch → study-type classification → visualization → strategy report → optional trajectory-archetype classification.

**Invoke:** `/author-strategy` · **Tools:** Read, Write, Edit, Bash, Glob, Grep · **Model:** inherit

## When to use

`author-strategy` activates on requests such as: author-strategy, 저자 분석, publication analysis, 다작 분석, 연구 전략 분석, author profile, reverse engineer strategy, trajectory archetype, career archetype.

## Quality Card

**Purpose** — Summarize an author's PubMed publication profile and surface strategy options from the actual record.

**Safety boundaries**

- Records are fetched from PubMed, not recalled from memory; author disambiguation is explicit.
- Reports describe the public record only; no private or speculative attribution.

**Known limitations**

- Name collisions on PubMed can blur profiles; the archetype path requires an explicit, manifest-gated disambiguation review.
- Archetype labels are explainable heuristics, not objective classifications; citation/h-index/venue-tier signals are unavailable and marked [VERIFY].
- No standalone demo; output is an advisory report.

**Validation**

- `manual review of the fetched record against PubMed`
- `bash skills/author-strategy/tests/test_archetype_classifier.sh`
- `python3 skills/author-strategy/render_archetype_doc.py --check`

**Evidence** — `manual_workflow`

## Bundled resources

**References** (`skills/author-strategy/references/`):

- `trajectory_archetypes.md`
- `trajectory_archetypes.yaml`

## Source

Canonical definition: [`skills/author-strategy/SKILL.md`](../../skills/author-strategy/SKILL.md)

---

*Part of [MedSci Skills](../../README.md) — Claude Code skills for the medical research lifecycle. This page is generated from the skill's `SKILL.md`; edit that file and re-run `scripts/gen_skill_docs.py`.*
