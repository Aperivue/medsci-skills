# Fine-tuning guide (model-scaffold — `--task finetune`)

Load-on-demand notes for the target workflow of a clinician-researcher: **fine-tune an
existing pretrained model on collected clinical data**, rather than train from scratch or
design a new architecture. `scaffold.py --task finetune` emits a leakage-safe transfer-learning
repo (frozen→unfrozen schedule, discriminative learning rates, a `PRETRAINED.md` provenance
record); this guide covers the decisions it deliberately leaves to you.

## When to fine-tune (vs train from scratch)
Fine-tuning a pretrained backbone is the right default whenever the labelled clinical set is
small (hundreds–low-thousands of patients) — the regime almost every solo clinical study is
in. From-scratch training needs far more data to beat a fine-tuned ImageNet/medical backbone.
Pick the backbone in `/architecture-zoo`; adapt it here.

## The provenance record is load-bearing — `PRETRAINED.md`
A fine-tune is only reproducible if the **exact** pretrained weights are recorded. `--task
finetune` emits `PRETRAINED.md` with `[VERIFY]` fields; fill them before publishing:
- **Source** — the exact model + weights tag (`timm:resnet50.a1_in1k`, `MedSAM`, a URL/DOI),
  set via `--from-pretrained`.
- **Pretraining data** — the dataset the backbone was pretrained on. **Confirm it does not
  overlap this study's test set.** A backbone pretrained on (or including) your evaluation
  images is *pretraining-set contamination*: leakage that no train/val/test split table can
  see, because it entered through the weights, not the split. This is the fine-tuning analogue
  of benchmark contamination in LLM evaluation (`/mllm-eval`).
- **License**, **checkpoint hash** (sha256), **access date** — for auditability.

`check_training_hygiene.py` fires `PRETRAINED_PROVENANCE_MISSING` (Minor) when a training
script loads pretrained weights (`pretrained=True` / `from_pretrained`) but the repo carries
no `PRETRAINED.md` and no `pretrained:` block in `config.yaml`. The scaffold passes by
construction; a hand-rolled repo (a copied Kaggle notebook that does
`timm.create_model(..., pretrained=True)` and records nothing) fails.

## The frozen→unfrozen schedule
The emitted `train.py` implements the standard two-phase transfer schedule:
1. **Freeze the backbone, warm up the fresh head** for a few epochs (`FREEZE_EPOCHS`). The
   randomly-initialised head would otherwise back-propagate large gradients that damage the
   pretrained features.
2. **Unfreeze with discriminative learning rates** — a small learning rate for the pretrained
   backbone (`BACKBONE_LR`, e.g. 1e-5) and a larger one for the head (`HEAD_LR`, e.g. 1e-3).
   The backbone should *adapt*, not be overwritten.

Tune the two rates and `FREEZE_EPOCHS` per task. For very small datasets, keep more of the
backbone frozen (train only the last block + head) and lean on regularisation (weight decay,
dropout, strong but physiology-preserving augmentation, early stopping on the **val** split).

## BatchNorm and small clinical batches
Fine-tuning with small batches destabilises BatchNorm running statistics. Options: keep the
backbone's BN layers in `eval()` (frozen running stats) while the backbone is frozen; switch
to GroupNorm; or use a larger effective batch (gradient accumulation). Record the choice in
Methods — it materially affects reproducibility.

## MedSAM / SAM adaptation
Promptable foundation segmenters (SAM, **MedSAM**) are adapted, not retrained. The common,
solo-doable path is **adapter / decoder fine-tuning**: freeze the heavy image encoder and
fine-tune only the mask decoder (and optionally a lightweight adapter or the prompt encoder)
on your labelled masks. Integrate the upstream implementation
([MedSAM](https://github.com/bowang-lab/MedSAM),
[SAM](https://github.com/facebookresearch/segment-anything)) — do not reimplement it. Keep the
scaffold's split-reading contract (`splits/split_assignment.csv`) so the patient-level split
is preserved, and record the SAM/MedSAM checkpoint in `PRETRAINED.md`. Prompt design (points /
boxes / automatic) is part of the method — report it, and report whether prompts used any
ground-truth information at test time (a leakage trap unique to promptable models).

## Diffusion augmentation — train split only
A diffusion model can synthesise extra training images (an off-the-shelf augmentation, **not**
a novel method here). Two hard rules keep it leakage-safe:
1. **Any generative model used for augmentation must be trained on the TRAIN split only.** If
   the diffusion (or GAN) model saw val/test images, its samples leak that distribution into
   training — the generative analogue of fitting a normaliser on full data
   (`/preprocess-imaging` `NORMALIZATION_LEAKAGE`).
2. **Synthetic images augment TRAIN only, never val/test.** Evaluating on — or augmenting —
   the held-out split with synthetic data invalidates the metric. `check_preprocessing_leakage`
   flags `AUGMENTATION_ON_EVAL`; declare synthetic augmentation in the preprocessing manifest
   as `applies_to: ["train"]`.
Report the synthetic:real ratio and show the result holds without synthetic data (a sensitivity
analysis) — reviewers discount models propped up by synthetic training data.

## Reporting
Fill `methods_stub.md` and `PRETRAINED.md`, then hand off to `/write-paper` +
`/check-reporting`. Fine-tuning specifics reviewers expect: the pretrained source + its
pretraining data (contamination check), the freeze/unfreeze schedule and learning rates,
and — for SAM/MedSAM — the prompt protocol. Report held-out metrics as **mean ± SD over ≥ 3
seeds** (`/model-evaluation` → `/analyze-stats`); fine-tuning is seed-sensitive on small data.

## Hand-offs
- Backbone / architecture choice (incl. SAM/MedSAM, diffusion) → `/architecture-zoo`.
- Data-stage leakage (normalisation fit, augmentation-on-eval, slice crossing) →
  `/preprocess-imaging` (`check_preprocessing_leakage`).
- Split / validation-design audit → `/model-validation` (`check_split_leakage.py`).
- Held-out metrics + CIs → `/model-evaluation` → `/analyze-stats`.
- Provenance/model documentation → `/model-card` (Model Card + Datasheet).
