# Exemplar anatomy — MRMC reader-study ROC (multi-reader multi-case)

A worked **anatomy model** for the ROC figure of a **multi-reader multi-case (MRMC)** study — the
reader-study counterpart to the single-model `roc_pr.md`. The point of an MRMC figure is to show
that readers are a *sample*: the curve must communicate both the reader-averaged performance and
the spread across readers, so a comparison (e.g., AI-aided vs unaided, or modality A vs B) is read
as generalising to the reader population, not to two specific experts. Complements
`critic_rubrics/data_plot.md` §C and pairs `analyze-stats`
`table-standards/table-types/reader_study.md`. Synthetic — describes *what each element must show*
and the errors to avoid; not an image to copy, no real citations.

## Elements
- **Fixed 0–1 axes**, sensitivity (y) vs 1 − specificity (x), with the chance diagonal.
- **Per-reader curves** (thin, one per reader) **and** the **reader-averaged curve** (bold) for each
  condition being compared — so the reader spread is visible, not hidden inside one mean line.
- The **reader-averaged AUC with an MRMC 95% CI** (accounting for **both reader and case** variance —
  Obuchowski–Rockette / DBM), per condition, in the legend or panel.
- For a comparison, **both conditions on the same axes** (e.g., unaided vs AI-aided) and the
  **ΔAUC with its MRMC CI / p**; if the design is non-inferiority, mark the **pre-specified margin**.
- The **operating point(s)** actually used by readers (e.g., recommend-biopsy threshold), and a note
  of the **unit of analysis** (per-patient vs per-lesion) and the **fully-crossed** design.

## Discipline (what the figure must not do)
- **Do not show only the reader-averaged curve** — without per-reader curves (or a reader-spread band)
  the figure hides whether the gain is uniform or driven by one weak reader.
- **Do not quote a naïve (fixed-reader) AUC CI** for a generalising claim — the CI must reflect reader
  sampling (MRMC variance); a DeLong CI that ignores reader variance understates uncertainty.
- **Do not pool all readers' reads as if independent**, and do not mix per-patient and per-lesion units
  on one curve without saying so.
- **Do not imply a population-level "AI matches radiologists" claim from 2–3 expert readers** — the
  figure (and caption) should make the reader sample and its generalisation limit explicit.
- If readers were aided by AI, **state the reading order/washout** so the comparison is not confounded
  by case recognition.

## Common omission
- The **per-reader curves**, the **MRMC (reader+case) CI** on the averaged AUC, and the **unit of
  analysis / fully-crossed design** note — the elements MRMC figures most often drop, and the ones
  that decide whether the comparison generalises to readers rather than to the specific panel.
  Cross-reference `critic_rubrics/data_plot.md` §C, the diagnostic-accuracy probes
  `peer-review/references/domain-probes/diagnostic_accuracy.md` (D5/D6), and
  `analyze-stats` `table-standards/table-types/reader_study.md`.
