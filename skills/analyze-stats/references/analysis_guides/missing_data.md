# Missing Data Guide

Strategies for handling missing data in medical research analyses.
This is a preprocessing step, not an independent analysis type.

---

## Missing Data Mechanisms

| Mechanism | Definition | Example | Implication |
|-----------|-----------|---------|-------------|
| **MCAR** | Missing completely at random | Specimen lost in transit | Complete case analysis unbiased (less precise) |
| **MAR** | Missingness depends on observed data | Older patients more likely to drop out | Depends on what is missing and on the analysis model (below) |
| **MNAR** | Missingness depends on unobserved value | Sicker patients miss follow-up | Sensitivity analysis required |

MNAR cannot be verified statistically — always consider as a possibility.

---

## Decide by mechanism and analysis model, not by the missing percentage

The proportion missing does not by itself decide whether complete-case analysis is biased or
whether multiple imputation (MI) helps (Madley-Dowd et al. 2019, doi:10.1016/j.jclinepi.2019.02.016;
Hughes et al. 2019, doi:10.1093/ije/dyz032). Ask, per analysis:

| Situation | Complete-case (CC) analysis | MI |
|-----------|-----------------------------|----|
| Missing **covariates**, missingness does not depend on the outcome (given covariates) | Regression estimates unbiased even if MAR or MNAR in the covariate | Adds precision if the auxiliary information is strong |
| Missing **covariates**, missingness depends on the outcome | Biased | Recommended, with the outcome in the imputation model |
| Missing **outcome** only, MAR given the model covariates (cross-sectional regression) | Unbiased; MI adds little unless there are auxiliary variables | Only with auxiliary variables not in the analysis model |
| Missing **outcomes** in longitudinal data analysed by likelihood (LMM, MMRM) | Not needed: the LMM already uses every observed outcome and is valid under MAR (Twisk et al. 2013, doi:10.1016/j.jclinepi.2013.03.017) | Not needed for the outcome |
| MNAR plausible | Biased | Also biased; add delta-adjusted / pattern-mixture sensitivity analyses |

A variable with a very large fraction missing is usually a design question (was it measured
on everyone?), not an imputation question. Report the missing count per variable either way.

---

## Multiple Imputation via Chained Equations (MICE)

### Procedure
1. Specify imputation model for each variable with missing data
2. Generate m imputed datasets: m at least the percentage of incomplete cases (e.g. 30% of
   cases with any missing value → m ≥ 30; White, Royston & Wood 2011, doi:10.1002/sim.4067)
3. Analyze each dataset independently (same analysis model)
4. Pool results using **Rubin's rules**: estimate = mean of the m estimates; total variance
   T = W + (1 + 1/m) B (W = mean within-imputation variance, B = between-imputation variance);
   CI on t with Rubin's degrees of freedom. Averaging the estimates alone gives the point estimate
   but no valid SE

### Imputation Model Rules
- Include ALL variables from the analysis model in the imputation model
- Include the outcome variable (in imputation model only)
- Match variable type to method:
  - Continuous → predictive mean matching (PMM) or regression
  - Binary → logistic regression
  - Multinomial → polytomous regression
  - Ordinal → proportional odds

### Methods NOT Recommended
- **Mean imputation**: underestimates variance — never use
- **LOCF (Last Observation Carried Forward)**: biased in most settings — avoid
- **Single imputation**: does not account for imputation uncertainty

---

## Reporting Template

"Missing data ranged from [X]% ([variable A]) to [Y]% ([variable B]); [Z]% of participants had at least one missing value. Assuming data were missing at random given [variables], multiple imputation by chained equations (MICE; [m] imputed datasets; imputation model including the outcome and [auxiliary variables]) was used, and estimates were pooled with Rubin's rules. In the complete-case analysis (n = [n]) the estimate was [X.XX] (95% CI [X.XX-X.XX]) versus [X.XX] (95% CI [X.XX-X.XX]) after imputation (Supplementary Table X)."

Report both results and let the reader compare; do not write "consistent results" unless the
numbers show it. Little's MCAR test cannot distinguish MAR from MNAR, so it is not a basis for
choosing the method.

---

## When to Trigger in analyze-stats

During Phase 1 (Data Assessment), whenever an analysis variable has missing values:
1. Report missing counts and percentages per variable, and the % of incomplete cases
2. Classify each by the table above (covariate vs outcome; longitudinal LMM; can missingness
   depend on the outcome?) and state the assumed mechanism
3. If MI is indicated, generate the imputation code as a preprocessing step and pool with
   Rubin's rules; keep the complete-case analysis as a sensitivity analysis
4. If the primary model is an LMM and only outcomes are missing, do not impute the outcome

---

## Python Implementation

`statsmodels` MICE imputes each variable by predictive mean matching (imputed values are drawn
from observed ones, so a 0/1 variable stays 0/1) and pools with Rubin's rules:

```python
import statsmodels.api as sm
from statsmodels.imputation import mice

imp = mice.MICEData(df)                        # df: numeric columns only (dummy-code categories)
fit = mice.MICE("outcome ~ exposure + age + sex", sm.GLM, imp,
                init_kwds={"family": sm.families.Binomial()}).fit(n_burnin=10, n_imputations=30)
print(fit.summary())                           # pooled estimates, Rubin's-rules SEs
```

To pool an estimate from any other analysis (m point estimates `q` and their variances `u`):

```python
import numpy as np
from scipy import stats

def rubin_pool(q, u, alpha=0.05):
    """Rubin's rules: pooled estimate, SE, CI and df (Rubin 1987)."""
    q, u = np.asarray(q, float), np.asarray(u, float); m = len(q)
    qbar, W, B = q.mean(), u.mean(), q.var(ddof=1)
    T = W + (1 + 1 / m) * B
    df = (m - 1) * (1 + W / ((1 + 1 / m) * B)) ** 2
    half = stats.t.ppf(1 - alpha / 2, df) * np.sqrt(T)
    return qbar, np.sqrt(T), (qbar - half, qbar + half), df
```

Do not impute with scikit-learn's `IterativeImputer` for inference: it imputes binary and
categorical variables as continuous values, and `np.mean` over the m results is not Rubin's
rules (it has no variance).

## R Implementation

```r
library(mice)
imp <- mice(df, m = 20, method = 'pmm', seed = 42)
fit <- with(imp, lm(y ~ x1 + x2))
pooled <- pool(fit)
summary(pooled)
```

---

## Common Reviewer Flags

1. Not reporting missing data counts per variable
2. Using listwise deletion without justification
3. Mean imputation or LOCF without acknowledging limitations
4. Not performing sensitivity analysis (complete case vs MI comparison)
5. Not stating the assumed missing mechanism (MCAR/MAR/MNAR)
