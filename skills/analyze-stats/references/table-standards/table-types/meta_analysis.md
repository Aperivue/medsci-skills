# Tables: Meta-Analysis

## Reporting Guidelines
- **PRISMA 2020**: Study characteristics + pooled results
- **PRISMA-DTA**: For diagnostic test accuracy meta-analyses

---

## Table A: Characteristics of Included Studies

```
Table 1. Characteristics of Included Studies

Author, Year   Country   Design   N      Population       Index Test        Reference Standard   Quality
Kim 2023       Korea     Retro    450    Suspected PE     CTPA AI (v2.1)    Expert consensus     Low
Smith 2024     USA       Prosp    1200   ED patients      CTPA AI (v3.0)    Pulmonary DSA        High (D1)
...

Retro = retrospective, Prosp = prospective, PE = pulmonary embolism,
CTPA = CT pulmonary angiography, ED = emergency department,
DSA = digital subtraction angiography.
```

### Rules
- **Column order**: Author/Year, Country, Design, N, Population, Index test, Reference standard, Quality/RoB
- **Author format**: First author surname + year
- **Study design**: Use standard abbreviations (Retro, Prosp, RCT)
- **Quality assessment tool**: QUADAS-3 (DTA; QUADAS-2 for legacy reviews), RoB 2 (RCT), ROBINS-I (non-randomised intervention studies), NOS (observational)
- **Quality rating**: use the chosen tool's own judgement levels and name the domain(s) driving a non-low rating:
  QUADAS-3 "Low / High / Insufficient information"; QUADAS-2 "Low / High / Unclear";
  RoB 2 "Low risk / Some concerns / High risk"; ROBINS-I "Low / Moderate / Serious / Critical / No information".
  Do not borrow one tool's labels for another (e.g. "Some concerns" is RoB 2, not QUADAS)

---

## Table B: Pooled Results / Summary Estimates

```
Table 2. Pooled Diagnostic Accuracy Estimates

                    k    N       Pooled Estimate (95% CI)

Sensitivity         12   3400    0.91 (0.87-0.94)
Specificity         12   3400    0.88 (0.83-0.92)
Positive LR         12   3400    7.58 (5.12-11.2)
Negative LR         12   3400    0.10 (0.07-0.15)
DOR                 12   3400    75.8 (42.1-136.5)

k = number of studies, N = total participants, CI = confidence interval,
LR = likelihood ratio, DOR = diagnostic odds ratio.
Pooled estimates from a bivariate random-effects model; LRs and DOR derived
from the bivariate model, not pooled separately. Between-study SD (logit
scale): sensitivity 0.62, false-positive rate 0.48; correlation 0.35. The 95%
prediction region is shown on the SROC plot (Figure X).
```

### Rules
- **k and N**: Always report number of studies and total participants
- **Heterogeneity (intervention / proportion pools)**: τ² (estimator named), I² and Cochran Q P, and the 95% prediction interval
- **Heterogeneity (DTA)**: the bivariate variance components (between-study SD of logit sensitivity and logit FPR, their correlation) and the 95% prediction region — **not** univariate I²/Q columns for Se, Sp, LRs or DOR, which ignore threshold effects (Cochrane DTA Handbook v1.0 ch.10 §10.4.3) and imply the LRs/DOR were pooled separately
- **Model**: State random-effects vs fixed-effects (and the estimator) in footnote
- **Subgroup analyses**: Separate rows or separate table
- **Prediction interval**: Include for random-effects if k >= 3
- **Forest plot complement**: Table complements but does not replace forest plot
