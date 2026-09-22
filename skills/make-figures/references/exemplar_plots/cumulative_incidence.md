# Exemplar anatomy — Cumulative incidence plot (competing risks)

A worked **anatomy model** for a publication-grade cumulative incidence function (CIF) figure,
the competing-risks counterpart of `km_curve.md`: when an event of interest (e.g., cancer
recurrence, cancer-specific death) can be precluded by a competing event (e.g., death from
other causes), 1 minus Kaplan-Meier overestimates the incidence of the event of interest, and
the CIF (Aalen-Johansen estimator) is the correct quantity to draw. Synthetic — describes
*what each element must show*; not an image to copy. Pairs the survival table-type in
`analyze-stats` (`table-types/survival_results.md`) and its competing-risks guidance in
`analysis_guides/survival.md`.

## Elements
- **Estimator named in the caption**: cumulative incidence by the Aalen-Johansen (non-parametric
  competing-risks) estimator, not 1 - KM.
- **One curve per event type**, starting at 0 and non-decreasing; the event of interest and each
  competing event drawn in distinguishable line styles (colourblind-safe, grayscale-distinct).
  Either separate curves per cause, or a **stacked** display where the top of the stack equals
  the all-cause cumulative incidence (1 - overall KM) — say which.
- **Group comparison** (e.g., treatment arms) as separate panels or paired curves per cause,
  with the **Gray's test p-value** for the cause of interest and, where modelled, the
  **subdistribution hazard ratio (Fine-Gray) with 95% CI** and/or the **cause-specific hazard
  ratio**, each labelled as such because they answer different questions.
- **Number-at-risk table** under the x-axis per group, exactly as in a KM figure; the number of
  events of each type by landmark times may be added as a second row set.
- **Confidence band or pointwise CIs** for the cause of interest, or the fixed-time estimates with
  CIs (e.g., 5-year cumulative incidence of recurrence 18% [95% CI 14-22]) in the caption.
- **Axes**: y from 0 to a stated maximum (often < 1, chosen so the curves are readable, with the
  scale labelled); x in a stated time unit from a stated origin (diagnosis, surgery, randomization).

## Discipline (what the figure must not do)
- **Do not draw 1 - KM for a single cause when competing events are present**, and do not label
  a KM complement as "cumulative incidence" — the two diverge as competing events accumulate.
- **Do not extend the curves past the thin-risk-set tail**; the same rule as in `km_curve.md`.
- **Do not interpret a subdistribution hazard ratio as an etiologic effect** or a cause-specific
  hazard ratio as a predictor of absolute risk; state which estimand the figure supports.
- **Do not omit the competing event.** If only the cause of interest is shown, the caption must
  give the competing-event incidence, otherwise the reader cannot judge how much of the plateau
  is death from other causes rather than absence of the event.
- Do not compare curves across groups whose competing-event rates differ without saying so; a
  lower recurrence incidence in the arm with more deaths from other causes is not benefit.

## Common omission
- The **name of the estimator** and the **competing-event curve** — the two things that
  distinguish a correct CIF figure from a relabelled KM complement, and the first things a
  statistical reviewer checks. Cross-reference `critic_rubrics/data_plot.md` §C (KM items
  apply: number at risk, CI, grayscale distinction) and the survival table-type.
