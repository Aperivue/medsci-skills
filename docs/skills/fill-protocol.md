<!-- AUTO-GENERATED from skills/fill-protocol/SKILL.md by scripts/gen_skill_docs.py. Do not edit by hand. -->

# fill-protocol

> Fill institutional Word form templates (.doc/.docx) for IRB protocols, ethics applications, grant proposals, and other structured research documents while preserving the original styles, table layouts, fonts, and page geometry. Pairs with write-protocol — write-protocol drafts the scientific content, fill-protocol renders it into the institutional template. Korean-aware (CJK eastAsia font enforcement, table cantSplit) but works for any language template.

**Invoke:** `/fill-protocol` · **Tools:** Read, Write, Edit, Bash, Grep, Glob · **Model:** inherit

## When to use

`fill-protocol` activates on requests such as: fill protocol, fill template, fill IRB form, IRB template, ethics template, grant template, 양식 채우기, 연구계획서 작성, 신청서 작성, 정부 양식, 병원 양식, 워드 템플릿.

## Quality Card

**Purpose** — Render approved content into an institutional Word template without losing its layout, styles, or page geometry.

**Safety boundaries**

- Operates on the original template (never rebuilds from a blank Document, which strips logos/headers/styles).
- CJK eastAsia fonts and table cantSplit are enforced for Korean templates.

**Known limitations**

- Requires the institutional template file; cannot invent a missing one.
- Content-controlled (SDT) fields may need manual handling in Word.

**Validation**

- `confirm [MISS] count is 0 after fill`
- `soffice --headless --convert-to pdf for visual check`

**Evidence** — `bundled_script`

## Bundled resources

**References** (`skills/fill-protocol/references/`):

- `best_practices.md`

**Scripts** (`skills/fill-protocol/scripts/`):

- `doc_to_docx.py`
- `fill_form.py`
- `inspect_template.py`

## Source

Canonical definition: [`skills/fill-protocol/SKILL.md`](../../skills/fill-protocol/SKILL.md)

---

*Part of [MedSci Skills](../../README.md) — Claude Code skills for the medical research lifecycle. This page is generated from the skill's `SKILL.md`; edit that file and re-run `scripts/gen_skill_docs.py`.*
