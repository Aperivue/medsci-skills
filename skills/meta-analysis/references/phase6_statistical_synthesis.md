# Phase 6 Reference — Statistical Synthesis

Load this reference when `/meta-analysis` Phase 6 begins executing the pooled
analysis. It contains the R code templates for DTA and intervention meta-analysis,
the dual-approach (comparative + single-arm pooled proportion) decision table, and
the practical cautions (method.tau, HK CI, zero-cell correction, publication-bias
test power).

**Always use R** (packages: `meta`, `metafor`, `mada`). Companion templates:
`${CLAUDE_SKILL_DIR}/references/r_templates.md`.

---

## DTA Meta-Analysis

```r
library(mada)      # bivariate model, forest/SROC plots
library(meta)      # general meta-analysis utilities
library(metafor)   # advanced models

# Bivariate model (recommended for DTA)
fit <- reitsma(data, formula = cbind(tsens, tfpr) ~ 1)
summary(fit)

# SROC curve with confidence and prediction regions
plot(fit, sroclwd = 2, main = "SROC Curve")

# Forest plot (paired: sensitivity + specificity)
forest(fit, type = "sens")
forest(fit, type = "spec")
```

### Key outputs for DTA
- Pooled sensitivity (95% CI)
- Pooled specificity (95% CI)
- Pooled positive LR, negative LR
- Pooled DOR
- SROC curve with AUC, confidence region, prediction region
- Heterogeneity: I-squared for sensitivity and specificity separately
- Threshold effect: Spearman correlation between sensitivity and FPR

---

## Intervention Meta-Analysis

```r
library(meta)
library(metafor)

res <- metagen(TE, seTE, data = dat, studlab = study,
               method.tau = "REML", sm = "OR")
forest(res)
funnel(res)

summary(res)  # I-squared, tau-squared, Q test
metabias(res, method.bias = "Egger")
metainf(res, pooled = "random")  # leave-one-out
```

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
# Comparative MA (binary outcomes)
res_comp <- metabin(ei, ni, ec, nc, data = dat,
                     studlab = study, sm = "OR",
                     method = "Inverse", method.tau = "DL",
                     common = FALSE, random = TRUE,
                     method.random.ci = "HK", incr = 0.5)

# Single-arm pooled proportion
res_prop <- metaprop(event, n, data = dat_single,
                      studlab = study, sm = "PLOGIT",
                      method.tau = "DL", method.ci = "CP")
```

### Key points
- Comparative answers "is adjunct effective?"; single-arm answers "what outcomes to expect?"
- Single-arm uses `metaprop()` with logit transformation + Clopper-Pearson CI
- GRADE certainty lower for single-arm — state explicitly
- Report both in Results: label PRIMARY/SECONDARY per pre-specified assignment
- **Selection bias warning**: Single-arm case series may introduce selection bias
  (experienced centres, favourable patients). When pooling with comparative arms,
  report both pooled estimates separately and discuss any numerically lower event
  rate in single-arm studies as a potential selection effect.

---

## Practical R Notes

- Use `method = "Inverse"`, not `"MH"`, to avoid a method.tau conflict.
- Use `method.tau = "DL"` (DerSimonian-Laird) — REML may not converge with sparse data.
- Use `method.random.ci = "HK"` (Hartung-Knapp) instead of the deprecated `hakn = TRUE`.
- Use `common = FALSE, random = TRUE` instead of deprecated `comb.fixed/comb.random`.
- For zero cells in **binary 2×2 outcomes** (OR/RR), apply `incr = 0.5` continuity correction. **Do NOT** apply a continuity correction when pooling **single-arm proportions**: use `metaprop(..., method = "GLMM", sm = "PLOGIT")`, which handles zero-event studies natively. See `single_arm_proportion_ma.md`.
- Egger's test is underpowered for k < 10 — note this in results. **Egger/funnel tests are invalid for pooled proportions** (the SE is a deterministic function of the proportion); see `single_arm_proportion_ma.md`.

---

## Subgroup / Meta-Regression

- Subgroup analysis for pre-specified covariates
- Meta-regression for continuous moderators
- Report interaction test p-value, not just within-subgroup p-values

---

## Publication Bias

- DTA: Deeks' funnel plot asymmetry test (standard funnel plots are inappropriate for DTA).
- Intervention: Funnel plot + Egger's or Peters' test.
- Note: tests are underpowered for <10 studies.

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
