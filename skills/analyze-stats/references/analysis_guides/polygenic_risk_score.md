# Polygenic Risk Score (PRS / PGS) Analysis Guide

Building and validating a genome-wide weighted allele sum as a predictor or risk-stratifier. The
score is easy to compute; what fails review is **ancestry transferability, base/target leakage,
incremental value over established clinical risk, calibration, and the discrimination-vs-utility
gap**. This is the analysis-side companion to review probes **PG1–PG8** in
`polygenic_risk_score.md`.

---

## When to Use

- Developing, validating, or applying a PRS/PGS as a predictor or risk-stratifier.
- NOT for: the instrumental-variable use of genetics (causal inference) — see
  `mendelian_randomization.md`; a generic non-genetic prediction model — see `regression.md` /
  the clinical-prediction-model probes.

## Construction & data hygiene

- **Base (discovery GWAS)** and **target (validation)** samples must be **independent** — overlap
  inflates performance. Reuse a **PGS Catalog** score (cite the PGS ID) or document the weights,
  variant set, genome build, allele/strand alignment, and imputation/missing-genotype handling.
- **Tuning** (P+T threshold, LDpred/PRS-CS shrinkage or proportion-of-causal-variants, the chosen
  quantile cut) is selected on a **separate tuning set** and the final score evaluated **out-of-
  sample** — never tune and report performance in the same data (overfitting / winner's curse).
- Tools: `PRSice-2`, `LDpred2` (`bigsnpr`), `PRS-CS`/`PRS-CSx`, `SBayesR`; for cross-ancestry,
  `PRS-CSx` / `BridgePRS`.

## Ancestry portability (the central issue)

- PRS transfers poorly across ancestries (LD, allele-frequency, and GxE differences). **Report
  performance separately per target ancestry**; differences *within* a broad ancestry group can be
  as large as across continental groups, so a single per-group number can mislead.
- Prefer **ancestry-matched or multi-ancestry discovery** GWAS; control population stratification
  with principal components. Do not extend a European-derived score to other ancestries without
  per-ancestry validation (equity harm).

## Effect-size, discrimination, calibration

- Standardize the PRS; report **OR/HR per SD** (with CI) and **quantile stratification** (decile/
  percentile, reference group stated) with **absolute risk** by stratum for a clinical claim.
- **Discrimination**: C-statistic / AUC with CI. **Calibration is separate** — calibration plot
  (observed vs expected by stratum), slope/intercept, in the **target population** (and re-checked
  across ancestries/cohorts where baseline incidence differs). A well-discriminating score can be
  badly miscalibrated for absolute risk.

## Incremental value over established clinical risk (the clinical crux)

- A clinical claim needs the PRS **on top of the guideline clinical model** (SCORE2 / QRISK3 /
  Pooled Cohort Equations / Tyrer-Cuzick / FRAX), not PRS-alone AUC: report **ΔC-statistic (with
  CI)**, **NRI / IDI**, and ideally **net benefit (decision curve)** vs the clinical model alone.

```r
# nested models: clinical vs clinical + PRS
m_clin <- coxph(Surv(time, event) ~ score2, data = d)
m_both <- coxph(Surv(time, event) ~ score2 + scale(prs), data = d)
# Delta C-index (Uno's C) with CI; NRI/IDI via survIDINRI / nricens; decision curve via dcurves
```

## Screening / stratification utility ≠ discrimination

- A **population-screening** claim needs the **detection rate at a fixed false-positive rate** (or
  the likelihood ratio for a PRS quantile) and the **number needed to screen / absolute risk
  difference** — AUC and HR-per-SD can look favourable while the detection-rate-at-acceptable-FPR
  is poor.

## Design caveat

- Prefer **prospective/incident** validation; a cross-sectional **case–control prevalent-disease**
  association overstates predictive utility (PRS predicts incident disease less well than it
  associates with prevalent disease).

## Reporting (PGS-RS / TRIPOD+AI)

Report against the **PGS Reporting Standards** and TRIPOD+AI: development and validation samples
with **ancestry composition**, score-construction provenance (PGS Catalog ID), and the full
performance set (discrimination, **calibration**, **incremental value**, and screening operating
characteristics where a screening claim is made). Scale the conclusion to the evidence — a
quantile relative-risk gradient is not, by itself, demonstrated clinical actionability. Review-side
probes: PG1–PG8 in `polygenic_risk_score.md`.
