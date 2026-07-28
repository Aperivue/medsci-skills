# Exemplar anatomy — segmentation failure panel (across cases, one model)

A worked **anatomy model** for the figure that carries a segmentation **usability** claim: one model,
one cohort, and the **distribution across cases with its tail visible**. It is the third axis of the
comparison family — `model_comparison_leaderboard.md` is *many models, one cohort*,
`external_validation_comparison.md` is *one model, many cohorts*, and this one is **one model, many
cases**. It exists because a bar of mean Dice is the single most common way a segmentation paper
shows nothing about whether the model is usable. Pairs
`design-study/references/segmentation_failure_characterization_design.md` and
`calc-sample-size/references/segmentation_acceptability_sample_size.md` (Test 17). Synthetic —
describes *what each element must show* and the errors to avoid; not an image to copy, no real
citations.

## Elements
- **Every case plotted** — a **strip / jitter / dot plot** (or violin *with* the points overlaid) of
  the per-case metric, one point per case, faceted by structure. The mean and its CI may be drawn on
  top; they may not replace the points. If the reader cannot count the bad cases, the figure has not
  reported them.
- **The acceptability threshold drawn as a line**, with the **fraction below it labelled** — the
  figure's actual claim ("N of M cases, 78%, met the acceptability rule"). The threshold must be the
  pre-specified one, and its definition belongs in the caption, not the reader's imagination.
- **Failure cases marked by class** — colour or facet by the pre-specified taxonomy (boundary drift /
  missed structure / hallucinated structure / catastrophic). A tail of boundary drift and a tail of
  catastrophic outputs look identical on a metric axis and mean opposite things clinically.
- **A qualitative panel of the actual worst cases** — image + contour overlay for the bottom cases,
  with the reference contour shown. This is not decoration: an anatomically impossible output is
  invisible in every summary statistic, and the small panel is the only place the reader can see
  whether the tail is "slightly ragged edge" or "contoured the wrong organ".
- **Stratification that explains the tail** — the same distribution split by the attribute the design
  pre-specified (structure size, contrast phase, pathology present, scanner / site), so the figure
  answers *where* the model fails and not only *how often*.
- **Caption carries N, the rating rule, and the raters** — number of cases, who judged acceptability
  and how many judged each case, and the metric's per-case definition. An acceptability fraction
  without its adjudication rule is not reproducible.

## Discipline (what the figure must not do)
- **Do not plot a bar of means with an SD whisker** — the default segmentation figure, and the one
  that hides everything this figure exists to show: a mean of 0.90 over a 5% catastrophic tail draws
  identically to a uniform 0.90.
- **Do not truncate or clip the y-axis to hide the tail** — the low outliers *are* the finding. An
  axis starting at 0.7 to "make the differences visible" deletes exactly the cases a reviewer wants.
- **Do not report the acceptability fraction without the threshold's provenance** — a threshold set
  after seeing the distribution converts the figure into a post-hoc claim.
- **Do not show only the structure that performed well** — facet every structure the claim covers;
  acceptability for one pipeline can differ by fifty points between target volumes and normal tissue,
  and showing the winner is the cherry-pick a reviewer flags first.
- **Do not average across readers without saying so** — a per-case point that is silently a
  3-reader mean, or a fraction pooled over reader×case as if independent, misstates both the
  distribution and its precision (Test 17).

## Common omission
- The **qualitative worst-case panel**, the **failure-class encoding**, and the **threshold line with
  its labelled fraction** — the three elements that turn a metric distribution into a usability
  claim, and the ones a segmentation figure most often drops. The case count behind a *bounded*
  failure rate is a design-time decision
  (`calc-sample-size/references/segmentation_acceptability_sample_size.md`). Cross-reference
  `model_comparison_leaderboard.md` (across-models sibling), `external_validation_comparison.md`
  (across-cohorts sibling), `critic_rubrics/data_plot.md`, and `/uncertainty-imaging` when the tail
  is handled by abstention rather than reported as a rate.
