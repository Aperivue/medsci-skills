# Results structure — AI/ML model development + validation (TRIPOD+AI / CLAIM)

A structure model for the Results of a clinical AI/ML model study. It follows its Methods
AI-validation sibling in Methods order. Each heading is a paragraph; each bullet is *what it must establish*.
Fill the `[brackets]`; do not copy this text. Report findings only — no interpretation.

## Cohort assembly and data partition (Figure 1)
- The flow as Figure 1: source → eligible → analyzed, with the **train / validation / test**
  split shown and the counts for each set (and each **external** set).
- Splits are **by patient**; state the counts so a reader can see no patient spans two sets.
- Numbers reconcile with the Abstract, Methods, and Table 1.

## Baseline characteristics, by set (Table 1)
- Population characteristics for development and each test set, so distribution shift between
  development and external data is visible (one decimal convention).
- The outcome/label prevalence in each set (it conditions PPV/NPV and calibration).

## Reference points before the headline
- Report the relevant baselines first — a simpler model (clinical-only / single-modality) and,
  where applicable, the unaided clinician — so the model's **increment** is legible rather
  than asserted.

## Primary discrimination
- The primary metric (AUROC, and AUPRC under class imbalance) with **95% CIs**, reported
  **separately for internal and each external set** (not a single pooled number).
- Where a gain over a baseline is claimed, the **difference** with a test (DeLong / paired),
  not two standalone estimates.

## Calibration and operating point
- **Calibration** (slope/intercept or a calibration plot; Brier/Hosmer–Lemeshow) on the test
  set — discrimination alone is insufficient when a probability drives a decision.
- The decision threshold used for any sensitivity/specificity, and that it was fixed on the
  development/training data, not the test set.

## Clinical utility (when a use claim is made)
- Decision-curve / net-benefit across plausible thresholds, or a reader study reporting the
  change in reader performance (e.g., false-positive reduction, agreement) with the model.

## Interpretability and error analysis
- If interpretability is claimed, **quantify** it (attribution overlap, importance ranking),
  and report failure modes as counts/rates by pre-specified error category, subgroup, or
  input condition (e.g., lesion size, image quality) — report-only; reserve causal
  explanation of the errors for the Discussion.

## Common omission
- **Calibration** and **per-set** (not pooled) external metrics with CIs — the elements most
  often missing, and both can make excellent discrimination misleading. Cross-reference
  `section_guides/results.md`, the
  `peer-review/references/exemplar_reviews/optimistic_validation_reporting.md` phrasing
  model, and the TRIPOD+AI / CLAIM critical items in
  `peer-review/references/reviewer_calibration/compliance_floor.md`.
