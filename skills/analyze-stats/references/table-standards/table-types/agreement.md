# Table: Reliability / Agreement Results

## Reporting Guidelines
- **GRRAS**: Reliability and agreement studies — report the coefficient, its model/definition,
  the 95% CI, and the number of raters/subjects/replicates.
- Distinguish **relative reliability** (how well raters/methods separate subjects relative to
  total variance — a consistency ICC) from **absolute agreement** (how close the actual values
  are — an absolute-agreement ICC, or Bland–Altman LoA for two continuous methods). κ measures
  categorical agreement *corrected for chance*. Report the metric that matches the question, and
  both when relevant.

## Standard Structure

```
Table 3. Inter-rater Reliability and Agreement for [measurement]
(n = [N] subjects, [R] raters, [k] replicates)

Measure / metric          Estimate (95% CI)        Notes

ICC (continuous)          0.88 (0.82-0.92)         two-way random, absolute agreement,
                                                   single measures [ICC(2,1)]
Weighted κ (ordinal)      0.74 (0.65-0.82)         quadratic weights
Bland-Altman bias          1.2 (0.6 to 1.8)        mean difference (rater A - rater B)
  Limits of agreement     -4.8 to 7.2              ±1.96 SD; CI on each limit in footnote
Percent agreement         86%                      within ±[clinically acceptable Δ]

ICC = intraclass correlation coefficient. Heteroscedasticity assessed (LoA constant across
the measurement range). Interpretation: ICC >0.90 excellent, 0.75-0.90 good, 0.50-0.75
moderate, <0.50 poor.
```

## Rules
- **ICC is uninterpretable without its model and definition** — always state: one-way vs
  **two-way**; **consistency vs absolute agreement**; **single vs average** measures (the
  Shrout–Fleiss form, e.g., ICC(2,1)). Report the point estimate **with its 95% CI**.
- **Ordinal categories → weighted κ** (state linear or quadratic weights); unweighted κ ignores
  the magnitude of disagreement. Nominal → unweighted κ (or Fleiss' κ for >2 raters). Report
  the CI; note that κ is prevalence-sensitive (report observed agreement alongside it).
- **Agreement of two continuous methods → Bland–Altman**: mean difference (bias) with its CI,
  and the **limits of agreement (bias ± 1.96 SD)** with a CI on each limit; assess
  **heteroscedasticity** (do the LoA widen with magnitude? — if so, log-transform or model the
  SD). State whether the LoA fall within a pre-defined clinically acceptable difference.
- **Never report Pearson/Spearman correlation as agreement** — high correlation is compatible
  with large systematic bias; correlation measures association, not agreement.
- **Sample**: report n subjects, n raters/methods, replicates per subject, and a sample-size /
  precision justification for the CI width.
- Match the metric to the data and the question; do not report an ICC for nominal categories or
  a κ for continuous measurements.

## Python / R Code
```r
library(irr); library(psych); library(blandr)

# ICC — specify model & type explicitly (psych::ICC reports all six forms)
psych::ICC(ratings_wide)                 # pick the row matching your design, e.g. ICC2 (2,1)

# Weighted kappa for ordinal (two raters)
irr::kappa2(cbind(rater_a, rater_b), weight = "squared")   # quadratic weights

# Bland-Altman (two continuous methods)
blandr::blandr.statistics(method_a, method_b)   # bias, LoA, and CIs; plot via blandr.draw()
```
```python
import pingouin as pg
pg.intraclass_corr(data=df, targets="subject", raters="rater", ratings="value")  # all ICC forms + CI
# pg.cohen_kappa(...) for categorical; Bland-Altman bias = mean(diff), LoA = mean ± 1.96*sd
```
