# Exemplar anatomy — meta-analysis funnel plot (small-study effects)

A worked **anatomy model** for the funnel plot that sits beside a pairwise intervention
meta-analysis forest plot. `forest_plot.md` answers *what is the pooled effect*; this one answers
*do smaller studies report systematically different effects* — the question the forest cannot.
`critic_rubrics/data_plot.md` §C has no funnel entry, so this model is the composition reference.
Synthetic — describes what each element must show, not an image to copy. Pairs with `analyze-stats`
`references/analysis_guides/meta_analysis.md` and `meta_analysis.R`.

## Elements
- **X-axis = the effect estimate on the analysis scale**, the same measure and direction as the
  forest plot: OR / RR / HR on a log scale (the ratios on a log axis, or the log ratios on a linear
  axis with ticks labelled as ratios, not both), MD or SMD on a linear axis.
- **Y-axis = the standard error, inverted** so the most precise studies sit at the top. Label it
  "Standard error". If another precision measure is used (1/SE, sample size), say so in the caption —
  the shape of the expected funnel depends on it.
- **One point per study**, the same k as the forest; the caption states k. A multi-arm study gives
  one point when its relevant arms are combined, the approach Cochrane recommends (Handbook 23.3.4).
  If the forest instead split a shared control group, that study gives one point per comparison,
  and those points are correlated: the caption gives the number of studies as well as the number of
  comparisons, and an asymmetry test that treats them as independent is not run.
- **Vertical line at the pooled estimate**, with the model named (common-effect or random-effects),
  visually distinct from a **null line** where one is drawn.
- **Pseudo 95% confidence limits** — the triangle of ±1.96·SE around the pooled estimate, labelled as
  pseudo-limits: the spread expected from sampling error alone, with no heterogeneity and no bias.
- **Contour enhancement** — shaded regions of conventional significance around the **null**
  (e.g., p < 0.01, 0.01–0.05, 0.05–0.10, > 0.10), so a reader can see whether missing studies would
  have fallen in the non-significant region (consistent with selective publication) or elsewhere
  (pointing to other causes).
- **Asymmetry test in the caption, matched to the measure** — OR: Harbord or Peters; RR: Peters;
  SMD: Pustejovsky; MD: Egger — with its p-value and k, or a plain statement of why no test was
  run: k < 10; studies of similar size, with similar standard errors (Sterne et al. 2011,
  doi:10.1136/bmj.d4002); or, for OR or RR, no 2×2 counts (only adjusted estimates and their SEs).
  Harbord and Peters need the counts; without them the funnel is descriptive, and the original
  Egger test is not run in their place (`meta-analysis` `references/phase6_statistical_synthesis.md`).
- **Trim-and-fill, if shown at all**: imputed studies as open markers, labelled as imputed, with the
  adjusted estimate reported as a sensitivity analysis next to the observed one.

## Discipline (what the figure must not do)
- **Do not draw or test with k < 10.** The test is underpowered and the eye sees asymmetry in noise;
  say that the funnel was not assessed rather than show an uninterpretable one.
- **Do not equate asymmetry with publication bias.** Asymmetry shows *small-study effects*: true
  heterogeneity, lower-quality small trials, selective outcome reporting, chance, or an artefact of
  measures whose SE depends on the effect can all produce it. The caption says "small-study effects".
- **Do not conclude "no publication bias"** from a symmetric funnel or a non-significant test — a
  low-powered test that fails to reject is not evidence of absence.
- **Do not use a standard funnel where it does not apply.** Pooled single-arm proportions: the SE is
  a function of the proportion, so the funnel is descriptive only and untested (`meta-analysis`
  `references/single_arm_proportion_ma.md` §7). Diagnostic accuracy: use Deeks' funnel (log DOR
  against 1/√ESS) and Deeks' test, never Egger. Network MA: a comparison-adjusted funnel with the
  treatment ordering stated (`analysis_guides/network_meta_analysis.md`).
- **Do not present a trim-and-fill estimate as the corrected effect.** It is one sensitivity
  analysis under strong assumptions, reported next to the observed estimate, never in its place.
- **Do not read the funnel before the heterogeneity.** Under substantial unexplained heterogeneity
  the pseudo-limits no longer describe the expected spread; say that asymmetry is hard to interpret.
- **Do not pool outcomes or measures on one funnel** — one funnel per outcome, matching one forest.

## Common omission
- The **contour shading**, the **asymmetry test named and matched to the effect measure with k**, and
  the **"small-study effects, not proof of publication bias" framing** — what funnel plots most often
  drop, and what separates a figure that informs the risk-of-bias judgement from one that decorates
  it. Cross-reference `forest_plot.md`, `critic_rubrics/data_plot.md` §C (forest), `meta-analysis`
  `references/phase6_statistical_synthesis.md`, and the PRISMA reporting items via
  `/check-reporting`.
