# Meta-Analysis Guide (pairwise and DTA)

Code-level rules for pooling effect sizes or diagnostic accuracy across studies. Prefer R
(`meta`, `metafor`; `mada` for DTA). For three or more interventions compared through a network,
use `network_meta_analysis.md`. Table formats: `table-standards/table-types/meta_analysis.md`.

---

## Comparative (pairwise) effect sizes

Template: `references/templates/meta_analysis.R` (OR/RR/MD/SMD).

- `metabin()` for binary outcomes (OR/RR); `metacont()` for continuous outcomes from means and
  SDs (MD/SMD), `metagen()` when only estimates and SEs are reported.
  - Use `method.tau = "REML"` (Cochrane Handbook v6.5 §10.10.4.4 default; `"PM"` if REML does
    not converge — not DL), and `method.random.ci = "HK"` **with `adhoc.hakn.ci = "se"`**: plain
    Hartung-Knapp can give a CI narrower than the common-effect CI when τ² is estimated as 0.
    Report the classic (Wald-type) CI as a sensitivity analysis. Name the estimator in Methods.
  - Ratio measures (OR/RR) are pooled on the log scale and back-transformed; MD/SMD are not —
    never `exp()` a difference.
  - Rare events (pooled rate < 1% or zero-event arms): Peto, MH without a correction, or
    `method = "GLMM"` — see the meta-analysis skill's `phase6_statistical_synthesis.md`.
  - Avoid deprecated arguments: `comb.fixed` → `common`, `hakn` → `method.random.ci`.
- Heterogeneity: I², Q test, τ², and a 95% prediction interval for the random-effects pooled
  estimate.
- Forest plot: individual studies + pooled estimate.
- Funnel plot + an asymmetry test matched to the measure — OR: Harbord or Peters; RR: Peters
  (regresses on 1/N, not on the SE); SMD: Pustejovsky; MD: Egger (the original Egger test is not
  recommended for OR or SMD, Cochrane Handbook v6.5 ch.13). Only when k ≥ 10. Asymmetry means small-study effects, of which
  publication bias is one possible cause; trim-and-fill is a sensitivity analysis, not a
  corrected estimate.
- Sensitivity analysis: leave-one-out (`metainf()`). Subgroups: `update(res, subgroup = variable)`.

## Single-arm pooled proportion

- `metaprop(event, n, sm = "PLOGIT", method = "GLMM", method.ci = "CP")`: logit GLMM with the
  exact binomial likelihood, no continuity correction (Clopper-Pearson CIs for the individual
  studies). Report the crude rate beside the pooled one.
- **Standard output**: τ² on the logit scale and a **95% prediction interval**
  (`metaprop(..., prediction = TRUE)`) beside the pooled estimate; the PI shows where a future
  study's proportion is expected to fall under the random-effects model.
- **Small-study test**: none. Egger, Begg and other funnel-asymmetry tests are uninterpretable
  for pooled proportions — the SE of a proportion is a function of the proportion itself, so the
  funnel is asymmetric without any publication bias (Hunter et al. 2014,
  doi:10.1016/j.jclinepi.2014.03.003). A funnel plot, if shown, is descriptive only; see the
  meta-analysis skill's `single_arm_proportion_ma.md` §7.
- **Units of observation**: per-patient, per-lesion and per-session proportions are different
  estimands — pre-specify one per outcome and pool each separately. Lesions or images within a
  patient are not independent binomial trials: a naive Wilson/binomial CI, or a GLMM with only a
  random intercept per study (which models between-study, not within-patient, variation), is too
  narrow. Use the study's cluster-adjusted estimate, a cluster bootstrap when patient-level data
  exist, or a design-effect adjustment (`single_arm_proportion_ma.md` §8).

## DTA meta-analysis

Template: `references/templates/dta_meta_analysis.R`.

- **Bivariate model** (Reitsma): `mada::reitsma()` — recommended over separate pooling of Se/Sp,
  because it accounts for the correlation between sensitivity and specificity; produces the SROC
  curve with confidence + prediction regions (`plot(fit, predict = TRUE)` — the prediction
  region is off by default). With any zero cell, fit the bivariate binomial GLMM (exact
  likelihood, `lme4::glmer`) as primary; the template does this.
- **Key outputs**: pooled Se/Sp (95% CI); positive/negative LR and DOR with 95% CIs derived from
  the bivariate fit (`SummaryPts()`), never pooled separately; SROC curve (partial AUC over the
  observed FPR range if an AUC is quoted).
- **Heterogeneity**: between-study SDs of logit(Se) and logit(FPR), their correlation, and the
  95% prediction region — not univariate I² for Se and Sp, which ignores threshold effects
  (Cochrane DTA Handbook v1.0 ch.10 §10.4.3). A correlation of ±1 or an SD near 0 is a boundary
  fit; say so.
- **Threshold effect**: judged from the SROC plot and the bivariate Se–FPR correlation. A
  Spearman correlation is descriptive only — a non-significant test on few studies does not show
  there is no threshold effect. If thresholds vary, the SROC/HSROC curve is the summary.
- **Forest plots**: paired (sensitivity + specificity side by side), from
  `mada::forest(madad(data), type = "sens")` and `type = "spec"` (the `mada::` prefix is needed
  when meta/metafor are attached after mada).
- **Publication bias**: Deeks' funnel plot asymmetry test —
  `metabias(metabin(TP, TP + FN, FP, FP + TN, sm = "DOR"), method.bias = "Deeks")`, weighted by
  effective sample size. NOT a standard funnel plot or Egger test, which are inappropriate for
  DTA studies. Only when k ≥ 10.
- **Dual approach** (comparative + single-arm): primary `metabin()` for comparative studies
  (OR/RR) with `method.tau = "REML"`, `method.random.ci = "HK"`, `adhoc.hakn.ci = "se"`;
  secondary `metaprop(..., sm = "PLOGIT", method = "GLMM")` for a single-arm pooled proportion.
- **Small studies (k < 10)**: the bivariate model may not converge; consider narrative synthesis.
- **Alternative**: if `mada` is unavailable, use `metafor::rma.mv()` with a bivariate structure.
