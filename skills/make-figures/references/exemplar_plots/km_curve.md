# Exemplar anatomy — Kaplan–Meier survival curve

A worked **anatomy model** for a publication-grade Kaplan–Meier figure, completing the figure
side of the survival pair (the table side is `analyze-stats/.../table-types/survival_results.md`).
Synthetic — describes *what each element must show* and the errors to avoid; not an image to
copy. Pairs with `analyze-stats` `templates/survival_analysis.py` / `survival` (R).

## Elements
- **Step curves**, one per group, visually distinguishable by line style as well as colour
  (colourblind-safe; do not rely on colour alone).
- **Number-at-risk table** aligned under the x-axis at each labelled time — the single most
  important KM element; without it a reader cannot judge how much of the tail is real.
- **Censoring marks** (ticks on the curve at censoring times), so attrition is visible.
- **Confidence band** around each curve, or at least the median's CI — a curve without
  uncertainty overstates precision in the sparse tail. Say which kind: a **pointwise** band
  covers each time separately and does *not* give simultaneous coverage over the whole curve;
  a **simultaneous** (e.g., Hall–Wellner / equal-precision) band does.
- **Group contrast** annotated: the **log-rank p** and/or the **HR (95% CI)** with its model,
  and **median survival per group with 95% CI** (or "not reached").
- **Axes**: y from 0 to 1 (or 0–100%) labelled with the estimand (overall survival, PFS, …);
  x labelled with the time unit; a reference line is optional.

## Discipline (what the figure must not do)
- **Do not extend the x-axis past where the risk set is thin.** Truncate at (or annotate) the
  point where estimation stops being supported — judge this by the **number at risk and the
  remaining events**, and by where the **CI widens sharply** (e.g., once n-at-risk falls below a
  small fraction of baseline) — the far tail is driven by a few patients and the steps are noise.
- **Do not read a survival probability off a horizon beyond the data**; if a fixed-time estimate
  (e.g., 5-year survival) is quoted, the number at risk at that time must support it.
- **Do not omit censoring** — heavy early censoring with a flat curve can masquerade as good
  survival.
- For **competing risks**, a KM of one cause overestimates its incidence — use a cumulative
  incidence function (CIF) instead, and say so.
- If proportional hazards is violated, the curves crossing is itself the message; pair with an
  RMST or a time-window statement rather than a single HR (see the survival table-type).

## Common omission
- The **number-at-risk table** and **censoring marks** — the two elements KM figures most often
  drop, and the two a reviewer checks first, because both govern whether the tail can be
  believed. Cross-reference `critic_rubrics/data_plot.md` §C (KM) and the survival table-type in
  `analyze-stats/references/table-standards/table-types/survival_results.md`.
