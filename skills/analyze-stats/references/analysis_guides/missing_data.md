# Missing Data Guide

Strategies for handling missing data in medical research analyses.
This is a preprocessing step, not an independent analysis type.

---

## Missing Data Mechanisms

| Mechanism | Definition | Example | Implication |
|-----------|-----------|---------|-------------|
| **MCAR** | Missing completely at random | Specimen lost in transit | Complete case analysis OK |
| **MAR** | Missingness depends on observed data | Older patients more likely to drop out | **Multiple imputation needed** |
| **MNAR** | Missingness depends on unobserved value | Sicker patients miss follow-up | Sensitivity analysis required |

MNAR cannot be verified statistically — always consider as a possibility.

---

## Decision by Missing Rate

| Missing % | Action |
|-----------|--------|
| < 5% | Complete case analysis generally acceptable |
| 5-20% | **Multiple imputation recommended** |
| 20-40% | MI + sensitivity analysis mandatory |
| > 40% | Consider excluding the variable from analysis |

---

## Multiple Imputation via Chained Equations (MICE)

### Procedure
1. Specify imputation model for each variable with missing data
2. Generate m imputed datasets (m = 5 minimum; m = 20 if missing > 20%)
3. Analyze each dataset independently (same analysis model)
4. Pool results using **Rubin's rules**: estimate = mean of m estimates; variance = within + between variance

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

"Missing data ranged from X% (variable A) to Y% (variable B). Little's MCAR test suggested data were not MCAR (P = 0.003). Multiple imputation using chained equations (MICE) was performed with m = 20 imputed datasets. Results were pooled using Rubin's rules. Sensitivity analyses using complete case analysis yielded consistent results (Supplementary Table X)."

---

## When to Trigger in analyze-stats

During Phase 1 (Data Assessment), if any analysis variable has > 5% missing:
1. Report missing counts and percentages
2. Suggest MICE before proceeding
3. Generate imputation code as a preprocessing step
4. Run the primary analysis on imputed data
5. Run complete case analysis as sensitivity analysis

---

## Python Implementation

```python
from sklearn.experimental import enable_iterative_imputer
from sklearn.impute import IterativeImputer
import numpy as np
import pandas as pd

m = 20  # number of imputations
results = []
for i in range(m):
    imputer = IterativeImputer(max_iter=10, random_state=i, sample_posterior=True)
    df_imputed = pd.DataFrame(imputer.fit_transform(df), columns=df.columns)
    # Run analysis on each imputed dataset
    # ... append results
# Pool using Rubin's rules
pooled_estimate = np.mean(results, axis=0)
```

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
