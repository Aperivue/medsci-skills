# Critic Rubric — Slide

Apply this rubric when the generated slide deck (PPTX, PDF export, or rendered preview)
is ready for review. Walk every slide and mark each item below as **PASS / PARTIAL / FAIL**
with a one-line justification.

After scoring, produce a list of concrete edits that would resolve every FAIL or PARTIAL
item. Return the scored rubric + edit list to the user.

> **Sources** for these rules: `slide_design_principles.md` (Reynolds, Duarte, Knaflic,
> Tufte) and `~/.claude/rules/pptx-mac-compatibility.md`. Items marked **medical** are
> drawn from RadioGraphics 2025 ("Winning at the Radiology Podium") and RSNA refresher
> course conventions.

---

## A. Message clarity (per slide)

1. **One key message** — the slide conveys exactly one take-home point. A slide with two
   key messages must be split.
2. **Sentence-headline title** — the title states the conclusion ("RFA reduced local
   recurrence by 38%"), not the topic ("Results").
3. **Glance Test ≤ 3 s** — a viewer can grasp the slide's meaning within 3 seconds and
   return attention to the speaker.
4. **Reading-time budget matches context** — slide content density is appropriate for
   journal club / grand rounds / conference / lecture (per `slide_design_principles.md`
   §2 table).

## B. Cognitive load

5. **Body text ≤ 6 lines** at the slide level (counting wrapped lines, not bullets).
6. **Bullet nesting ≤ 2 levels** — no 3-indent nested bullets.
7. **Charts per slide ≤ 1** — two charts on one slide compete for attention.
8. **No decorative animation** — animations exist only when they encode a step
   (build-up of a flow diagram), not for transition flair.
9. **No 3-D / drop-shadow / gradient fill** unless the third dimension encodes data.

## C. Visual hierarchy (Knaflic preattentive)

10. **Size hierarchy** — title > subtitle > body > caption (≥ 4 pt step between levels).
11. **Color carries meaning** — accent color used on the one element that matters; rest
    is neutral. Colors ≤ 3 + 1 accent.
12. **Position priority** — conclusion / take-home placed at slide top, not bottom.
13. **Direct labels on chart series** — legend only when ≥ 4 series; otherwise label
    each curve / bar / wedge directly.

## D. Typography

14. **Font count ≤ 2** throughout the deck (typically 1 for title, 1 for body).
15. **Font size ≥ 18 pt body** for slides; ≥ 24 pt for posters; ≥ 28 pt for room sizes
    > 100 seats.
16. **Single Korean font** when the deck mixes Korean + English (`Apple SD Gothic Neo`
    or `Pretendard`); avoid system Times-fallback for CJK text.
17. **Capitalization consistency** — sentence case OR title case throughout, not mixed.

## E. Native objects (editability)

18. **Charts are native PowerPoint objects** — double-clicking opens the data table,
    not an image preview. (Co-authors must be able to update numbers in revision.)
19. **Tables are native PowerPoint tables** — not pasted screenshots from the paper.
20. **Flow diagrams are grouped shapes** — not embedded `make-figures` PNG exports
    (PNG is acceptable only for visual abstracts and dataset-flow figures intended as
    one-shot graphics).
21. **Images are PNG ≥ 300 dpi or vector PDF** — TIFF prohibited (Mac PowerPoint silently
    drops TIFF — see `pptx-mac-compatibility` rule).

## F. Mac PowerPoint compatibility (deck-level)

Run this once on the final deck before sending to a Mac viewer:

22. **No TIFF in `ppt/media/`** — `find ppt/media -iname '*.tif*'` returns empty.
23. **No `<a:sp3d>` in slide XML** — `grep -l '<a:sp3d>' ppt/slides/*.xml` returns empty
    (3-D bevel renders as red outline only on Mac).
24. **`app.xml` count synced** — `<Slides>`, `<Notes>`, `HeadingPairs`, and `TitlesOfParts`
    match the actual file count (mismatch triggers Mac PowerPoint recovery dialog).
25. **No `<a:srcRect>` value > 100000** — values are in 1/1000-percent (cap 100000); a
    unit-conversion bug crops 99% of the image off-slide.

## G. Medical presentation specifics

26. **Slide pacing** — approximately 1 slide per minute of presentation time. A 30-min
    talk uses 25–30 content slides (excluding title, recap, Q&A buffer). Lectures may
    pace slower (1 slide / 2 min) when teaching concepts.
27. **Background slides ≤ 3** — extended background belongs in the discussion or in
    backup slides, not in the opening.
28. **PICO frame** — for evidence-based presentations (journal club, evidence reviews),
    Population / Intervention / Comparison / Outcome stated explicitly on one slide.
29. **Limitations slide present** — every paper-driven medical talk has a limitations
    slide; absence is grounds for FAIL.
30. **Strengths / weaknesses 2-column** — journal club decks must contrast study
    strengths and weaknesses (typically a 2-column slide).
31. **Statistical vs clinical significance** — when a p-value is shown, a follow-up
    framing of clinical significance (effect size, NNT, absolute risk reduction) is
    present on the same slide or the next.
32. **Disclosure / COI on title slide** (or slide 2) — institutional requirement for
    most medical conferences.

## H. References and AI policy

33. **Inline citation at point-of-use** — `[Smith 2024]` placed on the slide where the
    fact appears, not consolidated on a single end-slide.
34. **Reference list slide ≤ 1** — if mandated by venue, capped to one slide; otherwise
    move full bibliography to a handout or supplementary.
35. **AI-image policy verified** — if any visual abstract / Central Illustration is
    AI-generated, the target audience/journal AI policy is checked
    (`~/.claude/rules/journal-ai-image-policies.md`). JACC family prohibits without EIC
    permission; Radiology family allows with disclosure.

## I. Q&A readiness (Phase 4 cross-check)

36. **Backup slides exist** for foreseeable methodology questions (≥ 3 anticipated
    questions covered).
37. **Quick Review sheet present** — 1-page reference of must-know numbers, common
    pitfalls, and key takeaways (per SKILL.md Phase 4).

---

## Scoring output format

```
## Critic report (slide deck, round T)

### Slide-by-slide

| Slide # | Title | Item | Score | Note |
|---------|-------|------|-------|------|
| 1 | Title | A.32 disclosure | FAIL | No COI line |
| 5 | Methods | A.2 sentence-headline | PARTIAL | Reads "Methods" — convert to "Cohort: 142 RFA + adjuvant chemo" |
| 12 | Forest plot | C.13 direct labels | FAIL | Legend has 5 series but plot has only 3 |
| ... | | | | |

### Deck-level

| Item | Score | Note |
|------|-------|------|
| F.22 No TIFF | PASS | All images are PNG |
| F.23 No sp3d | FAIL | slide14.xml + slide17.xml have 3-D bevel — strip via regex |
| G.26 Pacing | PASS | 27 content slides for 30-min talk |
| G.29 Limitations | FAIL | Missing — add before take-home |
| ... |

### Required edits before next render
1. Slide 1: Add "Disclosure: No COI" line below presenter name.
2. Slide 5: Rewrite title from "Methods" to one-sentence summary of the cohort.
3. Slide 12: Replace 5-entry legend with direct labels on each curve.
4. Strip `<a:sp3d>` from slide14.xml and slide17.xml.
5. Insert Limitations slide between current slides 24 and 25.

### Overall verdict
[ ] PASS — ready for delivery
[ ] REFINE — items above must be fixed before next round
```

Record `critic_pass: yes | partial | no` and `refine_rounds: N` in `_quick_review.md` for
this presentation after the final round.
