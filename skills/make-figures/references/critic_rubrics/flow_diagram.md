# Critic Rubric — Flow Diagrams

Apply this rubric when the generated figure is a flow diagram: STARD,
CONSORT, PRISMA, or pipeline/methods. The Claude session should Read the
rendered PNG plus any available exemplars from
`references/exemplar_diagrams/{stard|consort|prisma|pipeline}/`, then mark
each item below as **PASS / PARTIAL / FAIL** with a one-line justification.

After scoring, produce a concrete list of source edits (D2 code changes,
node label fixes, count corrections) that would resolve every FAIL or
PARTIAL item. Return the scored rubric + edit list to the user.

---

## A. Structural integrity

1. **Box overlap** — No two boxes or text labels overlap. Arrows do not cross
   through node text.
2. **Readable edges** — Every edge has a clear source and target; direction is
   unambiguous; no dangling arrows.
3. **Hierarchy preserved** — Vertical or horizontal flow reads in a single
   dominant direction; upstream nodes appear before downstream ones.
4. **Alignment** — Peer nodes at the same logical level are aligned
   (baseline or center).
5. **Whitespace** — No excessive vertical gap (>2× box height) between
   sequential steps. No cramped collisions at decision points.

## B. Required elements (per figure type)

### STARD flow (diagnostic accuracy)
- Enrollment count (consecutive vs. random, eligible n)
- Included n (with inclusion criteria applied)
- Excluded n with itemized reasons
- Index test performed (n analyzed)
- Reference standard performed (n analyzed)
- Final analysis cohort (n with both tests)

### CONSORT flow (RCT)
- **Enrollment** section: Assessed for eligibility (n), Excluded (n with
  reasons: did not meet criteria, declined, other)
- **Allocation** section: Randomized (n), Allocated to each arm (n received /
  n did not receive intervention)
- **Follow-up** section: Lost to follow-up (n, reasons), Discontinued (n,
  reasons) per arm
- **Analysis** section: Analyzed (n), Excluded from analysis (n, reasons)
  per arm

### PRISMA 2020 flow (systematic review)
- Records identified from databases (n per database)
- Records identified from other sources (registers, citation search, etc.)
- Records after duplicates removed (n)
- Records screened (n) → Records excluded (n)
- Reports sought for retrieval (n) → Reports not retrieved (n)
- Reports assessed for eligibility (n) → Reports excluded with reasons (n, reason categories)
- Studies included in review (n) / Reports of included studies (n)

### Pipeline / methods
- Input data block clearly named (modality, cohort)
- Preprocessing steps in sequence (resampling, normalization, augmentation)
- Model / algorithm block with name or architecture
- Output / task block (segmentation, classification, regression)
- Evaluation metric block where applicable

## C. Numerical consistency

6. **Arithmetic balance** — At each branching node, `in = out + excluded`.
   Verify every subtraction explicitly. Flag any mismatch.
7. **Column totals consistent** — For parallel arms (CONSORT), arm totals
   sum to the randomized total at every stage.
8. **No duplicate counts** — A participant should not appear in two leaf
   nodes unless the diagram explicitly models this.
9. **Manuscript consistency** — Numbers in the diagram match the
   corresponding text in Methods/Results (apply the [VERIFY-CSV] rule —
   every count should trace to a CSV cell or source query).

## D. Typography and accessibility

10. **Font size ≥ 18pt** at the compact-recipe render dimensions (main boxes
    ≥ 20pt, exclusion boxes ≥ 18pt, italic notes ≥ 17pt). Check against the
    `critic_figure.py` OCR min-height flag.
11. **No truncated text** — No box shows clipped text ("Assessed for eli...").
    OCR coverage check (source_word_coverage ≥ 0.95).
12. **Consistent casing** — Sentence case everywhere, or Title Case
    everywhere — not mixed.
13. **Wong palette or neutral only** — Fill colors drawn from the Wong
    colorblind-safe set plus whites/light grays. No red-green only
    distinctions.
14. **Grayscale-safe** — Conversion to grayscale preserves all distinctions
    between box categories (intent vs. exclusion vs. outcome).

## E. Publication readiness

15. **Vector format available** — Both PNG (for DOCX embedding) and PDF
    (for journal submission) were produced. If PDF missing, flag.
16. **Dimensions match journal spec** — Width matches the target journal's
    single-column or double-column specification (±0.3 in).
17. **DPI meets spec** — ≥600 DPI for line-art submissions, ≥300 DPI for
    halftone.
18. **Policy compliance** — Tool is D2 or a permitted auto-layout engine,
    not matplotlib FancyBboxPatch and not Mermaid. (Mermaid is forbidden
    in papers per the project's figure-toolchain policy.)

## F. Exemplar comparison (if exemplars exist for this type)

19. **Hierarchy depth** matches one of the exemplars within ±1 level.
20. **Typographic weight** — Main step labels are visually heavier
    (bold/larger) than parenthetical / exclusion labels, as in the
    exemplars.
21. **Emphasis placement** — Key cohort counts (final analysis n, primary
    outcome n) are visually emphasized (thicker stroke, larger font, or
    fill distinction), consistent with exemplar conventions.

---

## Scoring output format

```
## Critic report (flow diagram, round T)

| Item | Score | Note |
|------|-------|------|
| A.1 Box overlap | PASS | — |
| A.2 Readable edges | PASS | — |
| ...
| C.6 Arithmetic balance | FAIL | Enrollment 500 ≠ Included 420 + Excluded 85 (off by 5) |
| ...

### Required edits before next render
1. Correct Excluded count in node X from 85 to 80.
2. Increase font-size of "Analysis" subsection header from 18 to 22.
3. ...

### Overall verdict
[ ] PASS — ready for manuscript
[ ] REFINE — items above must be fixed before next round
```

Record `critic_pass: yes | partial | no` and `refine_rounds: N` in the
`_figure_manifest.md` for this figure after the final round.
