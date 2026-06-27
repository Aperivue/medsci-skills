# Mendelian Randomization Analysis Guide

Using germline genetic variants as **instrumental variables (IVs)** for an exposure to
strengthen causal inference when an RCT is infeasible or unethical. The point estimate (a ratio
of GWAS associations) is easy; what fails review is **instrument validity, pleiotropy, and the
assumptions** — so the analysis is mostly the sensitivity suite, not the headline number. This is
the analysis-side companion to review probes **MR1–MR8** in `mendelian_randomization.md`.

---

## When to Use

- A causal question where an RCT is infeasible/unethical AND a **strong genetic instrument** for
  a **modifiable, well-defined, heritable** exposure exists.
- two-sample summary-data MR (most common), one-sample MR, multivariable MR (MVMR), drug-target /
  cis-MR, non-linear MR (NLMR).
- NOT for: a non-modifiable / ill-defined / composite exposure; a confirmatory **clinical-effect-
  size** claim — MR estimates a **lifelong genetic-proxy effect direction**, not the magnitude of
  a drug/behaviour change started in adulthood.

## The three IV assumptions (state and evidence each)

- **Relevance** — the instrument is strongly associated with the exposure → report the
  **F-statistic** and variance explained (R²).
- **Independence / exchangeability** — the instrument is independent of confounders → ancestry-
  matched GWAS + principal components; a PhenoScanner-style confounder scan.
- **Exclusion restriction** — the instrument affects the outcome only through the exposure (no
  **horizontal pleiotropy**). Untestable directly → addressed via the sensitivity suite below.

## Instrument construction

- Select at genome-wide significance (P < 5 × 10⁻⁸), **LD-clump** (e.g. r² < 0.001, 10 Mb window;
  report a stricter-r² sensitivity), handle **palindromic/ambiguous** SNPs, and **harmonize effect
  alleles** across the exposure and outcome GWAS (a harmonization error flips the sign).
- **Instrument strength**: per-SNP F = (β_GX / se_GX)²; overall F = [R²(N − k − 1)] / [(1 − R²)k];
  a mean F well above ~10. For **MVMR** report the **conditional F**.
- **Winner's curse**: select instruments in a GWAS **independent** of the one used for the β_GX
  estimate; selecting and estimating in the same sample inflates the instrument–exposure effect.
- **cis / drug-target**: variants within ±(gene window) of the target; correlated cis variants need
  a **GLS-corrected IVW** with the LD matrix (naive IVW assumes independent instruments).

## Estimation + sensitivity suite (pre-specify ALL, not IVW alone)

- **IVW** (random-effects) as the primary estimator.
- **MR-Egger** (its **intercept** tests directional pleiotropy), **weighted median** (valid if ≤50 %
  of weight is invalid), **weighted mode**, **MR-PRESSO** (outlier detection/correction).
- **Heterogeneity**: Cochran's Q, I²_GX; **leave-one-out** and **single-SNP** diagnostics.
- **Concordance across methods is the robustness claim** — not the IVW point estimate alone.

```r
library(TwoSampleMR)   # or the MendelianRandomization package
dat <- harmonise_data(exposure_dat, outcome_dat)          # align effect alleles
res <- mr(dat, method_list = c("mr_ivw", "mr_egger_regression",
                               "mr_weighted_median", "mr_weighted_mode"))
mr_pleiotropy_test(dat)    # MR-Egger intercept (directional pleiotropy)
mr_heterogeneity(dat)      # Cochran's Q
# MRPRESSO::mr_presso(...) for outlier detection/correction
# F-stat: with R2 and N -> F = (R2*(N-k-1))/((1-R2)*k)
```

## Direction, overlap, ancestry

- **Reverse causation**: Steiger filtering (the instrument should explain more variance in the
  exposure than the outcome) and/or **bidirectional MR**.
- **Sample overlap**: two-sample MR assumes independent samples. Report the overlap fraction; overlap
  biases toward the confounded observational estimate and, with weak instruments, inflates type-1
  error → use non-overlapping samples or an overlap-aware correction, or state the bias direction.
- **Ancestry**: instruments and LD reference must match the GWAS ancestry; control population
  stratification.

## MVMR, drug-target, non-linear

- **MVMR** for measured pleiotropy / mediation — estimate conditional (direct) effects; report the
  **conditional F** for instrument strength.
- **Drug-target / cis-MR**: report **colocalization** (`coloc`) to separate a shared causal variant
  from LD confounding, a **positive control** (a known on-target effect), and a **phenome-wide
  adverse-effect scan** for any safety claim.
- **Non-linear MR**: the residual and doubly-ranked methods can produce **artefactual shapes** — a
  quoted inflection/threshold is not validated. Require **negative + positive control outcomes**,
  **sensitivity excluding extreme strata**, biological plausibility, and triangulation before
  trusting an NLMR shape (the genetic analogue of data-driven threshold mining).

## Reporting (STROBE-MR)

Report against **STROBE-MR**: data sources + sample sizes, instrument-selection criteria and
strength, the three assumptions and how each was addressed, harmonization, the full sensitivity
suite, sample overlap, and ancestry. Interpret the estimate as a **lifelong genetic-proxy effect
direction**, not a clinical-intervention magnitude. Review-side probes: MR1–MR8 in
`mendelian_randomization.md`.
