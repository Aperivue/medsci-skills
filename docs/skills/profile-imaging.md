<!-- AUTO-GENERATED from skills/profile-imaging/SKILL.md by scripts/gen_skill_docs.py. Do not edit by hand. -->

# profile-imaging

> Profile a medical-imaging dataset before any modelling decision is made — the acquisition grid, voxel spacing and orientation spread, the intensity domain, which label values are actually present, how much of the volume the target occupies, and how large the target is in millilitres — then gate that profile against the researcher's declared plan. Catches, at the point where it is still cheap, the dataset facts that otherwise surface after a training run: a "test set" that carries no ground truth, labels whose grid does not match their image, a stray label index, a target occupying a fraction of a percent while accuracy is planned as a metric, and acquisition heterogeneity nobody declared a resampling decision for. Emits a dataset-profile JSON and a deterministic gate that reads it (stdlib-only, so an audit travels with the JSON). It describes the data and audits the plan against it; it does not preprocess, split, or train.

**Invoke:** `/profile-imaging` · **Tools:** Read, Write, Edit, Bash, Grep, Glob · **Model:** inherit

## When to use

`profile-imaging` activates on requests such as: profile dataset, dataset profile, EDA, exploratory data analysis, explore the data, what does the data look like, imaging dataset, NIfTI, voxel spacing, slice thickness, orientation, intensity distribution, Hounsfield, class imbalance, foreground fraction, label sanity, empty label, label QC, dataset QC, data audit, before training, target volume, organ volume, is my test set labelled, research direction, where do I start.

## Quality Card

**Purpose** — Establish what a medical-imaging dataset actually is — and what it will not support — before a plan is committed to, so the choices that follow (resampling target, loss and metric family, pre-specified subgroups, where the held-out set comes from) rest on measured facts rather than on tutorial defaults.

**Safety boundaries**

- Describe-and-audit only: never modifies, resamples, reorients, splits, or writes image data.
- Every profile figure is computed from the files by the profiler; the gate re-derives every verdict from that JSON by rule and arithmetic, never from prose.
- The gate is stdlib-only, so an audit can be reproduced anywhere the profile JSON travels — no nibabel, no images, no network.

**Known limitations**

- Profiles the files as they sit on disk: a mislabelled split name or a wrong --declared-labels argument is taken at face value, and DICOM metadata (scanner, vendor, protocol) is not read — vendor/centre subgroups need that metadata from elsewhere.
- --spacing-ratio and --imbalance-frac are screening defaults, not published cut-points; they are printed in the output so a reader can see what was applied.
- A clean profile is necessary, not sufficient: preprocessing leakage (preprocess-imaging), split disjointness (model-validation) and held-out metric choice (model-evaluation) are separate gates.

**Validation**

- `python3 scripts/check_dataset_profile.py --profile <profile.json> --strict`
- `bash scripts/check_dataset_profile_challenge/verify.sh  # deterministic, network-free`
- `bash tests/test_dataset_profile.sh`

**Evidence** — `ci_validator`

## Bundled resources

**Scripts** (`skills/profile-imaging/scripts/`):

- `check_dataset_profile.py`
- `check_dataset_profile_challenge/` (6 files)
- `profile_imaging_dataset.py`

## Source

Canonical definition: [`skills/profile-imaging/SKILL.md`](../../skills/profile-imaging/SKILL.md)

---

*Part of [MedSci Skills](../../README.md) — Claude Code skills for the medical research lifecycle. This page is generated from the skill's `SKILL.md`; edit that file and re-run `scripts/gen_skill_docs.py`.*
