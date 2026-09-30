# Prediction-Model Calibration Guide

For a clinical prediction model (a logistic risk score or a Cox/survival model at a fixed
horizon), **discrimination (AUC / C-index) is not enough** — a model that ranks well can still
output probabilities that are systematically too high or too low. The ways calibration fails
review are (1) reporting **apparent (in-sample)** calibration — a slope of exactly 1.00 is the
fingerprint — with no internal-validation correction, (2) leaning on the **Hosmer–Lemeshow**
test (deprecated), and (3) omitting calibration entirely for a model meant to guide care. This
guide produces the corrected estimand; it is the produce-side of probe **S7**.

---

## When to Use

- Any model that outputs a **risk / probability** used for a decision (surveillance intensity,
  treatment eligibility, triage) — logistic or survival-at-a-horizon.
- Reported **alongside** discrimination and, for a utility claim, decision-curve net benefit —
  never discrimination alone.
- NOT a substitute for external validation: internal (bootstrap/CV) calibration corrects
  optimism but does not establish transportability.

---

## Apparent calibration is optimistic — correct it (this is the S7 issue)

Fit a logistic model by maximum likelihood and its **apparent** calibration slope on the same
data is **exactly 1.00** and its calibration-in-the-large intercept **exactly 0** — by
construction, not because the model is well-calibrated. A slope printed as `1.00` (or metrics
with no `bootstrap` / `cross-valid` / `optimism` / `held-out` token nearby) is presumptively
in-sample. Produce the **bootstrap optimism-corrected** slope instead (Harrell/Steyerberg).

```python
import numpy as np, statsmodels.api as sm
X = ...            # design matrix (add_constant), y = 0/1 outcome
def cal_slope(y, lp):
    """Calibration slope: coefficient of lp in logit(y) ~ a + b*lp."""
    m = sm.GLM(y, sm.add_constant(lp), family=sm.families.Binomial()).fit()
    return m.params[1]

def citl(y, lp):
    """Calibration-in-the-large: the intercept with the slope FIXED at 1 (lp as an offset).
    The intercept of the joint model above is NOT calibration-in-the-large whenever the
    slope differs from 1."""
    m = sm.GLM(y, np.ones_like(lp), family=sm.families.Binomial(), offset=lp).fit()
    return m.params[0]

full = sm.GLM(y, X, family=sm.families.Binomial()).fit()
app_slope = cal_slope(y, X @ full.params)              # apparent: exactly 1.00
app_citl = citl(y, X @ full.params)                    # apparent: exactly 0

rng = np.random.default_rng(42); n = len(y); opt = []
for _ in range(500):                                    # bootstrap optimism (Harrell)
    idx = rng.integers(0, n, n)
    bm = sm.GLM(y[idx], X[idx], family=sm.families.Binomial()).fit()
    s_boot = cal_slope(y[idx], X[idx] @ bm.params)      # boot model on boot data (apparent)
    s_orig = cal_slope(y,      X      @ bm.params)      # boot model on original data (test)
    opt.append(s_boot - s_orig)
corrected_slope = app_slope - float(np.mean(opt))       # < 1.00 when the model overfits
print(f"apparent slope {app_slope:.3f} -> optimism-corrected {corrected_slope:.3f}")
```

A corrected slope **< 1** means predictions are too extreme (overfit) and should be shrunk
(a penalized/uniform-shrinkage refit); a slope **> 1** means they are too moderate.

On **held-out or external** data, compute both on that data's linear predictor
(`lp = X_ext @ full.params`): `citl(y_ext, lp)` and `cal_slope(y_ext, lp)`. Synthetic external
set (observed risk 26.2% vs mean predicted 16.8%, slope 0.62): the joint-model intercept was
0.04, which reads as "calibrated in the large", while CITL was 0.65 (R `glm(y ~ offset(lp),
binomial)`: 0.651). Note that `rms::val.prob` reports the joint intercept as "Intercept"; it is
not calibration-in-the-large either (Van Calster et al. 2019, doi:10.1186/s12916-019-1466-7).

---

## The four levels of calibration (report weak calibration at least)

Van Calster's hierarchy — report at minimum **weak calibration** (intercept + slope):

- **Mean** (calibration-in-the-large): mean predicted = observed event rate — the intercept
  estimated with the slope fixed at 1 (`citl()` above), not the joint-model intercept.
- **Weak**: calibration intercept ≈ 0 **and** slope ≈ 1.
- **Moderate**: a **flexible calibration curve** (loess / spline of observed on predicted),
  not decile bins — the plot most reviewers now expect.
- **Strong**: correct per-covariate (rarely achievable; not required).

```python
import matplotlib.pyplot as plt
from sklearn.calibration import calibration_curve
phat = full.predict(X)
frac_pos, mean_pred = calibration_curve(y, phat, n_bins=10, strategy="quantile")
plt.plot([0, 1], [0, 1], "--"); plt.plot(mean_pred, frac_pos, "o", alpha=0.6)   # grouped points
from statsmodels.nonparametric.smoothers_lowess import lowess
curve = lowess(y, phat, frac=2 / 3, it=0)                # flexible curve (moderate calibration)
plt.plot(curve[:, 0], curve[:, 1], "-")
plt.xlabel("Predicted probability"); plt.ylabel("Observed frequency")
```

---

## Brier score; do NOT rely on Hosmer–Lemeshow

- **Brier score** = mean squared error of the probabilities; report the **scaled Brier**
  (1 − Brier / Brier_null) so it is interpretable against the event rate.
- **Hosmer–Lemeshow is deprecated** (Van Calster 2016; Austin & Steyerberg): its p-value depends
  on an arbitrary number of bins, it is underpowered in small samples and rejects trivially in
  large ones, and it gives no direction or magnitude. Report the **calibration slope + intercept
  + a flexible calibration plot** instead of an H–L p-value.

```python
from sklearn.metrics import brier_score_loss
brier = brier_score_loss(y, phat); scaled = 1 - brier / (y.mean() * (1 - y.mean()))
```

## Survival models

For a Cox/survival model, calibrate the **predicted vs observed risk at a fixed horizon**
(e.g. 3-year): group by predicted-risk decile and compare to a Kaplan–Meier / pseudo-value
estimate at that time, or use `rms::calibrate` / `pec` in R with bootstrap optimism correction.
State the horizon; a model can be well-calibrated at 1 year and not at 5.

---

## Reporting

- **Calibration-in-the-large (slope fixed at 1) and slope** with the **internal-validation
  method named**
  (bootstrap/CV), not the apparent slope of 1.00; the flexible calibration plot.
- Scaled Brier; the horizon (survival); the cohort each metric was computed on (development vs
  held-out vs external) stated explicitly.
- Discrimination **and** calibration together; add decision-curve net benefit for a utility claim
  (see `table-standards/table-types/incremental_value.md` and the `make-figures` decision-curve
  exemplar).

---

## Common failures (flag at review)

- **Apparent calibration slope of exactly 1.00** (and intercept 0) with no bootstrap/CV/external
  token — in-sample fit presented as calibration (S7).
- **Hosmer–Lemeshow p-value** offered as the calibration evidence (deprecated).
- **Discrimination reported without calibration** for a model meant to guide care (S7 → MAJOR).
- **Decile-bin calibration only**, no flexible curve; or a survival calibration with no stated
  horizon.

---

## Anti-Hallucination

- Never hand-type a calibration slope/intercept, Brier, or CI — compute it from predictions with
  a seeded script.
- Do not report a calibration slope of 1.00 as evidence of good calibration — it is the
  apparent-fit artifact; report the optimism-corrected value the bootstrap produced.
- Name the validation source of every calibration number (development / bootstrap-corrected /
  external); do not present development-sample calibration as validated performance.
