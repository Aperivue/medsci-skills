# Radiomics / classical-ML — how to build a pipeline that passes review

Companion to `radiomics-ml`. *Produce* knowledge for a clinician building a radiomics or tabular
clinical-ML model without an engineer. It wires pyradiomics / scikit-learn / xgboost by name; it does
not reimplement them.

## 1. Feature extraction (radiomics) — reproducibly

Use **pyradiomics** with settings recorded for reproducibility (CLEAR / IBSI):

- **Resample** to a fixed voxel spacing; state interpolator.
- **Intensity discretisation** — a fixed **bin width** (preferred for CT/PET) or fixed bin count;
  state which and the value.
- **Normalisation** for MR (z-score) — fit per image or on train only (never on test).
- **Segmentation source** — who/what drew the ROI; single vs multi-rater (feeds stability, §2).
- Extract the standard classes (first-order, shape, GLCM/GLRLM/GLSZM/GLDM/NGTDM) ± wavelet/LoG; record
  the pyradiomics version and parameter file.

For **tabular clinical** data, the same pipeline applies from §2 onward — the "features" are labs,
demographics, and measurements instead of radiomic descriptors.

## 2. Feature stability (radiomics-specific)

Radiomic features drift with acquisition and segmentation. With test-retest or multi-rater ROIs,
compute **ICC** per feature and keep the stable ones (commonly ICC ≥ 0.75) *before* modelling. Report
how many features survived. No stability step → `NO_FEATURE_STABILITY`.

## 3. The events-per-feature problem (the classic trap)

Radiomics yields hundreds-to-thousands of features on tens of patients. Fitting a flexible model in
that regime overfits. Control it:

- **Reduce the candidates without the outcome first** — a stability filter (§2), a redundancy
  filter (drop one of each |r| > 0.9 pair), a clinical prior, or PCA (fit inside the fold). Only
  what survives is a candidate for outcome-driven selection.
- **Then size the study for those candidates** with `/calc-sample-size` Test 12 (Riley criteria,
  R `pmsampsize`), counting every candidate parameter that reaches outcome-driven selection or
  fitting, not only the features the final model keeps. It is demanding: at C = 0.75 and 35%
  prevalence, 100 candidate parameters need N = 4,755 (1,665 events). If the study falls short,
  say so as a limitation.
- **Penalisation does not fix a small sample.** LASSO / elastic-net select inside the fold, but at
  small n the amount of shrinkage they estimate is itself unstable, so the model can still be badly
  miscalibrated in new data (Riley et al., *J Clin Epidemiol* 2021; Van Calster et al., *Stat
  Methods Med Res* 2020).
- Features ≥ events → `HIGH_DIM_LOW_EVENTS`, whether or not dimensionality reduction or
  regularisation is declared (declaring it does not clear the verdict; events are counted as the
  minority class). That rule is a floor for the worst case, not a sample-size criterion: a pipeline
  with 100 features on 105 events passes it. Leaving out `n_features`, `n_samples` or `n_events`
  does not pass it: the gate reports `HIGH_DIM_NOT_ASSESSED` (Minor) unless the declared counts
  already prove features ≥ the bound.

## 4. Nested cross-validation (the non-negotiable)

If you tune hyperparameters and report performance from the **same** CV, the performance is
optimistic. Two acceptable designs:

- **Nested CV** — outer folds estimate performance; an inner CV inside each outer training fold tunes
  hyperparameters **and** does feature selection + scaling. Nothing from the outer test fold touches
  fitting.
- **Held-out test set** — tune with CV on the training split, evaluate once on an untouched test split.

**Everything data-driven goes inside the fold**: imputation, scaling, feature selection, class-imbalance
resampling. Selection on the whole dataset → `SELECTION_OUTSIDE_CV` (and, in prose,
`self-review/check_cv_leakage`). Flat CV or no validation → `NO_NESTED_CV`.

**The CV unit is the patient, not the row.** Radiomics tables are often lesion- or ROI-level (several
nodules, metastases or slices per patient). Split both loops by patient (`StratifiedGroupKFold` with
`groups=patient_id`) so the rows of one patient never straddle a training and a test fold (Saeb et al.,
*GigaScience* 2017). Row-wise folds let the model recognise the patient instead of the outcome: on
synthetic data with 4 lesions per patient and an outcome unrelated to the features (true AUROC 0.5),
row-wise nested CV with a random forest reported AUROC 0.99 and patient-grouped nested CV 0.48 (mean
of 8 datasets). The gate
reads the manifest only and cannot see the grouping, so keep the fold table below and prove it with
`/model-assessment`'s split-leakage gate (`check_split_leakage.py --splits cv_folds.csv --seed 42
--strict`: `PATIENT_OVERLAP` means a patient spans folds).

```python
# Nested-CV skeleton: the CV unit is the PATIENT (integrate, don't reimplement).
# X: features, one row per lesion/ROI; y: outcome per row; patient_id: one ID per row. NumPy arrays:
# X = df[feature_cols].to_numpy(); y = df["outcome"].to_numpy(); patient_id = df["patient_id"].to_numpy()
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.feature_selection import SelectKBest
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GridSearchCV, StratifiedGroupKFold
from sklearn.metrics import roc_auc_score

pipe = Pipeline([("scale", StandardScaler()),
                 ("select", SelectKBest(k=20)),        # selection INSIDE the fold
                 ("clf", LogisticRegression(max_iter=5000))])  # ridge-penalised baseline
# LASSO: l1_ratio=1 with solver="saga" (scikit-learn >= 1.8) or penalty="l1" (older). Swap in
# RandomForestClassifier / XGBClassifier(eval_metric="logloss") as needed: the fold structure is
# what makes the estimate honest, whichever learner sits in the pipeline
param_grid = {"clf__C": [0.01, 0.1, 1.0]}
outer = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42)
inner = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42)

oof = np.full(len(y), np.nan)                          # out-of-fold predicted risk per row
fold = np.empty(len(y), dtype=int)
auc = []
for k, (tr, te) in enumerate(outer.split(X, y, groups=patient_id)):
    grid = GridSearchCV(pipe, param_grid, cv=inner, scoring="roc_auc")
    grid.fit(X[tr], y[tr], groups=patient_id[tr])      # inner folds split by patient too
    oof[te] = grid.predict_proba(X[te])[:, 1]
    fold[te] = k
    auc.append(roc_auc_score(y[te], oof[te]))          # outer folds = the performance estimate

# one fold per patient, auditable: /model-assessment check_split_leakage.py --splits cv_folds.csv
pd.DataFrame({"patient_id": patient_id, "split": [f"fold{k}" for k in fold]}).to_csv(
    "cv_folds.csv", index=False)
```

## 5. Models — the full classical family (not just RF / XGBoost)

Always report a **simple baseline** (penalised logistic) alongside any complex learner — a model that
does not beat penalised logistic on your data is a finding, not a failure. Fix the seed. Pick by task
and sample size; the pipeline rigor in §2–§4 is identical across all of them (the gate is
learner-agnostic).

| Family | Learner (scikit-learn / library) | When |
|---|---|---|
| Penalised regression | `LogisticRegression(penalty=l1/l2/elasticnet)` — LASSO / ridge / elastic-net | baseline; small n; interpretable coefficients |
| Margin / kernel | `SVC` (linear / RBF) | moderate n, clear margin; scale features first |
| Instance-based | `KNeighborsClassifier` | small feature set, local structure |
| Probabilistic / discriminant | `GaussianNB`, `LinearDiscriminantAnalysis`, `QuadraticDiscriminantAnalysis` | fast baselines; LDA when classes ~Gaussian |
| Single tree | `DecisionTreeClassifier` | interpretability demo (rarely final) |
| Bagging | `RandomForestClassifier`, `ExtraTreesClassifier` | robust default, low tuning |
| Boosting | `XGBClassifier`, `LGBMClassifier`, `CatBoostClassifier`, `HistGradientBoostingClassifier`, `AdaBoost` | usually top tabular performance; tune with the inner CV |
| Shallow neural | `MLPClassifier` | non-linear, enough samples; scale + early-stop |
| Meta / ensemble | `StackingClassifier`, `VotingClassifier` | squeeze marginal gain; guard overfitting |
| Survival ML | random survival forest, Cox-net, DeepSurv | time-to-event outcome (+ `/analyze-stats` survival) |

**Unsupervised (upstream, not the endpoint):** PCA / UMAP for dimensionality reduction (fit inside the
fold, §4), and k-means / hierarchical / Gaussian-mixture for phenotype discovery — report cluster
stability, never as a supervised performance claim.

For imbalanced outcomes prefer probability-calibrated models + threshold analysis over resampling that
distorts prevalence (`/analyze-stats` calibration). If you recalibrate, the recalibration is fitted
from data too, so it goes **inside the training fold** — e.g. `CalibratedClassifierCV` as the
pipeline's last step, never fitted on the pooled predictions and then evaluated on them. At
radiomics sample sizes use Platt (`method="sigmoid"`): isotonic regression overfits small
calibration sets (scikit-learn advises against it well below ~1,000 samples). In a simulation with
150 training patients, in-fold isotonic recalibration of a random forest gave a test calibration
slope of 0.63 (predictions too extreme) and a worse Brier score than Platt.

## 6. Report discrimination AND calibration AND utility

- **Discrimination** — AUROC (+ AUPRC, reported with the prevalence, at low prevalence). With a
  held-out test set, bootstrap the test **patients**. With nested CV, the pooled out-of-fold
  predictions are not independent test data: a naive bootstrap over them ignores how much the
  fitted models vary between training sets and undercovers (in a simulation with n = 120 and
  5-fold CV, its nominal 95% CI covered the procedure's true AUROC in 85% of datasets). Repeat the
  nested CV to stabilise the point estimate (the spread over repeats is partition noise, not a CI);
  for the interval use the nested-CV method of Bates, Hastie & Tibshirani (*JASA* 2024) or a
  bootstrap that refits the whole procedure, tuning included, in every resample. Describe the
  result as the performance of the modelling procedure, not of one final model.
- **Calibration** — slope + intercept and a flexible calibration curve (not decile bins); use the
  `/analyze-stats` calibration guide. Discrimination-only → `NO_CALIBRATION`.
- **Clinical utility** — decision-curve net benefit / NNT at a stated threshold (`/analyze-stats`).
- **Interpretation** — SHAP for feature contributions (global + a few local), framed as association.

## 7. Validation and reporting

- **External / temporal validation** for a clinical claim; single-cohort development → report as
  development-only (`NO_EXTERNAL_VALIDATION`).
- **Reporting** — CLEAR (radiomics), TRIPOD+AI (prediction model), PROBAST-AI (risk of bias) via
  `/check-reporting`.

## 8. Common reviewer objections this pre-empts

1. "Was performance from nested CV or the same folds you tuned on?" → §4.
2. "Features ≥ patients — how did you avoid overfitting?" → §3.
3. "Were features selected inside the CV?" → §4.
4. "Several lesions per patient — were the folds split by patient?" → §4.
5. "Are the features reproducible (ICC)?" → §2.
6. "Calibration, not just AUC?" → §6.
7. "External validation?" → §7.
