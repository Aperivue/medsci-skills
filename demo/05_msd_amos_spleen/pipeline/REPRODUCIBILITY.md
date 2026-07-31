# Reproducibility

Every number in `../results/` and `../qc/` comes from an executed run. None is hand-entered, and the
one place a prediction was written before the data existed (`../EVALUATION_PLAN.md` §6) is marked as
partly wrong in `../README.md` rather than quietly aligned to the outcome.

## The published run

- **Datasets.** MSD Task09 Spleen (MSKCC, CC-BY-SA 4.0), 41 labelled cases used; AMOS22 (CC BY 4.0,
  Zenodo 7262581), 300 labelled CT + 60 labelled MRI. Neither is vendored — see `../README.md` for
  the download commands.
- **AMOS facts read from the shipped files, not from the paper.** `1 = spleen` (`dataset.json`).
  **ID ≤ 500 = CT**: the readme says both "less than 500" and "500 CT / 100 MRI", which cannot both
  hold on a contiguous 1–600 id space, and `amos_0500` is CT by its intensity range — so the prose
  rule is off by one. Labelled counts are 300 CT + 60 MRI (`labelsTs` is empty; 40 of the 100 MRI
  sit in the unlabelled test split). The CT label set runs 0–15 and the MRI set 0–13.
- **Split.** Seed **42**, patient-level, 32 train / 9 held-out (`../splits/split_assignment.csv`,
  `../splits/split_seed.txt`). Disjointness is proved by set arithmetic in
  `../qc/split_leakage.json` (`check_split_leakage.py --strict`), not asserted.
- **Preprocessing.** Declared in `../manifests/preprocessing_manifest.json` and gated by
  `check_preprocessing_leakage.py --strict` (`../qc/preprocessing_leakage.json`). The held-out cases
  are **physically absent** from `nnUNet_raw/imagesTr`, because nnU-Net's fingerprint — its resampling
  target *and* its CT intensity statistics — is fit from whatever is in that directory. The
  counterfactual is shipped as `preprocessing_manifest_naive.json` and fires 3 × `PREPROCESS_BEFORE_SPLIT`
  under the same gate.
- **Model.** nnU-Net v2, `3d_fullres`, plan `nnUNetPlans`, dataset `Dataset009_Spleen`. Target spacing
  2.55 × 0.789 × 0.789 mm, patch 56 × 192 × 192, batch 2 — all set by nnU-Net's fingerprint, all read
  back from the `plans.json` shipped beside the predictions.
- **Training.** 5 folds × **100 epochs** (`nnUNetTrainer_100epochs`), CUDA container, GTX 1080 Ti
  (compute capability 6.1) with `nnUNet_compile=f`. ~50 GPU-hours total. The 100-epoch schedule is a
  tenth of nnU-Net's default and is disclosed wherever a number from this model appears; the
  arithmetic that forced it is in `../FRICTION.md` 6.
- **Internal 5-fold CV** (nnU-Net's own validation, `foreground_mean` Dice from each fold's
  `validation/summary.json`; n = 7/7/6/6/6): **0.8437 / 0.9304 / 0.9659 / 0.9696 / 0.9507**. Fold 0 is
  the honest low. This is nnU-Net's internal cross-validation over the 32 training cases — it is not
  the held-out result, which is rung 1.
- **Inference.** 5-fold ensemble, nnU-Net **default** settings with mirroring TTA left on, for all
  three arms — no `--disable_tta` anywhere, confirmed from the run logs rather than from intent.
  RTX 3090. Wall clock: rung 1 (9 cases) **23 m 28 s**; rung 2 (300 cases) **21 h 43 m**; rung 3
  (60 cases) **75 m 32 s**.
- **Evaluation.** `evaluate_segmentation.py`, ground truth binarised to `== 1`, HD95 computed with
  the voxel spacing supplied (these volumes are anisotropic — an unscaled distance transform would
  be wrong by up to the slice-thickness ratio). 18 unit tests on synthetic volumes whose answers were
  derived on paper: `test_evaluate_segmentation.py`, all passing.
- **Analysis.** `aggregate_results.py`, bootstrap **10,000** resamples, seed **20260725**, numpy
  `default_rng`. Deterministic: re-running it regenerates `summary_across_cohorts.md` byte-identically.
  Subgroup cut-points are fixed and identical across arms (volume 100/250 mL, slice thickness
  2/5 mm) — a data-driven per-arm tertile would make the arms non-comparable.
- **Package versions**: not captured at run time. This is the gap in the record; reproducers should
  paste their own `pip freeze` below.

## How to reproduce

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r pipeline/requirements.txt
bash reproduce.sh
```

`reproduce.sh` runs tier A — both leakage gates (including the counterfactual, which **must** fail),
the metric unit tests, and the full across-cohort analysis from the shipped per-case CSVs. It prints
tier B (needs the datasets) and tier C (needs ~50 GPU-hours) rather than pretending to run them.

## Your environment (fill in when you reproduce)

- python / `pip freeze`:
- device (CPU / CUDA + driver):
- git commit:
