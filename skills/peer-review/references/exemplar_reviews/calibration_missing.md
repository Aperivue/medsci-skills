# Exemplar — calibration not reported for a clinical prediction model

**Finding class:** the model is presented for clinical decision-making, but only
discrimination (AUC/c-statistic) is reported — no calibration, and often no decision-curve
or clinical-utility analysis.
**Typical severity:** **Major** when the paper proposes clinical use (a probability that
drives a decision must be calibrated); **Minor** when the model is framed as a research
prototype only.

## What the reviewer noticed

Results report AUC with CIs for every model (Table 2, Figure 1), and the Discussion
proposes using predicted probabilities to triage patients, but there is no calibration plot
or metric (calibration slope/intercept, ECE) and no decision-curve analysis.

## Weak phrasing (avoid)

> AUC is not enough; the authors need calibration.

(True but terse; no reason, no anchor, no path.)

## Strong phrasing (model this)

> The discrimination results are clearly presented (Table 2, Figure 1). Because the
> Discussion proposes using the predicted probabilities to triage patients, it would help
> to add an assessment of calibration — how close predicted probabilities are to observed
> frequencies. AUC can be high while probabilities are systematically too confident, which
> would mislead a probability-based threshold. A calibration plot with slope and intercept
> (and ideally on the external set) would let readers judge whether the proposed thresholds
> are safe. A decision-curve analysis would further show the net benefit across plausible
> threshold probabilities relative to treat-all / treat-none. If recalibration was applied,
> stating the method would also be useful.

## Severity calibration

If the paper's contribution is a deployable triage tool, calibration is **Major** — the
clinical claim rests on the probabilities being trustworthy. If the model is explicitly a
methods demonstration with no decision claim, a calibration metric is a reasonable
**Minor** addition.

## Related checks

Signature check "Calibration (AUC alone insufficient)"; TRIPOD+AI / CLAIM calibration items
via `/check-reporting`; self-review category C (calibration [CRITICAL]).
