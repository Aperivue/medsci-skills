# Prediction-model sample size (Riley) — development & external validation

For a **clinical prediction model** (or a medical-AI model evaluated as one), the
events-per-variable rule of thumb (EPV ≥ 10) is **outdated and reviewer-vulnerable**. EPV
does not target the things that determine whether a developed model is trustworthy
(overfitting, precise risk estimates) or whether a validation is conclusive (precise
discrimination and calibration). Use the **Riley criteria** instead — they are the current
TRIPOD+AI-aligned standard, and they are implemented in the R packages `pmsampsize`
(development) and `pmvalsampsize` (external validation).

Apply this whenever the goal is **risk prediction / classification for use**, not a single
predictor's hypothesis test. (For a single-predictor association test, the Hsieh/logistic
power calculation in Test 9 is appropriate.)

## Development sample size — `pmsampsize` (Riley et al.)

The minimum development sample size is the largest N satisfying four criteria
simultaneously:

1. **Small overfitting** — global shrinkage factor ≥ 0.9.
2. **Small optimism in apparent fit** — absolute difference between apparent and adjusted
   Nagelkerke R² ≤ 0.05.
3. **Precise estimate of overall risk** — margin of error of the mean predicted outcome
   (the intercept) ≤ 0.05.
4. **(time-to-event)** precise estimate of the baseline survival at a key time point.

Inputs you must specify (and justify from prior literature, not guess):
- number of **candidate predictor parameters** (count dummy variables and non-linear terms,
  not just variables);
- the anticipated model performance — a conservative **Cox-Snell R²** (derivable from an
  expected **C-statistic** + outcome prevalence) or expected R²;
- the **outcome prevalence** (binary) or **event rate + mean follow-up** (time-to-event),
  or outcome mean/SD (continuous).

```r
library(pmsampsize)
# Binary outcome: prevalence 0.20, 30 candidate parameters, expected C ≈ 0.78
# (convert C to a conservative Cox-Snell R²; pmsampsize accepts csrsquared or cstatistic)
pmsampsize(type = "b", cstatistic = 0.78, parameters = 30, prevalence = 0.20)

# Time-to-event: rate per person-year, mean follow-up, timepoint of interest
pmsampsize(type = "s", csrsquared = 0.05, parameters = 30,
           rate = 0.08, timepoint = 5, meanfup = 4.2)
```

Report the **minimum N and the required number of events**, the assumed C-statistic / R²
and its source, and the binding criterion. A development set below this is a standard
high-impact-journal rejection.

## External-validation sample size — `pmvalsampsize` (Riley et al.)

Size the validation set to estimate the key performance metrics **precisely enough to be
conclusive** — target the confidence-interval width of each:

- **discrimination** — C-statistic (target CI width, e.g. ±0.05);
- **calibration slope** (target SE / CI width);
- **calibration-in-the-large / O:E ratio**;
- **(if reporting clinical utility)** the standardized **net benefit** at the decision
  threshold.

```r
library(pmvalsampsize)
# Validate a model with expected prevalence 0.20, anticipated C ≈ 0.78,
# targeting a C-statistic CI half-width of 0.05 and a precise calibration slope
pmvalsampsize(type = "b", prevalence = 0.20, cstatistic = 0.78,
              cslope = 1, oe = 1, lpnormal = c(-0.5, 0.5),
              cstatci = 0.10)   # target CI *width* for the C-statistic
```

A common **floor** is ≥ 100 events and ≥ 100 non-events (Vergouwe; Collins), but
`pmvalsampsize` gives the precise target for your metrics and usually requires more.

## Sample size for net benefit / decision-curve

If the model's value claim rests on **net benefit** (decision-curve analysis), size the
study to estimate net benefit at the relevant threshold with adequate precision —
`pmvalsampsize` supports a net-benefit target, and the development criteria should be met
so the model is not overfit before its utility is judged. Do not claim clinical utility
from a decision curve estimated on an underpowered validation set.

## Reporting

- State that sizing followed the **Riley criteria** (cite the originals) — not EPV-10.
- Report the assumed C-statistic / R² / prevalence and **where they came from**.
- For development, report N + events + the binding criterion; for validation, report the
  targeted CI widths and the resulting N (events and non-events).

## References (cite the originals)

- Riley RD, Snell KIE, Ensor J, et al. Minimum sample size for developing a multivariable
  prediction model: PART II — binary and time-to-event outcomes. *Stat Med* 2019.
- Riley RD, Ensor J, Snell KIE, et al. Calculating the sample size required for developing
  a clinical prediction model. *BMJ* 2020.
- Riley RD, Debray TPA, Collins GS, et al. Minimum sample size for external validation of a
  clinical prediction model with a binary outcome. *Stat Med* 2021.
- Collins GS, Ogundimu EO, Altman DG. Sample size considerations for the external
  validation of a multivariable prognostic model. *Stat Med* 2016.
