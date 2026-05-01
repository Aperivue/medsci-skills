---
name: present-paper
description: >
  Academic presentation preparation — paper-driven (journal club, grand rounds, seminar) and
  lecture/teaching decks (course material, workshop slides, conference talks). Analyzes source
  material, finds supporting references, drafts audience-adapted speaker scripts, generates or
  augments PPTX with speaker notes, and prepares Q&A.
triggers: present paper, paper presentation, journal club, seminar presentation, grand rounds, academic presentation, presentation prep, lecture, lecture material, teaching slides, course slides, 강의자료, 발표자료, 슬라이드, pptx
tools: Read, Write, Edit, Bash, Grep, Glob
model: inherit
---

# Present-Paper Skill

## Purpose

Prepare a polished academic presentation from a research paper. The skill walks through a 5-phase
pipeline: paper analysis, supporting research, script writing, slide note injection, and Q&A
preparation.

Use it when:

- preparing a journal club or seminar presentation
- presenting a paper for a graduate course
- preparing grand rounds or conference talks based on a published paper
- building speaker notes for an existing slide deck

---

## Communication Rules

- Communicate with the user in their preferred language.
- Use English for medical, statistical, and methodological terminology.
- Add pronunciation guides for drug names and technical abbreviations in the user's language.
- Be direct about paper limitations, but frame them constructively.

---

## Phase 0: Init & Outline

### Required Inputs

Before starting, collect these from the user:

| Input | Why |
|-------|-----|
| **Paper** | PDF path, DOI, or PMID |
| **Presentation time** | Determines depth and slide count |
| **Target audience** | Specialty mix, knowledge level — controls terminology depth |
| **Context** | Course name, conference, journal club format, prior session topics |
| **Extension section** | Optional topic to include (e.g., AI directions, clinical implications). Default: none |

### Paper Analysis

Read the paper and produce a structured analysis:

```text
## Paper Analysis

### Citation
[Full citation with DOI]

### Background
- What gap does this paper address?
- What was known vs. unknown before this study?

### Study Design
- Type: [RCT / cohort / case series / meta-analysis / etc.]
- Subjects: [n, inclusion/exclusion]
- Methods: [key methodological choices]
- Primary outcome: [what was measured]

### Key Results
1. [Finding 1 with effect size and CI/p-value]
2. [Finding 2]
3. [Finding 3]

### Patient/Case Summary Table
[If applicable — structured table of individual cases or subgroups]

### Limitations
1. [Limitation 1]
2. [Limitation 2]

### Significance
- Why does this matter?
- What changes because of this paper?
```

### Slide Outline

Create a slide-by-slide outline with time allocation:

```text
## Slide Outline ([N] slides, [M] minutes)

| # | Title | Time | Key Content |
|---|-------|------|-------------|
| 1 | Title slide | 0:30 | Paper citation, presenter |
| 2 | Context / Prior sessions | 1:00 | How this connects to prior knowledge |
| 3 | Background | 1:30 | The gap this paper fills |
| ... | ... | ... | ... |
| N | Take-home messages | 0:30 | 3-5 key points |
```

**Gate: User approves outline before proceeding.**

---

## Phase 1: Supporting Research

### Search Strategy

Find references that strengthen the presentation:

1. **Follow-up studies** — Has the main finding been replicated or extended?
2. **Clinical trial data** — Large-scale data that contextualizes the findings
3. **Review articles** — Authoritative summaries that frame the topic
4. **Contradicting evidence** — Important for balanced Q&A preparation

**Efficiency rule:** Limit supporting references to 5-8 total. Only search categories
that the approved outline (Phase 0) actually requires. Skip categories not needed for
the presentation type (e.g., skip clinical trials for a methods-focused paper).

### Selection Criteria

Do NOT summarize every paper found. Extract only:

- Specific data points needed for slides (incidence rates, OR/HR, AUC values)
- Findings that directly support or challenge the main paper
- Context that helps the audience understand significance

### Output

```text
## Verified References

### Main Paper
1. [Citation] — PMID: XXXXX, DOI: XX.XXXX/XXXXX

### Supporting References
2. [Citation] — PMID: XXXXX
   → Used for: [specific data point or context]
3. [Citation] — PMID: XXXXX
   → Used for: [specific data point or context]

### Key Data for Slides
- [Statistic 1]: [value] — Source: [Ref #]
- [Statistic 2]: [value] — Source: [Ref #]
```

**Every reference must have a verified DOI or PMID. Mark unverified references with [UNVERIFIED].**

---

## Phase 2: Script & Content

### Speaker Script

Draft a complete speaker script with these requirements:

1. **Language**: User's preferred language for narration; English for technical terms
2. **Audience adaptation**: Adjust explanation depth based on Phase 0 audience profile
   - For mixed audiences: add one-line plain-language explanations for specialty-specific terms
   - Example: "FLAIR sequence — an MRI technique that suppresses fluid signal to highlight edema"
3. **Pronunciation guide**: Include native-language pronunciation for drug names, abbreviations
   - Example: "lecanemab (leh-KAN-eh-mab)" or local equivalent
4. **Timing markers**: Note approximate time per slide
5. **Transition phrases**: Connect each slide to the narrative arc

### Structure

```text
## Speaker Script

### Slide 1: Title (0:30)
"[Opening — introduce yourself and the paper]"

### Slide 2: Context (1:00)
"[Connect to prior knowledge or clinical relevance]"

...

### Slide N: Take-home Messages (0:30)
"[Summarize 3-5 key points. Thank audience. Invite questions.]"
```

### Extension Section (Optional)

Only include if user requested in Phase 0. Examples:

- AI/computational research directions stemming from the paper
- Clinical practice implications
- Policy or guideline implications
- Connections to the user's own research

**Gate: User reviews script before proceeding.**

---

## Phase 3: Slides & Notes

### Two Modes

**Mode A: Generate new slide deck**

Generate a fully-editable PPTX from structured inline data using `python-pptx`. Use the
template library at `${CLAUDE_SKILL_DIR}/references/generate_pptx_templates.py` as the
canonical pattern — it ships a working showcase of every template type and a smoke-tested
`main()`.

### Architecture

```
inline structured data (lists/dicts in build_*_slides())
    ↓ template functions (T_lead / T_text / T_table / ...)
editable PPTX with native text frames (selectable, restyleable in PowerPoint)
```

Three rules that keep slides stable:

1. **No markdown parsing.** Every slide is a function call with explicit inline data.
2. **No `cur_top` cumulative position tracking.** Use the fixed coordinate zones below — `cur_top` accumulates rounding errors and breaks layout after ~10 slides.
3. **No Marp.** Marp renders to images; the deck becomes uneditable and reviewers cannot copy text or restyle.

### Slide-type templates

| Template | Use for | Required fields |
|----------|---------|-----------------|
| `T_lead` | Title slide, section divider | `title`, `subtitle?`, `extra?` |
| `T_text` | Bullet body (most common) | `title`, `body_lines[]`, `subtitle?` |
| `T_table` | Cohort tables, comparisons | `title`, `headers[]`, `rows[][]`, `body_before?` |
| `T_image_right` | Body + figure on right | `title`, `body_lines[]`, `img_path`, `img_pct?` |
| `T_quote_slide` | Verbatim citations, witness quotes | `title`, `quotes[]`, `body_after?`, `img_path?` |
| `T_two_col` | Compare/contrast | `title`, `left_lines[]`, `right_lines[]` |
| `T_two_col_with_box` | Compare + emphasis | as above + `metaphor_col`, `metaphor_lines[]` |
| `T_highlight_slide` | Single key result | `title`, `highlight_lines[]`, `body_before?` |
| `T_metaphor_body` | Body + analogy footer | `title`, `body_lines[]`, `metaphor_lines[]` |
| `T_table_two_col` | Take-aways + numeric table | `title`, `left_lines[]`, `headers[]`, `rows[][]` |

### Helpers (used by templates — usually you do not call directly)

| Helper | Role |
|--------|------|
| `_text` | Single text box with `**bold**` inline markup |
| `_multiline` | Multi-line block with bullet (`- `, `✓ `) and `### subhead` support |
| `_title_block` | Title + teal underline + optional subtitle |
| `_table` | Styled table (teal header row, alternating rows) |
| `_quote` | Blockquote — teal left bar + light-blue background |
| `_highlight` | Yellow rounded box + orange 2pt border |
| `_metaphor` | Same shape as quote, lighter font |
| `_image` | PIL aspect-preserving image insert (handles iPhone EXIF if you transpose first) |
| `_slidenum` | Bottom-right page number |

### Design tokens (defaults — change to fit institution/journal)

```python
NAVY    = #1B2A4A   # title text, section divider background
TEAL    = #0072B2   # subtitle, underline, table header bg, quote bar
ORANGE  = #D55E00   # highlight box border
GRAY    = #333333   # body text
FONT    = 'Apple SD Gothic Neo'   # use a Latin-only font on non-Korean decks
```

### Fixed coordinate zones (16:9 = 13.333" × 7.5")

```
ML / MR = 0.8"     MT = 0.5"     CW = SW − ML − MR = 11.733"

TITLE_Y = 0.5"    TITLE_H = 0.8"
SUB_Y   = 1.3"    SUB_H   = 0.5"
BODY_Y  ≈ 1.9"    BODY_H  ≈ 5.1"
```

### Build script responsibilities

A from-scratch generation script must:

- Convert TIFF images to PNG before `add_picture` (Mac PowerPoint silently drops TIFF).
- Apply EXIF transpose to iPhone photos before insertion.
- After inserting/removing slides, sync `docProps/app.xml` (`<Slides>`, `<Notes>`, `HeadingPairs`, `TitlesOfParts`) to the actual count, or PowerPoint Mac will raise a recovery dialog on open.
- If you copy `<a:srcRect>` from another deck, copy the values verbatim — they are 1/1000-percent (cap 100000), never EMU. A unit conversion bug here crops 99% of the image off-slide.
- Print slide count, notes count, file size, and editability check at the end.

### Forbidden in Mode A

- ❌ Marp CLI for PPTX (always image-rendered, uneditable).
- ❌ Markdown auto-parsing into slides (layout drifts on every regeneration).
- ❌ `cur_top` cumulative top tracking (accumulates rounding error).
- ❌ Direct iPhone photo insert without EXIF transpose (rotated 90° in PowerPoint).
- ❌ Using `python-pptx` from-scratch rebuild to *edit* an existing deck — see Patch over Rebuild below.

### Mac PowerPoint compatibility checklist

PowerPoint Mac is stricter than Windows / Keynote / LibreOffice on OOXML defects.
Verify before delivering any deck destined for a Mac viewer:

| Defect | Detect | Fix |
|---|---|---|
| **TIFF images** | `find ppt/media -iname '*.tif*'` | `sips -s format png in.tif --out out.png` + replace `.tif`→`.png` in `_rels/*.rels` |
| **`<a:sp3d>` in rPr** | `grep -l '<a:sp3d>' ppt/slides/*.xml` | Regex-strip the `<a:sp3d>...</a:sp3d>` block (renders as red outline only on Mac) |
| **`app.xml` count mismatch** | `<Slides>` value + `HeadingPairs` count + `TitlesOfParts` size vs actual slide files | Sync all four fields to real count |
| **`srcRect` corruption** | Any value > 100000 (1/1000-percent cap) | Compare with original deck; restore verbatim |

Validation must run on **PDF export AND Mac PowerPoint** — neither alone catches all four. PDF misses `sp3d` outlines and `srcRect` corruption.

### Patch over Rebuild — editing an existing PPTX

When the user supplies an existing deck and asks for surgical edits (textbox width, image
crop, font swap, sp3d removal), prefer **regex/sed patching of the unzipped XML** over
regenerating with `python-pptx`. From-scratch rebuild loses:

- `<a:srcRect>` image crops
- `<a:sp3d>` / `<a:scene3d>` (when intentional)
- Slide master / layout / theme details
- `app.xml` and `core.xml` metadata

```bash
unzip -q original.pptx -d /tmp/work
python3 -c "
import re; from pathlib import Path
p = Path('/tmp/work/ppt/slides/slide23.xml')
s = p.read_text()
s = s.replace('cx=\"9504720\"', 'cx=\"11200000\"')
p.write_text(s)
"
cd /tmp/work && zip -rq ../patched.pptx . -x '*.DS_Store'
```

`python-pptx` is reserved for (a) brand-new decks built via the templates above, or
(b) appending speaker notes via `slide.notes_slide.notes_text_frame.text`. The skill's
`scripts/inject_speaker_notes.py` is the canonical example of (b).

### Standard structure (10–15 min paper talk)

1. Title slide (`T_lead`) — paper citation + presenter
2. Background (`T_text` × 1–2)
3. Study design / Methods (`T_text` or `T_two_col`)
4. Key results with figures (`T_image_right` / `T_table` × 2–3)
5. Discussion (`T_text`)
6. Limitations (`T_two_col_with_box` works well)
7. Take-home (`T_text` or `T_highlight_slide`)

### Output

Save to `output/presentation.pptx`. Speaker notes go into the notes pane only — never
modify slide design when adding notes.

**Mode B: Add notes to existing slides** (more common)
- Read existing PPTX to understand slide structure and count
- Map speaker script sections to corresponding slides
- Generate `inject_notes.py` script tailored to the specific presentation

### Note Injection Script

Generate a tailored `inject_notes.py` following the pattern in
`${CLAUDE_SKILL_DIR}/references/inject_speaker_notes.py`. The generated script should
contain only the `notes` dictionary customized for this presentation and the main
injection loop from the template.

### Critical Rule

**Speaker notes are injected without modifying slide design, layout, text, or images.**
The script only touches the notes pane. Verify by comparing slide content before and after.

---

## Phase 4: Q&A Preparation

### Question Generation

Generate questions from multiple perspectives:

1. **Methodology critics**: "Why this design? Why not...?"
2. **Domain experts**: Deep technical questions about the specific field
3. **Generalists**: "What does this mean for clinical practice?"
4. **Students/trainees**: Clarification questions about unfamiliar concepts

### Answer Structure

Every answer should follow the pattern:

```
Acknowledge → Evidence → Conclude

"That's an important limitation. [Acknowledge the concern honestly.]
However, [cite specific supporting evidence — author, year, finding].
So while [restate limitation], [conclude with the paper's contribution despite it]."
```

### Quick Review Sheet

A single-page reference for last-minute review:

```text
## Quick Review

### Must-Know Numbers
| Metric | Value | Source |
|--------|-------|--------|
| [Key stat 1] | [value] | [Ref] |
| [Key stat 2] | [value] | [Ref] |

### Common Pitfalls
- Don't confuse [X] with [Y]
- [Classification A] and [Classification B] are independent frameworks
- Slide says [rounded value], precise value is [exact value]

### Key Takeaways (memorize these)
1. [Point 1]
2. [Point 2]
3. [Point 3]
```

---

## Output File Structure

All outputs go in the user's presentation directory:

```
{presentation_dir}/
├── _analysis.md              # Phase 0: Paper analysis + outline
├── _references.md            # Phase 1: Verified references + key data
├── _script.md                # Phase 2: Speaker script
├── _qa_prep.md               # Phase 4: Expected Q&A
├── _quick_review.md          # Phase 4: Pre-presentation review sheet
├── inject_notes.py           # Phase 3: Tailored note injection script
├── figures/                  # Extracted paper figures (if needed)
└── reference/                # Supporting paper PDFs (if downloaded)
```

---

## Constraints

- **Never fabricate references.** Every citation must be verified against PubMed, DOI, or the PDF itself.
- **Never modify slide design** when injecting notes. Notes and slides are separate concerns.
- **Always ask audience first.** Do not start drafting until the target audience is defined.
- **Extension sections are opt-in.** Do not add AI/clinical/policy sections unless explicitly requested.
- **Respect presentation time.** Script length must match allocated time (roughly 130-150 words per minute for academic presentations).

## Anti-Hallucination

- **Never fabricate references.** All citations must be verified via `/search-lit` with confirmed DOI or PMID. Mark unverified references as `[UNVERIFIED - NEEDS MANUAL CHECK]`.
- **Never invent clinical definitions, diagnostic criteria, or guideline recommendations.** If uncertain, flag with `[VERIFY]` and ask the user.
- **Never fabricate numerical results** — compliance percentages, scores, effect sizes, or sample sizes must come from actual data or analysis output.
- If a reporting guideline item, journal policy, or clinical standard is uncertain, state the uncertainty rather than guessing.
