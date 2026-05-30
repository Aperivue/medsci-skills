# Slide Visual Style — Nature / Lancet

Design spec for academic lecture, journal club, and conference-talk slides modeled
on the Nature / Lancet journal aesthetic. White background, navy primary, restrained
coral accent, hairline dividers, two-font sans-serif system.

> **Triggered from**: SKILL.md Phase 3 (Slides & Notes). Pair with
> `references/medical_presentation_templates.md` Template #5 "Academic lecture
> (multi-paper)". Reference build script: `templates/build_pptx_nature_lancet.py`.

---

## 1. Color palette

| Token | Hex | Usage |
|---|---|---|
| `NAVY` | `#1B2A4E` | Primary text on white, section title, headline |
| `NAVY_LIGHT` | `#3F5A8C` | Secondary navy (sub-headings, accents on dark bg) |
| `TEXT` | `#21252B` | Body text |
| `TEXT_SUB` | `#4A525C` | Sub-text, captions, subtitles |
| `MUTED` | `#8A929E` | Footer, page brand, low-emphasis labels |
| `HAIRLINE` | `#CCD0D6` | Thin dividers, image borders |
| `HIGHLIGHT` | `#B83E3A` | Coral accent — reserved for 1–2 emphasis points per slide |
| `WHITE` | `#FFFFFF` | Backgrounds, dark-bg text |
| `BG_SOFT` | `#F8F9FB` | Subtle panel background (optional) |
| `DIVIDER_BG` | `#121D36` | Section-divider slide background (deep navy) |

**Rule of restraint**: a content slide uses **white + navy + 1 coral accent**. Three
colors maximum. Avoid full-bleed bright bars, gradients, drop shadows beyond the
single 6pt offset on figure tiles.

## 2. Typography

| Role | Font (Latin) | Font (EastAsia / Korean) | Size | Weight |
|---|---|---|---|---|
| Slide title | Inter | Pretendard | 28–32 pt | Bold |
| Subtitle / sentence-headline | Inter | Pretendard | 15–18 pt | Italic |
| Body bullet (main) | Inter | Pretendard | 18–20 pt | Regular |
| Body bullet (sub) | Inter | Pretendard | 15–16 pt | Regular |
| Eyebrow text | Inter | Pretendard | 10–14 pt | Bold, letter-spaced 300–400 |
| Section title (divider) | Inter | Pretendard | 48–52 pt | Bold |
| Transition quote | Inter | Pretendard | 36 pt | Bold |
| Page-brand footer | Inter | Pretendard | 9 pt | Regular, letter-spaced 300 |
| Speaker notes | Inter | Pretendard | 13 pt | Regular |

**Font install** (macOS):
```bash
brew install --cask font-pretendard font-inter
```

EastAsia attribute **must** be set on every run that may contain Korean text — Mac
PowerPoint falls back to Times New Roman otherwise. See
`~/.claude/rules/pptx-mac-compatibility.md` §6.

## 3. Layout grid (16:9, 13.333" × 7.5")

| Region | Position | Content |
|---|---|---|
| Eyebrow | x=0.7", y=0.32", w=8", h=0.4" | All-caps topic label (10–14pt, coral or muted) |
| Title | x=0.7", y=0.75", w=12.0", h=1.1" | Slide title + optional subtitle |
| Hairline | x=0.7", y=2.05", w=0.6", h≈0.02" | Coral hairline (separator) |
| Body (no figure) | x=0.7", y=2.4", w=12.0", h=4.6" | Bullets full width |
| Body (with figure) | x=0.7", y=2.4", w=6.8", h=4.6" | Bullets left half |
| Figure (right half) | x=7.9", y=2.4", w=5.0", h=4.0" | Centered within tile |
| Figure caption | x=7.9", y=fig+0.10", w=5.0", h=0.6" | "Figure · {caption}" centered |
| Footer (page brand) | x=0.7", y=7.05", w=4.0", h=0.35" | "2026 · NEUROGENETICS" pattern |
| Footnote | x=0.7", y=7.05", w=12.0", h=0.35" | Right-aligned source ref |

**Margins**: 0.7" left/right, 0.32" top eyebrow, 0.35" bottom footer. Title-body
separation enforced by the **0.6" coral hairline** (never a 0.05"-tall bar).

## 4. Slide type templates

### 4a. Title slide
- Left navy bar (40k EMU wide × 3.5" tall) at x=0.7"
- "REVIEW LECTURE" eyebrow (14pt, coral, letter-spaced 300)
- 48pt navy bold title
- 18pt italic subtitle (TEXT_SUB)
- Bottom block: 16pt bold navy line ("Course · Professor · Date"), 13pt sub line
  ("Presenter Name · Affiliation"), separated by 2" navy hairline above

### 4b. Section divider
- Full-bleed deep navy background (`DIVIDER_BG`)
- 1.8"-tall coral accent strip at x=1.2", y=3.0", 15k EMU wide
- "SECTION {N}" 18pt coral eyebrow letter-spaced 400
- 52pt white bold section title
- 20pt italic light-navy (`#C0CBDC`) subtitle
- Bottom-right "{N} MIN" badge (13pt muted)

### 4c. Transition slide
- Full-bleed deep navy background
- Large coral curly quotes (72pt) flanking a 36pt white bold single-sentence question
- Center-anchored vertically

### 4d. Content slide
- Eyebrow (small caps topic label) → title + subtitle → coral hairline → bullets
  (left if figure, full-width if no figure) → figure tile (shadow offset 0.06",
  hairline border) → optional figure caption → footnote (right) + page brand (left)
- Bullet markers:
  - Main: `▪` (14pt coral bold) + 20pt body text
  - Sub (lines prefixed with 2 spaces): `—` (15pt muted) + 16pt sub text
- Inline `**bold**` and `*italic*` markdown is parsed into per-run styling (see
  `pptx-mac-compatibility.md` §4 for the parser pattern)

### 4e. TOC / outline slide
- Eyebrow "OUTLINE"
- Title "Outline" + sentence subtitle
- Coral hairline
- N rows, each: 22pt coral section number (or `·` for wrap-up), 22pt navy bold section
  title, 13pt sub-text English summary, 12pt muted time badge (right-aligned). Hairline
  divider between rows.

### 4f. Glossary slide (optional, for multidisciplinary audiences)
- Tier 1 (top, 4–7 items): disease/concept abbreviations with one-line context
- Tier 2 (bottom, 2-column, 8–12): method/statistics abbreviations with short defs
- See `~/.claude/rules/multidisciplinary-presentation.md` §1

### 4g. Closing slide
- Title "Take-home messages" or "Conclusions"
- 3 bullet maximum
- Optional contact / acknowledgments block at bottom

## 5. Figure handling

- Aspect-ratio preserving fit inside the figure tile (5.0" × 4.0" max)
- Shadow rectangle (hairline gray) offset +0.06" / +0.06" before image
- Image border: hairline gray (~6000 EMU)
- Caption format: `Figure  ·  {caption}` (coral "Figure" eyebrow, italic muted caption)

**EMU pitfall**: compute width/height in **inches** before wrapping in
`Inches()`. Never `Inches(fig_w / aspect_ratio)` when `fig_w` is already a pixel
value — see `pptx-mac-compatibility.md` §7.

## 6. Speaker notes density

- Korean narrative (서술형, `~합니다`체) per `~/.claude/rules/academic-lecture-style.md` §1
- 150–300 Korean characters per slide (30–60 seconds spoken)
- Run-level markdown parser for `**bold**` / `*italic*` (see
  `pptx-mac-compatibility.md` §4)
- 13pt Pretendard

## 7. Mac compatibility checklist (run before delivery)

| Check | Command |
|---|---|
| TIFF images | `find ppt/media -iname '*.tif*'` → must be empty |
| 3D bevel | `grep -l '<a:sp3d>' ppt/slides/*.xml` → must be empty |
| app.xml count sync | `unzip -p out.pptx docProps/app.xml \| grep -oE '<Slides>[0-9]+</Slides>'` → ≠ 0 |
| Raw markdown in notes | `unzip -p out.pptx ppt/notesSlides/notesSlide3.xml \| grep -oE '\*\*[^<*]+\*\*' \| wc -l` → 0 |
| Korean glyph in notes | `unzip -p out.pptx ppt/notesSlides/notesSlide3.xml \| grep -oE '[가-힣]+' \| head -5` → renders |

Always validate on **Mac PowerPoint** + PDF export. PDF alone misses some defects
(see `pptx-mac-compatibility.md` §1–§3).

## 8. Reference implementation

Canonical build script: `templates/build_pptx_nature_lancet.py` (in this skill).

Example output: 47-slide academic lecture deck (4-section narrative across multiple
lighthouse papers + supporting references), Mac PowerPoint verified.

## Cross-references

- `~/.claude/rules/academic-lecture-style.md` — global style rule (English body + Korean notes + this design)
- `~/.claude/rules/pptx-mac-compatibility.md` — Mac compatibility (TIFF / sp3d / app.xml / Inches EMU / markdown notes)
- `~/.claude/rules/multidisciplinary-presentation.md` — glossary slide + intuition box pattern
- `references/medical_presentation_templates.md` Template #5 — Academic lecture (multi-paper)
- `references/slide_design_principles.md` — Reynolds / Duarte / Knaflic / Tufte foundations
