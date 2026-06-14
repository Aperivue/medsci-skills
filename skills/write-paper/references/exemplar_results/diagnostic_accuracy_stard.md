# Results structure — diagnostic-accuracy study (STARD)

A structure model for the Results of an index-test-vs-reference-standard accuracy study. It
follows its Methods STARD sibling in Methods order. Each heading is a paragraph;
each bullet is *what it must establish*. Fill the `[brackets]`; do not copy this text. Report
findings only — no interpretation (that is the Discussion).

## Participant flow (Figure 1)
- The STARD flow as Figure 1: enrolled → received index test → received reference standard →
  analyzed, with exclusions and **counts and reasons** at each step.
- State how many had the reference standard by each route (e.g., `[N]` by pathology, `[N]` by
  `[interval]` follow-up) and how indeterminate/non-diagnostic results were counted (ITD vs
  per-protocol — match what Methods declared).
- Numbers must reconcile with the Abstract, Methods, Table 1, and the 2×2.

## Cohort characteristics and prevalence (Table 1)
- Baseline demographics/clinical features of the analyzed participants (one decimal
  convention, held throughout).
- The **prevalence** of the target condition by the reference standard — every PPV/NPV is
  read against it, so state it before the predictive values.

## Primary accuracy
- Sensitivity and specificity with **95% CIs**, at the **pre-specified positivity threshold**
  (name the operating point; state it was fixed in advance or derived only on a
  training/derivation set, not optimized on the analysis/test set).
- PPV/NPV with the prevalence they assume; accuracy if reported.
- State the **analysis unit** and keep it fixed (per-patient / per-lesion / per-segment); when
  units are nested, report each level and give the lesion-selection rule, so every metric's
  denominator is unambiguous.

## Agreement / measurement (if a quantitative index)
- For a continuous index read against the reference, report agreement (Bland–Altman mean
  difference + limits, or ICC), not only thresholded accuracy.

## Subgroups and comparator
- Pre-specified subgroups (e.g., by `[size / calcification / PSA stratum]`) showing where
  accuracy degrades; report the subgroup 2×2 or its metrics, not just a p-value.
- If two tests are compared, the **difference** with a paired test (McNemar / difference in
  AUC), not two standalone estimates.

## Common omission
- The **explicit flow diagram with per-step counts** and the **handling of indeterminate
  results**, plus **differential-verification bias** when the reference standard was applied
  more often after a positive index test — the elements most often missing, and each inflates
  the headline accuracy. Cross-reference `section_guides/results.md` and the STARD critical
  items in `peer-review/references/reviewer_calibration/compliance_floor.md`.
