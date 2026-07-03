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

- **Dimensionality reduction / regularisation** — LASSO (embedded selection), a stability + redundancy
  filter (drop |r| > 0.9 pairs), or PCA.
- Keep an eye on **events per candidate feature** (the limiting count is the minority class). Report
  the ratio honestly. Features ≥ events with no reduction → `HIGH_DIM_LOW_EVENTS`.

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

```python
# sklearn nested-CV skeleton (integrate, don't reimplement)
from sklearn.pipeline import Pipeline
from sklearn.feature_selection import SelectKBest
from sklearn.model_selection import GridSearchCV, StratifiedKFold, cross_val_score
pipe = Pipeline([("scale", StandardScaler()),
                 ("select", SelectKBest(k=20)),        # selection INSIDE the fold
                 ("clf", XGBClassifier(eval_metric="logloss"))])
inner = StratifiedKFold(5, shuffle=True, random_state=42)
outer = StratifiedKFold(5, shuffle=True, random_state=42)
grid  = GridSearchCV(pipe, param_grid, cv=inner, scoring="roc_auc")
auc   = cross_val_score(grid, X, y, cv=outer, scoring="roc_auc")  # outer = unbiased estimate
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
distorts prevalence; calibrate with Platt / isotonic (`/analyze-stats` calibration).

## 6. Report discrimination AND calibration AND utility

- **Discrimination** — AUROC (+ AUPRC at low prevalence) with bootstrap CIs.
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
4. "Are the features reproducible (ICC)?" → §2.
5. "Calibration, not just AUC?" → §6.
6. "External validation?" → §7.
