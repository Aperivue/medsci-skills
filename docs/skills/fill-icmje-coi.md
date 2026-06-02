<!-- AUTO-GENERATED from skills/fill-icmje-coi/SKILL.md by scripts/gen_skill_docs.py. Do not edit by hand. -->

# fill-icmje-coi

> Batch-generate per-author ICMJE Conflict of Interest Disclosure Forms (`coi_disclosure.docx`) for manuscript submission. Pre-fills all 13 disclosure items as "☒ None" + final certification ☒ using a synthetic seed template shipped with the skill, then clones the seed per author with Date, Name, and Manuscript Title replaced. Designed for the common case of hospital-based observational research where no author has real financial conflicts; the circulated forms become "reply 변경 없음 + sign" for most authors and only flag those who need to amend.

**Invoke:** `/fill-icmje-coi` · **Tools:** Read, Write, Edit, Bash, Grep, Glob · **Model:** inherit

## When to use

`fill-icmje-coi` activates on requests such as: ICMJE, COI form, conflict of interest form, disclosure form, coi_disclosure.docx, 이해상충, 이해상충 폼, icmje 폼, 저자 동의서, submission forms.

## Bundled resources

**Scripts** (`skills/fill-icmje-coi/scripts/`):

- `fill_icmje_coi.py`

**Templates** (`skills/fill-icmje-coi/templates/`):

- `icmje_coi_seed_synthetic.docx`

## Source

Canonical definition: [`skills/fill-icmje-coi/SKILL.md`](../../skills/fill-icmje-coi/SKILL.md)

---

*Part of [MedSci Skills](../../README.md) — Claude Code skills for the medical research lifecycle. This page is generated from the skill's `SKILL.md`; edit that file and re-run `scripts/gen_skill_docs.py`.*
