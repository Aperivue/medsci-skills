# Medical-imaging preprocessing — modality-aware guidance

Companion to `preprocess-imaging`. This is *produce* knowledge: what preprocessing is standard per
modality, which augmentations preserve versus break physiology, and where leakage hides. It wires
MONAI / TorchIO transforms by name; it does not reimplement them.

## 1. Intensity normalisation by modality

| Modality | Standard intensity handling | Fitted on data? | Leakage risk |
|---|---|---|---|
| **CT** | Fixed HU window/level per task (e.g. lung −600/1500, soft-tissue 40/400), then scale to [0,1] or [−1,1] | **No** — fixed HU bounds are physical, not fitted | None (fixed transform) |
| **MR** | Bias-field correction (N4) → intensity normalisation (z-score, or Nyúl/histogram matching to a reference) | **Yes** — z-score/Nyúl are fitted | Fit the reference/stats on **train only**; per-image z-score is leakage-free |
| **X-ray** | Per-image min–max or z-score; optional CLAHE | Per-image = **no**; dataset z-score = yes | Prefer per-image; if dataset-level, train-only |
| **Ultrasound** | Per-image normalisation; crop the vendor UI/annotation border | Per-image = **no** | Cropping is fixed; watch for burned-in PHI/annotations |
| **Pathology (WSI)** | Stain normalisation (Macenko/Vahadane/Reinhard) to a reference tile | **Yes** — reference is fitted | Choose the reference from the **train** split only |

**Rule of thumb:** a *fixed* transform (HU window, resample to a fixed spacing, fixed crop) never
leaks. A *fitted* transform (z-score with dataset statistics, histogram/stain matching to a reference,
PCA/whitening) leaks unless it is fit on the training split and applied after the split.

## 2. Resampling and geometry

- Resample to a **fixed target spacing** (a task constant, not fitted) — e.g. 1×1×1 mm, or the
  dataset median spacing computed **once on train** and then frozen as a constant.
- Register/reorient to a canonical orientation (e.g. RAS) before patch extraction.
- Foreground cropping by a fixed intensity threshold is fixed (safe); cropping by a *fitted* body-mask
  model is a fitted transform — train-only.

## 3. Augmentation appropriateness (physiology-preserving vs breaking)

Augmentation must keep the image clinically plausible and label-consistent.

| Augmentation | Usually safe | Breaks physiology / label when… |
|---|---|---|
| Flip (L–R) | Most 2-D texture tasks | **Laterality matters** — cardiac silhouette, situs, side-labelled findings; flipping mislabels side |
| Rotation (small) | Most tasks | Large rotations for orientation-dependent tasks (e.g. gravity-dependent effusion/air-fluid levels) |
| Elastic / grid deformation | Soft-tissue segmentation | Rigid structures (bone fracture morphology); can invent/erase small lesions |
| Intensity scale/shift, gamma | CT/MR within-modality | Beyond clinically plausible HU/contrast range; simulates a nonexistent scanner |
| Gaussian noise / blur | Robustness to acquisition | Enough to hide the target finding (micro-nodule, microcalcification) |
| Cutout / random erasing | General | Can erase the sole lesion in a positive case → label noise |
| MixUp / CutMix | Some classification | Segmentation/detection where mixed pixels have no valid mask/box |

**Apply augmentation to the training split only.** Augmenting val/test is test-time augmentation
(TTA): legitimate only if pre-specified and disclosed, never folded silently into the headline metric.

## 4. Where leakage hides (the gate's targets)

1. **Normalisation fit on non-train data** — z-score/histogram/stain statistics computed over
   all/test data. → `NORMALIZATION_LEAKAGE`. Fit on train; apply the frozen statistics to val/test.
2. **Fitted transform before the split** — computing dataset statistics, then splitting. There is no
   train/test distinction yet, so the fit is cross-partition. → `PREPROCESS_BEFORE_SPLIT`.
3. **Patient slices across splits** — splitting *images* instead of *patients*, so a patient's slices
   sit in train and test. → `PATIENT_CROSS_SPLIT`. Split at the patient level, then map slices.
4. **Augmentation on eval** — see §3. → `AUGMENTATION_ON_EVAL`.
5. **Undeclared fit scope** — a fitted transform with no stated scope cannot be cleared.
   → `UNSPECIFIED_FIT_SCOPE`. Declare `fit_scope=train`.

## 5. Library wiring (integrate, don't reimplement)

- **MONAI transforms** — `LoadImaged`, `Spacingd`, `ScaleIntensityRanged` (fixed HU window),
  `NormalizeIntensityd` (z-score; set on the train subset), `RandFlipd`/`RandAffined`/`RandGaussianNoised`
  (train pipeline only).
- **TorchIO** — `Resample`, `ZNormalization`, `HistogramStandardization` (fit `landmarks` on train),
  `RandomFlip`/`RandomElasticDeformation` (train only).
- **Stain normalisation (WSI)** — `torchstain` / `staintools` Macenko/Vahadane; fit the reference on a
  train tile.

Record every step in the preprocessing manifest with its `type`, `fit_scope`, and `stage` so the gate
can decide leakage deterministically.
