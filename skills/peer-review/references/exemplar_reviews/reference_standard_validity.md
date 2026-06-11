# Exemplar — reference-standard validity in a diagnostic-accuracy study

**Finding class:** the reference standard ("ground truth") is imprecisely defined, applied
non-independently of the index test, mistimed, or read without blinding — so the reported
sensitivity/specificity may be biased.
**Typical severity:** design-level → **Major** (often Major #1 for a DTA paper), because it
threatens the headline accuracy estimates.

## What the reviewer noticed

Methods describe the reference standard as "clinical consensus," but it is not stated who
adjudicated, whether they were blinded to the index test, or the time interval between
index test and reference. STARD items on the reference standard and blinding are not
addressed.

## Weak phrasing (avoid)

> The ground truth is unreliable, so the results cannot be trusted.

(Global dismissal, no anchor, no remedy.)

## Strong phrasing (model this)

> The reference standard is described as "clinical consensus" (Methods, *Reference
> standard*), but a few details would let readers judge the accuracy estimates. Could the
> authors specify: (1) who adjudicated and their expertise; (2) whether adjudicators were
> blinded to the index-test result — this matters because unblinded adjudication can pull
> the reference toward the index test and inflate agreement; (3) the interval between the
> index test and the reference, since a long gap allows disease progression/regression
> (verification timing); and (4) for cases where consensus was used, the inter-rater
> agreement before consensus. If blinding was not feasible, a sentence on the expected
> direction of bias and a sensitivity analysis on the subset with histologic confirmation
> would reassure readers.

## Severity calibration

If adjudication was unblinded and the reference partly incorporates the index test, this is
incorporation bias and belongs as **Major #1** — the sensitivity/specificity are the
paper's product. If only the *reporting* is thin (the design is sound but undescribed),
it is a **Minor** request for Methods detail.

## Related checks

Signature check "Reference standard precisely defined"; QUADAS-2 domains (reference
standard, flow & timing) via `/check-reporting`; self-review category B.
