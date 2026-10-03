# Phase 6 Reference — Statistical Synthesis

Load this reference when `/meta-analysis` Phase 6 begins executing the pooled
analysis. It contains the R code templates for DTA and intervention meta-analysis,
the dual-approach (comparative + single-arm pooled proportion) decision table, the
rare-event branch, the model-choice rationale required by PRISMA item 13d, the
handling of correlated effect sizes from the same participants, and the practical
cautions (method.tau, HK CI, zero-cell correction, publication-bias test power).

**Always use R** (packages: `meta`, `metafor`, `mada`). Companion templates:
`${CLAUDE_SKILL_DIR}/references/r_templates.md`.

---

## DTA Meta-Analysis

```r
library(mada)      # bivariate model, SROC plot, paired forest plots
library(meta)      # general meta-analysis utilities, Deeks' test
library(metafor)   # advanced models

# data: one row per study with columns TP, FN, FP, TN
# Bivariate model (recommended for DTA). The 0.5 zero-cell correction is
# confined to the studies that need it; with ANY zero cell, report the
# bivariate binomial GLMM as primary (analyze-stats dta_meta_analysis.R).
fit <- reitsma(data, formula = cbind(tsens, tfpr) ~ 1, correction.control = "single")
summary(fit)               # rows "sensitivity" / "false pos. rate": back-transformed CIs
summary(SummaryPts(fit))   # LR+, LR-, DOR with CIs derived from the bivariate fit

# SROC curve with confidence and prediction regions (predict = FALSE by default)
plot(fit, sroclwd = 2, predict = TRUE, predlty = 2, main = "SROC Curve")
points(fpr(data), sens(data), pch = 2)

# Paired forest plots come from the study-level data (madad), not the fit.
# mada:: is needed because meta and metafor, attached later, mask forest().
mada::forest(madad(data), type = "sens")
mada::forest(madad(data), type = "spec")
```

### Key outputs for DTA
- Pooled sensitivity (95% CI)
- Pooled specificity (95% CI)
- Positive LR, negative LR and DOR with 95% CIs, **derived from the bivariate model**
  (`SummaryPts`) — never pooled separately (Zwinderman & Bossuyt 2008, doi:10.1002/sim.2992)
- SROC curve with confidence region and 95% prediction region; if an AUC is quoted, give the
  partial AUC over the observed FPR range, not an AUC extrapolated beyond the data
- Heterogeneity: the between-study SDs of logit(Se) and logit(FPR), their correlation, and the
  prediction region. **Not** univariate I² for sensitivity and specificity: Cochrane DTA
  Handbook (v1.0, ch.10 §10.4.3) — univariate heterogeneity tests and I² "are not routinely
  used in Cochrane DTA reviews as they do not account for heterogeneity explained by phenomena
  such as positivity threshold effects". A correlation of ±1 or an SD near 0 is a boundary
  estimate — say so rather than interpreting it
- Threshold effect: judged from the SROC plot and the bivariate Se–FPR correlation. A Spearman
  correlation, if reported, is descriptive: with few studies a non-significant test does not
  show there is no threshold effect. If positivity thresholds differ across studies, the SROC
  (HSROC) curve with its prediction region is the summary
- Zero cells: the normal approximation with a 0.5 correction pulls Se/Sp towards 0.5; fit the
  bivariate binomial GLMM (exact likelihood) as primary — §10.5.2.1: Chu (2006) "recommended
  that software be used that can explicitly model the binomial within-study distributions"

---

## Intervention Meta-Analysis

```r
library(meta)
library(metafor)

# dat: one row per study with ei/ni (intervention) and ec/nc (control) counts
res <- metabin(ei, ni, ec, nc, data = dat, studlab = study, sm = "OR",
               method.tau = "REML",                        # PM if REML does not converge
               method.random.ci = "HK", adhoc.hakn.ci = "se",
               common = FALSE, random = TRUE, prediction = TRUE)
forest(res)
funnel(res)

summary(res)  # I-squared, tau-squared, Q test, prediction interval
metabias(res, method.bias = "Harbord")  # OR: Harbord or Peters, not the original Egger; k >= 10
metainf(res, pooled = "random")  # leave-one-out
```

When only estimates and standard errors are reported (e.g. adjusted ORs), use
`metagen(TE, seTE, sm = "OR", ...)` with the same `method.tau`/`method.random.ci`
arguments; Harbord and Peters need 2×2 counts, so without them present the funnel plot
descriptively rather than running the original Egger test on log ORs.

---

## Dual Approach: Comparative + Single-Arm Pooled Proportion

When both comparative and single-arm studies are available, use dual analysis
(precedent: Lin 2025 PMID:41419890, Su 2026 PMID:41653198). The assignment of
PRIMARY vs SECONDARY depends on the research question and available evidence:

| Scenario | Primary | Secondary | Rationale |
|----------|---------|-----------|-----------|
| Enough comparative studies (k≥8) | Comparative OR/RR | Pooled proportion | Direct comparison answers efficacy |
| Limited comparative (k<6), many single-arm | Pooled proportion | Comparative OR/RR | Insufficient power for comparative; pooled proportion provides descriptive evidence |
| Mixed (moderate k, each) | Discuss with co-authors | — | PI/methodologist decision |

The choice should be pre-specified in the PROSPERO protocol and remain consistent
throughout the manuscript.

```r
# Comparative MA (binary outcomes) — NON-RARE events only.
# If the outcome is rare (see "Rare Events" below), this specification is the
# one Cochrane tells you to avoid: do not reach for it by default.
res_comp <- metabin(ei, ni, ec, nc, data = dat,
                     studlab = study, sm = "OR",
                     method = "Inverse", method.tau = "REML",
                     common = FALSE, random = TRUE,
                     method.random.ci = "HK", adhoc.hakn.ci = "se")

# Single-arm pooled proportion: logit GLMM, no continuity correction
res_prop <- metaprop(event, n, data = dat_single,
                      studlab = study, sm = "PLOGIT",
                      method = "GLMM", method.ci = "CP",
                      common = FALSE, random = TRUE, prediction = TRUE)
```

### Key points
- Comparative answers "is adjunct effective?"; single-arm answers "what outcomes to expect?"
- Single-arm uses `metaprop()` with a logit GLMM (`method = "GLMM"`, no continuity correction) and Clopper-Pearson CIs for the individual studies; see `single_arm_proportion_ma.md`
- GRADE certainty lower for single-arm — state explicitly
- Report both in Results: label PRIMARY/SECONDARY per pre-specified assignment
- **Selection bias warning**: Single-arm case series may introduce selection bias
  (experienced centres, favourable patients). When pooling with comparative arms,
  report both pooled estimates separately and discuss any numerically lower event
  rate in single-arm studies as a potential selection effect.

---

## Practical R Notes

- For **non-rare** binary outcomes the random-effects pool is inverse-variance weighted whatever `method` is set to (`"Inverse"` or `"MH"` changes only the common-effect estimate); there is no `method.tau` conflict with `"MH"` in current `meta`. For **rare** events see "Rare Events" below.
- Use `method.tau = "REML"` — the Cochrane default (Handbook v6.5 §10.10.4.4; Veroniki et al. 2016, doi:10.1002/jrsm.1164). If REML fails to converge, use `"PM"` (Paule-Mandel), not DL. Name the estimator in Methods. Not for rare events (below).
- Use `method.random.ci = "HK"` (Hartung-Knapp) **with `adhoc.hakn.ci = "se"`** instead of the deprecated `hakn = TRUE`. Plain HK can give a CI narrower than the common-effect CI when τ² is estimated as 0 — Handbook v6.5 §10.10.4.4: "When no heterogeneity is observed … the HKSJ method can yield overly narrow confidence intervals"; the ad hoc correction (Knapp & Hartung 2003) never lets the HK variance fall below the classic one. Report the classic (Wald-type) CI as a sensitivity analysis. (Not available for GLMMs.)
- Use `common = FALSE, random = TRUE` instead of deprecated `comb.fixed/comb.random`.
- For zero cells in **non-rare binary 2×2 outcomes** (OR/RR), `meta` adds `incr = 0.5` to the zero-cell studies by default. **Do NOT** apply a continuity correction when the event is **rare** (below) or when pooling **single-arm proportions**: use `metaprop(..., method = "GLMM", sm = "PLOGIT")`, which handles zero-event studies natively. See `single_arm_proportion_ma.md`.
- Funnel-asymmetry tests need k ≥ 10. Match the test to the measure: OR → Harbord or Peters; RR → Peters; SMD → Pustejovsky; MD → Egger. The original Egger test is "not recommended for application to odds ratios and SMDs" (Handbook v6.5 ch.13). **Egger/funnel tests are invalid for pooled proportions** (the SE is a deterministic function of the proportion); see `single_arm_proportion_ma.md`.

---

## Rare Events (sparse 2×2 data)

The default specification above (inverse-variance random-effects pooling, with 0.5 added to
zero cells) is the wrong tool once the event is rare.
Inverse-variance weights are derived from a large-sample normal approximation that fails
with few events, and adding 0.5 to every cell biases the estimate toward the null and
distorts its variance — Cochrane Handbook §10.4.4.1, restated for radiology SR/MA in
Park 2022 (Korean J Radiol; PMID:35213097): *inverse-variance methods (including the
DerSimonian and Laird method) should be avoided in meta-analyses of rare events.*

**Trigger** — treat the outcome as rare and branch when any holds:

| Signal | Threshold |
|---|---|
| Pooled event rate | < 1% (Cochrane's working definition; < 5% warrants a sensitivity check) |
| Zero-event arms | any study with a structural zero in either arm |
| Double-zero studies | present (these carry no information for OR and are dropped by MH/Peto — say so) |

**Use instead** (pre-specify one; the others become the sensitivity analysis):

```r
# 1. Peto OR — a FIXED-effect estimator. Best when events are very rare, arms are
#    of similar size, and the true effect is not large. No continuity correction.
res_peto <- metabin(ei, ni, ec, nc, data = dat, studlab = study,
                    sm = "OR", method = "Peto",
                    common = TRUE, random = FALSE)

# 2. Mantel-Haenszel without a zero-cell correction — also FIXED-effect.
#    MH.exact = TRUE suppresses the continuity correction in the pooled estimate
#    (the 0.5 still appears in the per-study estimates drawn on the forest plot,
#    which is what RevMan does too — say so in the legend).
res_mh <- metabin(ei, ni, ec, nc, data = dat, studlab = study,
                  sm = "OR", method = "MH", MH.exact = TRUE,
                  common = TRUE, random = FALSE)

# 3. Binomial-normal GLMM — the route to a RANDOM-effects rare-event pool.
#    Exact likelihood, handles zero cells natively, tolerates unbalanced arms.
res_glmm <- metabin(ei, ni, ec, nc, data = dat, studlab = study,
                    sm = "OR", method = "GLMM",
                    common = FALSE, random = TRUE)
```

**Do not layer random effects onto Peto or MH.** Both are fixed-effect estimators, and
`meta` produces their random-effects companions by inverse-variance weighting the
per-study estimates with τ² added — which puts back exactly the weighting the branch was
taken to escape. If between-study heterogeneity has to be modelled for a rare outcome,
that is what the GLMM is for.

**Reporting**: name the method and why the rare-event branch was taken, state how
double-zero studies were handled, and report the alternative specification as a
sensitivity analysis. A rare-event pool reported without this sentence reads as an
unconsidered default.

**Caveat on Peto**: its advantage disappears when arm sizes are markedly unbalanced or
the effect is large — Peto ORs are biased in both cases. Check both before pre-specifying
it; if either fails, GLMM is the safer primary.

---

## Choosing the Model — and Reporting Why (PRISMA item 13d)

Item 13d asks for the *rationale* behind the synthesis method, and it is among the most
under-reported items in published radiology SR/MA (35% [VERIFY: the text implies 5/18 = 28%] in Park 2022, PMID:35213097).
The failure is rarely that no model was chosen — it is that the stated reason is the
wrong kind of reason.

**The choice between fixed- and random-effects is not a test result.** It is a judgment
about whether the studies estimate one identical true effect or a distribution of true
effects. Cochran's Q and Higgins' I² measure how much the observed effects scatter; they
do not answer that question, and Q is underpowered at small k while I² is not a measure
of the *amount* of heterogeneity at all.

**Forbidden phrasings** (a methods reviewer catches these on the first pass):

- "A random-effects model was used because I² was 65%."
- "Because I² was 0% and the Q test was non-significant, a fixed-effect model was used."
- "The model was selected according to the level of statistical heterogeneity."

**Write instead** — the reason lives in the studies, not in the output:

> A random-effects model was used because the included studies differed in scanner
> platform, reader experience, and positivity threshold, so a single common true effect
> could not be assumed. Between-study variance was estimated with [method], and
> heterogeneity is reported as I² and τ² with a 95% prediction interval.

**Default for radiology**: random-effects. Design, population, and threshold
heterogeneity is close to universal in imaging meta-analyses, which is exactly the
condition that makes the identical-true-effect assumption untenable. A fixed-effect
primary analysis needs an argument, not a p-value.

Methods must also carry, per 13d: the model, the between-study variance estimator, the
heterogeneity statistics reported, and the software package **with version**.

---

## Multiple Outcomes from the Same Participants (within-study covariance)

When one study contributes more than one effect size to the same synthesis — several
outcomes, several readers, several thresholds, several time points — those estimates are
correlated because they come from the same patients. Pooling them as if they were
independent counts the same participants more than once, understates the standard error,
and narrows every confidence interval in the forest plot.

Choose one, and say which:

| Approach | When | R |
|---|---|---|
| One effect size per study, pre-specified | Simplest; the outcome hierarchy must be in the protocol, not chosen after seeing results | filter before `metabin`/`metagen` |
| Multivariate / multilevel model | Several outcomes genuinely belong in one synthesis | `metafor::rma.mv` with a block-diagonal V built by `metafor::vcalc(..., rho = )` |
| Robust variance estimation | Correlation is unknown and k is reasonable | `clubSandwich::coef_test(..., vcov = "CR2")` |

The correlation ρ is usually not reported by the primary studies. State the assumed
value, and re-run across a plausible range (e.g. 0.4 / 0.6 / 0.8) as a sensitivity
analysis rather than presenting one assumed ρ as if it were measured.

For DTA this is already handled: sensitivity and specificity from the same 2×2 are
correlated by construction, which is why the bivariate/HSROC models are the requirement
and separate univariate pooling of sensitivity and specificity is not acceptable.

---

## Subgroup / Meta-Regression

- Subgroup analysis for pre-specified covariates
- Meta-regression for continuous moderators
- Report interaction test p-value, not just within-subgroup p-values

---

## Publication Bias

- DTA: Deeks' funnel plot asymmetry test — `metabias(metabin(TP, TP + FN, FP, FP + TN, data = data, sm = "DOR"), method.bias = "Deeks")`, drawn with `funnel(..., yaxis = "ess")`. Standard funnel plots and the Egger, Begg, Harbord and Peters tests "should not be used with diagnostic studies" (Cochrane DTA Handbook v1.0 ch.10 §10.6.3).
- Intervention: funnel plot + a test matched to the measure (OR → Harbord or Peters; RR → Peters; SMD → Pustejovsky; MD → Egger).
- Single-arm proportions: no test (`single_arm_proportion_ma.md` §7).
- Tests need k ≥ 10; below that, do not test.
- Asymmetry means small-study effects, of which publication bias is only one possible cause (Sterne et al. 2011, doi:10.1136/bmj.d4002). Trim-and-fill, if reported, is a sensitivity analysis, not a corrected estimate (Peters et al. 2007, doi:10.1002/sim.2889).

---

## Sensitivity Analysis

- Leave-one-out analysis (`metainf()`)
- Excluding high RoB studies
- Excluding overlapping populations (same institution + enrollment period)
- Including/excluding borderline studies (sensitivity to inclusion criteria)
- Alternative model specifications

---

## Error Handling

- If an R script fails, capture the error message, diagnose the likely cause
  (missing package, data format mismatch, convergence failure), and present a fix.
  Do not silently re-run.
- When reporting R output, separate statistical results (pooled estimates,
  heterogeneity metrics, I-squared) from interpretation. Present numbers first in
  a "Statistical Results" block, then interpretation guidance in a separate
  "Interpretation Notes" block.
