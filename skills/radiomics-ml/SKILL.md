---
name: radiomics-ml
description: >
  Produce or audit a radiomics / tabular clinical-ML study — imaging or clinical features → any
  classical learner (penalised logistic [LASSO / ridge / elastic-net], SVM, k-NN, naive Bayes,
  LDA/QDA, decision tree, random forest, gradient boosting [XGBoost / LightGBM / CatBoost], shallow
  MLP, stacked ensembles) → a clinical outcome — so it clears the rigor bar reviewers expect: nested
  cross-validation (tuning never on the reported folds), dimensionality control for the
  features-far-exceed-events regime, feature selection inside the fold, feature-stability (ICC /
  test-retest) filtering, calibration, and external/temporal validation. The deterministic gate is
  learner-agnostic (it audits the pipeline, not the algorithm). Emits a pipeline manifest and the gate.
  The most common solo-doable clinical-ML workflow — no GPU, no engineer. Integrates scikit-learn /
  xgboost / lightgbm / catboost / pyradiomics; it does not reimplement them.
triggers: radiomics, radiomic features, pyradiomics, tabular ML, clinical prediction model, random forest, XGBoost, LightGBM, CatBoost, gradient boosting, tree ensemble, SVM, support vector machine, k-NN, KNN, naive Bayes, LDA, QDA, elastic net, ridge, LASSO, logistic regression, MLP, stacking, ensemble, clustering, k-means, PCA, UMAP, dimensionality reduction, feature selection, nested cross-validation, nested CV, ICC feature stability, SHAP, machine learning model, classical ML, clinical machine learning, feature stability, decision curve, calibration, TRIPOD, CLEAR, PROBAST
tools: Read, Write, Edit, Bash, Grep, Glob
model: inherit
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
- Deep-learning imaging models → `/architecture-zoo` → `/model-scaffold` → `/model-validation`.
- Classical inferential statistics / a regression model as the estimand → `/analyze-stats`.
- Interpretability of a trained network → `/explainability`.
- Reimplementing scikit-learn / xgboost / pyradiomics → out of scope (this skill wires and audits them).

## The failure modes (what the gate enforces)
1. **No nested CV.** Tuning and reporting on the same folds inflates performance. Use nested CV or a
   held-out test set.
2. **High dimensionality, low events.** Features ≥ events with no dimensionality reduction overfits —
   the classic radiomics trap. Apply LASSO / PCA / a stability + redundancy filter.
3. **Selection outside the fold.** Feature selection fit on the whole dataset leaks the held-out folds.
   Nest selection inside each training fold.
4. **No feature stability.** Radiomics features are unstable across acquisition/segmentation — filter
   to reproducible features (ICC / test-retest).
5. **No calibration.** A clinical prediction model needs calibration (slope/intercept + a flexible
   curve), not discrimination alone.
6. **No external validation.** A single-cohort model needs external / temporal validation for a
   clinical claim.

## Workflow

### Phase 1 — Extract features (integrate, don't reimplement)
For radiomics, extract with **pyradiomics** under reproducible, IBSI-aligned settings (fixed bin width,
resampling, normalisation) — record them. For clinical/tabular data, assemble the feature table with a
patient/subject ID and the outcome. See `references/radiomics_ml_guide.md`.

### Phase 2 — Build the pipeline correctly
- **Feature stability** — with test-retest / multi-rater data, keep features with ICC ≥ 0.75.
- **Nested cross-validation** — outer folds estimate performance, inner folds tune; do **feature
  selection and scaling inside each training fold** (never on the whole dataset).
- **Dimensionality** — with features ≥ events, use LASSO / a stability+redundancy filter / PCA.
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
  "n_features": 1200, "n_samples": 300, "n_events": 110,
  "cv_scheme": "nested",
  "feature_selection_stage": "inside_cv",
  "dimensionality_reduction": true,
  "feature_stability": "icc",
  "calibration_reported": true,
  "external_validation": "temporal",
  "model": "xgboost"
}
```

### Phase 4 — Gate the pipeline (deterministic)
```bash
python3 scripts/check_radiomics_ml.py --manifest pipeline_manifest.json --strict
```
Verdicts: `NO_NESTED_CV`, `HIGH_DIM_LOW_EVENTS`, `SELECTION_OUTSIDE_CV` (Major);
`NO_FEATURE_STABILITY`, `NO_CALIBRATION`, `NO_EXTERNAL_VALIDATION` (Minor). Complements
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
