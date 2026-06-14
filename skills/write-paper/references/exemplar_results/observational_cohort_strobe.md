# Results structure — observational cohort (STROBE)

A structure model for the Results of an exposure→outcome cohort study. It follows its
Methods STROBE sibling in Methods order. Each heading is a paragraph; each bullet is *what it must establish*.
Fill the `[brackets]`; do not copy this text. Report findings only — no interpretation.

## Cohort assembly (Figure 1)
- The assembly cascade as Figure 1: source → eligible → analytic, with exclusion **counts and
  reasons**, and the exposed/unexposed counts.
- The cascade reconciles (start − Σ exclusions = analytic N); follow-up time / person-years
  stated. Numbers match the Abstract, Methods, and Table 1.

## Baseline characteristics, by exposure (Table 1)
- Table 1 stratified **by exposure status**, with a balance metric (standardized mean
  differences) and the imbalance threshold used; if matched/weighted, show pre- and
  post-balance.
- Show every pre-specified adjustment covariate in this table, so the reader can see whether
  any covariate imbalanced by exposure is missing from the adjustment set.

## Primary association — crude then adjusted
- The primary contrast and effect measure (OR / RR / HR) with **95% CIs**, reported **crude
  then adjusted** (or matched), so the effect of confounding control is visible.
- Report the **pre-specified primary** estimand; do not reassign the primary after seeing
  results. State events/N for each arm.

## Secondary, subgroup, and dose-response
- Subgroup / interaction estimates with CIs (report the interaction term, not two separate
  stratum estimates, when effect-modification is the question).
- Dose-response across exposure levels if available; keep multiplicity in view.

## Sensitivity analyses
- The robustness checks declared in Methods (alternative adjustment, complete-case vs
  imputation, tipping-point / E-value for unmeasured confounding), reported as results, not
  deferred.

## Missing data
- How much was missing and how the analytic set was reached (complete-case reconciles:
  total − missing = complete), with the footnote N matching the flow.

## Common omission
- **Crude-and-adjusted side by side** and an explicit **sensitivity analysis for unmeasured
  confounding** (E-value / tipping-point) — the elements cohort Results most often skip.
  Cross-reference `section_guides/results.md` and the STROBE critical items in
  `peer-review/references/reviewer_calibration/compliance_floor.md`.
