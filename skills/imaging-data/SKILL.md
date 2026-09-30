---
name: imaging-data
description: Use when preparing a medical-imaging dataset (DICOM/NIfTI) for modelling. Profiles spacing, orientation, intensity, label integrity, foreground fraction and target volume, gates them against the plan, then plans and audits preprocessing and augmentation for leakage.
triggers: profile dataset, dataset profile, EDA, exploratory data analysis, explore the data, what does the data look like, imaging dataset, NIfTI, voxel spacing, slice thickness, orientation, intensity distribution, Hounsfield, class imbalance, foreground fraction, label sanity, empty label, label QC, dataset QC, data audit, before training, target volume, organ volume, is my test set labelled, research direction, where do I start, profile imaging, preprocess imaging, preprocessing, data pipeline, DICOM, resample, spacing, intensity normalization, intensity normalisation, windowing, HU window, z-score, histogram matching, augmentation, augmentation plan, TorchIO, MONAI transforms, data leakage, normalization leakage, preprocessing manifest, fit on train, per-image normalization, patient-level split, slice-level leakage, imaging data prep
tools: Read, Write, Edit, Bash, Grep, Glob
model: inherit
---

# Imaging-Data Skill

The dataset decides more of a study than the architecture does, and it decides it first. Phases 1–3
establish what the data is and what it will not support, while that is still cheap; Phases 4–7 design
and audit the preparation pipeline so it is leakage-safe before `/model-scaffold` builds the repo.
Describe-and-audit only: never modify, resample, reorient, split or write image data, never run
preprocessing on real patient data, and wire MONAI / TorchIO transforms by reference rather than
writing a new normalisation or resampling implementation.

Elsewhere: tabular/clinical variables → `/generate-codebook`, `/clean-data`; auditing the split
table, held-out metrics, calibration, subgroup results → `/model-assessment`; choosing an
architecture → `/model-selection`; building the repo → `/model-scaffold`.

## Workflow

### Phase 1 — Profile every case
```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/profile_imaging_dataset.py \
    --split train:imagesTr:labelsTr \
    --split test:imagesTs \
    --dataset "MSD Task09 Spleen" \
    --declared-labels 0=background,1=spleen \
    --target-label 1 \
    --plan resample=true,reorient=false,loss=dice_ce,metrics=dice+hd95 \
    --out eda/profile.json
```
One record per case: grid, spacing, orientation, intensity percentiles, the label values actually
present, foreground fraction, and target volume in mL. A `--split` given no label directory is
recorded as **unlabelled** — itself a finding. Requires `nibabel` + `numpy`; the gate does not.
Every profile figure comes from opening the files — never from a dataset's README, a similar dataset,
or memory. A README can be wrong about its own label indices; the labels cannot.

**`--target-label` on a multi-structure atlas.** Foreground defaults to every non-zero index — the
whole annotated anatomy. Measured on AMOS22, that pools to 3.2 % instead of the spleen's 0.2 %, so the
pooled figure sits above the 1 % imbalance threshold while the target sits far below it and the
imbalance verdicts go quiet exactly where the risk is. Naming the target also makes `LABEL_EMPTY` mean
*this case has no spleen*. Pass `--target-label all` for a genuinely multi-class study; leave it out
on a multi-structure atlas and the gate raises `TARGET_LABEL_UNDECLARED`.

### Phase 2 — Gate the profile against the declared plan
```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/check_dataset_profile.py --profile eda/profile.json \
    --out qc/dataset_profile.json --strict
```
Stdlib-only, so the audit re-runs anywhere the JSON travels. Never report a profile "pass" without
running it.

| Verdict | Severity | Fires when |
|---|---|---|
| `LABEL_SHAPE_MISMATCH` | Major | label grid ≠ image grid |
| `LABEL_EMPTY` | Major | a labelled case has zero foreground |
| `LABEL_VALUE_UNEXPECTED` | Major | label values outside the declared set |
| `TEST_SET_UNLABELLED` | Major | a split named test/held-out/external/eval carries no labels |
| `ACCURACY_UNDER_IMBALANCE` | Major | accuracy is planned while the target is a sliver of the volume |
| `LABEL_MISSING` | Minor | a case in a labelled split has no label file |
| `SPACING_HETEROGENEOUS` | Minor | spacing spans ≥ ratio on an axis and no resampling is declared |
| `ORIENTATION_MIXED` | Minor | >1 orientation code and no reorientation declared |
| `INTENSITY_SCALE_INCONSISTENT` | Minor | some cases on the HU scale, others not |
| `EXTREME_IMBALANCE` | Minor | median foreground below the threshold with no Dice-family loss |
| `TARGET_LABEL_UNDECLARED` | Minor | >1 structure declared, no target named, so foreground pools them all |

The gate flags an **undeclared decision, not variability**: 5× spacing spread and two orientation
codes pass once resampling and reorientation are declared (the clean challenge fixture proves this).
`--spacing-ratio` (default 2.0) and `--imbalance-frac` (default 0.01) are **screening defaults, not
published cut-points** — never present them as such; the values applied are printed in the output
and belong in the Methods. A split the profile shows unlabelled is never a held-out test set, however
the directory is named.

### Phase 3 — Turn the profile into research decisions
Write these decision notes into the study record, so `/design-study`, the preparation phases below,
and `/write-paper` inherit them instead of re-deriving them:
1. **Resampling target** — from the spacing distribution, not a tutorial default (carried into Phase 5).
2. **Loss and metric family** — from the foreground fraction. Segmentation reports Dice **and** a
   boundary metric per structure (`/model-assessment`); accuracy is not on the list.
3. **Pre-specified subgroups** — from the clinical spread the profile shows (target volume, slice
   thickness, modality). Pre-specifying them here is what separates a subgroup finding from a post-hoc one.
4. **Where the held-out set comes from** — especially when the shipped "test" directory is unlabelled.
5. **What the cohort cannot support** — n, single-source acquisition, absent subgroups: the seed of
   the Limitations paragraph, written before results can bias it.

### Phase 4 — Inventory the preparation steps and fix fit scope
Collect the modality, the data manifest (one row per image/slice with a `patient_id`), the resample
spacing, the intensity transform (fixed HU window vs a fitted z-score / min-max / histogram match),
and the augmentation plan. Read `${CLAUDE_SKILL_DIR}/references/preprocessing_guide.md` for the
modality-aware normalisation, physiology-preserving vs -breaking augmentation, and MONAI / TorchIO wiring.
- Fit dataset-level normalisation on the **training split only** — never all/full/test.
- Run any data-fitted transform **after** the split; before it there is no train/test distinction.
- Prefer per-image (per-sample) normalisation where clinically appropriate — leakage-free even before the split.
- Keep augmentation **train-only**; augmenting val/test folds undisclosed test-time augmentation into the metric.
- Split at the **patient** level, then map slices to their patient's split.

### Phase 5 — Emit the preprocessing manifest
Write `preprocessing_manifest.json`, which `/model-scaffold` consumes and the gate checks. Every value
comes from the real data manifest and the declared pipeline — never invented patient IDs or split
assignments.

```json
{
  "split_seed": 42,
  "transforms": [
    {"name": "hu_window", "type": "clip", "fit_scope": "none", "stage": "before_split"},
    {"name": "train_zscore", "type": "standardize", "fit_scope": "train", "stage": "after_split"},
    {"name": "flip_rotate", "type": "augmentation", "stage": "after_split", "applies_to": ["train"]}
  ],
  "split_assignment": [
    {"patient_id": "P001", "unit_id": "P001_s1", "split": "train"}
  ]
}
```

`fit_scope`: `train` (OK) · `all`/`full`/`dataset`/`test` (leak) · `sample`/`per_image`/`none`/`fixed`
(not data-fitted). `stage`: `before_split` / `after_split`. The fields must describe what the code
actually does — never tag a dataset-fitted transform per-sample to clear the gate; that hides the leak.

**Declare the fit scope of resampling too.** A target spacing chosen in advance is `fit_scope: fixed`
and never leaks. A target derived from the cohort does: nnU-Net sets its target spacing from a
percentile of the dataset fingerprint, so a resample fitted over every case carries held-out geometry
into the training grid exactly as an intensity statistic would. The fingerprint's scope decides which
you have, not the word "resample".

### Phase 6 — Gate the manifest
```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/check_preprocessing_leakage.py --manifest preprocessing_manifest.json \
    --out qc/preprocessing_leakage.json --strict
```
Verdicts: `PREPROCESS_BEFORE_SPLIT`, `NORMALIZATION_LEAKAGE`, `PATIENT_CROSS_SPLIT` (Major);
`AUGMENTATION_ON_EVAL`, `UNSPECIFIED_FIT_SCOPE`, `MISSING_SEED` (Minor), reproduced by set arithmetic
and rule on the manifest. A green gate is the precondition for handing the manifest to
`/model-scaffold`; its `split_assignment` is the same patient-level split `/model-assessment` later
re-verifies. Never report a pass without running it.

### Phase 7 — Before inference on a new cohort: check the normaliser's domain
Phase 6 asks whether a transform was fit on the right **scope**. Before running a trained model on a
cohort it was not trained on, ask whether that cohort sits in the intensity **domain** the trained
normaliser assumes:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/check_normalizer_domain.py \
    --profile eda/<cohort>_profile.json \
    --contract work/nnUNet_results/.../plans.json \
    --splits external_mri --out qc/normalizer_domain.json --strict
```
Its challenge card holds a cohort in the contract's own domain that must come back clean, an
arbitrary-unit cohort that must raise a Major, and an unreadable contract that must refuse rather than pass.

## Outputs and hand-off

- `eda/profile.json` (Phase 1), `qc/dataset_profile.json` (Phase 2), and the decision notes (Phase 3).
- `preprocessing_manifest.json` with the augmentation-appropriateness and normalisation fit-scope
  notes (Phases 4–5), `qc/preprocessing_leakage.json` (Phase 6), `qc/normalizer_domain.json` (Phase 7).

The manifest feeds `/model-scaffold`; it documents the CLAIM 2024 / TRIPOD+AI data-preprocessing items
for `/check-reporting`; `/self-review`'s `model_development` probe looks for exactly this pipeline in a
finished manuscript. Regression: `bash ${CLAUDE_SKILL_DIR}/scripts/check_dataset_profile_challenge/verify.sh`,
`bash ${CLAUDE_SKILL_DIR}/scripts/check_preprocessing_leakage_challenge/verify.sh`,
`bash ${CLAUDE_SKILL_DIR}/scripts/check_normalizer_domain_challenge/verify.sh`,
`bash ${CLAUDE_SKILL_DIR}/tests/test_dataset_profile.sh`,
`bash ${CLAUDE_SKILL_DIR}/tests/test_preprocessing_leakage.sh`.
