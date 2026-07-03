<!-- AUTO-GENERATED from skills/radiomics-ml/SKILL.md by scripts/gen_skill_docs.py. Do not edit by hand. -->

# radiomics-ml

> Produce or audit a radiomics / tabular clinical-ML study — imaging or clinical features → random forest / XGBoost / regularised logistic → a clinical outcome — so it clears the rigor bar reviewers expect: nested cross-validation (tuning never on the reported folds), dimensionality control for the features-far-exceed-events regime, feature selection inside the fold, feature-stability (ICC / test-retest) filtering, calibration, and external/temporal validation. Emits a pipeline manifest and a deterministic rigor gate. The most common solo-doable clinical-ML workflow — no GPU, no engineer. Integrates scikit-learn / xgboost / pyradiomics; it does not reimplement them.

**Invoke:** `/radiomics-ml` · **Tools:** Read, Write, Edit, Bash, Grep, Glob · **Model:** inherit

## When to use

`radiomics-ml` activates on requests such as: radiomics, radiomic features, pyradiomics, tabular ML, clinical prediction model, random forest, XGBoost, gradient boosting, tree ensemble, feature selection, nested cross-validation, nested CV, ICC feature stability, SHAP, machine learning model, classical ML, clinical machine learning, LASSO, feature stability, decision curve, calibration, TRIPOD, CLEAR, PROBAST.

## Quality Card

**Purpose** — Stop the over-optimistic radiomics / tree-ensemble study — hundreds of features on tens of events, hyperparameters tuned on the reported folds, features selected on the whole dataset, unstable features unfiltered, discrimination without calibration — from reaching a clinical manuscript.

**Safety boundaries**

- Advisory plus deterministic-audit only: never alters features, metrics, or sample counts.
- The rigor verdict is reproduced by a stdlib script (rule on the pipeline manifest), never asserted from prose.
- Integrates scikit-learn / xgboost / pyradiomics by reference; it does not reimplement them and never runs a model on real patient data.

**Known limitations**

- Audits the declared pipeline manifest, not the executed code; a mislabelled field (e.g. flat CV recorded as nested) can hide a real problem — complements, does not replace, self-review/check_cv_leakage (prose audit).
- A clean pipeline audit is necessary, not sufficient — external validation and clinical-utility evidence still govern the clinical claim.

**Validation**

- `python3 scripts/check_radiomics_ml.py --manifest <pipeline_manifest.json> --strict`
- `bash scripts/check_radiomics_ml_challenge/verify.sh  # deterministic, network-free`

**Evidence** — `ci_validator`

## Bundled resources

**References** (`skills/radiomics-ml/references/`):

- `radiomics_ml_guide.md`

**Scripts** (`skills/radiomics-ml/scripts/`):

- `check_radiomics_ml.py`
- `check_radiomics_ml_challenge/` (6 files)

## Source

Canonical definition: [`skills/radiomics-ml/SKILL.md`](../../skills/radiomics-ml/SKILL.md)

---

*Part of [MedSci Skills](../../README.md) — Claude Code skills for the medical research lifecycle. This page is generated from the skill's `SKILL.md`; edit that file and re-run `scripts/gen_skill_docs.py`.*
