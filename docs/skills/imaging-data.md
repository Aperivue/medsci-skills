<!-- AUTO-GENERATED from skills/imaging-data/SKILL.md by scripts/gen_skill_docs.py. Do not edit by hand. -->

# imaging-data

> Use when preparing a medical-imaging dataset (DICOM/NIfTI) for modelling. Profiles spacing, orientation, intensity, label integrity, foreground fraction and target volume, gates them against the plan, then plans and audits preprocessing and augmentation for leakage.

**Invoke:** `/imaging-data` · **Tools:** Read, Write, Edit, Bash, Grep, Glob · **Model:** inherit

## When to use

`imaging-data` activates on requests such as: profile dataset, dataset profile, EDA, exploratory data analysis, explore the data, what does the data look like, imaging dataset, NIfTI, voxel spacing, slice thickness, orientation, intensity distribution, Hounsfield, class imbalance, foreground fraction, label sanity, empty label, label QC, dataset QC, data audit, before training, target volume, organ volume, is my test set labelled, research direction, where do I start, profile imaging, preprocess imaging, preprocessing, data pipeline, DICOM, resample, spacing, intensity normalization, intensity normalisation, windowing, HU window, z-score, histogram matching, augmentation, augmentation plan, TorchIO, MONAI transforms, data leakage, normalization leakage, preprocessing manifest, fit on train, per-image normalization, patient-level split, slice-level leakage, imaging data prep.

## Quality Card

**Purpose** — Establish what a medical-imaging dataset actually is — and what it will not support — before a plan is committed to, then catch data-stage leakage in the preparation pipeline before it silently inflates every downstream metric, so resampling, loss/metric family, pre-specified subgroups and the held-out set rest on measured facts rather than tutorial defaults.

**Safety boundaries**

- Describe-and-audit only: never modifies, resamples, reorients, splits, or writes image data, and never runs preprocessing on real patient data.
- Every profile figure is computed from the files by the profiler; every gate verdict is re-derived by rule and set arithmetic from the profile JSON or the manifest, never asserted from prose.
- The gates are stdlib-only, so an audit reproduces anywhere the JSON travels; MONAI / TorchIO transforms are integrated by reference, never reimplemented.

**Known limitations**

- Profiles the files as they sit on disk: a mislabelled split name or a wrong --declared-labels argument is taken at face value, and DICOM metadata (scanner, vendor, protocol) is not read — vendor/centre subgroups need that metadata from elsewhere.
- --spacing-ratio and --imbalance-frac are screening defaults, not published cut-points; they are printed in the output so a reader can see what was applied.
- The leakage gate audits the declared manifest, not the executed code; a transform mislabelled in the manifest (e.g. a dataset normaliser tagged fit_scope=sample) can hide a real leak.
- Clean data-stage audits are necessary, not sufficient: split disjointness and held-out metric choice (model-assessment) are separate gates.

**Validation**

- `python3 scripts/check_dataset_profile.py --profile <profile.json> --strict`
- `python3 scripts/check_preprocessing_leakage.py --manifest <preprocessing_manifest.json> --strict`
- `bash scripts/check_dataset_profile_challenge/verify.sh  # deterministic, network-free`
- `bash scripts/check_preprocessing_leakage_challenge/verify.sh  # deterministic, network-free`
- `bash scripts/check_normalizer_domain_challenge/verify.sh  # deterministic, network-free`
- `bash tests/test_dataset_profile.sh`
- `bash tests/test_preprocessing_leakage.sh`

**Evidence** — `ci_validator`

## Bundled resources

**References** (`skills/imaging-data/references/`):

- `preprocessing_guide.md`

**Scripts** (`skills/imaging-data/scripts/`):

- `check_dataset_profile.py`
- `check_dataset_profile_challenge/` (6 files)
- `check_normalizer_domain.py`
- `check_normalizer_domain_challenge/` (7 files)
- `check_preprocessing_leakage.py`
- `check_preprocessing_leakage_challenge/` (6 files)
- `profile_imaging_dataset.py`

## Source

Canonical definition: [`skills/imaging-data/SKILL.md`](../../skills/imaging-data/SKILL.md)

---

*Part of [MedSci Skills](../../README.md) — Claude Code skills for the medical research lifecycle. This page is generated from the skill's `SKILL.md`; edit that file and re-run `scripts/gen_skill_docs.py`.*
