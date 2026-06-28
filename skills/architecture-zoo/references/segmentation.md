# Segmentation architectures (architecture-zoo)

For "delineate / measure structure X" questions — a pixel/voxel mask, a volume, a boundary.
This is the family `/model-scaffold` currently generates (a configurable U-Net), so the
scaffold notes here are concrete.

Each card: **paper → core idea → when to use → medical-imaging use → reference impl →
validation/experiment setup → `/model-scaffold` note.** For 3-D volumetric structures, prefer
a 3-D model; do not collapse to independent slices if the structure is volumetric.

---

## The U-Net lineage (encoder–decoder + skip connections)

### U-Net (2-D)
- **Paper**: Ronneberger et al., "U-Net: Convolutional Networks for Biomedical Image
  Segmentation," *MICCAI* 2015.
- **Core idea**: a contracting encoder + expanding decoder with **skip connections** that
  copy high-resolution features across, so fine boundaries survive; works with few training
  images + heavy augmentation.
- **When to use**: the **default** for 2-D medical segmentation; transparent and controllable.
- **Medical-imaging use**: CXR bone suppression / nodule masks, fundus vessel/lesion masks,
  pathology gland/nucleus masks, single-slice CT/MR masks.
- **Reference impl**: MONAI `UNet`; the shipped `/model-scaffold` `model.py` is a small
  configurable 2-D U-Net.
- **Validation setup**: patient-level split; report **Dice/IoU AND a boundary metric (HD95 /
  Normalised Surface Distance)**, per structure not only a global mean (Dice is shape- and
  size-insensitive); loss = Dice+BCE or Tversky for imbalance.
- **Scaffold**: `python3 scaffold.py --task segmentation --arch unet ...` — emits exactly
  this, with the patient-disjoint seed-locked split.

### 3-D U-Net / V-Net (volumetric)
- **Papers**: Çiçek et al., 3-D U-Net, *MICCAI* 2016; Milletari et al., V-Net, *3DV* 2016
  (3-D + a Dice loss objective).
- **Core idea**: 3-D convolutions so the model sees through-plane context; V-Net popularised
  optimising Dice directly.
- **When to use**: CT/MR **volumes** where through-plane context matters (organs, tumours,
  vessels). Use patch-based training for large volumes (memory).
- **Reference impl**: MONAI `UNet(spatial_dims=3)` / `SegResNet`; TorchIO for 3-D patches +
  augmentation.
- **Validation setup**: as U-Net, but count **structures/lesions** (not just patients) for
  per-structure Dice/HD95; report at the patient level for the clinical claim.

### Attention U-Net / Residual U-Net
- **Papers**: Oktay et al., Attention U-Net, *MIDL* 2018 (attention gates on skips);
  Zhang et al., Residual U-Net 2018 (residual blocks in the U-Net).
- **Core idea**: attention gates suppress irrelevant skip features (focus on the target);
  residual blocks ease optimisation of deeper U-Nets.
- **When to use**: small / low-contrast / variable-location targets (e.g. small vessels,
  aneurysms) where plain U-Net leaks; combine both for hard 3-D targets.
- **Medical-imaging use**: 3-D vascular / aneurysm segmentation (residual + dual-attention
  U-Net), small-lesion delineation.
- **Reference impl**: MONAI building blocks; published Attention-U-Net repos.
- **Validation setup**: as 3-D U-Net; emphasise boundary metric + small-structure stability
  (Dice is unstable on tiny structures).

### nnU-Net (v2) — the self-configuring standard
- **Paper**: Isensee et al., "nnU-Net: a self-configuring method for deep learning-based
  biomedical image segmentation," *Nature Methods* 2021.
- **Core idea**: not a new architecture but a **pipeline** that auto-configures preprocessing,
  patch size, network topology, and training from the dataset fingerprint — a U-Net done
  rigorously. Hard to beat, especially with limited data.
- **When to use**: the **default to beat** for most 3-D (and 2-D) segmentation tasks; start
  here, justify any custom architecture against it.
- **Reference impl**: `nnunetv2` (MIC-DKFZ, Apache-2.0). Integrate, do not reimplement.
- **Validation setup**: nnU-Net's own cross-validation is **development-time** optimism
  correction, not external validation (`/model-validation` MD3). Preserve the patient-level
  split: build the nnU-Net `dataset.json` folds from `/model-scaffold`'s
  `splits/split_assignment.csv` so the partition is consistent end to end.
- **Scaffold**: `/model-scaffold` emits the split + a `nnUNet`-compatible note; use its
  `split_assignment.csv` to seed nnU-Net's folds (template breadth lands in a later phase).

### Transformer-based segmentation (SegResNet / Swin-UNETR / UNETR)
- **Papers**: UNETR (Hatamizadeh et al., *WACV* 2022) and Swin-UNETR (2022) — a ViT/Swin
  encoder with a U-Net-style decoder for 3-D.
- **When to use**: large 3-D datasets where a transformer encoder helps long-range context;
  otherwise nnU-Net/CNN U-Nets remain strong with less data.
- **Reference impl**: MONAI `UNETR`, `SwinUNETR`, `SegResNet`.

---

## Instance / detection bridge

### Mask R-CNN (instance segmentation + detection)
- **Paper**: He et al., "Mask R-CNN," *ICCV* 2017 (mask head on Faster R-CNN); pairs with
  **FPN** (Lin et al., *CVPR* 2017) for multi-scale features.
- **Core idea**: region proposals → per-instance box + class + mask; a ResNet-FPN backbone
  gives multi-scale detection.
- **When to use**: **count + localise + delineate** separate lesions (instance-level), not a
  single semantic mask.
- **Medical-imaging use**: HCC / nodule detection-and-segmentation on multi-phase CT
  (Mask R-CNN + ResNet-FPN).
- **Reference impl**: torchvision `maskrcnn_resnet50_fpn`; MONAI detection.
- **Validation setup**: detection metrics — **FROC / sensitivity per false-positive or mAP
  with the IoU match criterion stated** — not patient-level accuracy (`/model-validation`
  MD6); per-lesion analysis with patient-level clustering disclosed.

---

## Promptable / foundation segmentation
SAM / MedSAM / MedSAM2 / SegVol / TotalSegmentator (released weights, little or no training)
live in `foundation_models.md`. For organ masks on CT with no training budget, start there
(TotalSegmentator / MedSAM2) before building a U-Net.

## Choosing among these
2-D, custom, transparent → **U-Net / Attention U-Net (MONAI)**. 3-D, default → **nnU-Net**.
Few labels / no training budget → **TotalSegmentator / MedSAM2** (`foundation_models.md`).
Count + localise instances → **Mask R-CNN + FPN**. Always patient-level split, always Dice
**and** a boundary metric per structure. Record the choice + paper, hand to `/model-scaffold`,
validate with `/model-validation`.
