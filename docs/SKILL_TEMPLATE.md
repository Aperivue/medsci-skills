# Skill Template

Use this template when creating a new medsci-skill. Copy the structure below and fill in each section. Delete sections marked `(if applicable)` when they do not apply.

---

## Required YAML Frontmatter

```yaml
---
name: skill-name
description: One-sentence description of what this skill does.
triggers: english trigger, 한국어 트리거, comma separated keywords
tools: Read, Write, Edit, Bash, Grep, Glob
model: inherit
---
```

**Fields**:
- `name`: kebab-case, matches the directory name under `skills/`
- `description`: Under 200 characters. Start with a verb or noun phrase.
- `triggers`: Keywords that activate this skill. Include both English and Korean terms.
- `tools`: Only list tools the skill actually uses. Most skills need `Read, Write, Edit, Bash, Grep, Glob`.
- `model`: Use `inherit` unless the skill requires complex reasoning (then `opus`).

---

## Optional `skill.yml` Contract

Core skills and any skill that participates in multi-skill workflows should add
`skill.yml` beside `SKILL.md`. Missing contracts are currently migration warnings;
malformed contracts fail `scripts/validate_skills.sh`.

```yaml
schema_version: 1
name: skill-name
owner_domain: domain_from_capabilities_yml
inputs:
  - input_artifact
outputs:
  - output_artifact
deterministic_scripts:
  - scripts/example.py
side_effects:
  - writes_project_artifacts
downstream_consumers:
  - downstream-skill
forbidden_actions:
  - unsafe_action_this_skill_must_not_do
```

---

## Template Structure

```markdown
---
(frontmatter above)
---

# {Skill Name}

{Role statement: "You are assisting a medical researcher in..." — one paragraph.}

## When to Use

- Bullet list of scenarios when this skill should be invoked
- Include both positive triggers and disambiguation from similar skills

## Inputs

1. **Required input 1**: description
2. **Required input 2**: description
3. **Optional input** (optional): description with default value

## Reference Files

- `${SKILL_DIR}/references/filename.ext` — what it contains
- `${SKILL_DIR}/references/templates/filename.ext` — template files
- Upstream: `medsci-skills/skills/{other-skill}/references/filename.ext`

## Workflow

### Phase 0: Input Validation

1. Verify all required inputs are provided
2. Check file paths exist
3. **Gate**: Present input summary → user approval

### Phase 1: {First Major Step}

1. Step details
2. Step details
3. **Gate**: Present intermediate output → user approval

### Phase N: {Last Step}

1. Final steps
2. **Gate**: Present final output → user approval

## Output Contract

| Artifact | Filename | Format | Producer |
|----------|----------|--------|----------|
| {Main output} | `{filename}.md` | Markdown | This skill |
| {Analysis manifest} | `_analysis_outputs.md` | Markdown | This skill |

All output files are written to `{working_dir}/` unless the user specifies otherwise.

## Quality Gates

This skill has {N} mandatory user-approval gates:

1. **Gate 1** (Phase 0): Input validation — user confirms inputs are correct
2. **Gate 2** (Phase N): {Description} — user reviews before proceeding
3. **Gate 3** (Phase N): Final output — user approves deliverables

> Gates are blocking. Do not proceed past a gate without explicit user approval.

## Critical Rules

1. Rule with rationale
2. Rule with rationale

## Error Handling

- {Common error 1}: how to handle
- {Common error 2}: how to handle
- If blocked: inform user and suggest alternatives rather than guessing

## Skill Interactions

| Need | Skill | When |
|------|-------|------|
| {Upstream dependency} | `/skill-name` | Before this skill |
| {Downstream consumer} | `/skill-name` | After this skill |

## What This Skill Does NOT Do

- Explicit scope boundary 1
- Explicit scope boundary 2

## Anti-Hallucination

- **Never fabricate {domain-specific items}.** If uncertain, output `[VERIFY: item]` and ask the user.
- **Never generate references from memory.** Use `/search-lit` for all citations.
- If a tool, package, or resource does not exist, say so explicitly rather than guessing.

## Language

- Communication with user: Korean
- Code and variable names: English
- Manuscript content: English
- Medical terminology: always English
```

---

## Quality Tiers

Skills are classified by documentation depth and verification rigor:

| Tier | SKILL.md Lines | Min Gates | Anti-Halluc | Output Contract | Reference Files |
|------|---------------|-----------|-------------|-----------------|-----------------|
| **High** | 300+ | 3+ | Required | Required | Required |
| **Mid** | 150-300 | 2+ | Required | Required | Recommended |
| **Thin** | <150 | 1+ | Required | Recommended | Optional |

New skills should target **Mid** tier minimum. Core pipeline skills (write-paper, analyze-stats, meta-analysis) must be **High** tier.

---

## Checklist Before Publishing

- [ ] YAML frontmatter has all 5 required fields (name, description, triggers, tools, model)
- [ ] Anti-Hallucination section present with domain-specific rules
- [ ] At least 2 quality gates with explicit user-approval language
- [ ] Output Contract section lists all files the skill produces
- [ ] Reference files mentioned in SKILL.md actually exist in `references/`
- [ ] Skill Interactions section documents upstream/downstream dependencies
- [ ] `skill.yml` exists for pipeline/core skills and matches `capabilities.yml`
- [ ] "What This Skill Does NOT Do" section defines scope boundaries
- [ ] No hardcoded personal paths (use `${SKILL_DIR}` or `${CLAUDE_SKILL_DIR}`)
- [ ] No PII or institution-specific content in examples
- [ ] Triggers include both English and Korean keywords
- [ ] `bash scripts/validate_skills.sh --only <your-skill>` passes — seconds, instead of the whole
      repo. It prints `SCOPED PASS`, not `ALL CHECKS PASSED`: the unscoped run is still the gate,
      and CI runs it that way on your PR.
