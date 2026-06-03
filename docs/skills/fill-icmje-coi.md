<!-- AUTO-GENERATED from skills/fill-icmje-coi/SKILL.md by scripts/gen_skill_docs.py. Do not edit by hand. -->

# fill-icmje-coi

> Batch-generate per-author ICMJE Conflict of Interest Disclosure Forms (`coi_disclosure.docx`) for manuscript submission. Pre-fills all 13 disclosure items as "☒ None" + final certification ☒ using a synthetic seed template shipped with the skill, then clones the seed per author with Date, Name, and Manuscript Title replaced. Designed for the common case of hospital-based observational research where no author has real financial conflicts; the circulated forms become "reply 변경 없음 + sign" for most authors and only flag those who need to amend.

**Invoke:** `/fill-icmje-coi` · **Tools:** Read, Write, Edit, Bash, Grep, Glob · **Model:** inherit

## When to use

`fill-icmje-coi` activates on requests such as: ICMJE, COI form, conflict of interest form, disclosure form, coi_disclosure.docx, 이해상충, 이해상충 폼, icmje 폼, 저자 동의서, submission forms.

## Quality Card

**Purpose** — Clone the ICMJE COI form per author with date/name/title filled, defaulting all 13 items to 'None' for the no-conflict common case.

**Safety boundaries**

- Only date, name, and manuscript title are substituted; the 13 items and certification come from the seed unchanged.
- Ships a synthetic PII-free seed; never commits a seed with real author PII.

**Known limitations**

- Authors with real disclosures must edit their form in Word; the skill cannot infer conflicts.
- A blank ICMJE template cannot be used as the seed (the safety check requires the pre-filled 'None' strings).

**Validation**

- `verify each output: 14 checked boxes, 13 'None', no seed-placeholder leakage`

**Evidence** — `bundled_script`

## Bundled resources

**Scripts** (`skills/fill-icmje-coi/scripts/`):

- `fill_icmje_coi.py`

**Templates** (`skills/fill-icmje-coi/templates/`):

- `icmje_coi_seed_synthetic.docx`

## Source

Canonical definition: [`skills/fill-icmje-coi/SKILL.md`](../../skills/fill-icmje-coi/SKILL.md)

---

*Part of [MedSci Skills](../../README.md) — Claude Code skills for the medical research lifecycle. This page is generated from the skill's `SKILL.md`; edit that file and re-run `scripts/gen_skill_docs.py`.*
