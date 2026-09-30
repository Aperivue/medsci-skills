# Meta-Analysis Guide (pairwise and DTA)

Code-level rules for pooling effect sizes or diagnostic accuracy across studies. Prefer R
(`meta`, `metafor`; `mada` for DTA). For three or more interventions compared through a network,
use `network_meta_analysis.md`. Table formats: `table-standards/table-types/meta_analysis.md`.

---

## Comparative (pairwise) effect sizes

- `metabin()` for binary outcomes (OR/RR), `metagen()` for continuous outcomes.
  - Use `method = "Inverse"`, `method.tau = "DL"`, `method.random.ci = "HK"`.
  - Avoid deprecated arguments: `comb.fixed` → `common`, `hakn` → `method.random.ci`.
- Heterogeneity: I², Q test, τ², and a 95% prediction interval for the random-effects pooled
  estimate.
- Forest plot: individual studies + pooled estimate.
- Funnel plot + Egger's test for publication bias — comparative effect sizes only; note that it is
  underpowered for k < 10.
- Sensitivity analysis: leave-one-out (`metainf()`). Subgroups: `update(res, subgroup = variable)`.

## Single-arm pooled proportion

- `metaprop()` with `sm = "PLOGIT"`, `method.ci = "CP"`.
- **Standard output**: τ² on the logit scale and a **95% prediction interval**
  (`metaprop(..., prediction = TRUE)`) beside the pooled estimate; the PI shows where a future
  study's proportion is expected to fall under the random-effects model.
- **Small-study test**: do **not** use Egger's regression for a single-arm proportion
  meta-analysis — funnel-asymmetry tests assume an effect-size-vs-SE relationship that does not
  hold for raw proportions. If a small-study assessment is needed, use Peters' test or an
  arcsine-based variant, and only when `k >= 10` (note underpowered otherwise).
- **Nested observation units**: if the proportion's unit is nested within study (per-lesion within
  study, per-image within patient), do **not** report a naive Wilson/binomial CI that ignores
  clustering — use a cluster-bootstrap or a GLMM with a random intercept per study so the CI
  reflects the design.

## DTA meta-analysis

Template: `references/templates/dta_meta_analysis.R`.

- **Bivariate model** (Reitsma): `mada::reitsma()` — recommended over separate pooling of Se/Sp,
  because it accounts for the correlation between sensitivity and specificity; produces the SROC
  curve with confidence + prediction regions.
- **Key outputs**: pooled Se/Sp (95% CI), positive/negative LR, DOR, SROC AUC.
- **Threshold effect**: Spearman correlation between logit(Se) and logit(FPR). If significant,
  interpret a single pooled Se/Sp with caution and emphasise the SROC curve.
- **Forest plots**: paired (sensitivity + specificity side by side).
- **Publication bias**: Deeks' funnel plot asymmetry test — NOT a standard funnel plot, which is
  inappropriate for DTA studies. Underpowered for k < 10.
- **Dual approach** (comparative + single-arm): primary `metabin()` for comparative studies
  (OR/RR); secondary `metaprop()` with `sm = "PLOGIT"` for a single-arm pooled proportion; use
  `method = "Inverse"`, `method.tau = "DL"`, `method.random.ci = "HK"`.
- **Small studies (k < 10)**: the bivariate model may not converge; consider narrative synthesis.
- **Alternative**: if `mada` is unavailable, use `metafor::rma.mv()` with a bivariate structure.
