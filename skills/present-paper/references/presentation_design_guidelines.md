# Presentation Design Guidelines (operational)

Practical, enforceable rules for building a talk. This is the **operational** companion
to `references/slide_design_principles.md` (which holds the Reynolds / Duarte / Knaflic /
Tufte *theory*). Where the principles file answers *"what should the audience remember?"*,
this file answers *"what concrete rule do I apply on this slide right now?"* — sizes,
ratios, counts, and the medical-talk specifics.

Apply these during Phase 0 (outline), Phase 2 (script), and Phase 3 (slides). The
Phase 3.5 slide critic scores against them.

---

## 1. Structure — one idea per slide (assertion–evidence)

- **Headline = a full assertion, not a topic.** Write the slide title as a sentence
  the audience should believe after the slide (e.g. *"About half is reported"*, not
  *"Results"*). The body is the *evidence* for that assertion — a figure, a small
  table, or ≤3 short bullets — never a bullet list that repeats the headline.
- **One or two points per slide, maximum.** If a slide carries two assertions, split it.
- **The slide is the evidence; you are the narration.** Reduce text so the words come
  from the speaker, not the screen. The audience cannot read and listen at the same time.
- **Slide budget**: ≈ 1 slide per 45–60 s of talk for a conference talk; ≈ 1 per
  60–90 s for a lecture. An 8-min talk → ~9–11 content slides. Do not exceed.

## 2. Text — the 24-point floor

- **If a font is smaller than 24 pt, treat it as invisible.** Body text ≥ 24 pt for a
  large room; titles larger (28–40 pt). Footnotes/captions may go to ~14–18 pt but
  carry nothing the audience must read in real time.
- **≤ 6 lines of body text per slide**; ≤ ~10–12 words per line. Prefer phrases to
  sentences in bullets.
- **Sentence case** for bullets (easier to read than Title Case); reserve ALL-CAPS for
  short eyebrow labels only.

## 3. Space — let it breathe

- **30–35% of every content slide should be empty.** Negative space focuses attention
  and reads as confident, not unfinished.
- Consistent margins and a single alignment grid. One coral/accent element per slide,
  not five.

## 4. Color — restraint + accessibility (non-negotiable for medical talks)

- **Two to three colors maximum** per deck: one neutral background, one primary
  (text/structure), one accent (reserved for the single thing that matters on a slide).
- **Contrast ≥ 4.5:1** for all body text (WCAG AA). Dark text on off-white, or light
  text on deep navy — never mid-gray on white.
- **Do not encode meaning by red/green alone.** ~8% of men have red-green color
  vision deficiency. Two safe paths:
  1. **Redundant encoding** — pair color with a letter/shape/position. A PROBAST/RoB
     traffic-light (green/amber/red) is acceptable *only because* each cell also shows
     `L / U / H`; the letter, not the color, carries the judgement.
  2. **Colorblind-safe palette** — use the **Okabe–Ito** 8-color set (below) or a
     **Paul Tol** qualitative scheme for any categorical chart.
- **Okabe–Ito (CVD-safe, Nature Methods–endorsed)**: `#000000` black · `#E69F00`
  orange · `#56B4E9` sky blue · `#009E73` green · `#F0E442` yellow · `#0072B2` blue ·
  `#D55E00` vermillion · `#CC79A7` purple.

## 5. Tables & figures — redraw, don't screenshot

- **Never paste a raw screenshot of a journal table or a multi-panel figure.** Re-draw
  the 2–4 numbers that matter into a clean, large-font native table, or crop to the
  single panel you will narrate.
- A slide table is **≤ ~5 rows × ≤ ~5 columns** at ≥ 16 pt. More than that → move it to
  a backup slide or hand it out.
- Figure captions on a slide are written **for a listener** (one phrase), not the
  journal legend verbatim (written for a reader).
- Generate analysis figures with `/make-figures` (PNG ≥ 300 dpi); crop journal-PDF
  figures with `scripts/trim_caption.py` so only the figure body remains.

## 6. Animation & transitions — sparing

- Use builds **only** to reveal layered data step-by-step (e.g. add one curve at a time).
- **No decorative transitions** (cube, dissolve, fly-in). Excessive motion distracts the
  audience from the content and reads as amateur.

## 7. Citations & integrity

- Cite sources with a **concise in-slide reference** (Author Year, or a small numeric
  superscript), not a full reference list on the slide.
- Numbers on slides must match the manuscript/analysis exactly (the slide is not the
  SSOT). Run `/verify-refs` before delivery for any cited reference.
- Re-use of a published figure in slides is generally acceptable for scholarly critique
  **with on-slide attribution**; do not carry a lifted figure into the manuscript
  without permission (`~/.claude/rules/journal-ai-image-policies.md`).

## 8. Delivery-facing rules (carried by other skill assets)

- **Body language = English; speaker notes = the presenter's language** for non-native
  English presenters (`~/.claude/rules/academic-lecture-style.md`). Notes 150–300
  characters/slide (30–60 s).
- **Mac PowerPoint compatibility** is mandatory before delivery — TIFF→PNG, no `sp3d`,
  app.xml count sync, no raw `**markdown**` leaking into notes
  (`~/.claude/rules/pptx-mac-compatibility.md`; checklist in each visual-style spec).
- For a multidisciplinary audience, add a glossary slide
  (`~/.claude/rules/multidisciplinary-presentation.md`).

---

## Quick self-check (Phase 3.5)

| # | Rule | Pass if |
|---|------|---------|
| G1 | Headline is an assertion | Title is a sentence/claim, not a topic word |
| G2 | One idea per slide | ≤ 2 assertions; ≤ 6 body lines |
| G3 | 24-pt floor | Body ≥ 24 pt; nothing the audience must read < 24 pt |
| G4 | Negative space | ≥ ~30% of the slide is empty |
| G5 | Color restraint | ≤ 3 colors; 1 accent use per slide |
| G6 | CVD-safe | No meaning by red/green alone (redundant letter/shape, or Okabe–Ito) |
| G7 | Contrast | Body text ≥ 4.5:1 on its background |
| G8 | Tables redrawn | No raw journal-table screenshot; ≤ 5×5 native |
| G9 | Animation discipline | Builds only for layered reveal; no decorative transitions |
| G10 | Citations | Concise in-slide cite; numbers match SSOT |

---

## Sources

- Reynolds, *Presentation Zen* — design for the back of the room, high signal-to-noise:
  https://www.presentationzen.com/ and https://www.garrreynolds.com/design-tips
- Duarte, *slide:ology* — "slides are signs"; the Glance Test.
- Knaflic, *Storytelling with Data* — eliminate clutter, focus attention, tell a story.
- Assertion–evidence method (Penn State, Michael Alley): https://www.craftofscientificpresentations.com/ ;
  iBiology, *Rethinking Scientific Presentations*: https://www.ibiology.org/professional-development/power-point-slide-design/
- Good Practice for Conference Abstracts and Presentations (GPCAP), PMC6551883:
  https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6551883/
- Medical slide design / 24-pt rule, negative space, avoid red-green, redraw tables:
  https://editverse.com/creating-stunning-medical-presentations-with-powerpoint-2025-best-practices/ ;
  https://www.slidegenius.com/blog/design-principles-to-enhance-readability-in-healthcare-presentations ;
  UCSF Medical Education slide-design tips: https://meded.ucsf.edu/node/8625
- Okabe–Ito & Paul Tol colorblind-safe palettes: https://jfly.uni-koeln.de/color/ (Okabe & Ito) ;
  https://personal.sron.nl/~pault/ (Tol)
