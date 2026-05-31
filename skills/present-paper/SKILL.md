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

### Step 0a — Load design references (read before drafting outline)

Before collecting inputs, the skill loads three reference files:

1. **`references/slide_design_principles.md`** — Reynolds (Presentation Zen) +
   Duarte (Slide:ology Glance Test™) + Knaflic (Storytelling with Data preattentive
   attributes) + Tufte (Cognitive Style of PowerPoint). Defines the 5 design
   principles, reading-time budgets per audience, cognitive-load ceilings, and the
   anti-patterns this skill is built to avoid. **Read this first** — it shifts the
   outline from "what content fits" to "what should the audience remember 10 seconds
   after each slide."
2. **`references/medical_presentation_templates.md`** — Section structure, slide counts,
   and design seeds for the 5 contexts: journal club, grand rounds, conference talk,
   lecture, and academic lecture multi-paper survey. Pick the matching template after
   Phase 0 inputs are collected, then customize.
3. **`references/slide_visual_styles/`** — visual style specs (color palette, typography,
   layout grid, slide-type templates) callable from any of the 5 context templates.
   Currently available: `nature_lancet.md` (Nature/Lancet aesthetic — white background,
   navy primary, coral accent, Inter/Pretendard). Default for academic lectures per
   `~/.claude/rules/academic-lecture-style.md`. Paired with the generic builder
   `templates/build_pptx_nature_lancet.py` and the PDF figure extractor
   `scripts/extract_pdf_figures.py`.

These two files mirror the entry-point pattern used in
`make-figures/references/design_principles.md` (Step 1 "Specify"). Both skills share
the same Reynolds / Knaflic / Tufte foundations — slide-level (this skill) and
figure-level (make-figures) are companions, not duplicates.

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

Generate a fully-editable PPTX from structured inline data using `python-pptx`. Two
canonical template libraries:

- `${CLAUDE_SKILL_DIR}/references/generate_pptx_templates.py` — generic T_lead /
  T_text / T_table / T_image_right / etc. templates with smoke-tested `main()`. Use
  for journal club, grand rounds, conference talk, and short paper talks.
- `${CLAUDE_SKILL_DIR}/templates/build_pptx_nature_lancet.py` — Nature/Lancet visual
  style (white + navy + coral, Inter/Pretendard, 47-slide academic lecture proven).
  Use for **academic lecture multi-paper survey** (template #5). Functions:
  `new_presentation`, `add_title_slide`, `add_toc_slide`, `add_section_divider`,
  `add_transition_slide`, `add_content_slide`, `add_glossary_slide`,
  `add_closing_slide`, plus `fix_app_xml()` helper. Style spec:
  `references/slide_visual_styles/nature_lancet.md`.

For lecture decks pulling figures from PDFs (rather than from `/make-figures`
output), use `${CLAUDE_SKILL_DIR}/scripts/extract_pdf_figures.py` — pdftoppm + PIL
crop with normalized (0–1) box coordinates. Supports both single-crop CLI and YAML
batch config.

After raw extraction, run `${CLAUDE_SKILL_DIR}/scripts/trim_caption.py` to
**auto-remove journal headers / figure captions / surrounding whitespace** so
that only the figure body remains — the Adobe-Acrobat-crop equivalent in
automation. The script uses horizontal-projection segmentation plus
text-band detection (height + density + gap + line-pattern signature) and
preserves multi-panel figures intact:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/trim_caption.py" \
  --in-dir  figures/extracted \
  --out-dir figures/cropped
```

Handles four common journal layouts: top running-head bar, bottom multi-line
caption (sparse text), bottom caption *fused* with figure body (no clear gap,
detected via narrow dark/light alternation), and multi-row tables with
footnotes (footnote cut, table rows preserved). No tesseract / OCR
dependency — Pillow + numpy only. Verified on 12-figure academic deck
(80–95% height retention; captions, journal banners, and CellPress-style
headers all removed). When the deck slot expects only the figure body
(default for `build_pptx_nature_lancet.py`), point `FIG_DIR` at the cropped
output dir.

### Word-boundary aware markdown parser (mandatory for HLA-rich decks)

When the build script parses inline `**bold**` / `*italic*` markers in slide
body or speaker notes, the italic rule must use **word-boundary lookahead /
lookbehind** so asterisk-bearing scientific tokens (HLA alleles like
`DRB1*07:01`, `HLA-A*02:01`, SNP IDs, footnote markers) are not eaten as
italic delimiters:

```python
import re
pattern = re.compile(
    r"(\*\*(?:(?!\*\*).)+?\*\*"                           # bold; inner single * allowed
    r"|(?<![A-Za-z0-9])\*[^*\n]+?\*(?![A-Za-z0-9]))"      # italic (word-boundary)
)
```

Two regex tricks together:
1. **Italic with boundary**: `(?<![A-Za-z0-9])` and `(?![A-Za-z0-9])` reject
   `*` adjacent to alphanumerics, so `DRB1*07:01` is left intact.
2. **Bold tolerates inner single `*`**: `(?:(?!\*\*).)+?` allows
   `**DRB1*04:02**` (HLA allele inside bold) to match as a single bold span.

Without these, a naive `\*[^*]+\*` italic pattern silently corrupts every
HLA allele in the deck. Add the regex to `add_styled()` (or equivalent) in
every Nature/Lancet-style build script.

### Pronunciation auto-augment for non-native presenters

For decks where the presenter is uncomfortable with English pronunciation of
acronyms, author names, drug names, or gene symbols, append a per-slide
`[ Pronunciation ]` section to the speaker notes (audience sees nothing —
only Presenter View). Use
`${CLAUDE_SKILL_DIR}/scripts/inject_pronunciation_notes.py`:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/inject_pronunciation_notes.py" \
  input.pptx output.pptx \
  --dict pron_dict.yaml \
  --header "[ 발음 ]"            # or any header you like
```

The script:
- Loads a YAML/JSON `PRON_DICT` (term → [reading, full_name]) supplied by
  the caller. The dict is domain-specific — assemble it for your audience
  (Korean readings, French readings, Spanish readings, etc.).
- Uses **word-boundary regex** `(?<![A-Za-z0-9_]) … (?![A-Za-z0-9_])` so
  short acronyms (e.g. `AE`, `OR`) only match when standalone, never inside
  other words.
- Recognizes allele-style tokens via a separate regex
  (`\b(?:HLA-)?[A-Z]{1,5}[0-9]?\*[0-9]{2}:[0-9]{2}\b` by default) and
  synthesizes their reading from the base allele entry in the dict.
- Skips slides that already contain the header (idempotent — safe to re-run).

Realistic yield on a 47-slide academic deck: ~38 slides receive a section,
~300 total term entries, 5–10 per annotated slide. Transition and divider
slides have empty notes and are auto-skipped.

### Speaker notes statistics density

When the slide body already shows exact OR / 95% CI / p-value, the notes
should NOT repeat the same numbers — the presenter ends up reading
statistics aloud and the audience cannot keep up. Notes should be a
**narrative** (key anchors + one-line "see the slide body for the exact
numbers" reminder), not a numeric listing.

Quick measurement to spot dense slides during QC:

```python
import re
text = slide.notes_slide.notes_text_frame.text.split(pron_header)[0]
n_char = len(text)
n_stat = len(re.findall(r"\b(?:OR|p|CI)\s*[=<>]?\s*\d|\d+\.\d+|\d+%|×10", text))
needs_compression = n_char > 1000 and n_stat >= 5
```

Rule of thumb: 700–1,000 chars + 0–2 stat tokens is fine (30–60-second
narrative). >1,000 chars + ≥5 stat tokens → compress to narrative tone and
point at the slide body. Exact numbers belong in the slide body and
footnotes (SSOT), not the notes.

### Sharing-ready notes-stripped variant

After the presentation, when the deck is shared with the audience (e.g. a
professor asking for the slides), the speaker notes typically contain
presenter-only material — second-language narrative, pronunciation hints,
self-referential reminders ("Prof. ○○ will likely ask about …"). Stripping
notes is mandatory before circulation. Use
`${CLAUDE_SKILL_DIR}/scripts/strip_notes_for_sharing.py`:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/strip_notes_for_sharing.py" \
  presenter_v9.pptx share/<topic>_<initials>.pptx
```

The script:
- Clears every slide's `notes_text_frame` (idempotent, slide body and
  figures untouched).
- Re-writes `docProps/app.xml` with the correct `Slides=` and `Notes=`
  counts so PowerPoint Mac does not show its repair dialog (see also the
  app.xml canonical fix in `pptx-mac-compatibility.md` §5).
- Verifies that zero notes characters remain.

Recommended 3-file sharing package (filename pattern `<topic>_<initials>`):
- `<topic>_<initials>.pptx` — notes-stripped variant for slide reuse
- `<topic>_<initials>.pdf` — same deck, PDF for environment-agnostic
  preview (LibreOffice `--convert-to pdf` automatically drops the cleared
  notes pages)
- `<topic>_<initials>_references.zip` — optional bundle of the reference
  PDFs; if it exceeds the email attachment limit, send a Google Drive link.

In the cover email, mention the PPTX is included specifically so the
recipient can reuse individual slides if useful.

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
| `T_image_right` | Body + figure on right | `title`, `body_lines[]`, `img_path`, `img_pct?` (PNG ≥300dpi or vector PDF — see Figure source formats below) |
| `T_quote_slide` | Verbatim citations, witness quotes | `title`, `quotes[]`, `body_after?`, `img_path?` |
| `T_two_col` | Compare/contrast | `title`, `left_lines[]`, `right_lines[]` |
| `T_two_col_with_box` | Compare + emphasis | as above + `metaphor_col`, `metaphor_lines[]` |
| `T_highlight_slide` | Single key result | `title`, `highlight_lines[]`, `body_before?` |
| `T_metaphor_body` | Body + analogy footer | `title`, `body_lines[]`, `metaphor_lines[]` |
| `T_table_two_col` | Take-aways + numeric table | `title`, `left_lines[]`, `headers[]`, `rows[][]` |

### Figure source formats (when consuming `/make-figures` output)

When the deck pulls figures from `analysis/figures/` produced by `/make-figures`:

- **Preferred for slides**: PNG at ≥300 dpi. python-pptx `add_picture()` handles this directly. Set `img_pct` (template `T_image_right`) so the figure occupies ≥40 % of slide width on a 13.33 × 7.5-in widescreen layout.
- **Vector source available**: prefer PDF only if the slide will be projected at >1080p or printed as a handout — convert PDF → PNG at the target DPI (`pdftoppm -r 300 input.pdf out_prefix`) before insertion, because python-pptx PDF embedding is unreliable across PowerPoint versions.
- **Forbidden**: TIFF (Mac PowerPoint silently drops it — see Mac compatibility checklist below); JPEG for line art (compression artifacts on diagonal lines); raw SVG (PowerPoint Mac handles it inconsistently).
- **Caption / legend**: re-draft for spoken-narration context, not the journal legend verbatim. The journal legend assumes a reader; the slide caption assumes a listener with 5–10 seconds of attention.

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

### Step 3.5 — Slide critic (run before delivering deck)

After exporting the PPTX, run the slide critic rubric at
`references/critic_rubrics/slide.md`. Score each slide and the deck-level Mac
compatibility checks (Section F) as PASS / PARTIAL / FAIL. Produce concrete edits for
every FAIL or PARTIAL item before treating the deck as ready.

Mandatory deck-level checks (cross-link with `~/.claude/rules/pptx-mac-compatibility.md`):

```bash
# F.22 No TIFF
find ppt/media -iname '*.tif*' || true   # must be empty

# F.23 No 3-D bevel
grep -l '<a:sp3d>' ppt/slides/*.xml      # must be empty

# F.24 app.xml count sync
grep -c '<Slides>\|<Notes>' docProps/app.xml
ls ppt/slides/slide*.xml | wc -l         # must match

# F.25 srcRect bounds (any value > 100000 = bug)
grep -oE '"[0-9]{6,}"' ppt/slides/*.xml | head
```

Record `critic_pass: yes | partial | no` and `refine_rounds: N` in `_quick_review.md`.

**Mode B: Add notes to existing slides** (more common)
- Read existing PPTX to understand slide structure and count
- Map speaker script sections to corresponding slides
- Generate `inject_notes.py` script tailored to the specific presentation

### Note Injection Script

Generate a tailored `inject_notes.py` following the pattern in
`${CLAUDE_SKILL_DIR}/scripts/inject_speaker_notes.py`. The generated script should
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
├── _quick_review.md          # Phase 4: Pre-presentation review sheet + critic_pass record
├── _slide_critic.md          # Phase 3.5: Slide rubric scores per slide
├── inject_notes.py           # Phase 3: Tailored note injection script
├── figures/                  # Extracted paper figures (if needed)
└── reference/                # Supporting paper PDFs (if downloaded)
```

## Cross-skill / Cross-rule integration

This skill composes with adjacent skills and global rules:

| When | Use | Why |
|---|---|---|
| Need a figure on a slide (ROC, forest, KM, flow) | `/make-figures` first, then embed | Both skills share Reynolds/Knaflic/Tufte foundations; figure-level + slide-level companions |
| Manuscript reporting checklist parallel | `/check-reporting` for the same paper | Paper presentations often shadow manuscript revision; reporting-guideline gaps surface in Q&A |
| Visual abstract / Central Illustration | `/make-figures` visual-abstract templates | Then verify against `~/.claude/rules/journal-ai-image-policies.md` (JACC prohibits, Radiology allows with disclosure) |
| PPTX edits to existing institutional template | `~/.claude/rules/pptx-mac-compatibility.md` | Patch over rebuild; preserve master/layout/srcRect |
| Manuscript companion deck | `~/.claude/rules/manuscript-style-classical.md` | Heading style, AI-Disclosure policy, em-dash discipline carry over to slides for senior MA reviewer audiences |
| References on slides | `/verify-refs` (audit-only) before delivery | Same anti-hallucination gate as manuscript references |

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
