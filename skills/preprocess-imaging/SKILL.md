---
name: preprocess-imaging
description: >
  Design or audit the data-preparation stage of a medical-imaging model — DICOM/NIfTI intake,
  resampling and intensity normalisation, and the augmentation plan — so the pipeline is leakage-safe
  before model-scaffold builds the training repo. Emits a declarative preprocessing manifest and a
  deterministic data-stage leakage gate that catches the leaks a split table cannot see: a
  dataset-level normaliser fit on non-train data, any data-fitted transform run before the split, and
  the same patient's slices crossing splits. Integrates MONAI / TorchIO transforms; it does not
  reimplement them, and it never runs preprocessing on real patient data.
triggers: preprocess imaging, preprocessing, data pipeline, DICOM, NIfTI, resample, spacing, intensity normalization, intensity normalisation, windowing, HU window, z-score, histogram matching, augmentation, augmentation plan, TorchIO, MONAI transforms, data leakage, normalization leakage, preprocessing manifest, fit on train, per-image normalization, patient-level split, slice-level leakage, imaging data prep
tools: Read, Write, Edit, Bash, Grep, Glob
model: inherit
---

# Preprocess-Imaging Skill

## Purpose

This skill designs and audits the **data-preparation stage** of a medical-imaging model — the stage
*before* a training repo is built — and proves it is **leakage-safe by construction**. Data leakage
enters one step earlier than the split table can see: a normaliser fit on the whole dataset, a
data-fitted transform run before the split exists, or a patient whose slices land in more than one
partition. Each silently inflates every downstream metric (Kapoor & Narayanan, *Patterns* 2023;
Varoquaux & Cheplygina, *npj Digit Med* 2022; CLAIM 2024 data items).

It is the **missing first link** in the lane: **preprocess-imaging (prepare + audit)** →
`/model-scaffold` (build) → `/model-validation` (validate the split) → `/model-evaluation` +
`/analyze-stats` (metrics) → `/write-paper` + `/check-reporting` (publish). It **integrates**
MONAI / TorchIO transforms (referenced in the emitted plan); it does not reimplement them, and it
never executes preprocessing on real patient data.

## When to use
- You have a data manifest (one row per image/slice with a patient/subject ID) and want a
  leakage-safe preprocessing plan + a machine-checkable manifest before scaffolding a model.
- You want to audit an existing preprocessing pipeline for data-stage leakage.

## When NOT to use
- Auditing the train/val/test split table itself → `/model-validation` (split-leakage gate).
- Building the training repo / model code → `/model-scaffold` (it consumes this manifest).
- Choosing the architecture → `/architecture-zoo`.
- Held-out metrics / calibration → `/model-evaluation` then `/analyze-stats`.
- Reimplementing MONAI / TorchIO transforms → out of scope (this skill wires and audits them).

## Workflow

### Phase 1 — Inventory the data and the intended steps
Collect: modality (CT / MR / X-ray / US / path), the data manifest (one row per image/slice with a
`patient_id`), the intended resample spacing, the intensity transform (fixed HU window vs a fitted
z-score / min-max / histogram match), and the augmentation plan. See
[`references/preprocessing_guide.md`](references/preprocessing_guide.md) for modality-aware guidance
(what normalisation is standard per modality, which augmentations preserve vs break physiology).

### Phase 2 — Decide fit scope and order (the leakage-safe rules)
- **Fit dataset-level normalisation on the training split only** — never on all/full/test.
- **Run any data-fitted transform AFTER the split** — before the split there is no train/test
  distinction, so the fit spans partitions.
- **Prefer per-image (per-sample) normalisation** where clinically appropriate: it uses only that
  image's own statistics and is leakage-free even before the split.
- **Keep augmentation train-only** — augmenting val/test folds undisclosed test-time augmentation
  into the reported metric.
- **Split at the patient level**, then map slices to their patient's split (never split slices).

### Phase 3 — Emit the preprocessing manifest
Write a declarative JSON manifest that `model-scaffold` consumes and the gate checks:

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

`fit_scope`: `train` (OK) · `all`/`full`/`dataset`/`test` (leak) · `sample`/`per_image`/`none`
(not data-fitted, leakage-free). `stage`: `before_split` / `after_split`.

### Phase 4 — Gate the manifest (deterministic)
```bash
python3 scripts/check_preprocessing_leakage.py --manifest preprocessing_manifest.json --strict
```
Verdicts: `PREPROCESS_BEFORE_SPLIT`, `NORMALIZATION_LEAKAGE`, `PATIENT_CROSS_SPLIT` (Major);
`AUGMENTATION_ON_EVAL`, `UNSPECIFIED_FIT_SCOPE`, `MISSING_SEED` (Minor). The verdict is reproduced
by set arithmetic + rule on the manifest, never asserted from prose. A green gate is a precondition
for handing the manifest to `/model-scaffold`.

## Integration
- **Feeds `/model-scaffold`** — the audited manifest is the scaffold's preprocessing input; its
  `split_assignment` is the same patient-level split `/model-validation` later re-verifies.
- **`/self-review`** `model_development` probe audits data-stage leakage in a finished manuscript;
  this skill *produces* the leakage-safe pipeline it looks for.
- **`/check-reporting`** — the manifest documents the CLAIM 2024 / TRIPOD+AI data-preprocessing items.

## Anti-Hallucination

- **Never fabricate image statistics, patient IDs, or split assignments.** Every value in the
  manifest comes from the real data manifest and the researcher's declared pipeline — never invented.
  This skill designs and audits the plan; it does not run preprocessing on real patient data or
  synthesise the images it describes.
- **Never report a preprocessing-audit "pass" without running `check_preprocessing_leakage.py`.** The
  leakage verdict is reproduced deterministically (rule + set arithmetic on the manifest), never
  asserted from prose.
- **Never label a dataset-fitted transform as per-sample to clear the gate.** The manifest's
  `type` / `fit_scope` / `stage` must describe what the code actually does; a mislabelled transform
  hides a real leak the gate would otherwise catch.
- **Integrate, don't reimplement.** Reference MONAI / TorchIO transforms; do not write a new
  normalisation/resampling implementation or claim results for one.

## Reproducible challenge
`scripts/check_preprocessing_leakage_challenge/` ships a synthetic leak/clean manifest pair with a
network-free `verify.sh` wired into the skill's validation commands.
