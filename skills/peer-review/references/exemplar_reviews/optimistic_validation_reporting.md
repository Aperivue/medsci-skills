# Exemplar — optimistic / non-reproducible performance reporting

**Finding class:** the headline metric is reported in a way that biases it upward or makes
it impossible to reproduce — a single best cross-validation fold quoted as *the* result
(no mean ± SD or CI across folds), the decision threshold behind the reported
sensitivity/specificity left unstated, and accuracy emphasized over AUC / false-negative
rate while the classes were silently re-balanced away from the real prevalence.
**Typical severity:** **Major** when the load-bearing performance claim rests on it (the
number a reader would cite is optimistic or unreproducible); **Minor** when the cross-fold
summary and operating point are simply missing from an otherwise sound validation.

## What the reviewer noticed

The model is evaluated with k-fold cross-validation, but Table 2 reports the metrics from
the single best fold rather than the mean across folds, with no SD or confidence interval.
Sensitivity and specificity are given to two decimals, yet the classification threshold
that produced them is never stated. The training set was balanced to 1:1, while the
condition's real prevalence is far lower, and this is not noted where the headline
accuracy appears.

## Weak phrasing (avoid)

> The results are over-optimistic and not reproducible. Report proper validation.

(A verdict with no anchor, no specific ask, and a gatekeeping tone.)

## Strong phrasing (model this)

> The cross-validation design is appropriate, but Table 2 appears to report the
> single best-performing fold. Because best-fold figures are optimistically biased, it
> would strengthen the paper to report the mean across folds with its SD (or a 95% CI),
> so readers see the expected performance and its variability rather than the most
> favorable run.
>
> Relatedly, the sensitivity and specificity in Table 2 depend on a classification
> threshold that I could not find stated. Reporting the operating point used (and how it
> was chosen — e.g., Youden's J on the training folds only, to avoid tuning on the test
> data) would make these numbers reproducible.
>
> Finally, the training set was balanced to 1:1 while the clinical prevalence is much
> lower. If accuracy is also computed on a re-balanced set, it is not representative of
> performance at the true prevalence — at the real (low) base rate the same model can
> carry many more false positives (lower PPV) than the headline suggests. It would help to
> state the evaluation set's class distribution and to report threshold-independent
> discrimination with its uncertainty (AUROC, and AUPRC under imbalance, both with CIs)
> alongside class-aware operating-point metrics — sensitivity / false-negative rate and
> PPV / NPV at the stated threshold — so the clinical cost of a miss at the deployment
> prevalence is visible.

## Severity calibration

If the abstract's headline rests on the best-fold number, the missing operating point, or
an accuracy inflated by undisclosed rebalancing, this is **Major** — the claim a reader
takes away is not the claim the data support, and it is not reproducible as reported. If
cross-validation was done soundly and only the cross-fold summary, the threshold, or a
class-aware metric is absent from the write-up, it is a **Minor** reporting addition.

## Related checks

Signature check "Confidence intervals" (all primary metrics need 95% CIs) and the
Phase 2 "Validation strategy / confidence intervals / calibration" issue-checklist item;
AO4 in the AI/ML overclaiming probe (unstated decision
threshold proposed for use needs calibration + decision-curve evidence);
`calibration_missing.md` when discrimination is reported without calibration; TRIPOD+AI /
CLAIM / STARD-AI performance-reporting items via `/check-reporting`; self-review category
Calibration [CRITICAL] for the AUC-alone variant.
