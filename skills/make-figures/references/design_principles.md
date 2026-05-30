# Effective Scientific Figure Design

> **Primary source**: Brunner et al., "Designing effective figures for
> scientific communication." *Nat Hum Behav* (2026).
> DOI: 10.1038/s41562-026-02466-9 — communication-context strategies.
>
> **Companion sources** (cite in figure legends / Methods when used):
> - Rougier et al., "Ten simple rules for better figures." *PLoS Comput
>   Biol* 2014;10:e1003833 (PMID 25210732). General-purpose, foundational
>   ten-item checklist.
> - Crameri F., "Choosing the right colors: a perceptually uniform,
>   colorblind-safe approach." *Curr Protoc* 2024;4:e1126
>   (DOI 10.1002/cpz1.1126). Definitive 2024 reference for `viridis`,
>   `cividis`, `batlow` palettes and redundant encoding.
>
> **Triggered from**: SKILL.md Step 1 ("Specify"). Read this file **before**
> choosing a figure type — it shifts focus from "which chart fits the data" to
> "what message should the reader walk away with."

Most figure-design guidance focuses on technical execution (axis ranges,
palettes, DPI). This file complements that by adding a communication-first
layer: who reads the figure, under what time pressure, and what should they
remember 10 seconds later. Apply these strategies in Step 1 when specifying a
figure; revisit during Step 4 / 4b when reviewing.

---

## The 5 strategies (read in order)

### 1. Identify the key message *(most important)*

Before opening a plotting library, write **one sentence** describing what the
figure must convey. If you cannot, the figure is premature. Examples:

- "Model A outperforms Model B at every operating threshold."
- "Adverse-event rates differ by route of administration but not by dose."
- "The proposed pipeline runs end-to-end in under 30 seconds per case."

Pin that sentence as a comment at the top of the generation script. Every
panel, color, annotation, and label exists to support that message; anything
that does not should be removed or moved to supplementary material.

### 2. Consider time and interaction (audience-aware)

Different reading contexts allow different amounts of inspection time:

| Context | Reading time | Implication |
|---|---|---|
| Journal article (specialist) | 30–120 s per figure | Dense detail acceptable; legend lookups OK |
| Conference slide | 15–30 s, narrated | Direct labels mandatory; one message per slide |
| Visual / graphical abstract | 5–10 s, no narration | One panel; minimal text; readable thumbnail |
| Social-media share | 2–5 s | Self-contained; large fonts; high contrast |
| Public lecture / press | 10–30 s, narrated | Plain-language axis labels; analogy via icon |

Set the **reading-time budget** in Step 1, then design backwards. If the same
result will appear in a journal article *and* a conference talk, build two
distinct versions — the conference version usually drops half of what the
journal version contains.

### 3. Choose the right graph type and use color intentionally

The graph type should match the structure of the data, not aesthetic
preference.

| Data structure | Default | Avoid |
|---|---|---|
| One continuous variable, one group | Histogram, density | Pie chart |
| Two continuous variables | Scatter (+ regression line if appropriate) | Bar chart |
| Continuous over time | Line | Stacked bar |
| Categorical proportions | Bar (sorted), waffle | 3-D pie |
| Distribution by group | Box / violin / strip | Bar with SD error |
| Diagnostic performance | ROC, PR curve | Single accuracy bar |
| Effect size with CI | Forest plot, dot-and-whisker | Bar with asterisks |
| Workflow / cohort | Flow diagram (PRISMA / CONSORT / STARD) | Free-form arrows |

Color rules (compatible with this skill's `figure_specs.md`; full
justification in Crameri 2024):

- **Categorical groups**: Wong palette (8 colorblind-safe colors).
- **Sequential magnitude**: `viridis` or `cividis` (perceptually uniform,
  colorblind-safe). Avoid `jet` and `rainbow` — they introduce false
  perceptual edges.
- **Diverging around zero**: `RdBu`, `PuOr`, or `vik` (Crameri).
- **Encode meaning, not decoration.** If the same conclusion holds in
  grayscale, color is decorative — remove or use neutral grays.
- **Redundant encoding** when color carries diagnostic information: pair
  color with line style, marker shape, or direct label so the figure
  survives a deuteranopia simulation and a black-and-white print.
- **Maximum 3 colors per panel** unless the data structure genuinely demands
  more (and then label each directly, not via legend).

### 4. Reduce cognitive load

Every visual element competes for attention. The reader's working memory is
roughly 7 items; design under that ceiling.

- ≤7 distinct visual elements per panel (curves, boxes, annotations).
- ≤3 distinct shapes (e.g., square, circle, triangle).
- ≤3 colors as above.
- **Direct labels on series > legend.** Legend lookups cost ~2 seconds each.
- No 3-D, drop-shadow, gradient fill, or rotated axis labels unless they
  encode data.
- Sans-serif font ≥ 9 pt at print size; ≥ 18 pt for slides; ≥ 24 pt for
  posters.
- Whitespace is not wasted space — it groups related elements.

If a panel violates two or more of these, split it into multiple panels or
move detail to supplementary material.

### 5. Ask whether a figure is really needed

Sometimes a table, a single sentence, or a caption-only number conveys the
result more clearly. Use a figure when **at least one** of the following is
true:

- The reader needs to perceive a *shape* (trend, distribution, threshold).
- The reader needs to *compare* across many groups simultaneously.
- The result depends on a *spatial* or *anatomical* relationship.
- The audience will not read the prose carefully and needs a visual hook.

Otherwise, prefer a small table or in-line text. A 3-row × 2-column results
table beats a bar chart of two values.

---

## Decision: figure vs table

| Use a **figure** when… | Use a **table** when… |
|---|---|
| Trend or shape matters | Exact values matter (e.g., baseline characteristics) |
| ≥4 groups / conditions | ≤3 groups *and* ≤8 metrics |
| Distribution shape conveys meaning | Categorical labels with counts |
| Comparison across many dimensions | Reader will reuse the numbers (re-analysis, replication) |
| Visual-abstract / hero panel | Supplementary detail |

When in doubt, sketch both on paper for 60 seconds and decide which the eye
finishes first.

---

## Cognitive load checklist (Step 4 quick scan)

- [ ] One sentence describes the key message in the script comment.
- [ ] Reading-time budget matches the deployment context.
- [ ] ≤7 visual elements per panel.
- [ ] ≤3 colors carrying meaning (not decoration).
- [ ] No 3-D / shadow / gradient unless data-driven.
- [ ] Direct labels on series; legend has ≤4 entries.
- [ ] Font size meets context minimum (9 pt print / 18 pt slide / 24 pt poster).
- [ ] Same figure works in grayscale (run a `convert -colorspace Gray` test).

If two or more boxes are unchecked, return to Step 1 before exporting.

---

## Anti-patterns (drawn from this skill's critic rubrics)

These compose with the more granular checks in
`critic_rubrics/data_plot.md` and `critic_rubrics/flow_diagram.md`:

- **Default-palette syndrome** — using the matplotlib `tab10` palette without
  thought. Reads as a quick draft, not a finished figure.
- **Legend-dependence** — colored series without direct labels, forcing
  back-and-forth between legend and data.
- **Decorative 3-D** — bars or pies in 3-D with no third data dimension.
- **Chart-of-three-values** — figure where a sentence would be clearer.
- **Caption-as-Methods** — caption explains how the data were generated
  rather than what to look at; methodology belongs in the Methods section.
- **Mismatched detail** — slide-deck figure rendered at 6 pt because it was
  copied from the manuscript without adjustment.

---

## Cross-references

- `critic_rubrics/data_plot.md` — quantitative critic checks for non-flow figures
- `critic_rubrics/flow_diagram.md` — extended checks for flow diagrams
- `figure_specs.md` — journal-specific dimensions and DPI
- `flow_diagram_lessons.md` — production lessons specific to PRISMA / CONSORT / STARD
- `reporting_guideline_figure_map.md` — which figures CONSORT-AI / TRIPOD+AI / CLAIM 2024 / STARD-AI mandate
- `pipeline_concepts_medical_ai.md` — DICOM workflow, annotation, federated learning, model architecture conventions
