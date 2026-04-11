# Tables: Meta-Analysis

## Reporting Guidelines
- **PRISMA 2020**: Study characteristics + pooled results
- **PRISMA-DTA**: For diagnostic test accuracy meta-analyses

---

## Table A: Characteristics of Included Studies

```
Table 1. Characteristics of Included Studies

Author, Year   Country   Design   N      Population       Index Test        Reference Standard   Quality
Kim 2023       Korea     Retro    450    Suspected PE     CTPA AI (v2.1)    Expert consensus     Low risk
Smith 2024     USA       Prosp    1200   ED patients      CTPA AI (v3.0)    Pulmonary DSA        Some concerns
...

Retro = retrospective, Prosp = prospective, PE = pulmonary embolism,
CTPA = CT pulmonary angiography, ED = emergency department,
DSA = digital subtraction angiography.
```

### Rules
- **Column order**: Author/Year, Country, Design, N, Population, Index test, Reference standard, Quality/RoB
- **Author format**: First author surname + year
- **Study design**: Use standard abbreviations (Retro, Prosp, RCT)
- **Quality assessment tool**: QUADAS-2 (DTA), RoB 2 (RCT), NOS (observational)
- **Quality rating**: "Low risk" / "Some concerns" / "High risk" (QUADAS-2 terms)

---

## Table B: Pooled Results / Summary Estimates

```
Table 2. Pooled Diagnostic Accuracy Estimates

                    k    N       Pooled Estimate (95% CI)    I²     P_het

Sensitivity         12   3400    0.91 (0.87-0.94)           78%    <.001
Specificity         12   3400    0.88 (0.83-0.92)           65%    .002
Positive LR         12   3400    7.58 (5.12-11.2)           72%    <.001
Negative LR         12   3400    0.10 (0.07-0.15)           69%    .001
DOR                 12   3400    75.8 (42.1-136.5)          58%    .008

k = number of studies, N = total participants, CI = confidence interval,
LR = likelihood ratio, DOR = diagnostic odds ratio.
Pooled estimates from bivariate random-effects model.
I² = Higgins inconsistency statistic; P_het from Cochran Q test.
```

### Rules
- **k and N**: Always report number of studies and total participants
- **Heterogeneity**: I² + P from Cochran Q test (mandatory)
- **Model**: State random-effects vs fixed-effects in footnote
- **Subgroup analyses**: Separate rows or separate table
- **Prediction interval**: Include for random-effects if k >= 3
- **Forest plot complement**: Table complements but does not replace forest plot
