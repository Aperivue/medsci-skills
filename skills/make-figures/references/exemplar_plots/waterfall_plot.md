# Exemplar anatomy — Waterfall plot (best tumor response per patient)

A worked **anatomy model** for a publication-grade waterfall plot: one bar per evaluable patient
showing the **best percentage change from baseline** in the sum of target-lesion diameters
(RECIST 1.1 convention), sorted by magnitude. The figure side of the objective-response
pair; the table side is the response table you build with `/analyze-stats` (ORR with an exact binomial CI,
per-category counts). Synthetic — describes *what each element must show*; not an image to copy.

## Elements
- **One bar per evaluable patient**, sorted from the largest increase (left) to the largest
  decrease (right). Bars are the best post-baseline change, not the last one.
- **Y-axis** = percentage change from baseline in the sum of target-lesion diameters, with 0 as
  the baseline line; symmetric or clipped range stated (e.g., -100 to +100%).
- **Response-threshold reference lines** drawn and labelled: **-30%** (partial-response
  boundary) and **+20%** (progressive-disease boundary). Without them the reader cannot see
  which bars crossed a category.
- **Bar fill = confirmed best overall response category** (CR / PR / SD / PD / not evaluable),
  colourblind-safe and distinguishable in grayscale by hatching or lightness — *not* fill by
  percent change, which the height already shows.
- **Progression by criteria other than target-lesion size** marked on the bar (e.g., an
  asterisk or marker): new lesions or unequivocal non-target progression can make a patient PD
  even when the bar sits below -30%. The marker keeps the height and the category honest.
- **Denominator and exclusions** in the caption: evaluable n out of treated n, and why the rest
  are absent (no post-baseline scan, non-measurable disease, early death).
- **Optional annotation track** above or below the bars for a pre-specified subgroup or
  biomarker status (e.g., PD-L1 positive vs negative), one row, categorical, legend given.
- **Caption carries the summary statistic**: ORR = responders/evaluable with a 95% exact
  (Clopper-Pearson) CI, and whether responses were confirmed.

## Discipline (what the figure must not do)
- **Do not present unconfirmed responses as confirmed** without saying so; the bar colour must
  match the confirmed category used in the ORR.
- **Do not truncate bars silently.** A patient with > +100% change is clipped at the axis
  maximum with the true value written on the bar.
- **Do not sort by anything other than magnitude** (e.g., by treatment arm) — that turns the
  waterfall into a grouped bar chart and hides the response distribution; use colour or a track
  for the group instead.
- **Do not use the waterfall to compare arms statistically.** It is descriptive; a difference in
  ORR between arms belongs in the response table with its CI, not in a visual of bar heights.
- **Do not show time.** Durability belongs to the swimmer plot (`swimmer_plot.md`) and
  trajectory to the spider plot (`spider_plot.md`); the waterfall is one number per patient.
- Do not drop the patients who have no bar from the denominator quoted in the caption.

## Common omission
- The **threshold lines** and the **non-target/new-lesion progression markers** — without both,
  a bar below -30% is read as a responder when the patient actually progressed, and the
  visual ORR disagrees with the reported ORR. Cross-reference `critic_rubrics/data_plot.md`
  (general axes/legend items) and the response table that carries the same ORR.
