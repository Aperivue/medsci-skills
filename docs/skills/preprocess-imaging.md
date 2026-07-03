<!-- AUTO-GENERATED from skills/preprocess-imaging/SKILL.md by scripts/gen_skill_docs.py. Do not edit by hand. -->

# preprocess-imaging

> Design or audit the data-preparation stage of a medical-imaging model — DICOM/NIfTI intake, resampling and intensity normalisation, and the augmentation plan — so the pipeline is leakage-safe before model-scaffold builds the training repo. Emits a declarative preprocessing manifest and a deterministic data-stage leakage gate that catches the leaks a split table cannot see: a dataset-level normaliser fit on non-train data, any data-fitted transform run before the split, and the same patient's slices crossing splits. Integrates MONAI / TorchIO transforms; it does not reimplement them, and it never runs preprocessing on real patient data.

**Invoke:** `/preprocess-imaging` · **Tools:** Read, Write, Edit, Bash, Grep, Glob · **Model:** inherit

## When to use

`preprocess-imaging` activates on requests such as: preprocess imaging, preprocessing, data pipeline, DICOM, NIfTI, resample, spacing, intensity normalization, intensity normalisation, windowing, HU window, z-score, histogram matching, augmentation, augmentation plan, TorchIO, MONAI transforms, data leakage, normalization leakage, preprocessing manifest, fit on train, per-image normalization, patient-level split, slice-level leakage, imaging data prep.

## Quality Card

**Purpose** — Catch data-stage leakage in a medical-imaging pipeline — a normaliser fit on the test distribution, a data-fitted transform run before the split, or a patient's slices spread across splits — before it silently inflates every downstream metric.

**Safety boundaries**

- Advisory plus deterministic-audit only: never alters images, statistics, or split assignments.
- The leakage verdict is reproduced by a stdlib script (rule + set arithmetic on the manifest), never asserted from prose.
- Integrates MONAI / TorchIO transforms by reference; it does not reimplement them and never runs preprocessing on real patient data.

**Known limitations**

- Audits the declared manifest, not the executed code; a transform mislabelled in the manifest (e.g. a dataset normaliser tagged fit_scope=sample) can hide a real leak.
- A clean data-stage audit is necessary, not sufficient — the split table (model-validation) and held-out evaluation (model-evaluation) still apply.

**Validation**

- `python3 scripts/check_preprocessing_leakage.py --manifest <preprocessing_manifest.json> --strict`
- `bash scripts/check_preprocessing_leakage_challenge/verify.sh  # deterministic, network-free`

**Evidence** — `ci_validator`

## Bundled resources

**References** (`skills/preprocess-imaging/references/`):

- `preprocessing_guide.md`

**Scripts** (`skills/preprocess-imaging/scripts/`):

- `check_preprocessing_leakage.py`
- `check_preprocessing_leakage_challenge/` (6 files)

## Source

Canonical definition: [`skills/preprocess-imaging/SKILL.md`](../../skills/preprocess-imaging/SKILL.md)

---

*Part of [MedSci Skills](../../README.md) — Claude Code skills for the medical research lifecycle. This page is generated from the skill's `SKILL.md`; edit that file and re-run `scripts/gen_skill_docs.py`.*
