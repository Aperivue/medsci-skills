# Sizing a segmentation *usability* claim (acceptability rate, failure bound, edit time)

For a study whose claim is that a segmentation model is **clinically usable** — a share of cases a
clinician accepts, a bounded catastrophic-failure rate, a time saving — the endpoint is **not the
mean of a per-case metric**. Test 15 sizes a mean Dice to a target precision; that calculation says
nothing about how many cases you need to state an acceptability *rate*, and a study sized for
metric precision is routinely far too small to bound a failure rate. This is the **size**
counterpart to the fair-usability **design** in
`design-study/references/segmentation_failure_characterization_design.md`; decide it before data
collection.

## The endpoint is a proportion, not a mean

An acceptability endpoint (*use-as-is*, *acceptable after minor edits*, *clinically acceptable*) is a
**binomial proportion**. Size it to a target CI half-width δ:

```
n ≈ (z/δ)² · p(1−p)          z = 1.96 for 95%
```

At p = 0.90 and δ = 0.05 that is ≈ **138 cases**; at p = 0.50 (the worst case, and the value to use
when the pilot is thin) it is ≈ **384**. Two consequences follow immediately. A proportion near the
ceiling is cheap and one near 50% is expensive — and **you do not know which you have until you
measure**, so size on the pessimistic p unless a pilot in the same anatomy justifies otherwise. And
the rate is **per structure class**: acceptability is not one number (accepted use-as-is rates for a
single pipeline have ranged from ~40% for target volumes to ~89% for normal tissue), so size on the
**structure whose acceptability you must claim**, not on the pooled average.

If the claim is against a threshold ("≥80% of cases acceptable"), size the **one-sided** comparison
of the observed proportion to that threshold, and state the threshold and its justification before
the data — a threshold chosen after seeing the rate is not a threshold.

## Ratings are nested in cases — a rate judged by k readers is not a simple binomial

When m readers rate each of n cases, the total **is not** n·m independent observations. Ratings of
the same case are correlated (an easy case is easy for every reader) and ratings by the same reader
are correlated (a lenient reader is lenient throughout). Pooling them as independent overstates
precision by the **design effect**:

```
DE ≈ 1 + (m − 1)·ρ           n_effective ≈ n·m / DE
```

With 3 readers per case and ρ = 0.5, DE = 2 — half the apparent sample. Either analyse at the
**case level** (a pre-specified consensus or majority rule across readers, then a plain binomial on n
cases) or model the clustering (mixed-effects / GEE with case and reader as random effects) and size
with the inflation. Pick one at design time; the choice changes n by a factor of two or more.

## Bounding a catastrophic-failure rate — the rule of three

A usability claim usually carries an implicit safety claim: *catastrophic failures are rare*.
Rarity has to be sized for, and it is expensive. If **zero** events are observed in n cases, the
one-sided 95% upper bound on the rate is approximately

```
upper bound ≈ 3 / n
```

So bounding a catastrophic-failure rate at **≤ 1% requires ~300 clean cases**; at ≤ 0.5%, ~600. This
is the number that most often breaks a usability claim retrospectively: a study sized to estimate
mean Dice on 40–60 cases can observe zero catastrophic failures and still only bound the rate at
~5–8%, which is not a safety statement. If the design cannot reach n, say what the observed data can
actually bound rather than reporting "no failures occurred" as though it settled the question.

## Edit time / correction effort — paired, per structure

If the claim is that the model saves work, the endpoint is a **paired per-case time difference**
(edit the auto-contour vs contour from scratch, same cases): size on the **SD of the per-case
difference**, exactly as in Test 16, not on the SDs of the two marginal times. Two design points the
published record insists on:

- **Size per structure, not on the pooled saving.** A multi-centre evaluation reporting an overall
  46% saving simultaneously found **no significant saving** for five lymph-node levels, and some
  centres were **slower editing than contouring manually**. A study powered only on the pooled
  contrast cannot support or refute any per-structure claim.
- **Site is a second grouping factor.** If the claim is multi-centre, the per-centre effects differ
  in sign, so size for the centres you intend to claim over (or restrict the claim).

## Required parameters

The **acceptability definition and scale** and which level counts as "accepted" (*use-as-is* and
*acceptable-after-minor-edits* are different endpoints with different n); the **expected rate p** per
structure class (pilot, else 0.5) and the target **δ or threshold**; the **number of readers per
case** and the analysis unit (consensus vs mixed-effects) with the assumed ρ; the **catastrophic-rate
bound** you must be able to state; and, for a work-saving claim, the **SD of the per-case time
difference** per structure. Report n, the assumed p and ρ, the analysis unit, and what
failure rate the design can bound.

## Cross-links

The usability design this size serves → `design-study`
`references/segmentation_failure_characterization_design.md`; the single-metric precision (mean Dice
per structure) → `segmentation_metric_sample_size.md` (Test 15); the paired between-model delta →
`multi_model_comparison_sample_size.md` (Test 16); reader-in-the-loop diagnostic sizing →
`mrmc_reader_study_sample_size.md` (Test 14); presenting the result →
`make-figures` `exemplar_plots/segmentation_failure_panel.md`; abstention and risk–coverage instead
of a fixed acceptability rate → `/uncertainty-imaging`.
