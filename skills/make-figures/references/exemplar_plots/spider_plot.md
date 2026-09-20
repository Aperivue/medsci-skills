# Exemplar anatomy — Spider plot (per-patient tumor-burden trajectory over time)

A worked **anatomy model** for a publication-grade spider plot: one line per patient tracing
the **percentage change from baseline in the sum of target-lesion diameters at each
assessment**, all lines starting at 0 at baseline. It is the *trajectory* view of the response
trio (waterfall = depth, swimmer = duration, spider = kinetics). Synthetic — describes *what
each element must show*; not an image to copy. Pairs the response table in `analyze-stats`.

## Elements
- **One line per patient** from (time 0, 0%) through every post-baseline assessment; points
  at the actual scan dates, not at nominal cycle numbers unless the schedule was fixed and stated.
- **X-axis = time from treatment start** in a stated unit; **y-axis = percentage change from
  baseline**, 0 marked as the baseline line.
- **Response-threshold reference lines** drawn and labelled at **-30%** and **+20%**, exactly as
  in the waterfall, so crossing events are visible.
- **Terminal event marker at the end of each line**: progression (including new-lesion or
  non-target progression that does not show in the sum), death, discontinuation, or an
  ongoing marker for patients still being assessed at data cut-off.
- **Line colour = pre-specified group** (arm, cohort, biomarker status), colourblind-safe and
  grayscale-distinct by line style; a legend for both colour and terminal markers.
- **Faceting** by group when more than roughly 30 lines overlap, one panel per group with
  shared axes, rather than one unreadable tangle.
- **Caption**: n plotted out of n treated, assessment schedule, definition of the endpoint
  (target-lesion sum per RECIST 1.1), and what a terminal marker denotes.

## Discipline (what the figure must not do)
- **Do not connect through missing assessments as if they were observed**; a skipped scan is a
  gap or a dashed segment, and the caption says how many assessments were missing.
- **Do not add a mean or median trajectory line without an interval**; a summary curve over an
  informatively censored population (progressors leave early) is biased upward toward the
  survivors and misleads more than it helps. If a summary is needed, use a mixed model in
  `analyze-stats` and plot its fitted curve with a CI band, labelled as such.
- **Do not extrapolate a line past the last assessment** or past data cut-off.
- **Do not let new-lesion progression hide**: a line that stays below -30% but ends in a PD
  marker is a real pattern (new lesion), and the marker is what keeps the plot consistent
  with the reported ORR and PFS.
- Do not use the spider plot to claim a time-to-event result; PFS belongs in `km_curve.md`.

## Common omission
- The **terminal event markers** — without them every line ends the same way and the reader
  cannot tell an ongoing responder from a patient who progressed or died, which is the whole
  point of showing the trajectory. Cross-reference `critic_rubrics/data_plot.md` (axes,
  legend, overplotting) and the companion `waterfall_plot.md` / `swimmer_plot.md`.
