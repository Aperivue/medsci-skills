# Exemplar — a "negative" prediction study that conflates two different nulls

**Fired:** `clinical_prediction_model.md` probe **CP2** (incremental-value-vs-marginal-effect two-null
distinction), with **CP1** (apparent vs optimism-corrected calibration/DCA) alongside. Surfaced by
reading the negative conclusion against the powered analyses, not an automated gate. **Severity:**
Fatal → Anticipated **Major**. **Category:** C. Validation & Statistical Reporting (D. Clinical
Framing for the conclusion wording). Calibration re-correction is `requires_reanalysis: true`.

## Anticipated Major Comment (how a reviewer will put it)

> The Conclusion states the marker "did not predict" the outcome, but two distinct results are
> merged. The incremental-value analysis is well powered — the change in AUC is ≈ 0 and bootstrap
> optimism correction does not favour (and may reverse toward the parsimonious model away from) the
> larger model — so "adding the marker did not improve prediction" is supported. The marginal
> adjusted odds ratio, however, has a confidence interval that still admits an effect up to about
> 1.7; that arm is underpowered, so "the marker is not associated with the outcome" is *not*
> supported. Please report these separately. Relatedly, discrimination was optimism-corrected but the
> calibration slope (0.99) and the decision curves are in-sample and described as "well calibrated"
> and "clinically useful" without the apparent caveat — an in-sample slope near 1.0 is expected and
> does not establish out-of-sample calibration.

## Severity / category rationale

**Fatal** because the blanket "X did not predict Y" overreads the underpowered marginal arm and a
reader could wrongly abandon the marker. The CP1 calibration/DCA labelling and the optimism
extension are reporting-grade but mandatory. Splitting the two nulls is wording + correct framing;
re-correcting calibration/DCA needs a re-run, so that part is `fixable_by_ai: false`.

## Fix

Rewrite the conclusion to two sentences: (1) the well-powered incremental-value null ("adding the
marker did not improve discrimination, calibration, or net benefit"), and (2) the underpowered
marginal result ("the marginal association could not be excluded; the CI admits OR up to ~1.7").
Label in-sample calibration and decision-curve results "apparent," or extend optimism correction to
them via `/analyze-stats`. Report EPV per nested model (CP3).

## R0-ready line

> R0-C1 (Major, Fatal): negative prediction conclusion conflates a well-powered ΔAUC≈0 (incremental
> value) with an underpowered marginal OR (CI admits ~1.7); split the two nulls and label in-sample
> calibration/DCA "apparent." [probe: CP1/CP2]
