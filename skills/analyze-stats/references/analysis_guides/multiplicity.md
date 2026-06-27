# Multiple Testing & High-Dimensional Screening Guide

Testing **many exposures/predictors against one (or a few) outcomes at once** — an
exposome-/environment-/metabolome-/proteome-/nutrient-wide association scan (ExWAS / EWAS /
MWAS), or any "we screened N candidate predictors and report the significant ones" pass. The
test is easy; what fails review is the **multiplicity bookkeeping, the replication, and the
selective reporting**. This is the analysis-side companion to review probe **O17** in
`observational_confounding.md`.

---

## When to Use

- A scan that tests many exposures/biomarkers/features against an outcome simultaneously.
- Any procedure that **selects** "significant" predictors out of a large candidate set.
- NOT for: a single pre-specified exposure (use `regression.md`); a search for a cut-point or
  non-linear shape **within one** exposure (a different multiplicity — review probe O12); a
  confirmatory model with a handful of pre-registered covariates.

---

## Match the correction to the claim (FWER vs FDR)

The two control different things — pick by what the manuscript will claim, and **report the
method together with `m`, the number of tests** (the denominator).

- **FWER — family-wise error rate** (Bonferroni, Holm, or a permutation-based study-wide
  threshold). Controls the probability of **any** false positive. Use for a **confirmatory
  single-hit** claim. Bonferroni threshold = α / m (e.g. a proteome scan of 1463 proteins at a
  GWAS-style 5 × 10⁻⁸ gives ≈ 3.4 × 10⁻¹¹). A **permutation-based** "exposome-wide / metabolome-
  wide significance level" estimates the threshold that controls FWER **accounting for the
  correlation** among exposures, so it is less conservative than raw Bonferroni.
- **FDR — false discovery rate** (Benjamini–Hochberg q-value; Benjamini–Yekutieli under
  arbitrary dependence). Controls the **expected proportion of false positives among the
  declared hits**. Use for **discovery/screening**, and then **frame the result as hypothesis-
  generating, not confirmatory**.
- **Honest denominator.** Apply the correction to the **whole tested set** — count every
  exposure tested a priori, including ones too sparse to model well. Shrinking `m` to the
  favoured hits, or quoting raw p < 0.05 across hundreds of tests, is the core error.

## Replication is the real safeguard (not the correction alone)

Agnostic scans carry a **high false-discovery proportion even after FDR**. The load-bearing
control is an **independent replication**:

- a **split-half** discovery/replication within the cohort (keep the case proportion matched
  across splits), a **second cohort**, or a **second survey cycle** (e.g. NHANES cross-cycle);
- require **directional concordance** and **report the replication rate** (e.g. "110/164
  exposures replicated", "59% survived correction and were directionally concordant");
- a held-out **validation** set is used **once**, for the final model — never reused as a second
  discovery pass.

A single-cohort FDR-significant scan with no replication is **exploratory**; its top hits are
candidates, not findings.

## Correlated exposures (two consequences)

Exposome/omics exposures are heavily intercorrelated, so:

1. **Raw Bonferroni is over-conservative** — the effective number of independent tests is
   smaller than `m`. Use a permutation threshold, or an **effective-number-of-tests** adjustment
   (eigenvalue decomposition of the exposure correlation matrix; Li & Ji / `poolr::meff()`).
2. **A univariate hit can be a marker for a correlated true cause** — the single-exposure model
   ignores co-exposure confounding / mixtures. Before any causal reading, address the structure
   with **clustering / dimension reduction** or a **multi-exposure / mixture model**
   (elastic-net, WQS regression, quantile g-computation, or BKMR).

## Code patterns

```r
# FDR / FWER adjustment over a vector of p-values from the scan
padj_fdr <- p.adjust(pvals, method = "BH")     # discovery / screening
padj_fwer <- p.adjust(pvals, method = "holm")  # or "bonferroni" — confirmatory
q <- qvalue::qvalue(pvals)$qvalues             # Storey q-values

# effective number of independent tests under correlated exposures
m_eff <- poolr::meff(R = cor(exposure_matrix), method = "liji")  # then alpha / m_eff

# permutation-based study-wide significance threshold (correlation-aware)
# shuffle the outcome B times, refit the scan, keep the min p per permutation;
# the (alpha)-quantile of that min-p null is the study-wide threshold.
```

For mixture / multi-exposure modelling use `glmnet` (elastic-net), `gWQS` (WQS), `qgcomp`
(quantile g-computation), or `bkmr` (Bayesian kernel machine regression).

## Reporting checklist (what reviewers check)

- **Number of exposures tested (`m`)** stated; correction applied to the whole set.
- **Correction method named and matched to the claim** — FWER for confirmatory, FDR for
  discovery (and then framed as hypothesis-generating).
- **Replication design + rate** reported (split-half / second cohort / cross-cycle, directional
  concordance).
- **Full results in a supplement** — every tested exposure with its effect size and p/q, not
  only the winners; pre-registration of the exposure list is ideal (guards against
  selective-reporting / HARKing). Nominal (uncorrected) hits may be shown only if **labelled as
  not surviving correction**.
- **Effect sizes + the resolution floor** — with the large N these scans run on, trivial effects
  clear any threshold; report magnitudes and note that a permutation with `k` permutations
  cannot resolve p below ≈ 1/k. A bare "number of significant exposures" overstates the finding.
- **Complex-survey data** (NHANES / KNHANES / CHNS): combine **design-based standard errors**
  (weights + strata + PSU — see `survey_weighted.md`) **with** the multiplicity correction, not
  one or the other.
