# Sample Size Formulas Reference

Per-test parameter tables (with defaults), effect-size interpretation, formulas, R/Python implementations, and key references for Tests 1-11, plus effect-size conventions and attrition rates.

**Every formula carries a Check**: one realistic input and the number an established package (or
the method's own published worked example) returns for it. The R and Python blocks are set to that
input, so running a block unchanged prints the Check value. Replace the inputs with the study's
values only after that, one input per line as written. `tests/test_worked_examples.py` re-runs every
block against its Check.

---

## Test 1: Diagnostic Accuracy (Sensitivity/Specificity Precision)

### Parameters (ask the user; offer the default)
| Parameter | Description | Default |
|-----------|-------------|---------|
| `se_expected` | Expected sensitivity | 0.85 |
| `sp_expected` | Expected specificity | 0.85 |
| `ci_half_width` | Desired half-width of the 95% CI (for both, or set per target) | 0.05 |
| `prevalence` | Disease prevalence in the study population | 0.30 |
| `alpha` | 1 − confidence level | 0.05 |
| `attrition_rate` | Expected dropout/exclusion rate | 0.10 |

**Effect size interpretation**: The CI half-width determines precision. A half-width of 0.05 means the 95% CI for sensitivity will be within +/-5 percentage points. Narrower CIs require larger samples.

### Formula
Sensitivity is estimated in the diseased, specificity in the non-diseased (Buderer 1996):

```
n_se    = z²_{1−α/2} · Se(1 − Se) / (w² · prevalence)
n_sp    = z²_{1−α/2} · Sp(1 − Sp) / (w² · (1 − prevalence))
n_total = ceil( max(n_se, n_sp) )
```

Where:
- `w` = desired CI half-width
- `prevalence` = disease prevalence in the study population; specificity uses `1 − prevalence`
- the larger of the two drives N. At a prevalence above 0.5 specificity is usually the binding target.

If only one of the two is a target, still report the half-width the other one gets at the chosen N.
These are Wald intervals; for an expected value ≥ 0.95, size with a Wilson or exact interval
(`presize::prec_sens` / `prec_spec`), because the Wald interval under-covers near 1.

**Check**: Se = Sp = 0.85, w = 0.05, prevalence 0.60 → n_se 327, n_sp 490, **N = 490**
(`epiR::epi.ssdxsesp(se = 0.85, sp = 0.85, Py = 0.6, epsilon = 0.05, error = "absolute")`, epiR 2.0.91
→ se.n 327, sp.n 490, total.n 490). At prevalence 0.30 with Sp 0.90 → 654 (sensitivity binds).

### R Implementation
```r
# Worked example = the Check inputs; replace with the study's values
se_expected <- 0.85
sp_expected <- 0.85
ci_half_width <- 0.05
prevalence <- 0.60
alpha <- 0.05
attrition_rate <- 0.10

z <- qnorm(1 - alpha / 2)
n_se <- ceiling(z^2 * se_expected * (1 - se_expected) / (ci_half_width^2 * prevalence))
n_sp <- ceiling(z^2 * sp_expected * (1 - sp_expected) / (ci_half_width^2 * (1 - prevalence)))
n_total <- max(n_se, n_sp)
n_adj <- ceiling(n_total / (1 - attrition_rate))
cat(sprintf("N for Se = %d, N for Sp = %d -> N = %d (with attrition %d)\n",
            n_se, n_sp, n_total, n_adj))
# Same numbers: epiR::epi.ssdxsesp(se = se_expected, sp = sp_expected, Py = prevalence,
#                                  epsilon = ci_half_width, error = "absolute")
```

### Python Implementation
```python
import math
from scipy.stats import norm

# Worked example = the Check inputs; replace with the study's values
se_expected = 0.85
sp_expected = 0.85
ci_half_width = 0.05
prevalence = 0.60
alpha = 0.05
attrition_rate = 0.10

z = norm.ppf(1 - alpha / 2)
n_se = math.ceil(z**2 * se_expected * (1 - se_expected) / (ci_half_width**2 * prevalence))
n_sp = math.ceil(z**2 * sp_expected * (1 - sp_expected) / (ci_half_width**2 * (1 - prevalence)))
n_total = max(n_se, n_sp)
n_adj = math.ceil(n_total / (1 - attrition_rate))
print(f"N for Se = {n_se}, N for Sp = {n_sp} -> N = {n_total} (with attrition {n_adj})")
```

### R Package
Base R. Cross-check: `epiR::epi.ssdxsesp`.

### Key Reference
Buderer NMF. Statistical methodology: I. Incorporating the prevalence of disease into the sample size calculation for sensitivity and specificity. Acad Emerg Med. 1996;3(9):895-900. doi:10.1111/j.1553-2712.1996.tb03538.x

---

## Test 2: ICC Agreement (Walter 1998 test; Bonett 2002 precision)

Two different aims, two different formulas, two different N. Ask which one the study has:
**(A)** show the ICC exceeds a minimally acceptable value ρ0 (a one-sided test, Walter et al.), or
**(B)** estimate the ICC with a 95% CI of a given width (precision, Bonett).

### Parameters (ask the user; offer the default)
| Parameter | Description | Default |
|-----------|-------------|---------|
| `icc_expected` | Anticipated ICC (ρ1) | 0.75 |
| `icc_null` | (A) Minimally acceptable ICC, H0: ρ ≤ ρ0 | 0.50 |
| `n_raters` | Ratings per subject (k) | 2 |
| `ci_width` | (B) Full width of the 95% CI | 0.20 |
| `alpha` | (A) One-sided significance level | 0.05 |
| `power` | (A) Desired power | 0.80 |
| `attrition_rate` | Expected dropout rate | 0.10 |

**Effect size interpretation**: ICC < 0.50 = poor, 0.50-0.75 = moderate, 0.75-0.90 = good, > 0.90 = excellent (Koo & Li, 2016).

### Formula A — test against ρ0 (Walter, Eliasziw & Donner 1998)
```
C0 = (1 + k·ρ0/(1 − ρ0)) / (1 + k·ρ1/(1 − ρ1))
n  = 1 + 2·k·(z_{1−α} + z_{1−β})² / ((k − 1)·(ln C0)²)
```
For a two-sided test use z_{1−α/2}. N falls as raters are added (k = 2 → 36, k = 3 → 24 below).

**Check**: ρ1 0.75, ρ0 0.50, k = 3, α 0.05 one-sided, 80% power → 23.09 → **24 subjects**
(`ICC.Sample.Size::calculateIccSampleSize(p = 0.75, p0 = 0.5, k = 3, alpha = 0.05, tails = 1, power = 0.8)`,
ICC.Sample.Size 1.1 → N = 24); k = 2 → 36.

### Formula B — CI width (Bonett 2002)
```
n = 1 + 8·z²_{1−α/2}·(1 − ρ)²·(1 + (k − 1)ρ)² / (k·(k − 1)·w²)       w = full CI width
```
Bonett adds 5ρ to n when k = 2 and ρ ≥ 0.7.

**Check**: ρ 0.85, k = 4, w 0.20 → 19.2 → **20 subjects** (Bonett 2002's own worked example gives 19.2;
`presize::prec_icc(rho = 0.85, k = 4, conf.width = 0.2)`, presize 0.3.11 → 20).

### R Implementation
```r
# (A) Test H0: ICC <= icc_null. Worked example = the Check inputs
icc_expected <- 0.75
icc_null <- 0.50
n_raters <- 3
alpha <- 0.05
power <- 0.80
attrition_rate <- 0.10

C0 <- (1 + n_raters * icc_null / (1 - icc_null)) /
  (1 + n_raters * icc_expected / (1 - icc_expected))
n_icc_test <- ceiling(1 + 2 * n_raters * (qnorm(1 - alpha) + qnorm(power))^2 /
                        ((n_raters - 1) * log(C0)^2))
cat(sprintf("ICC test: N = %d subjects (with attrition %d)\n",
            n_icc_test, ceiling(n_icc_test / (1 - attrition_rate))))
# Same number: ICC.Sample.Size::calculateIccSampleSize(p = icc_expected, p0 = icc_null,
#   k = n_raters, alpha = alpha, tails = 1, power = power)
```

```r
# (B) Precision: full 95% CI width. Worked example = Bonett (2002)
icc_expected <- 0.85
n_raters <- 4
ci_width <- 0.20

z <- qnorm(0.975)
n_icc_prec <- 1 + 8 * z^2 * (1 - icc_expected)^2 * (1 + (n_raters - 1) * icc_expected)^2 /
  (n_raters * (n_raters - 1) * ci_width^2)
if (n_raters == 2 && icc_expected >= 0.7) n_icc_prec <- n_icc_prec + 5 * icc_expected
n_icc_prec <- ceiling(n_icc_prec)
cat(sprintf("ICC precision: N = %d subjects\n", n_icc_prec))
# Same number: presize::prec_icc(rho = icc_expected, k = n_raters, conf.width = ci_width)
```

### Python Implementation
```python
import math
from scipy.stats import norm

# (A) Test H0: ICC <= icc_null. Worked example = the Check inputs
icc_expected = 0.75
icc_null = 0.50
n_raters = 3
alpha = 0.05
power = 0.80
attrition_rate = 0.10

C0 = (1 + n_raters * icc_null / (1 - icc_null)) / (1 + n_raters * icc_expected / (1 - icc_expected))
n_icc_test = math.ceil(1 + 2 * n_raters * (norm.ppf(1 - alpha) + norm.ppf(power))**2
                       / ((n_raters - 1) * math.log(C0)**2))
print(f"ICC test: N = {n_icc_test} subjects (with attrition {math.ceil(n_icc_test / (1 - attrition_rate))})")
```

```python
import math
from scipy.stats import norm

# (B) Precision: full 95% CI width. Worked example = Bonett (2002)
icc_expected = 0.85
n_raters = 4
ci_width = 0.20

z = norm.ppf(0.975)
n_icc_prec = 1 + 8 * z**2 * (1 - icc_expected)**2 * (1 + (n_raters - 1) * icc_expected)**2 \
    / (n_raters * (n_raters - 1) * ci_width**2)
if n_raters == 2 and icc_expected >= 0.7:
    n_icc_prec += 5 * icc_expected
n_icc_prec = math.ceil(n_icc_prec)
print(f"ICC precision: N = {n_icc_prec} subjects")
```

### R Package
Base R. Cross-checks: `ICC.Sample.Size::calculateIccSampleSize` (A), `presize::prec_icc` (B).
(`MKpower` has no ICC sample-size function.)

### Key References
- Walter SD, Eliasziw M, Donner A. Sample size and optimal designs for reliability studies. Stat Med. 1998;17(1):101-110. doi:10.1002/(SICI)1097-0258(19980115)17:1<101::AID-SIM727>3.0.CO;2-E
- Bonett DG. Sample size requirements for estimating intraclass correlations with desired precision. Stat Med. 2002;21(9):1331-1335. doi:10.1002/sim.1108

---

## Test 3: Kappa Agreement (Donner & Eliasziw 1992)

### Parameters (ask the user; offer the default)
| Parameter | Description | Default |
|-----------|-------------|---------|
| `kappa_expected` | Expected kappa (κ1) | 0.70 |
| `kappa_null` | Null hypothesis kappa (κ0) | 0.40 |
| `prevalence` | Proportion of subjects in the positive category (trait prevalence) | 0.50 |
| `n_raters` | Raters per subject (2–6 via `kappaSize`) | 2 |
| `alpha` | Significance level (two-sided) | 0.05 |
| `power` | Desired power | 0.80 |
| `attrition_rate` | Expected dropout rate | 0.10 |

**Effect size interpretation**: Kappa < 0.20 = slight, 0.21-0.40 = fair, 0.41-0.60 = moderate, 0.61-0.80 = substantial, 0.81-1.00 = almost perfect (Landis & Koch, 1977).

The variance of kappa depends on the trait prevalence, so N does too: the Check below needs 74
subjects at prevalence 0.50 and 107 at 0.20. Always ask for the prevalence; do not size kappa
from κ1 and κ0 alone.

### Formula
Goodness-of-fit approach, two raters, binary rating, common prevalence π:

```
P_both_neg(κ) = (1 − π)² + κ·π(1 − π)
P_discord(κ)  = 2(1 − κ)·π(1 − π)
P_both_pos(κ) = π² + κ·π(1 − π)
χ² = Σ over the three cells of (P(κ1) − P(κ0))² / P(κ0)
n  = (z_{1−α/2} + z_{1−β})² / χ²
```

`(z_{1−α/2} + z_{1−β})²` is the non-centrality a 1-df χ² test needs for the target power
(7.849 at α 0.05, 80%; `kappaSize` solves it exactly and gets the same value to four decimals).
For 3–6 raters or 3–5 categories use the `kappaSize` functions below rather than extending the
formula by hand. If the two raters' marginal positive rates are expected to differ, Cantor's method
(`irr::N.cohen.kappa(rate1, rate2, k1, k0, alpha, power, twosided = TRUE)`) allows separate rates; it
uses a different variance and returns a different N (64 for the Check inputs), so name the method
used.

**Check**: κ1 0.70, κ0 0.40, π 0.50, 2 raters, α 0.05, 80% → 73.26 → **74 subjects**
(`kappaSize::PowerBinary(kappa0 = 0.4, kappa1 = 0.7, props = 0.5, raters = 2, alpha = 0.05, power = 0.8)`,
kappaSize 1.2 → N = 73.26); π 0.20 → 107.

### R Implementation
```r
library(kappaSize)

# Worked example = the Check inputs; replace with the study's values
kappa_expected <- 0.70
kappa_null <- 0.40
prevalence <- 0.50
n_raters <- 2
alpha <- 0.05
power <- 0.80
attrition_rate <- 0.10

res <- PowerBinary(kappa0 = kappa_null, kappa1 = kappa_expected, props = prevalence,
                   raters = n_raters, alpha = alpha, power = power)
n_kappa <- ceiling(res$N)
cat(sprintf("Kappa: N = %d subjects (with attrition %d)\n",
            n_kappa, ceiling(n_kappa / (1 - attrition_rate))))
# 3, 4 or 5 categories: Power3Cats / Power4Cats / Power5Cats with props = the category proportions
```

### Python Implementation
```python
import math
from scipy.stats import norm

# Worked example = the Check inputs; replace with the study's values (two raters, binary)
kappa_expected = 0.70
kappa_null = 0.40
prevalence = 0.50
alpha = 0.05
power = 0.80
attrition_rate = 0.10

def cell_probs(kappa, p):
    q = 1 - p
    return (q**2 + kappa * p * q, 2 * (1 - kappa) * p * q, p**2 + kappa * p * q)

p_alt = cell_probs(kappa_expected, prevalence)
p_null = cell_probs(kappa_null, prevalence)
chi2 = sum((a - b)**2 / b for a, b in zip(p_alt, p_null))
n_kappa = math.ceil((norm.ppf(1 - alpha / 2) + norm.ppf(power))**2 / chi2)
print(f"Kappa: N = {n_kappa} subjects (with attrition {math.ceil(n_kappa / (1 - attrition_rate))})")
```

### R Package
`kappaSize` (Donner & Eliasziw goodness-of-fit; 2–6 raters, 2–5 categories). Alternative with
unequal rater marginals: `irr::N.cohen.kappa` (Cantor 1996).

### Key References
- Donner A, Eliasziw M. A goodness-of-fit approach to inference procedures for the kappa statistic: confidence interval construction, significance-testing and sample size estimation. Stat Med. 1992;11(11):1511-1519. doi:10.1002/sim.4780111109
- Cantor AB. Sample-size calculations for Cohen's kappa. Psychol Methods. 1996;1(2):150-153. doi:10.1037/1082-989X.1.2.150

---

## Test 4: Two-Proportion Comparison (Chi-Square)

### Parameters (ask the user; offer the default)
| Parameter | Description | Default |
|-----------|-------------|---------|
| `p1` | Proportion in group 1 | -- |
| `p2` | Proportion in group 2 | -- |
| `alpha` | Significance level | 0.05 |
| `power` | Desired power | 0.80 |
| `attrition_rate` | Expected dropout rate | 0.15 |

**Effect size interpretation**: Cohen's h = 2 * arcsin(sqrt(p1)) - 2 * arcsin(sqrt(p2)). Small = 0.20, medium = 0.50, large = 0.80.

### Formula
Based on Cohen's h effect size (arcsine transformation):

```
h = 2 * arcsin(sqrt(p1)) - 2 * arcsin(sqrt(p2))
n_per_group = ceil( 2 * ((z_{alpha/2} + z_{beta}) / h)^2 )
```
Each arcsine-transformed proportion has variance 1/n, so their difference has 2/n: the factor 2 is
what `pwr.2p.test` and statsmodels use. Without it N is halved (81 instead of 162 below).

**Check**: p1 0.70, p2 0.55, α 0.05, 80% → h 0.311, 161.9 → **162 per group, 324 total**
(`pwr::pwr.2p.test(h = ES.h(0.70, 0.55), power = 0.8)` → n = 161.93; statsmodels `NormalIndPower` → 161.93).

### R Implementation
```r
library(pwr)

# Worked example = the Check inputs; replace with the study's values
p1 <- 0.70
p2 <- 0.55
alpha <- 0.05
power <- 0.80

h <- ES.h(p1, p2)
result <- pwr.2p.test(h = h, sig.level = alpha, power = power)
n_per_group <- ceiling(result$n)
n_total <- n_per_group * 2
cat(sprintf("h = %.3f: %d per group, %d total\n", h, n_per_group, n_total))
```

### Python Implementation
```python
import math
import numpy as np
from statsmodels.stats.power import NormalIndPower

# Worked example = the Check inputs; replace with the study's values
p1 = 0.70
p2 = 0.55
alpha = 0.05
power = 0.80

h = 2 * np.arcsin(np.sqrt(p1)) - 2 * np.arcsin(np.sqrt(p2))
n_per_group = math.ceil(NormalIndPower().solve_power(effect_size=h, alpha=alpha, power=power,
                                                     ratio=1, alternative='two-sided'))
n_total = n_per_group * 2
print(f"h = {h:.3f}: {n_per_group} per group, {n_total} total")
```

### R Package
`pwr`

### Key Reference
Cohen J. Statistical Power Analysis for the Behavioral Sciences. 2nd ed. Lawrence Erlbaum Associates; 1988.

---

## Test 5: McNemar Test (Paired Proportions)

### Parameters (ask the user; offer the default)
| Parameter | Description | Default |
|-----------|-------------|---------|
| `p01` | P(Method A negative, Method B positive) | -- |
| `p10` | P(Method A positive, Method B negative) | -- |
| `alpha` | Significance level | 0.05 |
| `power` | Desired power | 0.80 |
| `attrition_rate` | Expected dropout rate | 0.10 |

**Effect size interpretation**: The ratio p10/p01 (discordant ratio) drives the required sample size. Larger asymmetry in discordant pairs means fewer subjects needed. Only discordant pairs contribute information.

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

**Check**: p01 0.10, p10 0.25, α 0.05, 80% → 119.7 → **120 pairs**
(`TrialSize::McNemar.Test(alpha = 0.05, beta = 0.2, psai = 0.25/0.10, paid = 0.35)`, TrialSize 1.4.1 → 119.71).

### R Implementation
```r
# Worked example = the Check inputs; replace with the study's values
p01 <- 0.10
p10 <- 0.25
alpha <- 0.05
power <- 0.80

n_mc <- ceiling(
  (qnorm(1 - alpha / 2) * sqrt(p01 + p10) +
     qnorm(power) * sqrt(p01 + p10 - (p10 - p01)^2))^2 /
    (p10 - p01)^2
)
cat(sprintf("McNemar: %d pairs\n", n_mc))
```

### Python Implementation
```python
import math
from scipy.stats import norm

# Worked example = the Check inputs; replace with the study's values
p01 = 0.10
p10 = 0.25
alpha = 0.05
power = 0.80

z_a = norm.ppf(1 - alpha / 2)
z_b = norm.ppf(power)
disc_sum = p01 + p10
disc_diff = p10 - p01
n_mc = math.ceil((z_a * math.sqrt(disc_sum) +
                  z_b * math.sqrt(disc_sum - disc_diff**2))**2 / disc_diff**2)
print(f"McNemar: {n_mc} pairs")
```

### R Package
Base R. Cross-check: `TrialSize::McNemar.Test`.

### Key Reference
Connor RJ. Sample size for testing differences in proportions for the paired-sample design. Biometrics. 1987;43(1):207-211. doi:10.2307/2531961

---

## Test 6: Independent t-Test

### Parameters (ask the user; offer the default)
| Parameter | Description | Default |
|-----------|-------------|---------|
| `mean_diff` | Expected mean difference | -- |
| `pooled_sd` | Pooled standard deviation (from literature/pilot) | -- |
| `alpha` | Significance level | 0.05 |
| `power` | Desired power | 0.80 |
| `attrition_rate` | Expected dropout rate | 0.15 |

**Effect size interpretation**: Cohen's d = mean_diff / pooled_sd. Small = 0.20, medium = 0.50, large = 0.80. In clinical terms, d = 0.50 means the groups differ by half a standard deviation.

### Formula
```
d = mean_diff / pooled_sd    (Cohen's d)
n_per_group ≈ 2 * ((z_{alpha/2} + z_{beta}) / d)^2      (normal approximation)
```
The packages solve the non-central t exactly and return one or two more per group than the normal
approximation; report the package value.

**Check**: d 0.50 (mean_diff 5, SD 10), α 0.05, 80% → 63.8 → **64 per group** (normal approximation 63)
(`pwr::pwr.t.test(d = 0.5, power = 0.8)` → 63.77; statsmodels `TTestIndPower` → 63.77).

### R Implementation
```r
library(pwr)

# Worked example = the Check inputs; replace with the study's values
mean_diff <- 5
pooled_sd <- 10
alpha <- 0.05
power <- 0.80

d <- mean_diff / pooled_sd
result <- pwr.t.test(d = d, sig.level = alpha, power = power, type = "two.sample")
n_per_group <- ceiling(result$n)
n_total <- n_per_group * 2
cat(sprintf("d = %.2f: %d per group, %d total\n", d, n_per_group, n_total))
```

### Python Implementation
```python
import math
from statsmodels.stats.power import TTestIndPower

# Worked example = the Check inputs; replace with the study's values
mean_diff = 5
pooled_sd = 10
alpha = 0.05
power = 0.80

d = mean_diff / pooled_sd
n_per_group = math.ceil(TTestIndPower().solve_power(effect_size=d, alpha=alpha, power=power,
                                                    ratio=1, alternative='two-sided'))
n_total = n_per_group * 2
print(f"d = {d:.2f}: {n_per_group} per group, {n_total} total")
```

### R Package
`pwr`

### Key Reference
Cohen J. Statistical Power Analysis for the Behavioral Sciences. 2nd ed. Lawrence Erlbaum Associates; 1988.

---

## Test 7: Survival / Log-Rank Test (Schoenfeld)

### Parameters (ask the user; offer the default)
| Parameter | Description | Default |
|-----------|-------------|---------|
| `hr` | Expected hazard ratio (experimental vs control) | -- |
| `p_alloc` | Proportion randomised to the experimental arm (1:1 → 0.5, 2:1 → 2/3) | 0.5 |
| `median_ctrl` | Median survival in the control arm (months) | -- |
| `accrual_time` | Accrual period, uniform entry (months) | 12 |
| `follow_up` | Minimum follow-up after accrual closes (months) | 24 |
| `annual_dropout` | Proportion lost to follow-up per year | 0.05 |
| `alpha` | Significance level (two-sided) | 0.05 |
| `power` | Desired power | 0.80 |

**Effect size interpretation**: HR < 1 favors treatment. HR = 0.50 means treatment halves the hazard (strong effect). HR = 0.80 is a modest 20% reduction. Power comes from the number of **events**, not patients: size the events first, then the patients needed to observe them.

### Formula
Step 1 — required events (Schoenfeld 1983; the allocation term is not optional):
```
D = (z_{1−α/2} + z_{1−β})² / ( p·(1 − p)·(ln HR)² )          p = p_alloc
  = 4·(z_{1−α/2} + z_{1−β})² / (ln HR)²                        at 1:1
```

**Check**: HR 0.70, α 0.05 two-sided, 80%, 1:1 → 246.8 → **247 events**
(`gsDesign::nEvents(hr = 0.7, alpha = 0.05, beta = 0.2, sided = 2)`, gsDesign 3.11.0 → 246.79);
2:1 → 278 (`ratio = 2` → 277.64). Without `p(1 − p)` the formula gives 62, a quarter of the events,
and the study has about 29% power instead of 80%.

Step 2 — patients. Exponential survival, uniform accrual over R, total duration T = R + F
(F = minimum follow-up), exponential loss-to-follow-up hazard η:
```
λ_c = ln 2 / median_ctrl        λ_e = HR·λ_c
η   = −ln(1 − annual_dropout) / 12              (per month; use the unit of median_ctrl)
P(event | λ) = λ/(λ + η) · [ 1 − (e^{−(λ+η)F} − e^{−(λ+η)T}) / ((λ + η)·R) ]
P̄ = p·P(event | λ_e) + (1 − p)·P(event | λ_c)
N = D / P̄        (round each arm up)
```
Dropout is already inside P̄; do not divide N by (1 − dropout) again.

**Check**: median_ctrl 24 months, HR 0.70, R 12, F 24 (T 36), 5% lost per year, 1:1 → P̄ 0.4875,
N 506.3 → **254 per arm, 508 total**
(`gsDesign::nSurv(lambdaC = log(2)/24, hr = 0.7, eta = -log(0.95)/12, gamma = 1, R = 12, T = 36, minfup = 24, ratio = 1, alpha = 0.05, beta = 0.2, sided = 2, method = "Schoenfeld")`
→ n 506.28, d 246.79; the default Lachin–Foulkes method gives 505.85).

### R Implementation
```r
# Worked example = the Check inputs; replace with the study's values
hr <- 0.70
p_alloc <- 0.5
median_ctrl <- 24
accrual_time <- 12
follow_up <- 24
annual_dropout <- 0.05
alpha <- 0.05
power <- 0.80

d_raw <- (qnorm(1 - alpha / 2) + qnorm(power))^2 / (p_alloc * (1 - p_alloc) * log(hr)^2)
n_events <- ceiling(d_raw)

lambda_c <- log(2) / median_ctrl
lambda_e <- hr * lambda_c
eta <- -log(1 - annual_dropout) / 12
total_time <- accrual_time + follow_up
p_event <- function(lambda) {
  a <- lambda + eta
  lambda / a * (1 - (exp(-a * follow_up) - exp(-a * total_time)) / (a * accrual_time))
}
p_bar <- p_alloc * p_event(lambda_e) + (1 - p_alloc) * p_event(lambda_c)
n_exp <- ceiling(p_alloc * d_raw / p_bar)
n_ctrl <- ceiling((1 - p_alloc) * d_raw / p_bar)
n_total <- n_exp + n_ctrl
cat(sprintf("Events = %d; P(event) = %.4f; N = %d (%d experimental + %d control)\n",
            n_events, p_bar, n_total, n_exp, n_ctrl))

if (requireNamespace("gsDesign", quietly = TRUE)) {   # package cross-check, same inputs
  x <- gsDesign::nSurv(lambdaC = lambda_c, hr = hr, eta = eta, gamma = 1, R = accrual_time,
                       T = total_time, minfup = follow_up, ratio = p_alloc / (1 - p_alloc),
                       alpha = alpha, beta = 1 - power, sided = 2, method = "Schoenfeld")
  cat(sprintf("gsDesign::nSurv: n = %.2f, events = %.2f\n", x$n, x$d))
}
```

### Python Implementation
```python
import math
from scipy.stats import norm

# Worked example = the Check inputs; replace with the study's values
hr = 0.70
p_alloc = 0.5
median_ctrl = 24
accrual_time = 12
follow_up = 24
annual_dropout = 0.05
alpha = 0.05
power = 0.80

d_raw = (norm.ppf(1 - alpha / 2) + norm.ppf(power))**2 / (p_alloc * (1 - p_alloc) * math.log(hr)**2)
n_events = math.ceil(d_raw)

lambda_c = math.log(2) / median_ctrl
lambda_e = hr * lambda_c
eta = -math.log(1 - annual_dropout) / 12
total_time = accrual_time + follow_up

def p_event(lam):
    a = lam + eta
    return lam / a * (1 - (math.exp(-a * follow_up) - math.exp(-a * total_time)) / (a * accrual_time))

p_bar = p_alloc * p_event(lambda_e) + (1 - p_alloc) * p_event(lambda_c)
n_exp = math.ceil(p_alloc * d_raw / p_bar)
n_ctrl = math.ceil((1 - p_alloc) * d_raw / p_bar)
n_total = n_exp + n_ctrl
print(f"Events = {n_events}; P(event) = {p_bar:.4f}; N = {n_total} ({n_exp} experimental + {n_ctrl} control)")
```

### R Package
Base R. Cross-checks: `gsDesign::nEvents` (events), `gsDesign::nSurv` (patients; also non-uniform
accrual and piecewise hazards, which the closed form above does not cover).

### Key References
- Schoenfeld DA. Sample-size formula for the proportional-hazards regression model. Biometrics. 1983;39(2):499-503. doi:10.2307/2531021
- Schoenfeld DA. The asymptotic properties of nonparametric tests for comparing survival distributions. Biometrika. 1981;68(1):316-319. doi:10.1093/biomet/68.1.316
- Lachin JM, Foulkes MA. Evaluation of sample size and power for analyses of survival with allowance for nonuniform patient entry, losses to follow-up, noncompliance, and stratification. Biometrics. 1986;42(3):507-519. doi:10.2307/2531201

---

## Test 8: One-Way ANOVA

### Parameters (ask the user; offer the default)
| Parameter | Description | Default |
|-----------|-------------|---------|
| `k` | Number of groups | -- |
| `f` | Cohen's f effect size | -- |
| `alpha` | Significance level | 0.05 |
| `power` | Desired power | 0.80 |
| `attrition_rate` | Expected dropout rate | 0.15 |

**Effect size interpretation**: Cohen's f = 0.25 (medium) means the group means span about half a pooled SD. In clinical terms, this is typically a meaningful difference across treatment arms or measurement methods. To help the user estimate f, use the formulas below (group means + pooled SD, or eta-squared).

### Formula
Using Cohen's f effect size:

```
f = sigma_between / sigma_within
```

Where:
- `sigma_between` = SD of group means
- `sigma_within` = pooled within-group SD

From eta-squared: `f = sqrt(eta_sq / (1 - eta_sq))`

The sample size is obtained from the non-central F power function. `pwr.anova.test` returns n
**per group**; statsmodels `FTestAnovaPower.solve_power` returns the **total** N across all groups.
Divide the statsmodels value by k before rounding up; multiplying it by k triples the study.

**Check**: k = 3, f 0.25, α 0.05, 80% → **53 per group, 159 total**
(`pwr::pwr.anova.test(k = 3, f = 0.25, power = 0.8)` → n = 52.40 per group; statsmodels
`FTestAnovaPower().solve_power(effect_size=0.25, alpha=0.05, power=0.8, k_groups=3)` → 157.19 total).

### R Implementation
```r
library(pwr)

# Worked example = the Check inputs; replace with the study's values
k <- 3
f <- 0.25
alpha <- 0.05
power <- 0.80
attrition_rate <- 0.15

result <- pwr.anova.test(k = k, f = f, sig.level = alpha, power = power)
n_per_group <- ceiling(result$n)          # pwr returns n per group
n_total <- n_per_group * k
n_adj <- ceiling(n_total / (1 - attrition_rate))
cat(sprintf("%d per group, %d total (with attrition %d)\n", n_per_group, n_total, n_adj))
```

### Python Implementation
```python
import math
from statsmodels.stats.power import FTestAnovaPower

# Worked example = the Check inputs; replace with the study's values
k = 3
f = 0.25
alpha = 0.05
power = 0.80
attrition_rate = 0.15

n_total_raw = FTestAnovaPower().solve_power(effect_size=f, nobs=None, alpha=alpha,
                                            power=power, k_groups=k)   # TOTAL N, all groups
n_per_group = math.ceil(n_total_raw / k)
n_total = n_per_group * k
n_adj = math.ceil(n_total / (1 - attrition_rate))
print(f"{n_per_group} per group, {n_total} total (with attrition {n_adj})")
```

### R Package
`pwr`

### Key Reference
Cohen J. Statistical Power Analysis for the Behavioral Sciences. 2nd ed. Lawrence Erlbaum Associates; 1988. (Chapter 8: F tests for ANOVA)

---

## Test 9: Logistic Regression

### Parameters (ask the user; offer the default)
| Parameter | Description | Default |
|-----------|-------------|---------|
| `n_predictors` | Number of predictor parameters in the model | -- |
| `event_rate` | Overall event rate (continuous predictor: the event rate at the mean of X) | -- |
| `predictor_type` | Is the predictor of interest continuous or binary? | -- |
| `or_per_sd` | Continuous predictor: odds ratio per 1 SD of X | -- |
| `p_unexposed` | Binary predictor: P(outcome) when X = 0 | -- |
| `p_exposed` | Binary predictor: P(outcome) when X = 1 (from an OR: OR·p0 / (1 − p0 + OR·p0)) | -- |
| `exposure_prev` | Binary predictor: proportion with X = 1 (B) | -- |
| `r2_other` | R² of the predictor regressed on the other covariates | 0.0 |
| `alpha` | Significance level | 0.05 |
| `power` | Desired power | 0.80 |
| `attrition_rate` | Expected dropout rate | 0.10 |

**Effect size interpretation**: OR = 1.5 is a small-to-moderate effect; OR = 2.0 is moderate; OR = 3.0+ is large. The Peduzzi rule ensures model stability; the Hsieh formula targets power for the primary predictor. A continuous predictor's OR is per 1 SD; a binary predictor's OR is exposed vs unexposed, and the two are not interchangeable.

### Approach A: Peduzzi Rule of Thumb (EPV >= 10)

```
N_events = 10 * p   (where p = number of predictor parameters)
N_total = N_events / event_rate
```

This ensures at least 10 events per predictor variable (EPV), a minimum for stable estimates when the aim is one predictor's association. It is not a power calculation.

**Check (arithmetic)**: 10 predictors, event rate 0.20 → 100 events → **500**.

### Approach B1: Hsieh, continuous predictor (Hsieh, Bloch & Larsen 1998)

```
n = (z_{1−α/2} + z_{1−β})² / ( P(1 − P)·(ln OR_SD)² )        P = event rate at the mean of X
```

**Check**: P 0.20, OR 2.0 per SD → 102.1 → **103** (`powerMediation::SSizeLogisticCon(p1 = 0.2, OR = 2)`, powerMediation 0.3.4 → 103).

### Approach B2: Hsieh, binary predictor (Hsieh, Bloch & Larsen 1998)

```
P̄ = (1 − B)·P1 + B·P2              P1 = P(Y=1 | X=0), P2 = P(Y=1 | X=1), B = proportion exposed
n  = [ z_{1−α/2}·√(P̄(1 − P̄)/B) + z_{1−β}·√(P1(1 − P1) + P2(1 − P2)(1 − B)/B) ]² / ( (P1 − P2)²·(1 − B) )
```

N rises steeply as exposure becomes rare: the Check needs 398 at B = 0.5 and 575 at B = 0.2. Do not
use B1 for a binary exposure: it has no B term and returned 103 where B2 returns 424 (OR 2, B 0.5,
overall event rate 0.20): 26% power in 2,000 simulated logistic fits at N = 103, 80% at 424.

**Check**: P1 0.10, P2 0.20, B 0.5 → **398**; B 0.2 → 575
(`powerMediation::SSizeLogisticBin(p1 = 0.1, p2 = 0.2, B = 0.5)` → 398).

### Adjustment for the other covariates (both B1 and B2)
```
n_adj = n / (1 − R²)        R² = squared multiple correlation of the predictor with the other covariates
```

### R Implementation
```r
# Worked example = the Check inputs; replace with the study's values
n_predictors <- 10
event_rate <- 0.20
or_per_sd <- 2.0
p_unexposed <- 0.10
p_exposed <- 0.20
exposure_prev <- 0.5
r2_other <- 0
alpha <- 0.05
power <- 0.80

z_a <- qnorm(1 - alpha / 2)
z_b <- qnorm(power)

# Approach A: Peduzzi (stability floor, not power)
n_peduzzi <- ceiling(10 * n_predictors / event_rate)

# Approach B1: continuous predictor, OR per 1 SD
n_hsieh_con <- ceiling((z_a + z_b)^2 / (event_rate * (1 - event_rate) * log(or_per_sd)^2))

# Approach B2: binary predictor
p_bar <- (1 - exposure_prev) * p_unexposed + exposure_prev * p_exposed
n_hsieh_bin <- ceiling(
  (z_a * sqrt(p_bar * (1 - p_bar) / exposure_prev) +
     z_b * sqrt(p_unexposed * (1 - p_unexposed) +
                  p_exposed * (1 - p_exposed) * (1 - exposure_prev) / exposure_prev))^2 /
    ((p_unexposed - p_exposed)^2 * (1 - exposure_prev))
)

n_hsieh_con_adj <- ceiling(n_hsieh_con / (1 - r2_other))
n_hsieh_bin_adj <- ceiling(n_hsieh_bin / (1 - r2_other))
cat(sprintf("Peduzzi %d | Hsieh continuous %d | Hsieh binary %d\n",
            n_peduzzi, n_hsieh_con_adj, n_hsieh_bin_adj))
# Report the larger of Peduzzi and the Hsieh value that matches the predictor type.
# Same numbers: powerMediation::SSizeLogisticCon(event_rate, or_per_sd),
#               powerMediation::SSizeLogisticBin(p_unexposed, p_exposed, exposure_prev)
```

### Python Implementation
```python
import math
from scipy.stats import norm

# Worked example = the Check inputs; replace with the study's values
n_predictors = 10
event_rate = 0.20
or_per_sd = 2.0
p_unexposed = 0.10
p_exposed = 0.20
exposure_prev = 0.5
r2_other = 0
alpha = 0.05
power = 0.80

z_a = norm.ppf(1 - alpha / 2)
z_b = norm.ppf(power)

n_peduzzi = math.ceil(10 * n_predictors / event_rate)
n_hsieh_con = math.ceil((z_a + z_b)**2 / (event_rate * (1 - event_rate) * math.log(or_per_sd)**2))

p_bar = (1 - exposure_prev) * p_unexposed + exposure_prev * p_exposed
n_hsieh_bin = math.ceil(
    (z_a * math.sqrt(p_bar * (1 - p_bar) / exposure_prev)
     + z_b * math.sqrt(p_unexposed * (1 - p_unexposed)
                       + p_exposed * (1 - p_exposed) * (1 - exposure_prev) / exposure_prev))**2
    / ((p_unexposed - p_exposed)**2 * (1 - exposure_prev)))

n_hsieh_con_adj = math.ceil(n_hsieh_con / (1 - r2_other))
n_hsieh_bin_adj = math.ceil(n_hsieh_bin / (1 - r2_other))
print(f"Peduzzi {n_peduzzi} | Hsieh continuous {n_hsieh_con_adj} | Hsieh binary {n_hsieh_bin_adj}")
```

### R Package
Base R. Cross-checks: `powerMediation::SSizeLogisticCon` / `SSizeLogisticBin`.

### Key References
- Peduzzi P, Concato J, Kemper E, Holford TR, Feinstein AR. A simulation study of the number of events per variable in logistic regression analysis. J Clin Epidemiol. 1996;49(12):1373-1379. doi:10.1016/S0895-4356(96)00236-3
- Hsieh FY, Bloch DA, Larsen MD. A simple method of sample size calculation for linear and logistic regression. Stat Med. 1998;17(14):1623-1634. doi:10.1002/(SICI)1097-0258(19980730)17:14<1623::AID-SIM871>3.0.CO;2-S
- Hsieh FY. Sample size tables for logistic regression. Stat Med. 1989;8(7):795-802. doi:10.1002/sim.4780080704

---

## Test 10: Non-Inferiority / Equivalence

### Parameters (ask the user; offer the default)
| Parameter | Description | Default |
|-----------|-------------|---------|
| `design` | "non-inferiority" or "equivalence" | "non-inferiority" |
| `outcome_type` | "proportion" or "continuous" | -- |
| `p_reference` | Reference group proportion (if proportion) | -- |
| `p_new` | Anticipated proportion with the new method (if proportion) | = `p_reference` |
| `higher_is_better` | Is a higher value the better outcome (sensitivity, cure) or worse (complications)? | -- |
| `true_diff` | Anticipated true difference, continuous, oriented so > 0 favours new | 0 |
| `margin` | Non-inferiority or equivalence margin M (> 0, outcome units) | -- |
| `sd` | Standard deviation (if continuous) | -- |
| `alpha` | One-sided alpha for NI; each of the two one-sided tests for equivalence | 0.025 (NI) / 0.05 (equiv) |
| `power` | Desired power | 0.80 |
| `attrition_rate` | Expected dropout rate | 0.15 |

### Margin selection
- The margin must be clinically justified and smaller than the effect of the reference treatment vs. placebo.
- Common approach: margin = 50% of the established treatment effect (preservation of effect).
- For proportions: absolute difference margin (e.g., delta = 0.10 means new method can be at most 10 percentage points worse).
- For continuous: margin in the same unit as the outcome.

### Hypotheses and orientation
Define the difference so that **Δ > 0 favours the new method**: Δ = new − reference when higher is
better, Δ = reference − new when lower is better. Never take |new − reference|: an NI test is
directional, and the absolute value turns a new method that is *better* by 0.05 into one that is
worse by 0.05 (683 per group instead of 76 in the Check below).
- **Non-inferiority (one-sided test)**: H0: Δ ≤ −M; H1: Δ > −M. Alpha is one-sided (typically 0.025).
- **Equivalence (TOST)**: H0: |Δ| ≥ M; H1: |Δ| < M. Two one-sided tests, each at alpha (0.05 → the 90% CI must lie inside ±M). Power is the probability that **both** tests reject.

**Effect size interpretation**: The margin defines the largest clinically acceptable difference. A smaller margin requires a larger sample. Always justify the margin based on clinical reasoning and prior literature.

### Non-Inferiority (Proportions)
```
n_per_group = (z_{1−α} + z_{1−β})² · (p_ref(1 − p_ref) + p_new(1 − p_new)) / (Δ + M)²      requires Δ + M > 0
```
**Check**: p_ref = p_new = 0.85, M 0.10, α 0.025 one-sided, 80% → 200.1 → **201 per group**
(`TrialSize::TwoSampleProportion.NIS(alpha = 0.025, beta = 0.2, p1 = 0.85, p2 = 0.85, k = 1, delta = 0, margin = -0.10)`
→ 200.15). New better by 0.05 (p_new 0.90) → 75.9 → **76 per group** (same call with `p1 = 0.90, delta = 0.05` → 75.87).

### Non-Inferiority (Continuous)
```
n_per_group = 2σ²(z_{1−α} + z_{1−β})² / (Δ + M)²      requires Δ + M > 0
```
**Check**: σ 1, M 0.5, Δ 0, α 0.025, 80% → 62.8 → **63 per group**
(`TrialSize::TwoSampleMean.NIS(alpha = 0.025, beta = 0.2, sigma = 1, k = 1, delta = 0, margin = -0.5)` → 62.79).

### Equivalence / TOST
```
power(n) ≈ Φ((M − Δ)/SE − z_{1−α}) + Φ((M + Δ)/SE − z_{1−α}) − 1
           SE = σ·√(2/n)   or   √((p_ref(1 − p_ref) + p_new(1 − p_new))/n)
Δ = 0:  n_per_group = 2σ²(z_{1−α} + z_{1−β/2})² / M²          (proportions: 2p(1 − p) in place of 2σ²)
requires |Δ| < M
```
At Δ = 0 both one-sided tests must succeed, so the power term is z_{1−β/2}, not z_{1−β}. Reusing the
NI formula gives about 60% power where 80% was intended. For Δ ≠ 0 solve power(n) numerically, as
the code below does.

**Check (continuous)**: σ 1, M 0.5, Δ 0, α 0.05, 80% → normal approximation 68.5 → 69
(`TrialSize::TwoSampleMean.Equivalence(alpha = 0.05, beta = 0.2, sigma = 1, k = 1, delta = 0.5, margin = 0)`
→ 68.51; in this function `delta` is the equivalence limit and `margin` the true difference); t-based
**70 per group** (`TOSTER::power_t_TOST(delta = 0, sd = 1, eqb = 0.5, alpha = 0.05, power = 0.8, type = "two.sample")`,
TOSTER 0.8.6 → 69.20); Δ 0.1 → 82 (→ 81.44); Δ 0.45 → 4947 (→ 4946.72).
**Check (proportions)**: p_ref = p_new = 0.85, M 0.10, α 0.05, 80% → 218.4 → **219 per group**
(`TrialSize::TwoSampleProportion.Equivalence(alpha = 0.05, beta = 0.2, p1 = 0.85, p2 = 0.85, k = 1, delta = 0, margin = 0.10)` → 218.38).

### R Implementation
```r
# Non-inferiority, proportions. Worked example = the Check inputs
p_reference <- 0.85
p_new <- 0.90
higher_is_better <- TRUE
margin <- 0.10
alpha <- 0.025
power <- 0.80

delta <- if (higher_is_better) p_new - p_reference else p_reference - p_new   # > 0 favours new
if (delta + margin <= 0) stop("the anticipated difference lies beyond the non-inferiority margin: no N reaches the target power")
n_ni_prop <- ceiling((qnorm(1 - alpha) + qnorm(power))^2 *
                       (p_reference * (1 - p_reference) + p_new * (1 - p_new)) / (delta + margin)^2)
cat(sprintf("NI (proportions): %d per group\n", n_ni_prop))
```

```r
# Non-inferiority, continuous. Worked example = the Check inputs
sd <- 1
margin <- 0.5
true_diff <- 0
alpha <- 0.025
power <- 0.80

if (true_diff + margin <= 0) stop("the anticipated difference lies beyond the non-inferiority margin: no N reaches the target power")
n_ni_cont <- ceiling(2 * sd^2 * (qnorm(1 - alpha) + qnorm(power))^2 / (true_diff + margin)^2)
cat(sprintf("NI (continuous): %d per group\n", n_ni_cont))
```

```r
# Equivalence (TOST), continuous: exact t-based power. Worked example = the Check inputs
library(TOSTER)
sd <- 1
margin <- 0.5
true_diff <- 0
alpha <- 0.05
power <- 0.80

if (abs(true_diff) >= margin) stop("the anticipated difference lies outside the equivalence margin: no N reaches the target power")
res <- power_t_TOST(n = NULL, delta = true_diff, sd = sd, eqb = margin,
                    alpha = alpha, power = power, type = "two.sample")
n_eq_cont <- ceiling(res$n)
cat(sprintf("Equivalence (continuous): %d per group\n", n_eq_cont))
```

```r
# Equivalence (TOST), proportions: normal-approximation joint power. Worked example = the Check inputs
p_reference <- 0.85
p_new <- 0.85
higher_is_better <- TRUE
margin <- 0.10
alpha <- 0.05
power <- 0.80

delta <- if (higher_is_better) p_new - p_reference else p_reference - p_new
if (abs(delta) >= margin) stop("the anticipated difference lies outside the equivalence margin: no N reaches the target power")
tost_power <- function(n) {
  se <- sqrt((p_reference * (1 - p_reference) + p_new * (1 - p_new)) / n)
  pnorm((margin - delta) / se - qnorm(1 - alpha)) +
    pnorm((margin + delta) / se - qnorm(1 - alpha)) - 1
}
n_eq_prop <- 2
repeat {
  p_now <- tost_power(n_eq_prop)
  if (!is.finite(p_now)) stop(sprintf("power is not finite at n = %d", n_eq_prop))
  if (p_now >= power) break
  n_eq_prop <- n_eq_prop + 1
}
cat(sprintf("Equivalence (proportions): %d per group\n", n_eq_prop))
```

### Python Implementation
```python
import math
from scipy.stats import norm

# Non-inferiority, proportions. Worked example = the Check inputs
p_reference = 0.85
p_new = 0.90
higher_is_better = True
margin = 0.10
alpha = 0.025
power = 0.80

delta = (p_new - p_reference) if higher_is_better else (p_reference - p_new)   # > 0 favours new
if delta + margin <= 0:
    raise ValueError("the anticipated difference lies beyond the non-inferiority margin: no N reaches the target power")
n_ni_prop = math.ceil((norm.ppf(1 - alpha) + norm.ppf(power))**2
                      * (p_reference * (1 - p_reference) + p_new * (1 - p_new)) / (delta + margin)**2)
print(f"NI (proportions): {n_ni_prop} per group")
```

```python
import math
from scipy.stats import norm

# Non-inferiority, continuous. Worked example = the Check inputs
sd = 1
margin = 0.5
true_diff = 0
alpha = 0.025
power = 0.80

if true_diff + margin <= 0:
    raise ValueError("the anticipated difference lies beyond the non-inferiority margin: no N reaches the target power")
n_ni_cont = math.ceil(2 * sd**2 * (norm.ppf(1 - alpha) + norm.ppf(power))**2 / (true_diff + margin)**2)
print(f"NI (continuous): {n_ni_cont} per group")
```

```python
import math
from scipy.stats import nct, t

# Equivalence (TOST), continuous: non-central t power (reproduces TOSTER). Worked example = the Check inputs
sd = 1
margin = 0.5
true_diff = 0
alpha = 0.05
power = 0.80

if abs(true_diff) >= margin:
    raise ValueError("the anticipated difference lies outside the equivalence margin: no N reaches the target power")

def tost_power(n):
    df = 2 * n - 2
    se = sd * math.sqrt(2 / n)
    t_crit = t.ppf(1 - alpha, df)
    # P(T_upper < -t) - P(T_lower <= t). The second term is written as the survival function of
    # the mirrored variable: nct.cdf(t, df, ncp) returns NaN deep in its tail at a large ncp
    # (SciPy 1.17: n = 3073 at true_diff 0.45), and NaN < power would end the search early.
    return (nct.cdf(-t_crit, df, (true_diff - margin) / se)
            - nct.sf(-t_crit, df, -(true_diff + margin) / se))

n_eq_cont = 2
while True:
    p_now = tost_power(n_eq_cont)
    if not math.isfinite(p_now):
        raise ValueError(f"power is not finite at n = {n_eq_cont}")
    if p_now >= power:
        break
    n_eq_cont += 1
print(f"Equivalence (continuous): {n_eq_cont} per group")
```

```python
import math
from scipy.stats import norm

# Equivalence (TOST), proportions: normal-approximation joint power. Worked example = the Check inputs
p_reference = 0.85
p_new = 0.85
higher_is_better = True
margin = 0.10
alpha = 0.05
power = 0.80

delta = (p_new - p_reference) if higher_is_better else (p_reference - p_new)
if abs(delta) >= margin:
    raise ValueError("the anticipated difference lies outside the equivalence margin: no N reaches the target power")

def tost_power(n):
    se = math.sqrt((p_reference * (1 - p_reference) + p_new * (1 - p_new)) / n)
    z = norm.ppf(1 - alpha)
    return norm.cdf((margin - delta) / se - z) + norm.cdf((margin + delta) / se - z) - 1

n_eq_prop = 2
while True:
    p_now = tost_power(n_eq_prop)
    if not math.isfinite(p_now):
        raise ValueError(f"power is not finite at n = {n_eq_prop}")
    if p_now >= power:
        break
    n_eq_prop += 1
print(f"Equivalence (proportions): {n_eq_prop} per group")
```

Totals are 2 × per group; inflate for attrition as `ceil(n_total / (1 − attrition_rate))`.

### R Package
Base R; `TOSTER` for the t-based equivalence N. Cross-checks: `TrialSize` (`TwoSampleProportion.NIS`,
`TwoSampleMean.NIS`, `TwoSampleProportion.Equivalence`, `TwoSampleMean.Equivalence`), `PowerTOST`.

### Key References
- Julious SA. Sample sizes for clinical trials with normal data. Stat Med. 2004;23(12):1921-1986. doi:10.1002/sim.1783
- Schuirmann DJ. A comparison of the two one-sided tests procedure and the power approach for assessing the equivalence of average bioavailability. J Pharmacokinet Biopharm. 1987;15(6):657-680. doi:10.1007/BF01068419
- Chow SC, Shao J, Wang H. Sample Size Calculations in Clinical Research. 2nd ed. Chapman & Hall/CRC; 2008. (the formulas `TrialSize` implements)

---

## Test 11: Cox Regression EPV (Events Per Variable)

### Parameters (ask the user; offer the default)
| Parameter | Description | Default |
|-----------|-------------|---------|
| `n_predictors` | Number of predictor variables in Cox model | -- |
| `event_rate` | Expected proportion of subjects experiencing the event | -- |
| `epv` | Events per variable target | 10 |
| `attrition_rate` | Expected dropout rate | 0.10 |

### EPV guidelines
- EPV >= 10: minimum for stable estimates (Peduzzi et al., 1995)
- EPV >= 20: recommended for reliable CI coverage and type I error control
- EPV < 5: model likely unstable — reduce predictors or use penalized methods

**Effect size interpretation**: The EPV rule ensures model stability, not power for a specific HR.

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

**Check (arithmetic)**: 8 predictors, EPV 10, event rate 0.25, 10% attrition → 80 events, **320**, 356 after attrition.

### R Implementation
```r
# Worked example = the Check inputs; replace with the study's values
n_predictors <- 8
event_rate <- 0.25
epv <- 10
attrition_rate <- 0.10

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

# Worked example = the Check inputs; replace with the study's values
n_predictors = 8
event_rate = 0.25
epv = 10
attrition_rate = 0.10

n_events = epv * n_predictors
n_total = math.ceil(n_events / event_rate)
n_adj = math.ceil(n_total / (1 - attrition_rate))
print(f"{n_events} events, N = {n_total}, with attrition {n_adj}")
```

### R Package
Base R (no additional packages needed).

### Key References
- Peduzzi P, Concato J, Feinstein AR, Holford TR. Importance of events per independent variable in proportional hazards regression analysis. II. Accuracy and precision of regression estimates. J Clin Epidemiol. 1995;48(12):1503-1510. doi:10.1016/0895-4356(95)00048-8
- Vittinghoff E, McCulloch CE. Relaxing the rule of ten events per variable in logistic and Cox regression. Am J Epidemiol. 2007;165(6):710-718. doi:10.1093/aje/kwk052

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

**Note**: Attrition rates vary widely by disease, population, and follow-up duration. Use study-specific estimates when available. For a survival design, loss to follow-up belongs inside the event probability (Test 7, Step 2), not as a second division of N.

---

## Key References

1. **Cohen J.** Statistical Power Analysis for the Behavioral Sciences. 2nd ed. Hillsdale, NJ: Lawrence Erlbaum Associates; 1988.
   - Foundation for effect size conventions (d, f, h, w) and power analysis methodology.

2. **Schoenfeld DA.** Sample-size formula for the proportional-hazards regression model. Biometrics. 1983;39(2):499-503. doi:10.2307/2531021
   - Required number of events, with the allocation term p(1 − p).

3. **Schoenfeld DA.** The asymptotic properties of nonparametric tests for comparing survival distributions. Biometrika. 1981;68(1):316-319. doi:10.1093/biomet/68.1.316
   - Asymptotic power of the log-rank test.

4. **Lachin JM, Foulkes MA.** Evaluation of sample size and power for analyses of survival with allowance for nonuniform patient entry, losses to follow-up, noncompliance, and stratification. Biometrics. 1986;42(3):507-519. doi:10.2307/2531201
   - Converting events to patients under accrual and loss to follow-up.

5. **Walter SD, Eliasziw M, Donner A.** Sample size and optimal designs for reliability studies. Stat Med. 1998;17(1):101-110. doi:10.1002/(SICI)1097-0258(19980115)17:1<101::AID-SIM727>3.0.CO;2-E
   - Sample size to test an ICC against a minimally acceptable value, for k ratings per subject.

6. **Bonett DG.** Sample size requirements for estimating intraclass correlations with desired precision. Stat Med. 2002;21(9):1331-1335. doi:10.1002/sim.1108
   - Sample size for a target ICC confidence-interval width.

7. **Hsieh FY, Bloch DA, Larsen MD.** A simple method of sample size calculation for linear and logistic regression. Stat Med. 1998;17(14):1623-1634. doi:10.1002/(SICI)1097-0258(19980730)17:14<1623::AID-SIM871>3.0.CO;2-S
   - Logistic regression: continuous and binary predictor formulas, variance inflation 1/(1 − R²).

8. **Hsieh FY.** Sample size tables for logistic regression. Stat Med. 1989;8(7):795-802. doi:10.1002/sim.4780080704
   - Earlier tables for detecting a specific odds ratio.

9. **Peduzzi P, Concato J, Kemper E, Holford TR, Feinstein AR.** A simulation study of the number of events per variable in logistic regression analysis. J Clin Epidemiol. 1996;49(12):1373-1379. doi:10.1016/S0895-4356(96)00236-3
   - EPV >= 10 rule for logistic regression model stability.

10. **Donner A, Eliasziw M.** A goodness-of-fit approach to inference procedures for the kappa statistic: confidence interval construction, significance-testing and sample size estimation. Stat Med. 1992;11(11):1511-1519. doi:10.1002/sim.4780111109
    - Sample size for testing kappa against a null value, given the trait prevalence.

11. **Cantor AB.** Sample-size calculations for Cohen's kappa. Psychol Methods. 1996;1(2):150-153. doi:10.1037/1082-989X.1.2.150
    - Kappa sample size with separate rater marginals.

12. **Buderer NMF.** Statistical methodology: I. Incorporating the prevalence of disease into the sample size calculation for sensitivity and specificity. Acad Emerg Med. 1996;3(9):895-900. doi:10.1111/j.1553-2712.1996.tb03538.x
    - Prevalence-adjusted sample size for diagnostic accuracy.

13. **Julious SA.** Sample sizes for clinical trials with normal data. Stat Med. 2004;23(12):1921-1986. doi:10.1002/sim.1783
    - Non-inferiority and equivalence sample size formulas.

14. **Schuirmann DJ.** A comparison of the two one-sided tests procedure and the power approach for assessing the equivalence of average bioavailability. J Pharmacokinet Biopharm. 1987;15(6):657-680. doi:10.1007/BF01068419
    - TOST (two one-sided tests) procedure for equivalence testing.

15. **Koo TK, Li MY.** A guideline of selecting and reporting intraclass correlation coefficients for reliability research. J Chiropr Med. 2016;15(2):155-163. doi:10.1016/j.jcm.2016.02.012
    - ICC interpretation benchmarks.

16. **Landis JR, Koch GG.** The measurement of observer agreement for categorical data. Biometrics. 1977;33(1):159-174. doi:10.2307/2529310
    - Kappa interpretation benchmarks.

17. **Connor RJ.** Sample size for testing differences in proportions for the paired-sample design. Biometrics. 1987;43(1):207-211. doi:10.2307/2531961
    - McNemar test sample size formula.

18. **Peduzzi P, Concato J, Feinstein AR, Holford TR.** Importance of events per independent variable in proportional hazards regression analysis. II. Accuracy and precision of regression estimates. J Clin Epidemiol. 1995;48(12):1503-1510. doi:10.1016/0895-4356(95)00048-8
    - EPV >= 10 rule for Cox regression model stability.

19. **Vittinghoff E, McCulloch CE.** Relaxing the rule of ten events per variable in logistic and Cox regression. Am J Epidemiol. 2007;165(6):710-718. doi:10.1093/aje/kwk052
    - Evidence that EPV 5-10 may be acceptable with careful validation.

20. **Chow SC, Shao J, Wang H.** Sample Size Calculations in Clinical Research. 2nd ed. Chapman & Hall/CRC; 2008.
    - Non-inferiority and equivalence formulas for proportions and means (implemented in `TrialSize`).
