---
name: radiomics-ml
description: Use when building or auditing a radiomics or tabular clinical-ML prediction model with a classical learner (LASSO, SVM, random forest, XGBoost and similar). Enforces nested CV, dimensionality control, in-fold feature selection, feature stability, calibration and external validation.
metadata:
  triggers: "radiomics, radiomic features, pyradiomics, tabular ML, clinical prediction model, random forest, XGBoost, LightGBM, CatBoost, gradient boosting, tree ensemble, SVM, support vector machine, k-NN, KNN, naive Bayes, LDA, QDA, elastic net, ridge, LASSO, logistic regression, MLP, stacking, ensemble, clustering, k-means, PCA, UMAP, dimensionality reduction, feature selection, nested cross-validation, nested CV, ICC feature stability, SHAP, machine learning model, classical ML, clinical machine learning, feature stability, decision curve, calibration, TRIPOD, CLEAR, PROBAST"
---

# Radiomics / Classical-ML Skill

## Purpose

Radiomics + tree-ensemble studies (features → random forest / XGBoost → a clinical outcome) are the
**most common solo-doable clinical-ML workflow** — no GPU, no engineer — and the **most commonly
over-optimistic**: hundreds-to-thousands of features on tens of patients, hyperparameters tuned on the
same folds the performance is reported from, features selected on the whole dataset, unstable features
never filtered, and discrimination (AUC) reported without calibration. This skill produces the pipeline
correctly and audits an existing one, so the clinical result survives review (Lambin 2017; CLEAR;
TRIPOD+AI; PROBAST-AI).

It sits beside the imaging-DL lane: where `/model-scaffold` builds a deep network, **radiomics-ml**
covers the feature-based classical-ML path. It **integrates** scikit-learn / xgboost / pyradiomics
(referenced in the emitted code); it does not reimplement them and never runs a model on real patient
data.

## When to use
- You have a radiomics or clinical/tabular feature table and want to build a random-forest / XGBoost
  clinical prediction model that will pass statistical review.
- You want to audit an existing radiomics/ML pipeline for the failure modes below.

## When NOT to use
- Deep-learning imaging models → `/model-selection` → `/model-scaffold` → `/model-assessment`.
- Classical inferential statistics / a regression model as the estimand → `/analyze-stats`.
- Interpretability of a trained network → `/model-assessment`.
- Reimplementing scikit-learn / xgboost / pyradiomics → out of scope (this skill wires and audits them).

## The failure modes (what the gate enforces)
1. **No nested CV.** Tuning and reporting on the same folds inflates performance. Use nested CV or a
   held-out test set.
2. **High dimensionality, low events.** Candidate features ≥ events overfits — the classic radiomics
   trap. Declaring `dimensionality_reduction` does not clear it: `n_features` already counts what is
   left after outcome-blind reduction. The gate's `p ≥ events` rule (events = the minority class) is a floor that catches the worst case,
   **not a sample-size criterion**: size the study with `/calc-sample-size` Test 12 (Riley criteria,
   `pmsampsize`), counting every **candidate** feature that reaches outcome-driven selection or
   fitting. At C = 0.75 and 35% prevalence that is about 48 patients per candidate parameter: 100
   candidates need N = 4,755 (1,665 events), and the gate passes 100 features on 105 events. Reduce
   candidates **without the outcome** first (stability, redundancy, clinical prior); LASSO or other
   penalisation does not substitute for sample size, because the shrinkage it estimates is itself
   unstable at small n (Riley et al., *J Clin Epidemiol* 2021; Van Calster et al., *Stat Methods Med
   Res* 2020).
3. **Selection outside the fold.** Feature selection fit on the whole dataset leaks the held-out folds.
   Nest selection inside each training fold.
4. **No feature stability.** Radiomics features are unstable across acquisition/segmentation — filter
   to reproducible features (ICC / test-retest).
5. **No calibration.** A clinical prediction model needs calibration (slope/intercept + a flexible
   curve), not discrimination alone.
6. **No external validation.** A single-cohort model needs external / temporal validation for a
   clinical claim.

Not in the gate, because the manifest cannot show it: **rows of one patient on both sides of a
split.** Lesion-level tables with row-wise folds let the model recognise the patient; on null
synthetic data this took nested-CV AUROC from 0.48 to 0.99. Split by patient and check the fold
table (Phase 2).

## Workflow

### Phase 1 — Extract features (integrate, don't reimplement)
For radiomics, extract with **pyradiomics** under reproducible, IBSI-aligned settings (fixed bin width,
resampling, normalisation) — record them. For clinical/tabular data, assemble the feature table with a
patient/subject ID and the outcome. One row per lesion or ROI is fine; the ID is what the folds are
split by. See `references/radiomics_ml_guide.md`.

### Phase 2 — Build the pipeline correctly
- **Feature stability** — with test-retest / multi-rater data, keep features with ICC ≥ 0.75.
- **Nested cross-validation** — outer folds estimate performance, inner folds tune; do **feature
  selection and scaling inside each training fold** (never on the whole dataset). **The CV unit is
  the patient**: split both loops with `StratifiedGroupKFold(groups=patient_id)` so one patient's
  lesions never straddle folds, write the fold table (`patient_id,split`), and prove it with
  `/model-assessment`'s `check_split_leakage.py --splits cv_folds.csv --seed <seed> --strict`
  (skeleton in the guide §4).
- **Dimensionality** — reduce the candidate set without the outcome (ICC stability, |r| redundancy
  filter, clinical prior; PCA fit inside the fold), then size the study for the candidates that
  remain with `/calc-sample-size` Test 12 (`pmsampsize`). LASSO selects inside the fold but does not
  make a small sample large enough; report the shortfall as a limitation if N falls below the Riley
  minimum.
- **Model** — pick from the full classical family for the task; a simple baseline (penalised logistic)
  is mandatory alongside any complex learner:
  - *penalised regression* — LASSO / ridge / elastic-net logistic (also the baseline)
  - *margin / kernel* — linear or RBF SVM
  - *instance-based* — k-NN
  - *probabilistic / discriminant* — naive Bayes, LDA / QDA
  - *trees & bagging* — decision tree, random forest, extra-trees
  - *boosting* — XGBoost, LightGBM, CatBoost, HistGBM, AdaBoost
  - *shallow neural* — MLP
  - *meta* — stacking / voting ensembles
  - *unsupervised (upstream)* — PCA / UMAP for reduction, k-means / hierarchical / GMM for phenotyping
  The gate below is **learner-agnostic** — it audits the pipeline (nested CV, leakage, dimensionality,
  calibration), so it applies identically to any of these. See the full method map in
  [`docs/method_coverage_map.md`](../../docs/method_coverage_map.md).
- **Report** — discrimination **and** calibration (slope/intercept + flexible curve, via the
  `/analyze-stats` calibration guide) and clinical utility (decision curve). SHAP for interpretation.

### Phase 3 — Emit the pipeline manifest
```json
{
  "task": "classification",
  "n_features": 40, "n_samples": 300, "n_events": 110,
  "cv_scheme": "nested",
  "feature_selection_stage": "inside_cv",
  "dimensionality_reduction": true,
  "feature_stability": "icc",
  "calibration_reported": true,
  "external_validation": "temporal",
  "model": "xgboost"
}
```
- `n_features` — the **candidate** features that reach outcome-driven selection or fitting, after
  outcome-blind reduction (here 1,200 extracted → ICC ≥ 0.75 → |r| < 0.9 → 40). This example passes
  the gate, yet `pmsampsize` (C = 0.75, prevalence 110/300) asks for N = 1,868 with 685 events for
  40 candidate parameters: the gate does not size the study, Test 12 does. `n_features`,
  `n_samples` and `n_events` must be non-negative integers (`n_events` ≤ `n_samples`); anything else
  is an input error (exit 2). `dimensionality_reduction` is informational and clears nothing.
- `feature_selection_stage` — `inside_cv`, `outside_cv`, or `none` (no outcome-driven selection).
  Missing or unrecognised is treated as not shown to be in-fold (`SELECTION_OUTSIDE_CV`).
- `feature_stability` — `icc` / `test_retest`; `external_validation` — `external` / `temporal` /
  `geographic`. Any other value (e.g. `planned`, `internal`, `bootstrap`, `random_split`) is flagged.
  Values are case-insensitive; `-` and spaces read as `_`.
- `cv_scheme` — `nested`, or `held_out_test` / `single_split` when hyperparameters and model choice
  were tuned on the training split only and the test split was touched once. A split that was also
  used for tuning, model selection or a threshold is `flat` (choosing among 12 candidate models on
  the test split of null data reported AUROC 0.63 instead of 0.51). At radiomics sample sizes a
  single random split wastes data and is unstable; prefer (repeated) nested CV (Steyerberg,
  *J Clin Epidemiol* 2018).

### Phase 4 — Gate the pipeline (deterministic)
```bash
python3 scripts/check_radiomics_ml.py --manifest pipeline_manifest.json --strict
```
Verdicts: `NO_NESTED_CV`, `HIGH_DIM_LOW_EVENTS`, `SELECTION_OUTSIDE_CV` (Major);
`NO_FEATURE_STABILITY`, `NO_CALIBRATION`, `NO_EXTERNAL_VALIDATION`, and `HIGH_DIM_NOT_ASSESSED`
when `n_features`, `n_samples` or `n_events` is missing (Minor). Complements
`self-review`'s `check_cv_leakage` (which audits a finished manuscript's prose) at the pipeline-spec
level.

## Integration
- **`/analyze-stats`** — calibration + clinical-utility (decision curve, NNT) guides for the reporting.
- **`/check-reporting`** — CLEAR (radiomics), TRIPOD+AI, PROBAST-AI item coverage.
- **`/self-review`** `clinical_prediction_model` probe audits the finished manuscript; this skill
  *produces* the rigorous pipeline it looks for.

## Anti-Hallucination

- **Never fabricate features, performance metrics, or sample/event counts.** Every value in the
  manifest and every reported metric comes from the researcher's executed code — never invented. This
  skill designs and audits the pipeline; it does not run a model on real patient data.
- **Never report flat-CV performance as if it were nested or held-out.** Tuning on the reported folds
  is the optimism this skill exists to prevent (`NO_NESTED_CV`).
- **Never report a radiomics/ML audit "pass" without running `check_radiomics_ml.py`.** The rigor
  verdict is reproduced deterministically, never asserted from prose.
- **Integrate, don't reimplement.** Reference scikit-learn / xgboost / pyradiomics; do not write a new
  feature extractor or learner or claim results for one.

## Reproducible challenge
`scripts/check_radiomics_ml_challenge/` ships a synthetic weak/strong pipeline pair with a network-free
`verify.sh` wired into the skill's validation commands.
