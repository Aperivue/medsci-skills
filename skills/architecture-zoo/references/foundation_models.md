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

---

## Choosing among these
Many unlabelled scans + few labels → **SSL pretrain (DINO/MAE/SimCLR) → fine-tune**, and
report the label-efficiency curve. Need masks now, no budget → **TotalSegmentator (CT) /
MedSAM2 (interactive)**. Zero-shot classification/retrieval → **BiomedCLIP**. In every case
keep the pretraining/transfer corpus disjoint from the test patients and disclose
model-derived labels. Record the choice + paper, then hand the fine-tuning to
`/model-scaffold` and validate with `/model-validation`.
