# Skill Template

Use this template when creating a new medsci-skill. Copy the structure below and fill in each section. Delete sections marked `(if applicable)` when they do not apply.

---

## Required YAML Frontmatter

```yaml
---
name: skill-name
description: Use when {the situation the user is in}. {What the skill does, and which skill takes over at its boundary.}
metadata:
  triggers: "english trigger, 한국어 트리거, comma separated keywords"
---
```

**Fields**:
- `name`: kebab-case, matches the directory name under `skills/`
- `description`: At most 300 characters. The first sentence starts "Use when …" and names the
  situation in the words a user would type, because the model picks skills from this text. Name
  the boundary with the skill it is most easily confused with. No marketing, no implementation
  detail, no claim the SKILL.md body does not back.
- `metadata.triggers`: Keywords that activate this skill. Include both English and Korean terms.
  It sits under the Agent Skills `metadata` map because a top-level `triggers` is non-standard.
- `model` (optional, Claude Code only): leave it out, and the skill runs on the session's model.
  Add `model: opus` only when the skill needs a stronger model than the user may have chosen. The
  field belongs to Claude Code, not to the [Agent Skills spec](https://agentskills.io/specification):
  other hosts do not act on it, and the spec's `skills-ref validate` and a claude.ai skill upload
  reject a SKILL.md that has it.

There is no `tools` field: hosts ignore it. Do not add `allowed-tools` in its place — that field
pre-approves tools rather than listing them.

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

## Gotchas

- {Something an agent gets wrong in this domain without being told, and why.} Example: a
  number or reference the skill cannot verify is marked `[VERIFY: item]`, not filled in.
```

---

## Size

Keep SKILL.md short: under about 500 lines (≈5k tokens). Worked examples, long tables and
templates go in `references/` and are read when a step needs them. For each line ask whether the
agent would get the task wrong without it; if not, cut it. Give the reason for a rule instead of
writing MUST. `scripts/check_phase_budget.py` enforces the upper bound; nothing rewards length.

---

## Checklist Before Publishing

- [ ] YAML frontmatter has `name`, `description` (≤300 characters, led by "Use when") and `metadata.triggers`, no `tools`, and `model` only if the skill needs a named model
- [ ] Every instruction is one the agent would otherwise get wrong (no generic boilerplate)
- [ ] Steps that need the user's approval say so where they happen
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
