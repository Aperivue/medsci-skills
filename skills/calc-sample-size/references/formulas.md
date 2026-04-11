# Sample Size Formulas Reference

Mathematical formulas, R/Python implementations, and effect size conventions for all 10 supported tests.

---

## Test 1: Diagnostic Accuracy (Sensitivity/Specificity Precision)

### Formula
For estimating a single proportion p with desired 95% CI half-width w:

```
n_positive = ceil( (z_{alpha/2} / w)^2 * p * (1 - p) )
n_total = ceil( n_positive / prevalence )
```

Where:
- `z_{alpha/2}` = 1.96 for alpha = 0.05
- `p` = expected sensitivity (or specificity)
- `w` = desired CI half-width
- `prevalence` = disease prevalence in the study population

### R Implementation
```r
z <- qnorm(1 - alpha / 2)
n_pos <- ceiling((z / ci_half_width)^2 * se_expected * (1 - se_expected))
n_total <- ceiling(n_pos / prevalence)
n_adj <- ceiling(n_total / (1 - attrition_rate))
```

### Python Implementation
```python
from scipy.stats import norm
import math

z = norm.ppf(1 - alpha / 2)
n_pos = math.ceil((z / ci_half_width)**2 * se_expected * (1 - se_expected))
n_total = math.ceil(n_pos / prevalence)
n_adj = math.ceil(n_total / (1 - attrition_rate))
```

### R Package
Base R (no additional packages needed).

### Key Reference
Buderer NMF. Statistical methodology: I. Incorporating the prevalence of disease into the sample size calculation for sensitivity and specificity. Acad Emerg Med. 1996;3(9):895-900.

---

## Test 2: ICC Agreement (Bonett 2002)

### Formula
Fisher z-transformation approach:

```
z_1 = 0.5 * ln((1 + rho_1) / (1 - rho_1))    # expected ICC
z_0 = 0.5 * ln((1 + rho_0) / (1 - rho_0))    # null ICC
n = ceil( ((z_{alpha} + z_{beta}) / (z_1 - z_0))^2 + 3 )
```

Where:
- `rho_1` = expected ICC
- `rho_0` = null hypothesis ICC
- `z_{alpha}` = qnorm(1 - alpha) for one-sided, qnorm(1 - alpha/2) for two-sided
- `z_{beta}` = qnorm(power)

### R Implementation
```r
# Option A: MKpower package (preferred)
library(MKpower)
result <- sampleSize.ICC(rho0 = icc_null, rho1 = icc_expected,
                          k = n_raters, alpha = alpha, power = power)
n <- result$n

# Option B: Manual Fisher z (if MKpower unavailable)
z_exp  <- 0.5 * log((1 + icc_expected) / (1 - icc_expected))
z_null <- 0.5 * log((1 + icc_null) / (1 - icc_null))
n <- ceiling(((qnorm(1 - alpha) + qnorm(power)) / (z_exp - z_null))^2 + 3)
```

### Python Implementation
```python
from scipy.stats import norm
import math
import numpy as np

z_exp  = 0.5 * np.log((1 + icc_expected) / (1 - icc_expected))
z_null = 0.5 * np.log((1 + icc_null) / (1 - icc_null))
z_alpha = norm.ppf(1 - alpha)
z_beta  = norm.ppf(power)
n = math.ceil(((z_alpha + z_beta) / (z_exp - z_null))**2 + 3)
```

### R Package
`MKpower` (preferred), or base R for manual calculation.

### Key Reference
Bonett DG. Sample size requirements for estimating intraclass correlations with desired precision. Stat Med. 2002;21(9):1331-1335.

---

## Test 3: Kappa Agreement (Donner & Eliasziw 1992)

### Formula
Z-test approximation for testing kappa_1 vs kappa_0:

```
n = ceil( ((z_{alpha/2} + z_{beta})^2 * kappa_1 * (1 - kappa_1)) / (kappa_1 - kappa_0)^2 + 1 )
```

Where:
- `kappa_1` = expected kappa
- `kappa_0` = null hypothesis kappa
- `pe` = expected chance agreement = (po - kappa) / (1 - kappa)

### R Implementation
```r
n_kappa <- ceiling(
  ((qnorm(1 - alpha / 2) + qnorm(power))^2 *
     kappa_expected * (1 - kappa_expected)) /
    (kappa_expected - kappa_null)^2 + 1
)
```

### Python Implementation
```python
from scipy.stats import norm
import math

z_a = norm.ppf(1 - alpha / 2)
z_b = norm.ppf(power)
n = math.ceil(((z_a + z_b)**2 * kappa_exp * (1 - kappa_exp)) /
              (kappa_exp - kappa_null)**2 + 1)
```

### R Package
Base R. Also available via `kappaSize` package.

### Key Reference
Donner A, Eliasziw M. A goodness-of-fit approach to inference procedures for the kappa statistic: confidence interval construction, significance-testing and sample size estimation. Stat Med. 1992;11(11):1511-1519.

---

## Test 4: Two-Proportion Comparison (Chi-Square)

### Formula
Based on Cohen's h effect size (arcsine transformation):

```
h = 2 * arcsin(sqrt(p1)) - 2 * arcsin(sqrt(p2))
n_per_group = ceil( ((z_{alpha/2} + z_{beta}) / h)^2 )
```

### R Implementation
```r
library(pwr)
h <- ES.h(p1, p2)
result <- pwr.2p.test(h = h, sig.level = alpha, power = power)
n_per_group <- ceiling(result$n)
n_total <- n_per_group * 2
```

### Python Implementation
```python
from statsmodels.stats.power import NormalIndPower
import numpy as np
import math

h = 2 * np.arcsin(np.sqrt(p1)) - 2 * np.arcsin(np.sqrt(p2))
analysis = NormalIndPower()
n_per_group = math.ceil(analysis.solve_power(effect_size=h, alpha=alpha, power=power,
                                              ratio=1, alternative='two-sided'))
n_total = n_per_group * 2
```

### R Package
`pwr`

### Key Reference
Cohen J. Statistical Power Analysis for the Behavioral Sciences. 2nd ed. Lawrence Erlbaum Associates; 1988.

---

## Test 5: McNemar Test (Paired Proportions)

### Formula
```
n = ceil(
  (z_{alpha/2} * sqrt(p01 + p10) + z_{beta} * sqrt(p01 + p10 - (p10 - p01)^2))^2
  / (p10 - p01)^2
)
```

Where:
- `p01` = P(Method A negative, Method B positive)
- `p10` = P(Method A positive, Method B negative)

### R Implementation
```r
n_mc <- ceiling(
  (qnorm(1 - alpha / 2) * sqrt(p01 + p10) +
     qnorm(power) * sqrt(p01 + p10 - (p10 - p01)^2))^2 /
    (p10 - p01)^2
)
```

### Python Implementation
```python
from scipy.stats import norm
import math

z_a = norm.ppf(1 - alpha / 2)
z_b = norm.ppf(power)
disc_sum = p01 + p10
disc_diff = p10 - p01
n = math.ceil((z_a * math.sqrt(disc_sum) +
               z_b * math.sqrt(disc_sum - disc_diff**2))**2 / disc_diff**2)
```

### R Package
Base R. Also available via `exact2x2` package.

### Key Reference
Connor RJ. Sample size for testing differences in proportions for the paired-sample design. Biometrics. 1987;43(1):207-211.

---

## Test 6: Independent t-Test

### Formula
```
d = mean_diff / pooled_sd    (Cohen's d)
n_per_group = ceil( 2 * ((z_{alpha/2} + z_{beta}) / d)^2 )
```

### R Implementation
```r
library(pwr)
d <- mean_diff / pooled_sd
result <- pwr.t.test(d = d, sig.level = alpha, power = power, type = "two.sample")
n_per_group <- ceiling(result$n)
n_total <- n_per_group * 2
```

### Python Implementation
```python
from statsmodels.stats.power import TTestIndPower
import math

d = mean_diff / pooled_sd
analysis = TTestIndPower()
n_per_group = math.ceil(analysis.solve_power(effect_size=d, alpha=alpha, power=power,
                                              ratio=1, alternative='two-sided'))
n_total = n_per_group * 2
```

### R Package
`pwr`

### Key Reference
Cohen J. Statistical Power Analysis for the Behavioral Sciences. 2nd ed. Lawrence Erlbaum Associates; 1988.

---

## Test 7: Survival / Log-Rank Test (Schoenfeld 1981)

### Formula
Step 1 -- Required number of events:
```
d = ceil( ((z_{alpha/2} + z_{beta}) / ln(HR))^2 )
```

Step 2 -- Total sample size:
```
lambda_ctrl = ln(2) / median_ctrl
lambda_trt  = lambda_ctrl * HR
p_event_ctrl = 1 - exp(-lambda_ctrl * follow_up)
p_event_trt  = 1 - exp(-lambda_trt * follow_up)
avg_p_event  = (p_event_ctrl + p_event_trt) / 2
n_total = ceil( d / avg_p_event )
```

### R Implementation
```r
n_events <- ceiling((qnorm(1 - alpha / 2) + qnorm(power))^2 / (log(hr))^2)
lambda_ctrl <- log(2) / median_ctrl
lambda_trt  <- lambda_ctrl * hr
p_event_ctrl <- 1 - exp(-lambda_ctrl * follow_up)
p_event_trt  <- 1 - exp(-lambda_trt * follow_up)
avg_p_event  <- (p_event_ctrl + p_event_trt) / 2
n_total <- ceiling(n_events / avg_p_event)
n_adj <- ceiling(n_total / (1 - drop_rate))
```

### Python Implementation
```python
from scipy.stats import norm
import math
import numpy as np

z_a = norm.ppf(1 - alpha / 2)
z_b = norm.ppf(power)
n_events = math.ceil((z_a + z_b)**2 / np.log(hr)**2)
lambda_ctrl = np.log(2) / median_ctrl
lambda_trt = lambda_ctrl * hr
p_event_ctrl = 1 - np.exp(-lambda_ctrl * follow_up)
p_event_trt = 1 - np.exp(-lambda_trt * follow_up)
avg_p_event = (p_event_ctrl + p_event_trt) / 2
n_total = math.ceil(n_events / avg_p_event)
n_adj = math.ceil(n_total / (1 - drop_rate))
```

### R Package
Base R. Also available via `gsDesign`, `survival` packages.

### Key Reference
Schoenfeld DA. The asymptotic properties of nonparametric tests for comparing survival distributions. Biometrika. 1981;68(1):316-319.

---

## Test 8: One-Way ANOVA

### Formula
Using Cohen's f effect size:

```
f = sigma_between / sigma_within
```

Where:
- `sigma_between` = SD of group means
- `sigma_within` = pooled within-group SD

From eta-squared: `f = sqrt(eta_sq / (1 - eta_sq))`

The sample size per group is obtained via the F-test power formula (implemented in `pwr`).

### R Implementation
```r
library(pwr)
result <- pwr.anova.test(k = k, f = f, sig.level = alpha, power = power)
n_per_group <- ceiling(result$n)
n_total <- n_per_group * k
n_adj <- ceiling(n_total / (1 - attrition_rate))
```

### Python Implementation
```python
from statsmodels.stats.power import FTestAnovaPower
import math

analysis = FTestAnovaPower()
n_per_group = math.ceil(analysis.solve_power(effect_size=f, nobs=None, alpha=alpha,
                                              power=power, k_groups=k))
n_total = n_per_group * k
n_adj = math.ceil(n_total / (1 - attrition_rate))
```

### R Package
`pwr`

### Key Reference
Cohen J. Statistical Power Analysis for the Behavioral Sciences. 2nd ed. Lawrence Erlbaum Associates; 1988. (Chapter 8: F tests for ANOVA)

---

## Test 9: Logistic Regression

### Approach A: Peduzzi Rule of Thumb (EPV >= 10)

```
N_events = 10 * p   (where p = number of predictor variables)
N_total = N_events / event_rate
```

This ensures at least 10 events per predictor variable (EPV), the widely accepted minimum for stable logistic regression estimates.

### Approach B: Hsieh (1989) Formula

For detecting a specific odds ratio (OR) for a continuous or binary predictor:

```
# For a binary predictor (proportion B exposed):
n_unadj = ((z_{alpha/2} + z_{beta})^2) / (B * (1-B) * ln(OR)^2)

# Adjusted for correlation with other predictors:
n_adj = n_unadj / (1 - R^2)
```

Where:
- `OR` = odds ratio of interest
- `B` = proportion of subjects exposed (for binary predictor) or use p*(1-p) for the outcome
- `R^2` = multiple correlation of the predictor with other covariates

For a continuous predictor, the formula uses the standard normal density.

### R Implementation
```r
# Approach A: Peduzzi
n_events_peduzzi <- 10 * n_predictors
n_total_peduzzi <- ceiling(n_events_peduzzi / event_rate)

# Approach B: Hsieh (binary predictor)
z_a <- qnorm(1 - alpha / 2)
z_b <- qnorm(power)
n_hsieh <- ceiling((z_a + z_b)^2 /
                     (event_rate * (1 - event_rate) * log(or_interest)^2))
n_hsieh_adj <- ceiling(n_hsieh / (1 - r2_other))

# Report the larger of the two
n_final <- max(n_total_peduzzi, n_hsieh_adj)
```

### Python Implementation
```python
from scipy.stats import norm
import math
import numpy as np

# Approach A: Peduzzi
n_events_peduzzi = 10 * n_predictors
n_total_peduzzi = math.ceil(n_events_peduzzi / event_rate)

# Approach B: Hsieh (binary predictor)
z_a = norm.ppf(1 - alpha / 2)
z_b = norm.ppf(power)
n_hsieh = math.ceil((z_a + z_b)**2 /
                     (event_rate * (1 - event_rate) * np.log(or_interest)**2))
n_hsieh_adj = math.ceil(n_hsieh / (1 - r2_other))

n_final = max(n_total_peduzzi, n_hsieh_adj)
```

### R Package
Base R. Also see `powerMediation` package for Hsieh's formula.

### Key References
- Peduzzi P, Concato J, Kemper E, Holford TR, Feinstein AR. A simulation study of the number of events per variable in logistic regression analysis. J Clin Epidemiol. 1996;49(12):1373-1379.
- Hsieh FY. Sample size tables for logistic regression. Stat Med. 1989;8(7):795-802.

---

## Test 10: Non-Inferiority / Equivalence

### Non-Inferiority (Proportions)

```
n_per_group = ceil(
  ((z_{1-alpha} + z_{beta})^2 * (p_ref*(1-p_ref) + p_new*(1-p_new))) /
  (margin - |p_new - p_ref|)^2
)
```

When assuming p_new = p_ref (no true difference):
```
n_per_group = ceil( ((z_{1-alpha} + z_{beta})^2 * 2 * p*(1-p)) / margin^2 )
```

Note: alpha is one-sided (typically 0.025) for non-inferiority.

### Non-Inferiority (Continuous)

```
n_per_group = ceil( ((z_{1-alpha} + z_{beta})^2 * 2 * sd^2) / margin^2 )
```

### Equivalence / TOST (Proportions)

```
n_per_group = ceil(
  ((z_{1-alpha/2} + z_{beta})^2 * 2 * p*(1-p)) / margin^2
)
```

Note: For TOST, each one-sided test uses alpha (e.g., alpha = 0.05 for overall 5% type I error).

### Equivalence / TOST (Continuous)

```
n_per_group = ceil( ((z_{1-alpha} + z_{beta})^2 * 2 * sd^2) / margin^2 )
```

### R Implementation
```r
# Non-inferiority for proportions (assuming no true difference)
z_a <- qnorm(1 - alpha)  # one-sided, alpha = 0.025
z_b <- qnorm(power)
p <- p_reference
n_per_group <- ceiling(((z_a + z_b)^2 * 2 * p * (1 - p)) / margin^2)
n_total <- n_per_group * 2

# Non-inferiority for continuous
n_per_group <- ceiling(((z_a + z_b)^2 * 2 * sd^2) / margin^2)
n_total <- n_per_group * 2

# Equivalence / TOST for continuous
n_per_group <- ceiling(((z_a + z_b)^2 * 2 * sd^2) / margin^2)
n_total <- n_per_group * 2

n_adj <- ceiling(n_total / (1 - attrition_rate))
```

### Python Implementation
```python
from scipy.stats import norm
import math

# Non-inferiority for proportions (assuming no true difference)
z_a = norm.ppf(1 - alpha)  # one-sided, alpha = 0.025
z_b = norm.ppf(power)
p = p_reference
n_per_group = math.ceil(((z_a + z_b)**2 * 2 * p * (1 - p)) / margin**2)
n_total = n_per_group * 2

# Non-inferiority for continuous
n_per_group = math.ceil(((z_a + z_b)**2 * 2 * sd**2) / margin**2)
n_total = n_per_group * 2

# Equivalence / TOST for continuous
# Same formula; the difference is in the hypothesis and alpha interpretation
n_per_group = math.ceil(((z_a + z_b)**2 * 2 * sd**2) / margin**2)
n_total = n_per_group * 2

n_adj = math.ceil(n_total / (1 - attrition_rate))
```

### R Package
Base R. Also see `TrialSize`, `PowerTOST` packages.

### Key References
- Julious SA. Sample sizes for clinical trials with normal data. Stat Med. 2004;23(12):1921-1986.
- Schuirmann DJ. A comparison of the two one-sided tests procedure and the power approach for assessing the equivalence of average bioavailability. J Pharmacokinet Biopharm. 1987;15(6):657-680.

---

## Test 11: Cox Regression EPV (Events Per Variable)

### Formula
```
N_events = EPV × k    (where k = number of predictor variables)
N_total = ceil( N_events / event_rate )
N_adj = ceil( N_total / (1 - attrition_rate) )
```

Where:
- `EPV` = events per variable (minimum 10, recommended 20)
- `k` = number of predictors in the Cox model
- `event_rate` = proportion of subjects experiencing the event

### R Implementation
```r
n_events <- epv * n_predictors
n_total <- ceiling(n_events / event_rate)
n_adj <- ceiling(n_total / (1 - attrition_rate))

cat(sprintf("EPV = %d, Predictors = %d\n", epv, n_predictors))
cat(sprintf("Required events = %d\n", n_events))
cat(sprintf("Total N = %d (event rate = %.0f%%)\n", n_total, event_rate * 100))
cat(sprintf("Adjusted N = %d (attrition = %.0f%%)\n", n_adj, attrition_rate * 100))
```

### Python Implementation
```python
import math

n_events = epv * n_predictors
n_total = math.ceil(n_events / event_rate)
n_adj = math.ceil(n_total / (1 - attrition_rate))
```

### R Package
Base R (no additional packages needed).

### Key References
- Peduzzi P, Concato J, Feinstein AR, Holford TR. Importance of events per independent variable in proportional hazards regression analysis. II. Accuracy and precision of regression estimates. J Clin Epidemiol. 1995;48(12):1503-1510.
- Vittinghoff E, McCulloch CE. Relaxing the rule of ten events per variable in logistic and Cox regression. Am J Epidemiol. 2007;165(6):710-718.

---

## Cohen's Effect Size Conventions

| Measure | Small | Medium | Large | Context |
|---------|-------|--------|-------|---------|
| d (t-test) | 0.20 | 0.50 | 0.80 | Difference in means / pooled SD |
| f (ANOVA) | 0.10 | 0.25 | 0.40 | SD of group means / within-group SD |
| h (proportions) | 0.20 | 0.50 | 0.80 | Arcsine-transformed proportion difference |
| w (chi-square) | 0.10 | 0.30 | 0.50 | Chi-square contingency effect |
| OR (logistic) | 1.5 | 2.0 | 3.0+ | Odds ratio (approximate equivalence) |
| HR (survival) | 0.80 | 0.65 | 0.50 | Hazard ratio (values < 1 favor treatment) |
| ICC | 0.50-0.75 | 0.75-0.90 | > 0.90 | Poor/moderate/good/excellent |
| Kappa | 0.21-0.40 | 0.41-0.60 | 0.61-0.80 | Fair/moderate/substantial |

**Important**: Cohen's conventions are rules of thumb. Always prefer effect sizes estimated from prior literature or pilot data. When conventions are used, explicitly state this limitation in the IRB justification.

---

## Common Attrition Rates by Study Type

| Study Type | Typical Attrition | Recommended Adjustment |
|------------|-------------------|------------------------|
| Randomized controlled trial (RCT) | 15-20% | 20% |
| Prospective observational / cohort | 10-15% | 15% |
| Cross-sectional / survey | 5-10% | 10% |
| Retrospective chart review | 3-5% | 5% |
| Diagnostic accuracy (imaging) | 5-10% | 10% |
| Inter-rater agreement study | 5-10% | 10% |
| Survival / long follow-up (> 2 yr) | 15-25% | 20% |

**Note**: Attrition rates vary widely by disease, population, and follow-up duration. Use study-specific estimates when available.

---

## Key References

1. **Cohen J.** Statistical Power Analysis for the Behavioral Sciences. 2nd ed. Hillsdale, NJ: Lawrence Erlbaum Associates; 1988.
   - Foundation for effect size conventions (d, f, h, w) and power analysis methodology.

2. **Schoenfeld DA.** The asymptotic properties of nonparametric tests for comparing survival distributions. Biometrika. 1981;68(1):316-319.
   - Formula for required number of events in log-rank test.

3. **Bonett DG.** Sample size requirements for estimating intraclass correlations with desired precision. Stat Med. 2002;21(9):1331-1335.
   - ICC-based sample size using Fisher z-transformation.

4. **Hsieh FY.** Sample size tables for logistic regression. Stat Med. 1989;8(7):795-802.
   - Power-based sample size for detecting a specific odds ratio.

5. **Peduzzi P, Concato J, Kemper E, Holford TR, Feinstein AR.** A simulation study of the number of events per variable in logistic regression analysis. J Clin Epidemiol. 1996;49(12):1373-1379.
   - EPV >= 10 rule for logistic regression model stability.

6. **Donner A, Eliasziw M.** A goodness-of-fit approach to inference procedures for the kappa statistic: confidence interval construction, significance-testing and sample size estimation. Stat Med. 1992;11(11):1511-1519.
   - Sample size for testing kappa against a null value.

7. **Buderer NMF.** Statistical methodology: I. Incorporating the prevalence of disease into the sample size calculation for sensitivity and specificity. Acad Emerg Med. 1996;3(9):895-900.
   - Prevalence-adjusted sample size for diagnostic accuracy.

8. **Julious SA.** Sample sizes for clinical trials with normal data. Stat Med. 2004;23(12):1921-1986.
   - Comprehensive non-inferiority and equivalence sample size formulas.

9. **Schuirmann DJ.** A comparison of the two one-sided tests procedure and the power approach for assessing the equivalence of average bioavailability. J Pharmacokinet Biopharm. 1987;15(6):657-680.
   - TOST (two one-sided tests) procedure for equivalence testing.

10. **Koo TK, Li MY.** A guideline of selecting and reporting intraclass correlation coefficients for reliability research. J Chiropr Med. 2016;15(2):155-163.
    - ICC interpretation benchmarks.

11. **Landis JR, Koch GG.** The measurement of observer agreement for categorical data. Biometrics. 1977;33(1):159-174.
    - Kappa interpretation benchmarks.

12. **Connor RJ.** Sample size for testing differences in proportions for the paired-sample design. Biometrics. 1987;43(1):207-211.
    - McNemar test sample size formula.

13. **Peduzzi P, Concato J, Feinstein AR, Holford TR.** Importance of events per independent variable in proportional hazards regression analysis. II. Accuracy and precision of regression estimates. J Clin Epidemiol. 1995;48(12):1503-1510.
    - EPV >= 10 rule for Cox regression model stability.

14. **Vittinghoff E, McCulloch CE.** Relaxing the rule of ten events per variable in logistic and Cox regression. Am J Epidemiol. 2007;165(6):710-718.
    - Evidence that EPV 5-10 may be acceptable with careful validation.
