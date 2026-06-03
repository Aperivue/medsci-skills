<!-- AUTO-GENERATED from skills/write-protocol/SKILL.md by scripts/gen_skill_docs.py. Do not edit by hand. -->

# write-protocol

> IRB/ethics committee research protocol generator. Produces 4 core sections (Background, Study Design, Sample Size, Statistical Plan) with full prose, plus 6 skeleton sections with TODO markers for institution-specific content. Integrates outputs from design-study, calc-sample-size, and search-lit.

**Invoke:** `/write-protocol` · **Tools:** Read, Write, Edit, Bash, Grep, Glob · **Model:** inherit

## When to use

`write-protocol` activates on requests such as: write protocol, IRB protocol, ethics protocol, research protocol, IRB submission, ethics submission, protocol draft.

## Quality Card

**Purpose** — Draft the scientific core of an IRB protocol and leave institution-specific sections as explicit TODO skeletons.

**Safety boundaries**

- Institution-specific content is left as TODO markers, never fabricated.
- Citations come from search-lit; references are not generated from memory.

**Known limitations**

- Core sections need design-study/calc-sample-size inputs to be sound.
- Skeleton sections require the researcher's institutional knowledge to complete.

**Validation**

- `/verify-refs --strict on cited work`
- `hand off to fill-protocol for the institutional template`

**Evidence** — `manual_workflow`

## Bundled resources

**References** (`skills/write-protocol/references/`):

- `ethics_checklist.md`
- `protocol_template.md`

## Source

Canonical definition: [`skills/write-protocol/SKILL.md`](../../skills/write-protocol/SKILL.md)

---

*Part of [MedSci Skills](../../README.md) — Claude Code skills for the medical research lifecycle. This page is generated from the skill's `SKILL.md`; edit that file and re-run `scripts/gen_skill_docs.py`.*
