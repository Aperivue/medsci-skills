# Metric guide (model-evaluation)

Load-on-demand reference for computing task-correct held-out metrics. Anchored to
**Metrics Reloaded** (Maier-Hein & Reinke et al., *Nat Methods* 2024) and its pitfalls
companion, and CLAIM 2024. The deliverable is a **per-case CSV** plus a results section;
the comparative inference is `/analyze-stats`.

## Segmentation
- **Overlap + boundary**: report Dice (or IoU) **with** a boundary metric — **HD95**
  (95th-percentile Hausdorff) or **NSD** (Normalised Surface Distance) — because Dice is
  insensitive to boundary error and unstable on small structures.
- **Per structure, not just global mean**: a global mean Dice hides per-organ/per-lesion
  failure; report per-structure with a distribution.
- **Empty references / false positives**: define behaviour for cases with no target
  (a Dice of 0/0 is undefined) — Metrics Reloaded discusses this explicitly.
- **CIs**: bootstrap over cases (resample patients, not pixels).

## Interactive / promptable segmentation
For promptable / interactive methods (SAM2, MedSAM2, nnInteractive), a single static Dice omits the
axis that makes the method interactive, and **Metrics Reloaded does not cover this regime**. Report,
in addition to the overlap + boundary metrics above:
- **Accuracy-vs-interaction trajectory**: Dice as a function of the number of corrective interactions
  (the click / interaction budget), not one operating point.
- **Interactions-to-threshold**: the number of clicks / interactions to reach a target Dice — the
  **NoC** (Number of Clicks) convention from the interactive-segmentation literature (e.g. RITM,
  SimpleClick); state the target threshold explicitly (e.g. NoC@0.80).
- **Initial vs converged / peak Dice**: the first-prompt Dice and the converged (or peak) Dice, so the
  interactive gain is visible rather than folded into one number.
- **Per-case interaction / inference time**: efficiency is a primary claim — a high-Dice method that
  needs many slow interactions may be clinically unusable.
- **Threshold-reached fraction**: the proportion of cases that reach the target Dice within the budget.
- **Subgroup robustness**: the trajectory and NoC sliced by tumor size / type / modality.

**Deterministic gate** — `check_metric_reporting.py --task interactive` still applies the
segmentation overlap + boundary checks and additionally flags an interactive claim whose report omits
the interaction axis (`INTERACTIVE_NO_INTERACTION_COUNT`, Major), the initial-vs-converged split
(`INTERACTIVE_NO_CONVERGENCE`, Minor), or per-case time (`INTERACTIVE_NO_TIME`, Minor). The **study
design** for an interactive evaluation — the human-as-operator reader arm and the two-arm
(simulated-prompting + human-operator validation) protocol-fidelity check — is covered in
`/design-study` and `/model-validation`.

## Classification
- **Discrimination with CIs**: **AUROC and AUPRC** (AUPRC tracks the minority class under
  imbalance), with bootstrap 95% CIs.
- **Operating-point metrics at the deployment prevalence**: sensitivity/specificity and
  **PPV/NPV computed at the real base rate**, not on an artificially balanced set; fix the
  threshold on the training/tuning folds, never the test set.
- **Calibration**: a reliability diagram + ECE; a discriminating model can still be
  miscalibrated.

## Detection
- **FROC / mAP with the IoU match criterion stated**: report sensitivity per false-positive
  (FROC) or mAP, and **state the IoU threshold** used to match predictions to ground truth —
  the metric is undefined without it. Patient-level accuracy is not a detection metric.

## Subgroup / fairness
- Slice every headline metric by the Model Card **Factors** (scanner/vendor, site, age, sex,
  severity); enough events per subgroup to estimate it (else say so). Defer fairness depth to
  `/model-validation` + the equity probe.

## Run variance
- Report the headline as **mean ± SD over ≥ 3 seeds/runs**, or a fixed reported seed with the
  determinism caveat — a single run overstates precision.

## Hand-off
Emit `eval/per_case_metrics.csv` (one row per case, columns = the metrics) and hand to
`/analyze-stats` for DeLong/NRI/IDI/decision-curve and the publication tables; `/make-figures`
for ROC/calibration/overlay; `/model-card` for the numbers + subgroup performance.
