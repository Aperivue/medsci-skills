<!-- AUTO-GENERATED from skills/check-reporting/SKILL.md by scripts/gen_skill_docs.py. Do not edit by hand. -->

# check-reporting

> Check manuscript compliance with medical research reporting guidelines. Supports 32 guidelines including STROBE, CONSORT, STARD, STARD-AI, TRIPOD, TRIPOD+AI, ARRIVE, PRISMA, PRISMA-DTA, PRISMA-P, CARE, SPIRIT, CLAIM, MI-CLEAR-LLM, SQUIRE 2.0, CLEAR, MOOSE, GRRAS, SWiM, AMSTAR 2, and risk of bias tools (QUADAS-2, QUADAS-C, RoB 2, ROBINS-I, ROBINS-E, ROBIS, ROB-ME, PROBAST, PROBAST+AI, NOS, COSMIN, RoB NMA). Generates item-by-item assessment with PRESENT/MISSING/PARTIAL status.

**Invoke:** `/check-reporting` · **Tools:** Read, Write, Edit, Bash, Grep, Glob · **Model:** inherit

## When to use

`check-reporting` activates on requests such as: checklist, reporting guideline, STROBE, CONSORT, STARD, STARD-AI, TRIPOD, PRISMA, PRISMA-DTA, PRISMA-P, ARRIVE, CARE, CLAIM, MI-CLEAR-LLM, SPIRIT, QUADAS, QUADAS-C, RoB, ROBINS, ROBINS-E, ROBIS, ROB-ME, PROBAST, NOS, COSMIN, AMSTAR, SWiM, risk of bias, compliance check, LLM accuracy.

## Bundled resources

**References** (`skills/check-reporting/references/`):

- `LICENSES.md`
- `checklists/` (32 files)
- `step4c_registration_timing.md`
- `step4d_prisma_figure_audit.md`

**Scripts** (`skills/check-reporting/scripts/`):

- `check_checklist_exists.py`
- `check_prisma_figure.py`
- `prisma_cascade_check.py`

## Source

Canonical definition: [`skills/check-reporting/SKILL.md`](../../skills/check-reporting/SKILL.md)

---

*Part of [MedSci Skills](../../README.md) — Claude Code skills for the medical research lifecycle. This page is generated from the skill's `SKILL.md`; edit that file and re-run `scripts/gen_skill_docs.py`.*
