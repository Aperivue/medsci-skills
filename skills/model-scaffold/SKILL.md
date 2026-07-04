---
name: model-scaffold
description: >
  Generate a reproducible, runnable PyTorch training repo for a medical-imaging task — segmentation,
  classification, detection, image-to-image synthesis, self-supervised pretraining, or fine-tuning a
  pretrained backbone (transfer learning) — the missing middle link between choosing an architecture and
  validating a trained model. Emits a patient-level seed-locked split as an auditable artifact, a
  task-appropriate model, train and evaluate scripts that seed every RNG and infer under eval mode, a
  config, requirements, a reproducibility record, and a Methods stub with VERIFY placeholders (no
  fabricated numbers). Fine-tuning mode adds a frozen-then-unfrozen schedule, discriminative learning
  rates, and a pretrained-weight provenance record. The reproducibility guarantees hold by construction,
  so the build is leakage-safe before any training runs. Integrates with MONAI, nnU-Net, TorchIO, timm,
  and torchvision — it does not reimplement them.
triggers: model scaffold, scaffold a model, training repo, PyTorch repo, build a model, train a model, fine-tune, finetune, transfer learning, pretrained backbone, MedSAM, SAM adaptation, segmentation, classification, detection, image synthesis, self-supervised, SimCLR, Pix2Pix, Faster R-CNN, U-Net, UNet, nnU-Net, MONAI, timm, torchvision, dataloader, train.py, patient-level split, reproducible training, seed everything, generate training code, medical imaging model
tools: Read, Write, Edit, Bash, Grep, Glob
model: inherit
---

# Model-Scaffold Skill

## Purpose

This skill stamps out a **runnable PyTorch training repo** for a medical-imaging task — `--task`
**segmentation** (U-Net), **classification** (CNN / `timm` backbone), **detection** (torchvision Faster
R-CNN / FPN), **synthesis** (Pix2Pix generator + PatchGAN), **ssl** (SimCLR encoder), or **finetune**
(transfer-learning a pretrained backbone with a frozen→unfrozen schedule + a provenance record) —
with the reproducibility guarantees **baked in by construction** — so the build is leakage-safe and
reproducible before a single epoch runs. It is the imaging analogue of how `/analyze-stats` generates
runnable statistical code: the generator produces the repo, you run the training on your GPU / Colab,
and the lane's deterministic gates verify the network-free parts.

It is the **missing middle link** in the lane: `/architecture-zoo` (choose) → **model-scaffold (build)**
→ `/model-validation` (validate the split / design) → `/model-evaluation` + `/analyze-stats` (metrics)
→ `/write-paper` + `/check-reporting` (publish). It **integrates** MONAI / nnU-Net / TorchIO (referenced
in the generated `requirements.txt`); it does not reimplement them.

## When to use
- You have a data manifest (one row per image, with a patient/subject ID) and want a reproducible,
  leakage-safe starting repo for a segmentation model.
- You want to **fine-tune a pretrained backbone** (transfer learning — the common clinician workflow:
  a `timm` / MONAI / MedSAM checkpoint adapted to your collected clinical data) with the freeze schedule,
  discriminative learning rates, and pretrained-weight provenance recorded (`--task finetune`).

## When NOT to use
- Auditing an already-trained model's validation design → `/model-validation`.
- Held-out metrics / calibration / bootstrap CIs → `/model-evaluation` then `/analyze-stats`.
- Choosing the architecture for the research question → `/architecture-zoo` (when available).
- Reimplementing MONAI / nnU-Net → out of scope (the scaffold integrates them).
- LLM / MLLM evaluation → `/mllm-eval`.

## Workflow

### Phase 1 — Prepare the manifest
A CSV with **one row per image** and a **patient/subject ID** column (`patient_id` / `subject_id` /
`case_id`), plus image and label path columns. The ID column is load-bearing: the split is done at the
patient level off this column.

### Phase 2 — Generate the repo
```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/scaffold.py \
  --manifest <manifest.csv> --task segmentation --out model_repo --seed 42 \
  --in-channels 1 --out-channels 1
# --task = segmentation | classification | detection | synthesis | ssl | finetune
#   (out-channels = num classes for classification/finetune, target channels for synthesis)
# fine-tuning a pretrained backbone (transfer learning) on collected clinical data:
python3 ${CLAUDE_SKILL_DIR}/scripts/scaffold.py \
  --manifest <manifest.csv> --task finetune --out model_repo --seed 42 \
  --out-channels <num_classes> --from-pretrained timm:resnet50.a1_in1k
#   emits PRETRAINED.md (provenance) + a frozen→unfrozen train.py with discriminative LRs;
#   record the exact pretrained source so the fine-tune is reproducible.
```
This writes `model_repo/` with `config.yaml`, `model.py` (the task's model — U-Net / CNN / Faster R-CNN
/ Pix2Pix / SimCLR encoder), `dataset.py` (reads the frozen split), `losses.py` (task-appropriate),
`train.py`, `evaluate.py`, `requirements.txt`,
`REPRODUCIBILITY.md`, `methods_stub.md`, and — the key artifact — `splits/split_assignment.csv` +
`splits/split_seed.txt`. The split is **patient-disjoint by construction** (a deterministic group split)
and the emitted code seeds every RNG, sets cuDNN deterministic, builds the training loader from the
**train split only**, and infers under `model.eval()` + `torch.no_grad()`.

### Phase 3 — Verify the build (network-free)
```bash
# this skill's own training-hygiene gate
python3 ${CLAUDE_SKILL_DIR}/scripts/check_training_hygiene.py --repo model_repo --strict
# the split-leakage gate (proves patient disjointness) — owned by /model-validation
```
Route the emitted `splits/split_assignment.csv` to `/model-validation`
(`check_split_leakage.py --splits model_repo/splits/split_assignment.csv --strict`) for the
patient-disjointness proof, and (optionally, locally with torch installed)
`bash ${CLAUDE_SKILL_DIR}/scripts/scaffold_challenge/verify.sh` to smoke the forward pass.

### Phase 4 — Plug in your data and train
Implement `dataset.py`'s `_load_image` / `_load_label` for your modality (DICOM / NIfTI / TIFF via
nibabel / pydicom / tifffile / TorchIO / MONAI transforms). For production, swap `model.py` for MONAI
`UNet` / `SegResNet` or an nnU-Net plan (see `${CLAUDE_SKILL_DIR}/references/training_guide.md`). For a
fine-tuning repo (`--task finetune`), fill `PRETRAINED.md` and set the freeze schedule / discriminative
learning rates (see `${CLAUDE_SKILL_DIR}/references/finetuning_guide.md`, which also covers MedSAM/SAM
adaptation and train-only diffusion augmentation). Run `python train.py` (best model selected on the
**val** split), then `python evaluate.py` (predictions on the **test** split, touched once).

### Phase 5 — Validate, evaluate, publish
Hand off to `/model-validation` (validation-tier + comparator + metric-selection audit),
`/model-evaluation` + `/analyze-stats` (Dice + HD95/NSD with CIs), `/make-figures`, and `/write-paper`
(fill the `methods_stub.md` `[VERIFY]` placeholders) + `/check-reporting` (CLAIM 2024 / TRIPOD+AI). For
reproducibility-safe wiring of experiment tracking (W&B / MLflow), config / data / environment
versioning, and the MLOps reporting checklist, see `${CLAUDE_SKILL_DIR}/references/mlops_guide.md`
(a wiring + reporting reference — it points to the frameworks, it does not replace them).

## Runnability — honest contract
The generated repo is **runnable**, but runnability is **not a CI guarantee**. The default gates prove
the network-free properties (the emitted split is patient-disjoint + seeded; the emitted training code
is hygienic) by parsing the produced artifacts — no torch is executed. A torch forward-pass smoke
(`build + forward shape + gradients flow + reproducible loss`) is a **self-skipping** tier in the
challenge `verify.sh` and a documented local command; it is never counted as CI coverage of
runnability.

## Anti-Hallucination

- **Never fabricate training or evaluation metrics.** The scaffold emits `[VERIFY]` placeholders;
  every number must come from the user's executed run and from `/model-evaluation` + `/analyze-stats`.
- **Never emit a split that is not patient-disjoint or not seed-locked.** The generator does this by
  construction; do not hand-edit the split table to introduce overlap or remove the seed.
- **Never claim the generated repo was trained or that it achieved a result** — it is a starting point
  the user runs.
- If a library API, default, or architecture detail is uncertain, flag `[VERIFY]` and ask rather than
  guessing.

## Deterministic gates
- `scripts/scaffold.py` — the generator (stdlib + numpy; deterministic given manifest + seed).
- `scripts/check_training_hygiene.py` — AST linter: all RNGs seeded, cuDNN deterministic,
  `eval()` + `no_grad()` inference, no training on a non-train split, and (fine-tuning) a
  recorded pretrained-weight provenance when pretrained weights are loaded
  (`PRETRAINED_PROVENANCE_MISSING`).
- `scripts/scaffold_challenge/verify.sh` — the build → validate chain, network-free (torch tier
  self-skips).

## Boundaries

```
architecture-zoo (choose)
  └─ model-scaffold (this skill: generate the reproducible repo)
       ├─ check_training_hygiene.py   (training-code hygiene)
       ├─ model-validation            (split-leakage proof + validation design)
       ├─ model-evaluation -> analyze-stats   (metrics + CIs)
       └─ write-paper + check-reporting        (Methods stub -> compliant manuscript)
```
