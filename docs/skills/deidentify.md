<!-- AUTO-GENERATED from skills/deidentify/SKILL.md by scripts/gen_skill_docs.py. Do not edit by hand. -->

# deidentify

> De-identify clinical research data before LLM-assisted analysis. Standalone Python CLI detects PHI via regex + heuristics with 10 country locale packs (kr, us, jp, cn, de, uk, fr, ca, au, in). Interactive terminal review. No LLM touches raw data — the script runs locally without any network or AI calls.

**Invoke:** `/deidentify` · **Tools:** Read, Bash, Glob · **Model:** inherit

## When to use

`deidentify` activates on requests such as: deidentify, de-identify, anonymize, 비식별화, 익명화, remove PHI, remove PII, strip patient info.

## Bundled resources

**References** (`skills/deidentify/references/`):

- `date_shift_guide.md`
- `hipaa_18_identifiers.md`
- `korean_phi_patterns.md`

## Source

Canonical definition: [`skills/deidentify/SKILL.md`](../../skills/deidentify/SKILL.md)

---

*Part of [MedSci Skills](../../README.md) — Claude Code skills for the medical research lifecycle. This page is generated from the skill's `SKILL.md`; edit that file and re-run `scripts/gen_skill_docs.py`.*
