# Exemplar anatomy — Swimmer plot (per-patient time on treatment and response duration)

A worked **anatomy model** for a publication-grade swimmer plot: one horizontal lane per
patient, bar length = time on treatment (or time in the study), with response onset,
progression, death, and ongoing status marked along the lane. It is the *durability* view of
the objective-response pair (waterfall = depth, swimmer = duration). Synthetic — describes
*what each element must show*; not an image to copy. Pairs the response table you build and the
survival table-type in `analyze-stats` (median duration of response with its CI).

## Elements
- **One lane per patient**, ordered by bar length (or grouped by cohort/dose level with a
  separator), patient identifiers replaced by row numbers.
- **X-axis = time from treatment start** in a stated unit (weeks or months), starting at 0;
  the same origin for every lane.
- **Bar = duration on treatment** (state explicitly if it is duration of study follow-up
  instead), with a distinct segment or overlay for the **period in response** so depth and
  durability are both readable.
- **Event markers with a legend**: first response (CR/PR onset), confirmation scan,
  progression, treatment discontinuation with reason category, death.
- **Ongoing status arrow** at the right end of any bar for a patient still on treatment or
  still in response at data cut-off — the swimmer equivalent of a censoring mark.
- **Data cut-off line** or date stated in the caption so the reader knows what "ongoing" means.
- **Lane fill = cohort, dose level, or biomarker group**, colourblind-safe and grayscale-distinct.
- **Caption**: n plotted out of n treated, definition of the bar (treatment vs follow-up), how
  response duration was measured (from first response to progression or death), and the median
  duration of response with a 95% CI for the responder subset.

## Discipline (what the figure must not do)
- **Do not omit the ongoing arrows.** A short bar without an arrow reads as early failure; a
  short bar with an arrow is a recently enrolled patient.
- **Do not use swimmer bars to compare arms.** Lane counts differ, follow-up differs, and there
  is no denominator on the plot; any comparison belongs in a time-to-event analysis
  (`km_curve.md`, survival table-type).
- **Do not mix time origins** (e.g., some lanes from randomization, some from first dose) —
  state one origin and use it throughout.
- **Do not let the marker set outgrow the legend**: every glyph on any lane must be in the
  legend; unexplained symbols are the most frequent reviewer query on swimmer plots.
- Keep it to the population it describes (typically responders, or a phase I/II cohort of
  manageable size). Beyond roughly 60 lanes, summarise with a KM of duration of response and
  move the swimmer to the supplement.

## Common omission
- The **ongoing-status arrow** and the **data cut-off** — together they distinguish censoring
  from failure; without them the durability claim cannot be checked against the median
  duration of response quoted in the text. Cross-reference `critic_rubrics/data_plot.md`
  (legend and axis discipline) and `waterfall_plot.md` for the depth-of-response companion.
