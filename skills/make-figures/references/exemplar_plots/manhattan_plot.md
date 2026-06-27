# Exemplar anatomy — Manhattan / volcano plot (agnostic many-exposure scan)

A worked **anatomy model** for the figure that summarizes an **agnostic many-exposure
association scan** — an exposome-/environment-/metabolome-/proteome-/nutrient-wide association
study (ExWAS / EWAS / MWAS), or any "we screened N predictors" pass. Complements the
`critic_rubrics/data_plot.md` §C *Manhattan / volcano* checklist (this composes; the rubric
scores). Synthetic — describes *what each element must show* and the errors to avoid; not an
image to copy. Pairs with `analyze-stats` `analysis_guides/multiplicity.md` and review probe
**O17** in `observational_confounding.md`.

## Which plot

- **Manhattan** — x = the exposures (grouped/ordered by domain or category), y = **−log10(p)**.
  Best when there are many tests and you want to show *which* exposures cross threshold across
  domains.
- **Volcano** — x = **effect size** (β / log-OR / log-HR), y = **−log10(p)**. Best when the
  effect *magnitude and direction* matter as much as significance — it forces effect size onto
  the figure so a trivially small but "significant" hit is visibly trivial.

Prefer a **volcano** (or pair the two) whenever the manuscript will make an effect-size claim; a
Manhattan plot alone shows significance without magnitude.

## Elements

- **A significance threshold line** drawn across the plot, **and its basis named** — family-wise
  (Bonferroni / permutation-based study-wide threshold) for a confirmatory framing, or **FDR**
  (a horizontal line at the p corresponding to the q-cutoff) for discovery — with the **number of
  tests `m`** stated in the caption (the denominator the threshold was computed against).
- **Effect size on the axis (volcano)** or a **signed direction track (Manhattan)** so up- vs
  down-associations are distinguishable; never significance alone.
- **Sparse labelling** — annotate only the threshold-crossing / top hits; the **full tested set
  (every exposure with effect size + p/q) lives in a supplementary table**, not crowded onto the
  plot.
- **Domain/category banding (Manhattan)** — group exposures (diet, chemicals, lifestyle,
  socio-economic …) with alternating colour bands and category labels on the x-axis, so a reader
  sees *where* signal concentrates.
- **Replication encoded** — when the scan has a discovery + replication design, mark which hits
  replicated (e.g. filled = replicated, open = discovery-only) or show discovery and replication
  as paired panels; the caption states the replication rate.
- **Grayscale-safe** — distinguish categories/direction by shape or band as well as colour.

## Discipline (what the figure must not do)

- **Do not omit the threshold's basis or the test count** — a threshold line with no stated
  correction method and no `m` is uninterpretable; the same −log10(p) means different things at
  m = 30 vs m = 3000.
- **Do not present a discovery-only Manhattan as confirmatory** — without replication the crossing
  hits are candidates; say so in the caption (frame as screening — review probe O17).
- **Do not let significance stand in for effect** — a Manhattan with no effect-size channel hides
  that the top hit may be clinically trivial at the study's large N; use a volcano or add an
  effect-size panel/track.
- **Do not interpret a single crossing hit causally when exposures are correlated** — it may be a
  marker for a correlated true cause; that is a co-exposure/mixture-model question, not something
  the plot resolves (`analysis_guides/multiplicity.md`).
- **Do not hand-pick the plotted exposures** — plot the whole tested set; selective inclusion is
  the visual form of selective top-hit reporting.

## Common omission

The **named threshold basis + test count `m`**, the **effect-size channel** (volcano axis or a
Manhattan direction track), and the **replication encoding** — the three elements that separate a
defensible agnostic-scan figure from a significance-only screen. Pair with a supplementary
full-results table (every exposure, effect size, p and q).
