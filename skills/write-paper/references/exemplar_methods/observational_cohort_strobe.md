# Methods structure — observational cohort (STROBE)

A structure model for an exposure→outcome cohort study. Each heading is a paragraph; each
bullet is *what it must establish*. Fill the `[brackets]`; do not copy this text.

## Study design and setting
- Design (prospective / retrospective cohort) and why; data source (`[registry / EMR /
  health-screening DB]`), sites, and the enrollment and follow-up dates (keep enrollment
  distinct from follow-up end — do not conflate them).
- Ethics approval / consent or waiver; registration if applicable.

## Participants and eligibility
- Eligibility as a numbered list (inclusion / exclusion).
- The assembly cascade with counts (source → eligible → analytic), so the STROBE flow
  reconciles (start − Σ exclusions = analytic N).

## Variables — exposure, outcome, covariates
- Exposure definition, how it was measured/classified, and the cut-points with their source
  (cite the canonical definition; quote the data-dictionary mapping for a DB variable).
- Outcome definition, ascertainment, and timing.
- Covariates/confounders and how each was measured; pre-specify the adjustment set and its
  rationale (a DAG), not a data-driven selection.

## Bias, missing data, and study size
- Sources of bias and how they were addressed (selection, measurement, confounding).
- How missing data were handled (complete-case vs imputation — state which; complete-case
  must reconcile: total − missing = complete).
- Study size: the precision / event-budget justification (events per variable for the model).

## Statistical analysis
- The primary model and estimand (the contrast and effect measure), with 95% CIs; the
  pre-registered primary if applicable (do not reassign the primary after seeing results).
- Subgroup/interaction and sensitivity analyses, multiplicity handling, and how continuous
  variables were modeled (linearity assumption).
- Software + version.

## Reporting-guideline fit
- STROBE. Critical items: eligibility/selection, exposure/outcome definitions, missing-data
  handling, participant flow (see `peer-review/references/reviewer_calibration/compliance_floor.md`).

## Common omission
- A pre-specified **adjustment set with rationale** and explicit **missing-data handling** —
  the two paragraphs cohort drafts most often skip, and both are first-line reviewer targets.
