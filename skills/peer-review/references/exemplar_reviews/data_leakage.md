# Exemplar — data leakage (split contamination / label-bearing inputs)

**Finding class:** information from the test set or the outcome reaches the model at
training time — via a patient appearing in both train and test, or via an input feature
that encodes the label.
**Typical severity:** design-level → **Major #1**, because leakage inflates every reported
metric and is often invisible in the results themselves.

## What the reviewer noticed

Methods report a 70/30 split "by image," but many patients contributed multiple images
(Table 1, mean 2.4 studies/patient), so the same patient can fall on both sides of the
split. Separately, one input feature is the radiology report impression text, while the
outcome is the report-derived diagnosis — the input may contain the label.

## Weak phrasing (avoid)

> There is leakage so the model is invalid.

(Asserts the conclusion; gives the authors nothing to act on.)

## Strong phrasing (model this)

> Two points about independence between training and evaluation that, if addressed, would
> considerably strengthen confidence in the metrics:
>
> First, the 70/30 split is described as by image (Methods, *Data split*), but patients
> contributed multiple studies (Table 1). A patient-level split prevents the model from
> seeing the same patient in training and test; an image-level split can inflate
> performance. I'd suggest re-splitting by patient and reporting whether the metrics change
> — if they are stable, that is a strong robustness result to include.
>
> Second, one input is the report impression text while the outcome is derived from the
> report (Methods, *Inputs* / *Outcome*). If the impression states the diagnosis, the model
> may be reading the label rather than predicting it. Could the authors either mask the
> diagnosis-bearing portion of the text, or report a sensitivity analysis with that feature
> removed, to show the result does not depend on it?

## Why this is Major #1

Leakage does not announce itself in the results — the metrics look excellent precisely
because of it. Anchoring to the multi-study patients (Table 1) and the report-derived
outcome makes the concern concrete and gives two specific, runnable remedies.

## Related checks

Signature check "Patient-level data splitting"; self-review categories A (independence/
leakage) and H (circularity / label-feature overlap).
