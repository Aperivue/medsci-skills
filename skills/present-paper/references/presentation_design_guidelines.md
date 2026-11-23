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
  large room is the target; titles larger (28–40 pt). The hard floor is 20 pt: that is what
  `check_deck_budget.py` enforces for a conference talk or a lecture, and what the medsci
  template's smallest body slots use. Between 20 and 24 pt is allowed, not aimed for. Footnotes/captions may go to ~14–18 pt but
  carry nothing the audience must read in real time.
- **≤ 6 lines of body text per slide**; ≤ ~10–12 words per line. Prefer phrases to
  sentences in bullets.
- **Sentence case** for bullets (easier to read than Title Case); reserve ALL-CAPS for
  short eyebrow labels only.

## 3. Space — let it breathe

- **30–35% of every content slide should be empty.** Negative space focuses attention
  and reads as confident, not unfinished.
- Consistent margins and a single alignment grid. One or two accented elements per slide,
  not five.

## 4. Color — restraint + accessibility (non-negotiable for medical talks)

- **A neutral background, one text colour, and at most two accents** per deck. Each accent
  means one thing from the first slide to the last: the first marks the point of the slide, the
  second what it is set against (the comparator, the exception, the caution). The colour of a
  term in the text is the colour of its curve, bar, arrow or table cell. Colour is never the only
  carrier: the two accents can look alike to a colour-blind reader and do in a greyscale print,
  so the wording, the position or a label says the same thing.
- **Emphasise with colour before weight.** A phrase in the accent colour is found at a glance; a
  bold phrase in the text colour is found only by reading. Mark a phrase, not a sentence, and not
  more than one or two phrases a slide: when half the slide is coloured, nothing is.
- **A figure sits on the slide's own ground.** Draw it on pure white (or transparent) for a white
  slide and on black for a black one. A plot saved on an off-white or grey panel shows on the
  slide as a tinted rectangle; set the figure and axes face colour, and look at the render.
- **A slide of text alone gets one thing to look at, taken from the study.** A small table of the
  actual values, the paper's own panel, a plot drawn from the data. Not a row of three or four
  oversized numbers with captions, which reads as a dashboard and as generated (see
  `ai_slide_tells.md` §3), and not an icon or stock picture that carries no information.
- **Short lines do not wrap.** A take-home line, a headline or a label set in large type is cut
  until it fits on one line; a stray last word on a second line is the first thing the eye lands
  on. In a two-column arrangement the column of short names is the narrow one.
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
- **A talk about your own paper may show that paper's own panels.** Crop to the one panel the
  slide narrates and use it when its labels can be read at slide size; redraw when they cannot, or
  when no published panel carries the slide's claim. Showing a figure in a room and handing out
  the deck are different acts: check the article's licence before the file is shared.
- **A crop keeps what is needed to read the evidence.** Before a cropped panel goes on a slide,
  look at it at the size it will be shown and check that none of these is cut or covered: the
  panel letter the slide refers to; both axes with their titles, ticks and units; the legend, the
  colour bar and the scale bar; group and condition names; a table's header row. On an image:
  the side marker, the orientation and the plane or sequence label stay; patient fields go (from
  the pixels and the metadata, not under a shape). Leave a small margin instead of cutting at
  the ink, and keep the slide's own label or arrow off the figure's labels. If the crop cannot
  keep them and stay legible, widen it, give the figure the whole slide, split it over two
  slides, or redraw the few numbers as a table.
- **Every borrowed figure carries a source line, and a row in the image log.** On the slide, at
  least: figure and panel, first author, journal, year (`Fig. 2b · Author, Journal 2024`),
  through the layout's source slot or `new_deck.credit`. A figure you redrew from someone's data
  says so (`Redrawn from Fig. 2b · ...`); your own unpublished figure needs no line. That line is
  a citation, not a licence notice: a copy of the deck that leaves the room carries whatever the
  licence or permission asks for as well (for CC BY, the licence name or link and a note that the
  panel was cropped or adapted), on the slide or on a credits slide at the end. The log is the one
  in `references/generated_illustrations.md` §4, `assets/SOURCES.md`; for a panel taken from a
  paper its row also gives the source figure and panel, the page, how it was extracted and
  cropped, what was left out on purpose and the slide it is on, so a corrected figure can be
  re-cut the same way.
- A slide table is **≤ ~5 rows × ≤ ~5 columns** at ≥ 16 pt. More than that → move it to
  a backup slide or hand it out.
- Figure captions on a slide are written **for a listener** (one phrase), not the
  journal legend verbatim (written for a reader).
- Generate analysis figures with `/make-figures` (PNG ≥ 300 dpi); crop journal-PDF
  figures with `scripts/trim_caption.py` so only the figure body remains.

## 6. Animation & transitions — sparing

- Use builds **only** where one step is needed to follow the next: layered data (e.g. add one
  curve at a time), or blocks the speaker walks through in that order. Items meant to be
  compared stay on screen together.
- **No decorative transitions** (cube, dissolve, fly-in). Excessive motion distracts the
  audience from the content and reads as amateur.

## 7. Citations & integrity

- Cite sources with a **concise in-slide reference** (Author Year, or a small numeric
  superscript), not a full reference list on the slide.
- Numbers on slides must match the manuscript/analysis exactly (the slide is not the
  SSOT). Run `/verify-refs` before delivery for any cited reference.
- Re-use of a published figure in slides is generally acceptable for scholarly critique
  **with on-slide attribution**; do not carry a lifted figure into the manuscript
  without the publisher's permission.

## 8. Delivery-facing rules (carried by other skill assets)

- **Body language = English; speaker notes = the presenter's language** for non-native
  English presenters. Size each slide's notes to the time that slide gets, at
  speaking pace: about 130–150 words a minute in English, about 300 characters a minute in
  Korean. The notes of the presented slides together fill the slot; a 10-minute talk is about
  1,300–1,500 English words or about 3,000 Korean characters, not 300 characters times the
  number of slides.
- **Mac PowerPoint compatibility** is mandatory before delivery — TIFF→PNG, no `sp3d`,
  app.xml count sync, no raw `**markdown**` leaking into notes
  (checklist: `references/slide_visual_styles/nature_lancet.md` §7).
- For a multidisciplinary audience, add a glossary slide.

---

## Quick self-check (Phase 3.5)

| # | Rule | Pass if |
|---|------|---------|
| G1 | Headline is an assertion | Title is a sentence/claim, not a topic word |
| G2 | One idea per slide | ≤ 2 assertions; ≤ 6 body lines |
| G3 | 24-pt floor | Body ≥ 24 pt; nothing the audience must read < 24 pt |
| G4 | Negative space | ≥ ~30% of the slide is empty |
| G5 | Color restraint | ≤ 2 accents in the deck, each with one meaning; 1–2 accented phrases per slide |
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
