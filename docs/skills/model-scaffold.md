<!-- AUTO-GENERATED from skills/model-scaffold/SKILL.md by scripts/gen_skill_docs.py. Do not edit by hand. -->

# model-scaffold

> Generate a reproducible, runnable PyTorch training repo for a medical-imaging task — segmentation, classification, detection, image-to-image synthesis, self-supervised pretraining, or fine-tuning a pretrained backbone (transfer learning) — the missing middle link between choosing an architecture and validating a trained model. Emits a patient-level seed-locked split as an auditable artifact, a task-appropriate model, train and evaluate scripts that seed every RNG and infer under eval mode, a config, requirements, a reproducibility record, and a Methods stub with VERIFY placeholders (no fabricated numbers). Fine-tuning mode adds a frozen-then-unfrozen schedule, discriminative learning rates, and a pretrained-weight provenance record. The reproducibility guarantees hold by construction, so the build is leakage-safe before any training runs. Integrates with MONAI, nnU-Net, TorchIO, timm, and torchvision — it does not reimplement them.

**Invoke:** `/model-scaffold` · **Tools:** Read, Write, Edit, Bash, Grep, Glob · **Model:** inherit

## When to use

`model-scaffold` activates on requests such as: model scaffold, scaffold a model, training repo, PyTorch repo, build a model, train a model, fine-tune, finetune, transfer learning, pretrained backbone, MedSAM, SAM adaptation, segmentation, classification, detection, image synthesis, self-supervised, SimCLR, Pix2Pix, Faster R-CNN, U-Net, UNet, nnU-Net, MONAI, timm, torchvision, dataloader, train.py, patient-level split, reproducible training, seed everything, generate training code, medical imaging model.

## Quality Card

**Purpose** — Generate a leakage-safe, reproducible training repo for a medical-imaging model so the reproducibility guarantees (patient-disjoint seed-locked split, all-RNG seeding, cuDNN determinism, eval-mode inference) hold by construction rather than by hand-editing.

**Safety boundaries**

- The split is patient-level and seed-locked by construction (deterministic group split); the generator never emits an image-level or unseeded split.
- No metric is fabricated — methods_stub.md carries [VERIFY] placeholders; numbers come only from the user's executed training and from model-evaluation / analyze-stats.

**Known limitations**

- Runnability of the generated repo (build + forward pass) is verified by an optional local torch-cpu command, not by the default CI gate (which checks the network-free parts: split disjointness + training hygiene).
- Dataset I/O is a stub (the user plugs in their DICOM / NIfTI / TIFF reader); the generator does not read pixels.

**Validation**

- `python3 scripts/scaffold.py --manifest <manifest.csv> --out model_repo --seed 42`
- `python3 scripts/scaffold.py --manifest <manifest.csv> --task finetune --from-pretrained timm:resnet50.a1_in1k --out ft_repo --seed 42`
- `python3 scripts/check_training_hygiene.py --repo model_repo --strict`
- `bash scripts/scaffold_challenge/verify.sh  # deterministic, network-free (torch tier self-skips)`

**Evidence** — `ci_validator`

## Bundled resources

**References** (`skills/model-scaffold/references/`):

- `finetuning_guide.md`
- `training_guide.md`

**Scripts** (`skills/model-scaffold/scripts/`):

- `check_training_hygiene.py`
- `scaffold.py`
- `scaffold_challenge/` (4 files)

## Source

Canonical definition: [`skills/model-scaffold/SKILL.md`](../../skills/model-scaffold/SKILL.md)

---

*Part of [MedSci Skills](../../README.md) — Claude Code skills for the medical research lifecycle. This page is generated from the skill's `SKILL.md`; edit that file and re-run `scripts/gen_skill_docs.py`.*
