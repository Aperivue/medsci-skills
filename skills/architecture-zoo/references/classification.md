# Classification architectures (architecture-zoo)

For "is finding X present / which class" questions — per image or per patient, binary or
multi-label. Almost always start from a **pretrained** backbone (ImageNet via `timm`, or a
medical foundation model — see `foundation_models.md`) and fine-tune; training a large
backbone from scratch on a few thousand medical images underperforms and overfits.

Each card: **paper → core idea → when to use → medical-imaging use → reference impl →
validation/experiment setup → `/model-scaffold` note.** Cite the paper in your decision
note; never quote a benchmark you have not cited.

---

## CNN backbones

### AlexNet / VGG (the baseline lineage)
- **Papers**: Krizhevsky et al., *NeurIPS* 2012 (AlexNet); Simonyan & Zisserman, *ICLR*
  2015 (VGG).
- **Core idea**: deep stacks of small convolutions + ReLU + pooling; VGG showed depth with
  3×3 convs. Historically important, now mostly superseded as backbones.
- **When to use**: rarely as a primary backbone today; VGG features still appear as a
  **perceptual loss** network in synthesis. Use ResNet/EfficientNet instead.

### ResNet (residual learning) — the default workhorse
- **Paper**: He et al., "Deep Residual Learning for Image Recognition," *CVPR* 2016.
- **Core idea**: identity skip connections let very deep nets train (the residual `F(x)+x`
  eases optimisation / vanishing gradients).
- **When to use**: the **safe default** for 2-D medical classification; ResNet-50 is a
  strong, well-understood, well-calibrated baseline that plays nicely with Grad-CAM.
- **Medical-imaging use**: CXR multi-label classification, fundus grading, path-tile
  classification; a ResNet-FPN is the backbone for detection (see `segmentation.md`).
- **Reference impl**: `timm` (`resnet50`, pretrained); torchvision.
- **Validation setup**: patient-level split; report **AUROC + AUPRC with CIs** (AUPRC for
  the minority class), sensitivity/specificity, and PPV/NPV at the deployment prevalence;
  Grad-CAM sanity check that attention is on pathology, not a shortcut.
- **Scaffold**: a `timm` classifier head on a pretrained ResNet (classification template,
  forthcoming in `/model-scaffold`; today, segmentation is the shipped template).

### DenseNet (dense connectivity)
- **Paper**: Huang et al., "Densely Connected Convolutional Networks," *CVPR* 2017.
- **Core idea**: each layer receives all preceding feature maps (concatenation) — strong
  feature reuse, parameter-efficient.
- **When to use**: a strong CXR baseline (DenseNet-121 is the CheXNet backbone); good when
  parameters/compute are tight.
- **Medical-imaging use**: chest-X-ray pathology classification (CheXpert/MIMIC-CXR-style).
- **Reference impl**: `timm` (`densenet121`).
- **Validation setup**: as ResNet; multi-label → per-label AUROC/AUPRC + a macro/micro
  average, calibration per label.

### EfficientNet (compound scaling)
- **Paper**: Tan & Le, "EfficientNet," *ICML* 2019.
- **Core idea**: jointly scale depth/width/resolution by a compound coefficient — better
  accuracy/compute trade-off.
- **When to use**: when you want the **best accuracy-per-FLOP** baseline; good on
  higher-resolution images where input resolution matters (mammography, path).
- **Reference impl**: `timm` (`efficientnet_b0..b7`, `tf_efficientnetv2`).
- **Validation setup**: as ResNet; watch that the chosen resolution matches the clinically
  relevant detail; report compute if deployment-constrained.

### Inception / GoogLeNet (multi-scale)
- **Papers**: Szegedy et al., *CVPR* 2015 (Inception v1) and the BN-Inception / v3 line.
- **Core idea**: parallel multi-scale convolution branches (1×1/3×3/5×5) per block.
- **When to use**: legacy strong baseline; multi-scale lesions. Usually ResNet/EfficientNet
  preferred now.

---

## Vision transformers (when data is large)

### ViT (Vision Transformer)
- **Paper**: Dosovitskiy et al., "An Image is Worth 16×16 Words," *ICLR* 2021.
- **Core idea**: split the image into patches, treat them as tokens, apply a standard
  transformer; global attention from layer 1, but **data-hungry** (needs large pretraining).
- **When to use**: large labelled sets **or** a strong pretrained ViT (ImageNet-21k, DINO,
  or a medical foundation model); underperforms CNNs on small medical sets trained from
  scratch.
- **Reference impl**: `timm` (`vit_base_patch16_224`); pretrained essential.
- **Validation setup**: as ResNet; be explicit that performance leans on the pretraining
  corpus (contamination/transfer caveat — `/model-validation` MD3/MD7).

### Swin Transformer (hierarchical, windowed attention)
- **Paper**: Liu et al., "Swin Transformer," *ICCV* 2021.
- **Core idea**: hierarchical feature maps with **shifted-window** local attention — linear
  complexity in image size; a strong **backbone for dense tasks** (detection/segmentation),
  not only classification (Swin-UNETR is its segmentation form, see `segmentation.md`).
- **When to use**: higher-resolution inputs, or when you want a transformer backbone that
  also feeds a segmentation/detection head.
- **Reference impl**: `timm` (`swin_base_patch4_window7_224`); MONAI `SwinUNETR` for 3-D seg.

### DeiT / MLP-Mixer (efficiency / token-mixing)
- **Papers**: Touvron et al., DeiT, *ICML* 2021 (data-efficient ViT via distillation);
  Tolstikhin et al., MLP-Mixer, *NeurIPS* 2021 (attention-free token mixing).
- **When to use**: DeiT when you want a ViT that trains on less data via distillation;
  MLP-Mixer mostly of conceptual interest. CNNs/Swin usually preferred for medical work.

---

## Choosing among these
Small/medium labelled data → **pretrained ResNet/DenseNet/EfficientNet**. Large data or a
strong pretrained transformer → **ViT/Swin**. Always pretrained, always patient-level split,
always AUROC **and** AUPRC with CIs. Record the choice + paper in the decision note and hand
to `/model-scaffold`; validate with `/model-validation`, evaluate with `/model-evaluation`.
