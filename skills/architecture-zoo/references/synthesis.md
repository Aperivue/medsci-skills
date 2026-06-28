# Image synthesis / translation architectures (architecture-zoo)

For "synthesise or translate a modality" questions — MRI→CT, non-contrast→contrast,
low-dose→full-dose, denoising, super-resolution, or generating training images.
`/model-scaffold --task synthesis` emits a Pix2Pix repo. **Caveat**: a synthetic image can
carry hallucinated structure, so a downstream-task or reader validation is mandatory (the
`image_synthesis.md` reviewer probe, IS1–IS4, owns this).

Each card: **paper → core idea → when to use → medical-imaging use → reference impl →
validation/experiment setup.**

---

## Conditional GANs (image-to-image)

### Pix2Pix (paired) / CycleGAN (unpaired)
- **Papers**: Isola et al., Pix2Pix, *CVPR* 2017 (paired, U-Net generator + PatchGAN);
  Zhu et al., CycleGAN, *ICCV* 2017 (unpaired, cycle-consistency).
- **Core idea**: a conditional GAN maps a source image to a target domain; Pix2Pix needs
  **paired** (registered) images, CycleGAN works **unpaired** via cycle consistency.
- **When to use**: cross-modality translation when paired data exist (Pix2Pix) or do not
  (CycleGAN — but it can hallucinate, so validate carefully).
- **Medical-imaging use**: MRI→CT for attenuation correction / planning, CBCT→CT, virtual
  contrast, stain transfer in pathology; bone suppression on CXR (paired).
- **Reference impl**: the official pytorch-CycleGAN-and-pix2pix repo; `/model-scaffold
  --task synthesis` emits a small Pix2Pix (U-Net generator + PatchGAN).
- **Validation setup**: image-fidelity metrics (SSIM / PSNR) are necessary but **not
  sufficient** — add a **downstream-task** metric (does a model / clinician perform the
  clinical task as well on synthetic as on real?) and disclose hallucination risk
  (`image_synthesis.md` IS1–IS4).

### SPADE / conditional generators
- **Paper**: Park et al., SPADE, *CVPR* 2019 (spatially-adaptive normalisation from a
  semantic map).
- **When to use**: generating images conditioned on a segmentation map (e.g. lesion
  insertion / data augmentation with controlled anatomy).
- **Medical-imaging use**: nodule / lesion synthesis for augmentation (with a perceptual
  loss; Johnson et al. 2016).

## Diffusion models (current SOTA for fidelity / diversity)

### DDPM / latent diffusion
- **Papers**: Ho et al., DDPM, *NeurIPS* 2020; Rombach et al., latent diffusion, *CVPR*
  2022.
- **Core idea**: learn to reverse a gradual noising process; higher fidelity and mode
  coverage than GANs, at higher compute.
- **When to use**: when sample quality / diversity matters and compute allows; increasingly
  the default for medical image generation and reconstruction.
- **Reference impl**: MONAI `generative` (DiffusionModelUNet); HuggingFace `diffusers`.
- **Validation setup**: as GANs — fidelity + downstream-task + hallucination disclosure;
  for reconstruction, compare against the acquired ground truth.

## Reconstruction / restoration

### VAE / U-Net restoration / fastMRI baselines
- **Papers**: Kingma & Welling, VAE, *ICLR* 2014; the fastMRI benchmark (Zbontar et al.
  2018) for MRI reconstruction.
- **When to use**: denoising, artefact removal, accelerated MRI reconstruction (often a
  U-Net or unrolled model rather than a GAN).
- **Validation setup**: against the fully-sampled / full-dose reference, with a downstream
  diagnostic metric.

---

## Choosing among these
Paired translation → **Pix2Pix** (`/model-scaffold --task synthesis`). Unpaired → **CycleGAN**
(validate for hallucination). Conditioned on a map / augmentation → **SPADE**. Highest fidelity,
compute available → **diffusion** (MONAI generative). Reconstruction / denoising → **U-Net /
unrolled / fastMRI baselines**. In every case, **image-fidelity metrics are not enough** — add a
downstream-task or reader validation and disclose hallucination risk. Record the choice + paper,
hand to `/model-scaffold`, validate with `/model-validation` (and the `image_synthesis` probe).
