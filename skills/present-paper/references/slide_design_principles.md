# Effective Slide Design for Medical Presentations

> **Primary sources** (cite when invoking specific principles):
> - Reynolds G., *Presentation Zen: Simple Ideas on Presentation Design and Delivery*, 3rd ed.
>   New Riders, 2019. — Simplicity / Clarity / Restraint / Harmony.
> - Duarte N., *Slide:ology: The Art and Science of Creating Great Presentations*. O'Reilly, 2008.
>   — Glance Test™ (3-second rule); slides as "glance media."
> - Knaflic CN., *Storytelling with Data: A Data Visualization Guide for Business Professionals*.
>   Wiley, 2015. — Preattentive attributes (size, color, position).
> - Tufte ER., *The Cognitive Style of PowerPoint: Pitching Out Corrupts Within*, 2nd ed.
>   Graphics Press, 2006. — Chartjunk; data-ink ratio; bullet-point critique.
>
> **Medical-presentation specific**:
> - Bhargava R, et al. "Winning at the Radiology Podium: First-timer's Guide to Crafting and
>   Delivering a Memorable Conference Presentation." *RadioGraphics* 2025; DOI 10.1148/rg.250003.
> - RSNA Refresher Course Committee guidelines (case-based, audience-response interactive format).
>
> **Triggered from**: SKILL.md Phase 0 (Outline) and Phase 3 (Slides). Read this file **before**
> sketching the slide outline — it shifts focus from "what content fits" to "what should the
> audience remember 10 seconds after each slide."

Most slide-design guidance focuses on aesthetic templates (color, font, layout). This file
adds a communication-first layer: how the audience parses a slide under time pressure, what
they retain, and how the slide supports the speaker rather than replacing them.

---

## The 5 design principles (read in order)

### 1. Identify the key message *(most important)*

Before opening PowerPoint or python-pptx, write **one sentence** describing what the slide
must convey. If you cannot, the slide is premature. Examples:

- "Adjuvant RFA reduces local recurrence vs. surgery alone (HR 0.62)."
- "FLAIR sequence highlights the lesion that T2 missed."
- "The proposed CAD model maintains AUC across three external sites."

Pin that sentence at the top of the slide outline (Phase 0 of SKILL.md). Every bullet,
figure, color, and animation exists to support that one sentence; anything that does not
should be removed or moved to a separate slide.

A slide with **two key messages is two slides**.

### 2. Audience-aware reading-time budget

Different presentation contexts allow different inspection time per slide. Set the
**reading-time budget** in Phase 0, then design backwards.

| Context | Reading time | Implication |
|---|---|---|
| Journal club (peer trainees) | 30–60 s/slide narrated | Methodology detail acceptable; figures from paper allowed |
| Grand rounds (mixed audience) | 20–40 s/slide narrated | Plain-language framing; one teaching point per slide |
| Conference talk (RSNA / ECR) | 15–30 s/slide narrated | Direct labels mandatory; data visuals over text |
| Lecture / didactic (residents) | 60–120 s/slide narrated | Worked examples; build-ups acceptable; recap slides |
| Visual abstract (no narration) | 5–10 s total | One panel; minimal text; readable thumbnail |

The same paper presented at journal club and at RSNA needs **two different decks** — the
RSNA version usually drops half of what the journal-club version contains.

### 3. The Glance Test (Duarte) — 3-second rule

After each slide is drafted, perform the Glance Test™:

> *Can the audience grasp the slide's meaning within 3 seconds, then return their attention
> to the speaker?*

If a slide fails the test, the audience is **reading the slide** instead of **listening to
the speaker**. People cannot read and listen simultaneously; one channel wins, and on slides
the reading channel wins. Slides are *glance media*, not reading documents.

Failure modes that break the Glance Test:
- ≥ 6 lines of body text (audience starts reading paragraph-style).
- Two competing visuals (eye does not know where to land).
- A title that does not state the conclusion (forces reading the body to find the point).

**Fix patterns**:
- Convert the slide title from a topic ("Methods") to a sentence-summary ("Inclusion required
  ≥ 1 cm tumor on MRI").
- Split into 2 slides if the message is genuinely two-part.
- Replace bullets with one annotated figure.

### 4. Reduce cognitive load (Reynolds + Tufte)

Working memory holds ~7 items, and a slide must compete with the speaker's voice. Design
under that ceiling.

| Element | Slide ceiling | Reason |
|---|---|---|
| Body text lines | ≤ 6 | Beyond 6, audience reads instead of listening |
| Distinct colors | ≤ 3 + 1 accent | More colors fragment attention |
| Fonts | ≤ 2 (title + body) | Mixed fonts break institutional brand and look unfinished |
| Bullet levels | ≤ 2 | Deep nesting (3 indents) signals reading-document |
| Chart types per slide | 1 | Two charts compete for attention |
| Animations | only purposeful | Decorative motion = noise |

Tufte's data-ink ratio applies: every pixel should encode either content or essential
context. 3-D bars, drop shadows, gradient fills, and rotated axis labels add ink without
data — remove them. The Columbia Space Shuttle disaster slide is the canonical
counterexample: the O-ring failure data was buried in small type on a crowded slide.

### 5. Native objects, not images

Charts, tables, and diagrams must be **editable native PowerPoint objects**, not exported
images. This is non-negotiable in academic medicine because:

- Co-authors edit numbers in revision rounds.
- Mac PowerPoint renders TIFF/SVG inconsistently (see `pptx-mac-compatibility` rule).
- Reviewers / session chairs may project the deck on lower-resolution displays where
  rasterized charts pixelate.

Specifically:
- Excel-linked charts → double-click opens the data table.
- Tables → native PowerPoint tables, not screenshots.
- Flow diagrams → grouped shapes, not a `make-figures` PNG export embedded as image.
- Single fonts (Pretendard / Apple SD Gothic Neo for Korean decks; Helvetica/Calibri for
  English-only) — declared once at the deck level, not per-slide.

Allowed exceptions: photographs, anatomical illustrations (SMART Servier, NIAID BioArt),
medical imaging frames (CT/MRI slices) — all rasterized by nature.

---

## Preattentive attributes (Knaflic) — directing audience attention

Preattentive attributes are visual properties the brain processes automatically (in <250 ms,
before conscious attention). Use them to guide the audience to the part of the slide that
matters.

| Attribute | Use for | Example |
|---|---|---|
| **Size** | Hierarchy: title > subtitle > body | Take-home line at 32 pt; body at 18 pt |
| **Color saturation** | Highlight 1 element vs. background | Key result row in orange; comparators in gray |
| **Position** | Left-to-right reading order; top = priority | Conclusion at top of slide, not bottom |
| **Bold weight** | Emphasize the key number in a sentence | "AUC = **0.91** (95% CI 0.87–0.94)" |
| **Enclosure** | Group related elements | Box around the "key finding" panel |
| **Spatial separation** | Group vs. distinguish | Whitespace between Methods and Results panels |

**Two purposes**: (1) draw immediate attention to a key element; (2) build a visual
hierarchy that walks the eye through the content.

**Anti-pattern**: applying preattentive emphasis to *everything* — when 5 things are bold,
red, and boxed, none of them stand out.

---

## Slide-anti-patterns (cumulative — drawn from this skill's critic rubric)

These compose with the more granular checks in `critic_rubrics/slide.md`:

- **Topic-titled slide** — title says "Results" instead of stating the result. Fix: convert
  to a sentence-headline ("RFA reduced local recurrence by 38%").
- **Wall-of-text** — > 6 body lines, full sentences. Fix: replace with one annotated figure
  + the take-home sentence at top.
- **Bullet-cascade** — 3-level nested bullets. Fix: split into 2 slides or use a 2-column
  layout.
- **Chart junk** — 3-D bar, gradient fill, rotated axis label, secondary y-axis with no
  shared scale. Fix: 2-D, single y-axis, direct labels.
- **Image-of-table** — pasted screenshot of a table from the paper. Fix: rebuild as native
  PowerPoint table; keep the paper-table image for backup slides only.
- **Reference-flood** — citation list slide listing 15 references at 8 pt. Fix: cite
  inline at point-of-use (`[Smith 2024]`); full bibliography in handout/supplementary.
- **Logo-tax** — institutional logos on every slide masking content. Fix: title slide and
  closing slide only; corner-only on intermediate slides if mandated.
- **AI-image without disclosure** — AI-generated illustration on a slide destined for a
  journal that prohibits AI imagery. Fix: see `journal-ai-image-policies` rule before
  building visual abstract / Central Illustration.

---

## Cognitive load checklist (Phase 3 quick scan)

Before exporting to PPTX, walk every slide:

- [ ] One-sentence key message stated at slide top (sentence-headline).
- [ ] Body text ≤ 6 lines.
- [ ] Glance test ≤ 3 seconds.
- [ ] Colors ≤ 3 + 1 accent; carry meaning, not decoration.
- [ ] Fonts ≤ 2 throughout deck; ≥ 18 pt body for slides; ≥ 24 pt for posters.
- [ ] Charts/tables are native objects (not images).
- [ ] No 3-D / drop-shadow / gradient unless data-driven.
- [ ] Direct labels on chart series; legends only when ≥ 4 series.
- [ ] Same slide works in grayscale (run a `convert -colorspace Gray` test).
- [ ] AI-image policy verified for target audience/journal context.

If two or more boxes are unchecked, return to Phase 0 outline before continuing.

---

## Cross-references

- `critic_rubrics/slide.md` — quantitative critic checks per slide
- `medical_presentation_templates.md` — section structure for journal club, grand rounds,
  conference, lecture
- `workflow-checklist.md` — end-to-end Phase 0 → 4 production checklist
- `make-figures/references/design_principles.md` — figure-level design (this skill is the
  slide-level companion; both share Reynolds/Knaflic/Tufte foundations)
- `~/.claude/rules/pptx-mac-compatibility.md` — TIFF, sp3d, app.xml, srcRect defects
- `~/.claude/rules/journal-ai-image-policies.md` — AI-image policy (JACC prohibits, Radiology
  allows with disclosure)
- `~/.claude/rules/manuscript-style-classical.md` — heading style for slides paired with
  manuscript submission
