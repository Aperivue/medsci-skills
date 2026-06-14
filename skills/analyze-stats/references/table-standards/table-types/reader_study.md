# Table: Multi-Reader Multi-Case (MRMC) Reader-Study Results

The table standard for a **reader study** — multiple readers interpreting the same cases under one
or more conditions (e.g., unaided vs AI-aided, or modality A vs B). The headline is a
**reader-averaged** performance with a confidence interval that accounts for **both reader and case
variability**, with **per-reader** results shown so a single average cannot hide a weak reader.

## Reporting Guidelines
- **STARD / STARD-AI**: diagnostic accuracy reporting (index test, reference standard, flow)
- **CLAIM**: AI in medical imaging (reader study is a common CLAIM design)
- MRMC analysis convention: Obuchowski–Rockette (OR) / Dorfman–Berbaum–Metz (DBM) for reader+case variance

## Standard Structure

```
Table 3. Reader Performance, Unaided vs AI-aided (MRMC, fully crossed; N readers, M cases; per-patient)

Reader            Unaided AUC (95% CI)     AI-aided AUC (95% CI)     ΔAUC (95% CI)
Reader 1          0.82 (0.76-0.88)         0.88 (0.83-0.93)          +0.06 (0.01-0.11)
Reader 2          0.79 (0.72-0.86)         0.86 (0.80-0.92)          +0.07 (0.02-0.12)
...               ...                      ...                       ...
Reader N          0.85 (0.79-0.90)         0.89 (0.84-0.94)          +0.04 (-0.01-0.09)
Reader-averaged   0.82 (0.77-0.87)*        0.88 (0.84-0.92)*         +0.06 (0.02-0.10)*

* Reader-averaged AUC and ΔAUC with MRMC 95% CIs (Obuchowski-Rockette), accounting for
  reader and case variance. N readers (random), M cases. Fully crossed. Unit: per-patient.
  Non-inferiority margin (if applicable): ΔAUC > -0.05, pre-specified.
```

## Rules
- **Reader-averaged headline + per-reader rows**: report the reader-averaged estimate (the inferential
  target) *and* each reader, so reader spread is visible. A single averaged AUC alone is insufficient.
- **MRMC CI, not fixed-reader CI**: the reader-averaged CI and any ΔAUC CI must come from an MRMC method
  (OR/DBM) that accounts for **reader + case** variance. Do **not** report a DeLong CI (case-only) for a
  generalising reader claim — it understates uncertainty.
- **State the design**: fully crossed vs split-plot; number of readers (and that they are a random
  sample of the reader population for generalisation); number of cases / prevalence.
- **Unit of analysis**: per-patient vs per-lesion (clustered) — state it; do not analyse clustered
  lesion data as independent.
- **Reading order / washout**: for a within-reader condition comparison, state order randomisation and
  the washout interval (footnote) — it is part of the design's validity.
- **Estimand**: superiority vs non-inferiority; for non-inferiority, pre-specify and report the margin.
  Report ΔAUC (or Δsensitivity/Δspecificity at a fixed operating point) with its MRMC CI.
- **Operating-point metrics**: if sensitivity/specificity are reported, fix and state the operating
  point (reader-declared threshold), and apply the same MRMC variance treatment.

## Common pitfalls (flag in review)
- Reader-averaged AUC only, no per-reader rows (hides a weak reader).
- DeLong / fixed-reader CI used for a claim that generalises to readers (ignores reader variance).
- Clustered per-lesion data analysed as independent.
- Non-inferiority asserted with no pre-specified margin.

## Code (illustrative)

```r
# MRMC reader-study analysis (Obuchowski-Rockette / DBM) — e.g., the RJafroc or MRMCaov package.
# Input: long data frame (readerID, caseID, modality/condition, score, truth).
# Output: reader-averaged AUC per condition + ΔAUC with MRMC (reader+case) CI and p; per-reader AUCs
# from the same fit. Pair the figure with make-figures exemplar_plots/mrmc_roc.md (per-reader +
# reader-averaged curves). Report the unit of analysis (per-patient vs per-lesion) and the design
# (fully crossed, N readers random, M cases).
```
