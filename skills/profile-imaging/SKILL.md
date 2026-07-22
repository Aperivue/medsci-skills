---
name: profile-imaging
description: >
  Profile a medical-imaging dataset before any modelling decision is made — the acquisition grid,
  voxel spacing and orientation spread, the intensity domain, which label values are actually
  present, how much of the volume the target occupies, and how large the target is in millilitres —
  then gate that profile against the researcher's declared plan. Catches, at the point where it is
  still cheap, the dataset facts that otherwise surface after a training run: a "test set" that
  carries no ground truth, labels whose grid does not match their image, a stray label index, a
  target occupying a fraction of a percent while accuracy is planned as a metric, and acquisition
  heterogeneity nobody declared a resampling decision for. Emits a dataset-profile JSON and a
  deterministic gate that reads it (stdlib-only, so an audit travels with the JSON). It describes
  the data and audits the plan against it; it does not preprocess, split, or train.
triggers: profile dataset, dataset profile, EDA, exploratory data analysis, explore the data, what does the data look like, imaging dataset, NIfTI, voxel spacing, slice thickness, orientation, intensity distribution, Hounsfield, class imbalance, foreground fraction, label sanity, empty label, label QC, dataset QC, data audit, before training, target volume, organ volume, is my test set labelled, research direction, where do I start
tools: Read, Write, Edit, Bash, Grep, Glob
model: inherit
---

# Profile-Imaging Skill

## Purpose

A dataset decides more of a study than the architecture does, and it decides it **first**. Before
anything is preprocessed, split, or trained, a handful of facts are already true about the data, and
each one closes off or opens up a research plan:

- If the target occupies 0.4 % of the volume, accuracy is not a metric — predicting background
  everywhere scores 99.6 %.
- If through-plane spacing runs 1.5–8 mm inside a single institution, resampling is not a default to
  accept quietly; it is the most consequential preprocessing choice in the study, and it is also the
  axis along which an external dataset will differ.
- If the directory named `imagesTs` has no labels, it is not a test set, and the held-out set has to
  come from somewhere else — better known before training than after.
- If the organ volume spans 56–502 mL when normal is roughly 100–250, the cohort contains disease
  that a subgroup analysis should be **pre-specified** for, rather than discovered post hoc.

None of that requires a model, a GPU, or an engineer. It requires reading every file once and
writing down what is there. This skill does that, and then audits the plan against it.

It is the **front door** of the model-engineering lane:
`profile-imaging (describe)` → `/design-study` + `/architecture-zoo` (decide) →
`/preprocess-imaging` (plan the pipeline) → `/model-scaffold` (build) → `/model-validation` →
`/model-evaluation`.

## When to use
- You have a dataset and a task, and need to know what the data will and will not support before
  committing to a plan.
- You inherited a dataset and need its integrity established (labels intact, splits labelled,
  label values as declared) before anyone trains on it.
- You are about to write a Methods section that describes the cohort and its acquisition.

## When NOT to use
- Tabular / clinical variables → `/generate-codebook` (data dictionary) and `/clean-data`.
- Designing the preprocessing pipeline and auditing it for data-stage leakage →
  `/preprocess-imaging` (it consumes what this skill describes).
- Auditing the train/val/test split table → `/model-validation`.
- Choosing an architecture → `/architecture-zoo`. Building the repo → `/model-scaffold`.
- Held-out metrics, calibration, subgroup results → `/model-evaluation` then `/analyze-stats`.

## Workflow

### Step 1 — profile every case

```bash
python3 scripts/profile_imaging_dataset.py \
    --split train:imagesTr:labelsTr \
    --split test:imagesTs \
    --dataset "MSD Task09 Spleen" \
    --declared-labels 0=background,1=spleen \
    --plan resample=true,reorient=false,loss=dice_ce,metrics=dice+hd95 \
    --out eda/profile.json
```

One record per case: grid, spacing, orientation, intensity percentiles, the label values actually
present, foreground fraction, and target volume in mL. A `--split` given no label directory is
recorded as **unlabelled** — which is itself a finding.

Requires `nibabel` + `numpy` (it has to open images). The gate below does not.

### Step 2 — gate the profile against the declared plan

```bash
python3 scripts/check_dataset_profile.py --profile eda/profile.json \
    --out qc/dataset_profile.json --strict
```

Stdlib-only, so the audit re-runs anywhere the JSON travels. Verdicts:

| Verdict | Severity | Fires when |
|---|---|---|
| `LABEL_SHAPE_MISMATCH` | Major | label grid ≠ image grid |
| `LABEL_EMPTY` | Major | a labelled case has zero foreground |
| `LABEL_VALUE_UNEXPECTED` | Major | label values outside the declared set |
| `TEST_SET_UNLABELLED` | Major | a split named test/held-out/external carries no labels |
| `ACCURACY_UNDER_IMBALANCE` | Major | accuracy is planned while the target is a sliver of the volume |
| `LABEL_MISSING` | Minor | a case in a labelled split has no label file |
| `SPACING_HETEROGENEOUS` | Minor | spacing spans ≥ ratio on an axis and no resampling is declared |
| `ORIENTATION_MIXED` | Minor | >1 orientation code and no reorientation declared |
| `INTENSITY_SCALE_INCONSISTENT` | Minor | some cases sit on the HU scale and others do not |
| `EXTREME_IMBALANCE` | Minor | median foreground below the threshold with no Dice-family loss |

**The gate flags an undeclared decision, not variability itself.** A dataset with 5× spacing spread
and two orientation codes passes cleanly once resampling and reorientation are declared —
heterogeneity that has been dealt with is not a defect. That distinction is what the challenge card's
clean fixture exists to prove.

`--spacing-ratio` (default 2.0) and `--imbalance-frac` (default 0.01) are **screening defaults, not
published cut-points**: 2× through-plane spacing changes what a fixed-size patch sees, and 1 %
foreground is roughly where plain accuracy stops carrying information. Both are adjustable and both
are printed in the output, so a reader knows what was applied.

### Step 3 — turn the profile into research decisions

The profile is evidence; the decisions are yours, and the ones worth writing down are:

1. **Resampling target** — from the spacing distribution, not from a tutorial default. Carry it into
   `/preprocess-imaging` as a declared transform.
2. **Loss and metric family** — from the foreground fraction. Segmentation reports Dice **and** a
   boundary metric per structure (`/model-evaluation`); accuracy is not on the list.
3. **Pre-specified subgroups** — from the clinical spread the profile reveals (target volume,
   slice thickness, modality). Pre-specifying them here is what separates a subgroup finding from a
   post-hoc one.
4. **Where the held-out set comes from** — especially when the shipped "test" directory is unlabelled.
5. **What the cohort cannot support** — n, single-source acquisition, absent subgroups. This is the
   honest seed of the Limitations paragraph, written before the results can bias it.

Record these in the study record so `/design-study`, `/preprocess-imaging`, and eventually
`/write-paper` inherit them rather than re-deriving them.

## Outputs

- `eda/profile.json` — per-case dataset profile (the artifact downstream skills read).
- `qc/dataset_profile.json` — deterministic audit with verdicts.
- Decision notes for the study record (resampling target, loss/metric family, pre-specified
  subgroups, held-out provenance, cohort limitations).

## Forbidden

- Reporting a profile figure that was not computed from the files (no remembered spacings, no
  assumed label indices — open the labels and look).
- Declaring an audit pass without running the gate.
- Using a split's images as a held-out test set when the profile says it has no labels.
- Reading `--spacing-ratio` / `--imbalance-frac` defaults as published thresholds.

## Anti-Hallucination

- **Never report a profile figure that was not computed from the files.** Spacings, label indices,
  foreground fractions and organ volumes come from opening every image and label — not from a
  dataset's documentation, not from what a similar dataset looked like, and not from memory. A
  dataset's README can be wrong about its own label indices; the labels cannot.
- **Never report a profile audit "pass" without running `check_dataset_profile.py`.** The verdicts
  are re-derived from the profile JSON by rule and arithmetic; a prose claim that the data "looks
  fine" is not the audit.
- **Never treat an unlabelled split as a test set.** If the profile says a split has no labels, no
  held-out metric can come from it, however the directory is named.
- **Never present `--spacing-ratio` / `--imbalance-frac` as published cut-points.** They are
  screening defaults; the values applied are printed in the output and belong in the Methods.

## Validation

```bash
python3 scripts/check_dataset_profile.py --profile <profile.json> --strict
bash scripts/check_dataset_profile_challenge/verify.sh   # deterministic, network-free
bash tests/test_dataset_profile.sh
```
