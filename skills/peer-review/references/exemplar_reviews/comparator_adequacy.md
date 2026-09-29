# Exemplar — comparator too weak to establish added value

**Finding class:** the manuscript claims a model, marker, or test adds value *beyond* an
existing tool — or simply reports it "outperforming" something — but the comparator is
absent, trivial, or mismatched: a majority-class or single-feature baseline, an outdated
standard of care, an arm run on a different input set / task / time horizon, or a
"baseline" that is not the thing the new tool is meant to replace. The reported gain is
then not a gain over the alternative a reader would actually use.
**Typical severity:** **Major** when the incremental claim is the paper's reason to exist
(the Abstract's contribution is "beyond X", and the comparator is missing or the wrong one);
**Minor** when a meaningful baseline is already in place and only one axis of the
comparison — the paired difference, the reclassification split, or net benefit — is absent.

## What the reviewer noticed

The Abstract states the marker "adds value beyond the established clinical risk score."
Table 2 compares the new model against (a) a logistic model built from two routinely
available variables and (b) a prior published nomogram evaluated on an earlier cohort. No
model containing the predictors a clinician already uses is present, and the improvement is
reported as two separate AUCs with no difference and its interval. The comparator nomogram
was published for a long-horizon endpoint while this cohort's median follow-up is shorter,
so its side of the comparison is measured on a different question.

## Weak phrasing (avoid)

> The baseline is unfair, so the model does not show added value over current practice.

(Verdict with no anchor, no specific ask, and a gatekeeping tone.)

## Strong phrasing (model this)

> The comparison in Table 2 does not yet establish *added value*, which is what the
> Abstract claims. The two arms a reader would want are not present: the "baseline" model
> is built from two variables, and the second comparator is a prior nomogram applied to an
> earlier cohort. Because a new marker has to beat the model a clinician would already run
> — not a deliberately thin one — I'd suggest adding a **base model containing the
> predictors in routine use**, fitted on the same patients as the full model, so the
> nested comparison is paired.
>
> Reported as two separate AUCs, the gain also has no interval. I'd suggest reporting
> the paired difference in discrimination (ΔAUC or ΔC-index) with its confidence interval
> as the size of the gain, and testing whether the marker adds anything through its
> coefficient in the full model (a likelihood-ratio test) rather than through a test of
> ΔAUC, which is unreliable when nested models are fitted and evaluated on the same
> patients. That would let readers judge whether the improvement is distinguishable from
> noise — and would honestly show the result if the interval is wide.
>
> On the comparator's side, the published nomogram was developed for a [time-horizon]
> endpoint and applied here in a cohort with shorter follow-up, so part of its
> underperformance may be horizon mismatch rather than inferiority. Stating the horizon at
> which each model was evaluated — and whether the comparator was applied as published,
> recalibrated locally, or refit — would close that gap.
>
> Finally, since the claim is about what the marker *adds for decisions*, the comparison
> would be most useful with the remaining two axes: reclassification, if reported, with
> its event and non-event components given separately, and decision-curve net benefit
> against treat-all / treat-none. Both depend on calibrated probabilities, so this pairs
> with `calibration_missing.md` rather than replacing it.

## Severity calibration

If the Abstract's contribution is "adds value beyond X" and the comparator is missing,
thin, or answering a different question, this is **Major** — the paper's central claim is
untestable as reported, and the remedy (a nested base model) is a design-level requirement
that cannot be added by prose. If the right comparator is already there and only the
paired difference, the reclassification split, or net benefit is missing, it is a
**Minor** statistical-completeness addition.

## What this is not

`ai_overclaiming.md` handles a claim outrunning the evidence, where wording is the defect;
here the numbers may be accurate and the claim honest, and what is missing is an arm the
comparison needs. `optimistic_validation_reporting.md` covers a biased estimate, not a weak arm.

## Related checks

Signature checks "Clinical comparator / incremental value" and "Added-value / actionability",
and the Phase 2 adaptation-baseline audit; PG4 (incremental value over the guideline
clinical model) in `polygenic_risk_score.md`; the incremental-value probe in
`clinical_prediction_model.md`; S5 comparator horizon alignment in `survival_prognostic.md`;
HE1 comparator choice in `health_economic_evaluation.md`; P1 comparator existence in
`sr_ma.md`; `analyze-stats` `table-standards/table-types/incremental_value.md`; TRIPOD+AI /
PGS-RS items via `/check-reporting`.
