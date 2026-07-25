# Foundation models & self-supervised pretraining (architecture-zoo)

For "I have few labels / many unlabelled scans" or "adapt a released medical model" — the
label-efficient route. Two sub-families: **self-supervised pretraining** (learn features
from unlabelled data, then fine-tune) and **released foundation models** (use or prompt
existing weights). All listed weights are open / permissively licensed; verify the licence
before vendoring (the lane's `distill.py` firewall rules apply if you reuse code).

Each card: **paper → core idea → when to use → medical-imaging use → reference impl →
validation/experiment setup.**

---

## Self-supervised pretraining (label-efficient features)

### SimCLR / MoCo (contrastive)
- **Papers**: Chen et al., SimCLR, *ICML* 2020; He et al., MoCo, *CVPR* 2020.
- **Core idea**: pull augmented views of the same image together, push different images apart
  (contrastive); MoCo adds a momentum encoder + queue for many negatives.
- **When to use**: a large **unlabelled** medical pool + a small labelled set; pretrain on the
  unlabelled scans, then fine-tune the backbone on labels.
- **Medical-imaging use**: contrastive CXR pretraining (e.g. CheSS-style) before multi-label
  fine-tuning.
- **Reference impl**: `lightly`, MONAI SSL tutorials; public SimCLR/MoCo repos.
- **Validation setup**: report the **label-efficiency curve** (downstream metric vs. number
  of labels) to justify the pretraining; keep the pretraining pool disjoint from the test
  patients (contamination — `/model-validation` MD1).

### DINO / DINOv2 (self-distillation) and MAE (masked autoencoding)
- **Papers**: Caron et al., DINO, *ICCV* 2021; Oquab et al., DINOv2, 2023; He et al., MAE,
  *CVPR* 2022.
- **Core idea**: DINO self-distills (student/teacher) to learn strong ViT features without
  labels; MAE masks most patches and reconstructs them. Both yield transferable ViT backbones.
- **When to use**: pretraining ViT/Swin backbones on unlabelled medical images; DINOv2-style
  features transfer well with linear probing.
- **Medical-imaging use**: **RAD-DINO** (chest-X-ray DINOv2 backbone) and similar domain
  pretrainings.
- **Reference impl**: official DINO/DINOv2/MAE repos; `timm` for the ViT backbones.
- **Validation setup**: linear-probe + fine-tune comparison; same contamination discipline.

---

## Released foundation models (use / prompt existing weights)

### SAM → MedSAM / MedSAM2 / SAM-Med2D (promptable segmentation)
- **Papers**: Kirillov et al., Segment Anything (SAM), *ICCV* 2023; Ma et al., MedSAM,
  *Nature Communications* 2024; MedSAM2 (2025) for 3-D + video.
- **Core idea**: a promptable segmentation foundation model (point/box/text prompt → mask);
  the medical variants fine-tune SAM on large medical corpora.
- **When to use**: **few-shot / interactive** segmentation, annotation acceleration, or a
  strong zero-/low-shot baseline before training a dedicated U-Net.
- **Medical-imaging use**: prompt-driven lesion/organ masks across CT/MR/US/path/endoscopy;
  speeding up labelling for a downstream U-Net.
- **Reference impl**: `segment-anything`; OpenMedLab MedSAM / MedSAM2 (Apache-2.0).
- **Validation setup**: report performance **by prompt type** and whether prompts were
  human or automated; for a fully-automatic claim, no oracle prompts at test time.

### Interactive 3-D promptable segmentation — nnInteractive / VISTA3D / SAM-Med3D (labelling acceleration)
- **Papers/tools**: nnInteractive (Isensee et al., DKFZ, 2025); VISTA3D (NVIDIA / Project-MONAI,
  2024–25); SAM-Med3D (Wang et al., 2023); MedSAM2 / SAM2 (Meta SAM2, 2024) for 3-D + video.
- **Core idea**: **native-3-D** promptable models — a click / scribble / box / lasso on a few
  slices yields the whole volumetric mask — trained on many 3-D datasets, so they generalise
  across organs and modalities without task-specific training. (2-D SAM/MedSAM applied
  slice-by-slice loses through-plane coherence; these are built for the volume.)
- **When to use**: the **labelling-throughput lever**. When expert 3-D labels are the
  bottleneck (e.g. neuro-faculty ground truth), an interactive model turns from-scratch
  hand-segmentation into a **prompt-and-correct** pass — often several-fold faster per case.
  Also a strong zero-training 3-D baseline, or an interactive tool in the reading loop.
- **Medical-imaging use**: expert-in-the-loop CT/MR volume labelling; semi-automatic organ /
  lesion / vessel masks that seed the training set a dedicated nnU-Net then learns.
- **Reference impl**: `MIC-DKFZ/nnInteractive` (fast; point/scribble/box/lasso),
  `Project-MONAI/VISTA` (VISTA3D), `uni-medical/SAM-Med3D`. **Licence — check before
  commercial use**: nnInteractive **code is Apache-2.0 but its released weights are
  CC BY-NC-SA 4.0 (non-commercial)**; confirm the VISTA3D and SAM-Med3D *weight* licences too
  (bundled model licences often differ from the code repo). This matters when the labels feed
  a product, not only a paper.
- **Validation setup**: masks produced this way are **silver labels** — an expert must
  correct/adjudicate them, and model-derived labels must not evaluate the same or a related
  model (circularity — `/model-validation` MD8). Report the **human-correction effort**
  (edits or time per case), not only the final Dice.

### TotalSegmentator / SegVol (automatic CT organ masks)
- **Papers**: Wasserthal et al., TotalSegmentator, *Radiology: AI* 2023; SegVol (2024).
- **Core idea**: released models that segment 100+ anatomical structures from CT
  automatically (TotalSegmentator) / with semantic+spatial prompts (SegVol).
- **When to use**: you need organ/structure masks on CT and have **no training budget** —
  run it, no labels required; also a strong anatomical prior for downstream tasks.
- **Reference impl**: `TotalSegmentator` (Apache-2.0).
- **Validation setup**: if you use its masks as input or weak labels, disclose that the
  reference standard is **model-derived** (silver labels) — do not let model-derived labels
  evaluate the same model (circularity — `/model-validation` MD8).

### BiomedCLIP / PubMedCLIP (cross-modal retrieval + zero-shot)
- **Papers**: Zhang et al., BiomedCLIP, 2023 (15M biomedical image–text pairs).
- **Core idea**: a CLIP-style image–text model → zero-shot classification and image–text
  retrieval without task labels.
- **When to use**: zero-shot classification, retrieval, or as a pretrained image encoder when
  labels are scarce.
- **Reference impl**: Microsoft BiomedCLIP (Hugging Face).
- **Validation setup**: zero-shot claims need a **held-out / post-cutoff** set and a
  contamination statement (the pretraining corpus may overlap public benchmarks).

### Domain-specific medical foundation backbones (RETFound / UNI / CONCH / RAD-DINO / Merlin)
- **Papers/tools**: RETFound (Zhou et al., *Nature* 2023 — retinal SSL backbone); UNI +
  CONCH (Chen / Lu et al., *Nature Medicine* 2024 — pathology, UNI a vision backbone, CONCH a
  vision–language model); RAD-DINO (Microsoft — chest-X-ray DINOv2); Merlin (Stanford — a
  3-D abdominal-CT foundation model).
- **Core idea**: organ-/modality-specific backbones pretrained on large **domain** corpora →
  **fine-tune or linear-probe** for your task with far fewer labels than training from
  scratch or transferring from ImageNet. The domain counterpart to the general SSL backbones
  above.
- **When to use**: your task sits in one of these domains (retina, pathology WSI, chest
  X-ray, abdominal CT) and labels are scarce — start from the domain FM, not ImageNet.
- **Reference impl**: `rmaphoh/RETFound_MAE`, `mahmoodlab/UNI`, `mahmoodlab/CONCH`,
  `StanfordMIMI/Merlin` (GitHub + Hugging Face).
- **Licence — the recurring gotcha (verified)**: **most medical-FM weights are non-commercial
  / gated research licences.** RETFound, UNI and CONCH ship custom CC-BY-NC-style terms and
  gate access on Hugging Face; Merlin's *code* is MIT but confirm its *weight* terms. Verify
  per model before anything beyond a paper — a product cannot ship on CC-BY-NC weights (same
  trap as nnInteractive / ConvNeXt V2).
- **Validation setup**: keep the FM's pretraining corpus disjoint from your test patients
  (many public benchmarks sit inside these corpora — contamination, `/model-validation`
  MD1/MD3); report the **label-efficiency curve** to justify the transfer.

---

## Choosing among these
Many unlabelled scans + few labels → **SSL pretrain (DINO/MAE/SimCLR) → fine-tune**, and
report the label-efficiency curve. Need masks now, no budget → **TotalSegmentator (CT) /
MedSAM2 (interactive)**. Accelerate expert 3-D labelling → **interactive FM (nnInteractive /
VISTA3D)** — mind the non-commercial weight licence. Task in a covered domain (retina /
pathology / CXR / abdominal CT) + few labels → **domain FM transfer (RETFound / UNI / CONCH /
Merlin)** — most weights are non-commercial / gated, verify before a product. Zero-shot
classification/retrieval → **BiomedCLIP**. In every case
keep the pretraining/transfer corpus disjoint from the test patients and disclose
model-derived labels. Record the choice + paper, then hand the fine-tuning to
`/model-scaffold` and validate with `/model-validation`.
