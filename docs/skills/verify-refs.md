<!-- AUTO-GENERATED from skills/verify-refs/SKILL.md by scripts/gen_skill_docs.py. Do not edit by hand. -->

# verify-refs

> Audit-only verification of manuscript references against PubMed and CrossRef. Detects fabricated or mismatched citations and writes qc/reference_audit.json. Does not modify references/ or refs.bib.

**Invoke:** `/verify-refs` · **Tools:** Read, Write, Edit, Bash, Grep, Glob · **Model:** inherit

## When to use

`verify-refs` activates on requests such as: verify refs, verify references, citation audit, reference hallucination, fabricated references, bibliography check, PMID check, DOI check.

## Bundled resources

**References** (`skills/verify-refs/references/`):

- `manual_checkpoint_guide.md`

**Scripts** (`skills/verify-refs/scripts/`):

- `verify_cli.sh`
- `verify_refs.py`

## Source

Canonical definition: [`skills/verify-refs/SKILL.md`](../../skills/verify-refs/SKILL.md)

---

*Part of [MedSci Skills](../../README.md) — Claude Code skills for the medical research lifecycle. This page is generated from the skill's `SKILL.md`; edit that file and re-run `scripts/gen_skill_docs.py`.*
