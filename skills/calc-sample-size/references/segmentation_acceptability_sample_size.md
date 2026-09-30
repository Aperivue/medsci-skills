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

At p = 0.90 and δ = 0.05 that is **139 cases**; at p = 0.50 (the worst case, and the value to use
when the pilot is thin) it is **385**.

**Check**: `presize::prec_prop(p = 0.9, conf.width = 0.1, method = "wald")` → 138.29 → 139;
`p = 0.5` → 384.15 → 385.

```python
import math
from scipy.stats import norm

# Worked example = the Check inputs; replace with the pilot rate for the structure class
p_accept = 0.90
half_width = 0.05
n_accept = math.ceil((norm.ppf(0.975) / half_width)**2 * p_accept * (1 - p_accept))
print(f"{n_accept} cases")
```

 Two consequences follow immediately. A proportion near the
ceiling is cheap and one near 50% is expensive — and **you do not know which you have until you
measure**, so size on the pessimistic p unless a pilot in the same anatomy justifies otherwise. And
the rate is **per structure class**: acceptability is not one number (accepted use-as-is rates for a
single pipeline have ranged from ~40% for target volumes to ~89% for normal tissue), so size on the
**structure whose acceptability you must claim**, not on the pooled average.

If the claim is against a threshold ("≥80% of cases acceptable"), size the **one-sided** comparison
of the observed proportion to that threshold, and state the threshold and its justification before
the data — a threshold chosen after seeing the rate is not a threshold.

## Ratings by several readers are clustered — nested or crossed

When m readers rate each of n cases, the total **is not** n·m independent observations. Two
correlations matter: ratings of the same case (an easy case is easy for every reader, ρ_case) and
ratings by the same reader (a lenient reader is lenient throughout, ρ_reader). Which of them inflates
the variance depends on who rates what:

- **Readers nested in cases** — each case gets its own m readers (different readers for different
  cases). Only the case correlation clusters the ratings:

  ```
  DE ≈ 1 + (m − 1)·ρ_case           n_effective ≈ n·m / DE
  ```

- **Readers crossed with cases** — the same m readers rate every case, the usual reader-study design.
  Every case shares the same readers' leniency, so the reader variance enters as a term that adding
  cases cannot shrink:

  ```
  Var(mean) = σ²_case/n + σ²_reader/m + σ²_resid/(n·m)
  DE = 1 + (m − 1)·ρ_case + (n − 1)·ρ_reader        (ρ = component / total variance)
  ```

  Treating a crossed design as nested understates the variance. With n = 100, m = 3, ρ_case 0.5 and
  ρ_reader 0.05 the crossed DE is 6.95, not 2.0: the 300 ratings are worth about 43 independent
  ones, not 150. Past a point, only more readers buy precision; size readers as well as cases
  (the Test 14 tools, or simulation), or state the claim for these particular readers (readers fixed).

**Check**: the formula is the variance of the mean in a balanced two-way random-effects model; no
package computes this DE, so the Check is a simulation: 20,000 simulated studies with Gaussian case,
reader and residual effects in these proportions give 7.06 (Monte Carlo SE ≈ 0.07) against the
formula's **6.95**.

```python
# Worked example = the Check inputs; replace with pilot variance components
n_cases = 100
m_readers = 3
rho_case = 0.5
rho_reader = 0.05
de_nested = 1 + (m_readers - 1) * rho_case
de_crossed = 1 + (m_readers - 1) * rho_case + (n_cases - 1) * rho_reader
n_effective = n_cases * m_readers / de_crossed
print(f"DE crossed {de_crossed:.2f} (nested {de_nested:.2f}); effective n {n_effective:.0f}")
```

Either analyse at the **case level** (a pre-specified consensus or majority rule across readers, then
a plain binomial on n cases — the claim is then about this panel's consensus) or model the clustering
(mixed-effects / GEE with case and reader as crossed random effects) and size with the inflation.
Pick one at design time; the choice changes n by a factor of two or more.

## Bounding a catastrophic-failure rate — the rule of three

A usability claim usually carries an implicit safety claim: *catastrophic failures are rare*.
Rarity has to be sized for, and it is expensive. If **zero** events are observed in n cases, the
one-sided 95% upper bound on the rate is approximately

```
upper bound ≈ 3 / n
```

So bounding a catastrophic-failure rate at **≤ 1% requires ~300 clean cases**; at ≤ 0.5%, ~600
(Hanley & Lippman-Hand, *JAMA* 1983;249(13):1743-1745).

**Check**: 0 failures in 300 cases → exact one-sided 95% upper bound 0.0099
(`binom.test(0, 300, alternative = "less")$conf.int[2]` → 0.009936); 3/300 = 0.010.

```python
# Zero failures in n clean cases: exact one-sided 95% upper bound (and the 3/n shortcut)
n_clean = 300
upper_bound = 1 - 0.05 ** (1 / n_clean)
print(f"upper bound {upper_bound:.4f} (3/n = {3 / n_clean:.4f})")
```
 This
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
case**, whether the same readers rate every case (crossed) or not (nested), and the analysis unit
(consensus vs mixed-effects) with the assumed ρ_case (and ρ_reader if crossed); the **catastrophic-rate
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
of a fixed acceptability rate → `/model-assessment`.
