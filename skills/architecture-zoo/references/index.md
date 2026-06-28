# Architecture decision tree (architecture-zoo)

Pick an architecture from the **research question + modality + data scale + label
availability**, not from what is fashionable. Read this index, then open the matching
family card (`classification.md`, `segmentation.md`, `foundation_models.md`) for the
per-paper detail and the `/model-scaffold` template to instantiate.

## Step 1 — name the task
| The research question is about… | Task | Family card |
|---|---|---|
| "is finding X present / which class" (per image / per patient) | **classification** (binary / multi-label) | `classification.md` |
| "delineate / measure structure X" (pixel/voxel mask, volume, boundary) | **segmentation** | `segmentation.md` |
| "find and localise lesions" (boxes / points, count, FROC) | **detection** | *(forthcoming — see segmentation's Mask R-CNN note)* |
| "I have few labels / want to pretrain on unlabelled scans" | **self-supervised pretraining → fine-tune** | `foundation_models.md` |
| "adapt a released medical foundation model" | **transfer / prompt a foundation model** | `foundation_models.md` |
| "synthesise / translate a modality" (MRI→CT, denoise) | **image-to-image / generative** | *(forthcoming)* |
| "generate a report / answer a visual question" | **multimodal LLM** | *(use `/mllm-eval`; not a CNN choice)* |

## Step 2 — let the constraints narrow it
- **Modality / dimensionality**: 2-D (CXR, fundus, path tiles, single CT/MR slices) →
  2-D backbones / 2-D U-Net. 3-D volumes (CT, MR) → **3-D U-Net / SegResNet / nnU-Net**
  (3-D context matters; do not collapse to slices if the structure is volumetric).
- **Labelled data scale** (events/structures, not just images):
  - **small** (hundreds) → a **pretrained** backbone fine-tuned (ImageNet / a medical
    foundation model), strong augmentation, heavy regularisation; prefer **nnU-Net**
    for segmentation (self-configuring, hard to beat with little data).
  - **medium** (thousands) → ResNet/DenseNet/EfficientNet (classification) or
    U-Net/SegResNet (segmentation), still pretrained.
  - **large** (tens of thousands+) → ViT / Swin become competitive; consider
    self-supervised pretraining on your own unlabelled pool first.
- **Class imbalance / small structures** → segmentation: Dice/Tversky/boundary-aware
  losses + a boundary metric; classification: AUPRC alongside AUROC. (Metric choice is
  `/model-validation` / `/model-evaluation`; it constrains the loss here.)
- **Interpretability / deployment need** → simpler, well-understood backbones
  (ResNet + Grad-CAM) over a marginally better but opaque model.

## Step 3 — default picks (a safe starting point, then justify deviations)
| Task + setting | Default | Why |
|---|---|---|
| 2-D multi-label CXR classification | **ResNet-50 / EfficientNet (pretrained, `timm`)** | strong, cheap, well-calibrated baselines |
| 3-D organ / lesion segmentation | **nnU-Net (v2)** | self-configuring; the standard to beat |
| 2-D segmentation, custom pipeline | **U-Net / Attention U-Net (MONAI)** | transparent, controllable |
| few labels, many unlabelled scans | **SSL pretrain (DINO/MAE) → fine-tune**, or **MedSAM/TotalSegmentator transfer** | label-efficient |
| zero-/few-shot organ masks on CT | **TotalSegmentator / MedSAM2** | released weights, no training |

## Step 4 — write the decision note
Record the choice as a short note (`decisions/architecture_choice.md`): the **task**, the
**chosen architecture**, the **source paper** it comes from, the **reason** (against the
constraints above), the **runner-up + why not**, and the matching **`/model-scaffold`
template**. Never recommend an architecture without naming its source paper, and never
quote a benchmark number you have not cited. Then hand the choice to `/model-scaffold`.

> The zoo describes **archetypes**, not a live leaderboard. SOTA churns; the task →
> family → constraint logic does not. When a newer model claims to beat these, evaluate
> it with `/model-validation` rather than adopting it on the strength of a headline.
