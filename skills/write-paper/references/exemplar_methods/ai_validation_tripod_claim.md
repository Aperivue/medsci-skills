# Methods structure — AI/ML model development + validation (TRIPOD+AI / CLAIM)

A structure model for a clinical AI/ML model study. Each heading is a paragraph; each bullet
is *what it must establish*. Fill the `[brackets]`; do not copy this text.

## Study design and data sources
- Design (retrospective/prospective), the prediction task, and the intended use (where in
  the workflow the output acts, and which decision it informs).
- Data sources, sites, and dates for each split; how the cohort was assembled.

## Participants, inputs, and outcome
- Eligibility as a numbered list; the population the model is meant to serve.
- Input data types and exactly which fields the model sees (flag any field that could carry
  the label — report a no-leaky-field sensitivity analysis or mask it).
- Outcome/label definition, who assigned it, and the reference standard for the label.

## Data partition and leakage control
- Train / validation / test split **by patient** (not by image/record), and how
  independence was enforced; any external (geographic/temporal) test set.
- Explicit statement that no test data informed development (preprocessing, feature/threshold
  selection, model choice) — leakage inflates every metric and is invisible in the results.

## Model development
- Architecture, key hyperparameters, training procedure, and how the operating threshold was
  chosen (and on which split).
- Whether training was from scratch or fine-tuned; for an adaptation claim, a same-backbone
  zero-shot/few-shot baseline.
- Reproducibility: hardware/software/versions, random-seed handling, code/model availability.

## Evaluation
- Primary metric(s) with 95% CIs; **calibration** (slope/intercept or a calibration plot),
  not discrimination alone, when probabilities drive a decision.
- Comparator: if vs clinicians, the **same task on the same inputs under the same
  constraints**, with a test of the difference (not two standalone AUCs); decision-curve /
  net-benefit if a deployment/utility claim is made.

## Sample size
- Events-per-variable / minimum test-set events for the target precision, or the
  available-sample justification.

## Reporting-guideline fit
- TRIPOD+AI (name base TRIPOD + the AI extension) and/or CLAIM 2024. Critical items: input
  data + outcome, partition/leakage control, model + training details, calibration.

## Common omission
- **Calibration** and a **patient-level** (not image-level) split — the two most commonly
  missing, and both can make excellent-looking metrics misleading.
