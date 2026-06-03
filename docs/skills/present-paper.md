<!-- AUTO-GENERATED from skills/present-paper/SKILL.md by scripts/gen_skill_docs.py. Do not edit by hand. -->

# present-paper

> Academic presentation preparation — paper-driven (journal club, grand rounds, seminar) and lecture/teaching decks (course material, workshop slides, conference talks). Analyzes source material, finds supporting references, drafts audience-adapted speaker scripts, generates or augments PPTX with speaker notes, and prepares Q&A.

**Invoke:** `/present-paper` · **Tools:** Read, Write, Edit, Bash, Grep, Glob · **Model:** inherit

## When to use

`present-paper` activates on requests such as: present paper, paper presentation, journal club, seminar presentation, grand rounds, academic presentation, presentation prep, lecture, lecture material, teaching slides, course slides, 강의자료, 발표자료, 슬라이드, pptx.

## Quality Card

**Purpose** — Turn source papers into an audience-adapted deck with speaker notes, Mac-compatible PPTX, and a sharing-stripped variant.

**Safety boundaries**

- Slide claims trace to the source material; findings are not invented for narrative effect.
- A notes-stripped variant is produced for sharing so private speaker notes never leak.

**Known limitations**

- Figure cropping and notes parsing are heuristic; verify the built PPTX in PowerPoint.
- Mac OOXML quirks require the bundled compatibility checks; not every host renders identically.

**Validation**

- `unzip the .pptx and confirm 0 markdown-raw notes / 0 TIFF / app.xml counts synced`
- `python3 scripts/strip_notes_for_sharing.py before sharing`

**Evidence** — `bundled_script`

## Bundled resources

**References** (`skills/present-paper/references/`):

- `critic_rubrics/` (1 file)
- `generate_pptx_templates.py`
- `medical_presentation_templates.md`
- `slide_design_principles.md`
- `slide_visual_styles/` (1 file)
- `workflow-checklist.md`

**Scripts** (`skills/present-paper/scripts/`):

- `extract_pdf_figures.py`
- `inject_pronunciation_notes.py`
- `inject_speaker_notes.py`
- `strip_notes_for_sharing.py`
- `trim_caption.py`

**Templates** (`skills/present-paper/templates/`):

- `build_pptx_nature_lancet.py`

## Source

Canonical definition: [`skills/present-paper/SKILL.md`](../../skills/present-paper/SKILL.md)

---

*Part of [MedSci Skills](../../README.md) — Claude Code skills for the medical research lifecycle. This page is generated from the skill's `SKILL.md`; edit that file and re-run `scripts/gen_skill_docs.py`.*
