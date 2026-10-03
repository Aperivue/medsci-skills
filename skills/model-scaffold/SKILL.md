---
name: model-scaffold
description: Use when you need a runnable PyTorch training repo for a medical-imaging task (segmentation, classification, detection, synthesis, self-supervised, or fine-tuning a pretrained backbone). Emits a patient-level seed-locked split, train/evaluate scripts, config and a Methods stub.
metadata:
  triggers: "model scaffold, scaffold a model, training repo, PyTorch repo, build a model, train a model, fine-tune, finetune, transfer learning, pretrained backbone, MedSAM, SAM adaptation, segmentation, classification, detection, image synthesis, self-supervised, SimCLR, Pix2Pix, Faster R-CNN, U-Net, UNet, nnU-Net, MONAI, timm, torchvision, dataloader, train.py, patient-level split, reproducible training, seed everything, generate training code, medical imaging model"
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

It is the **missing middle link** in the lane: `/model-selection` (choose) → **model-scaffold (build)**
→ `/model-assessment` (validate the split / design, compute metrics) → `/analyze-stats`
→ `/write-paper` + `/check-reporting` (publish). It **integrates** MONAI / nnU-Net / TorchIO (referenced
in the generated `requirements.txt`); it does not reimplement them.

## When to use
- You have a data manifest (one row per image, with a patient/subject ID) and want a reproducible,
  leakage-safe starting repo for a segmentation model.
- You want to **fine-tune a pretrained backbone** (transfer learning — the common clinician workflow:
  a `timm` / MONAI / MedSAM checkpoint adapted to your collected clinical data) with the freeze schedule,
  discriminative learning rates, and pretrained-weight provenance recorded (`--task finetune`).

## When NOT to use
- Auditing an already-trained model's validation design → `/model-assessment`.
- Held-out metrics / calibration / bootstrap CIs → `/model-assessment` then `/analyze-stats`.
- Choosing the architecture for the research question → `/model-selection` (when available).
- Reimplementing MONAI / nnU-Net → out of scope (the scaffold integrates them).
- LLM / MLLM evaluation → `/mllm-eval`.

## Workflow

### Phase 1 — Prepare the manifest
A CSV with **one row per image** and a **patient/subject ID** column (`patient_id` / `subject_id` /
`case_id`), plus image and label path columns. The ID column is load-bearing: the split is done at the
patient level off this column. IDs are compared after stripping surrounding whitespace (`P01` and
`P01 ` are one patient), in the split and in the generated `dataset.py` alike.

### Phase 2 — Generate the repo
```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/scaffold.py \
  --manifest <manifest.csv> --task segmentation --out model_repo --seed 42 \
  --in-channels 1 --out-channels 1
# --task = segmentation | classification | detection | synthesis | ssl | finetune
#   (out-channels = num classes for classification/finetune, target channels for synthesis;
#    finetune uses a softmax CrossEntropy head, so it refuses --out-channels < 2 — binary = 2)
# fine-tuning a pretrained backbone (transfer learning) on collected clinical data:
python3 ${CLAUDE_SKILL_DIR}/scripts/scaffold.py \
  --manifest <manifest.csv> --task finetune --out model_repo --seed 42 \
  --out-channels <num_classes> --from-pretrained timm:resnet50.a1_in1k
#   emits PRETRAINED.md (provenance) + a frozen→unfrozen train.py with discriminative LRs;
#   record the exact pretrained source so the fine-tune is reproducible. build_model(pretrained=True)
#   raises if timm is missing (never a silent random-init stand-in); best.pt records backbone_class.
# reuse the split /imaging-data's preprocessing gate checked (do not draw a new one):
python3 ${CLAUDE_SKILL_DIR}/scripts/scaffold.py \
  --manifest <manifest.csv> --preprocessing-manifest preprocessing_manifest.json --out model_repo
#   copies its split_assignment + split_seed into splits/, reading rows with the gate's own rules
#   (patient key patient_id/subject_id/patient/id; split synonyms such as training/validation/holdout);
#   exits 2 if a manifest patient has no split there, a patient sits in two splits, a split does not
#   map to train/val/test, or split_seed is absent.
```

**The imaging-data QC handoff is enforced, not advisory.** With `--preprocessing-manifest` the
scaffold also reads `/imaging-data`'s gate reports (`check_dataset_profile`,
`check_preprocessing_leakage`, `check_normalizer_domain` JSON) from `<manifest dir>/qc/` and
`<manifest dir>/../qc/` (the manifest path is resolved first). `--imaging-qc <file|dir>` (repeatable)
**replaces** that search: pointed at an empty directory, every gate is recorded NOT ASSESSED. A
leakage report is skipped only when its recorded manifest path resolves to a different existing file
(the reason is shown); an ambiguous one is read.
- A **Major** claim — or any severity that is not plainly Minor/Flag, or a report whose
  `summary.n_major` exceeds its listed Majors — refuses: exit 1, nothing written, each code + report
  listed. Resolve it upstream and re-run the gate, or pass `--ack-qc CODE='reason'` once per code.
- **Minor / Flag** claims never block; they are carried forward as warnings.
- A gate with no readable report is **NOT ASSESSED**; an unparseable or off-shape file in `qc/` is
  listed as UNREADABLE (stderr + record), never dropped.

All of it lands in `model_repo/IMAGING_QC.md`, referenced from `config.yaml` (`imaging_qc:`) and
`REPRODUCIBILITY.md`, so training, evaluation and the Methods read what `/imaging-data` found. Never
write an `--ack-qc` reason the user has not given. Without either flag the output is unchanged.
This writes `model_repo/` with `config.yaml`, `model.py` (the task's model — U-Net / CNN / Faster R-CNN
/ Pix2Pix / SimCLR encoder), `dataset.py` (reads the frozen split), `losses.py` (task-appropriate),
`train.py`, `evaluate.py`, `requirements.txt`,
`REPRODUCIBILITY.md`, `methods_stub.md` (+ `IMAGING_QC.md` when imaging-data outputs are given), and — the key artifact — `splits/split_assignment.csv` +
`splits/split_seed.txt`. The split is **patient-disjoint by construction** (a deterministic group split)
and the emitted code seeds every RNG, sets cuDNN deterministic, builds the training loader from the
**train split only**, and infers under `model.eval()` + `torch.no_grad()`.

### Phase 3 — Verify the build (network-free)
```bash
# this skill's own training-hygiene gate
python3 ${CLAUDE_SKILL_DIR}/scripts/check_training_hygiene.py --repo model_repo --strict
# the split-leakage gate (proves patient disjointness) — owned by /model-assessment
```
Route the emitted `splits/split_assignment.csv` to `/model-assessment`
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
Hand off to `/model-assessment` (validation-tier + comparator + metric-selection audit; Dice +
HD95/NSD with CIs) + `/analyze-stats`, `/make-figures`, and `/write-paper`
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
  every number must come from the user's executed run and from `/model-assessment` + `/analyze-stats`.
- **Never emit a split that is not patient-disjoint or not seed-locked.** The generator does this by
  construction; do not hand-edit the split table to introduce overlap or remove the seed.
- **Never claim the generated repo was trained or that it achieved a result** — it is a starting point
  the user runs.
- If a library API, default, or architecture detail is uncertain, flag `[VERIFY]` and ask rather than
  guessing.

## Deterministic gates
- `scripts/scaffold.py` — the generator (stdlib + numpy; deterministic given manifest + seed); also
  the imaging-data QC handoff (`tests/test_imaging_qc_handoff.sh`).
- `scripts/check_training_hygiene.py` — AST linter: all RNGs seeded, cuDNN deterministic,
  `eval()` + `no_grad()` inference, no training on a non-train split, and (fine-tuning) a
  recorded pretrained-weight provenance when pretrained weights are loaded
  (`PRETRAINED_PROVENANCE_MISSING`).
- `scripts/scaffold_challenge/verify.sh` — the build → validate chain, network-free (torch tier
  self-skips).

### Known limits of `check_training_hygiene.py`
- It counts seeding / cuDNN / `eval()` / `no_grad()` only in code a run reaches from the script's
  import-time statements. A file with no import-time call into its own functions is entered through
  every public top-level function nothing references, so an uncalled public `seed_everything` in such
  a file still counts. Every decorated function or method (a click/typer command, a route, a
  `@staticmethod`) is also an entry point, so an uncalled decorated seeding helper still counts.
- It does not check statement order: inference placed before `model.eval()` in the same function is
  not detected.
- `--repo` without `train.py` / `evaluate.py` reports those checks as NOT CHECKED; with `--strict`
  it exits 2 rather than clearing them.
- Dataset variables are resolved by one name-to-split map for the whole file (later assignment in
  source order wins, across functions), not per scope; a shuffled loader that combines train with
  val only (a train+val refit) is not flagged.

## Boundaries

```
model-selection (choose)
  └─ model-scaffold (this skill: generate the reproducible repo)
       ├─ check_training_hygiene.py   (training-code hygiene)
       ├─ model-assessment -> analyze-stats   (split-leakage proof, validation design, metrics + CIs)
       └─ write-paper + check-reporting        (Methods stub -> compliant manuscript)
```
