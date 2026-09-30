<!-- AUTO-GENERATED from skills/publish-skill/SKILL.md by scripts/gen_skill_docs.py. Do not edit by hand. -->

# publish-skill

> Use when turning a personal agent skill into an open-source, distributable one. Runs a PII audit, generalizes personal details, checks licence compatibility, reviews cross-platform adapters and walks through packaging.

**Invoke:** `/publish-skill`

## When to use

`publish-skill` activates on requests such as: publish skill, distribute skill, open-source skill, package skill, universalize skill.

## Quality Card

**Purpose** — Harden a personal skill for open-source release through a PII audit, generalization, and license/portability checks.

**Safety boundaries**

- Publication is gated on a passing PII audit; the blocklist is conservative and not weakened to pass.
- Personal paths, names, and document metadata are scrubbed before release.

**Known limitations**

- The audit catches known PII patterns; novel identifiers still need human review.
- Generalization preserves behavior but a maintainer should re-read the result.

**Validation**

- `bash scripts/audit_skill.sh <skill-dir>`
- `bash scripts/validate_skills.sh`

**Evidence** — `bundled_script`

## Bundled resources

**References** (`skills/publish-skill/references/`):

- `classroom-distribution.md`
- `license-compatibility-matrix.md`
- `pii-patterns.md`

**Scripts** (`skills/publish-skill/scripts/`):

- `audit_skill.sh`

## Source

Canonical definition: [`skills/publish-skill/SKILL.md`](../../skills/publish-skill/SKILL.md)

---

*Part of [MedSci Skills](../../README.md) — Claude Code skills for the medical research lifecycle. This page is generated from the skill's `SKILL.md`; edit that file and re-run `scripts/gen_skill_docs.py`.*
