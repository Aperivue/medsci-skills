# MLOps wiring guide (model-scaffold)

Load-on-demand notes for taking a scaffolded repo through a **reproducible, reportable**
training run. This is a **wiring and reporting** reference, **not** a training-loop,
hyperparameter-search, or experiment-tracking reimplementation. Training and tracking stay
with the frameworks — MONAI / nnU-Net / timm for the model, Weights & Biases / MLflow /
TensorBoard for tracking, DVC / git-lfs for data — and this guide covers how to wire them so
the run is reproducible and what to record so a reviewer can trust it. Everything here points
to a framework; nothing here replaces one (the [ROADMAP out-of-scope clause](../../../ROADMAP.md)).

## The reproducibility contract (what a run must be able to reproduce)
A training run is reproducible when, from the recorded artifacts alone, someone else can
re-derive the same result. That needs five things pinned, all of which the scaffold already
emits a slot for:
1. **Code** — the git commit of the repo (dirty trees are not reproducible; commit first).
2. **Config** — `config.yaml` as the single source of truth (task, arch, channels, split
   fractions, seed). Do not scatter hyperparameters across the CLI and the code.
3. **Data** — a content hash of the exact dataset (see `/version-dataset`), not just a path.
4. **Seed + determinism** — the scaffold's `seed_everything` seeds Python / NumPy / torch /
   CUDA and sets cuDNN deterministic; record the seed in the tracker and `REPRODUCIBILITY.md`.
5. **Environment** — a pinned `requirements.txt` (exact versions), CUDA / driver, GPU model.

## Experiment tracking (integrate, don't build one)
Log to **W&B**, **MLflow**, or **TensorBoard** — pick one, do not write a tracker. At run
start, log the whole `config.yaml`, the git commit, the dataset hash, and the seed as the run
config; during training log per-epoch train/val loss + the val metric; at the end log the best
checkpoint as an artifact. The tracker's run URL / ID becomes part of the Methods record. Keep
the scaffold's contract intact — the best model is still selected on the **val** split, the
**test** split is still touched once by `evaluate.py`.

## Config management
The emitted `config.yaml` is the SSOT for one run. For sweeps, drive them with **Hydra /
OmegaConf** (or the tracker's sweep feature) that *reads* this config — never hand-edit values
into `train.py`. A hyperparameter that isn't in the config isn't reproducible.

## Data & model versioning
- **Data** — hash the training set with `/version-dataset` and record the manifest hash in the
  run config, so "trained on dataset X" is verifiable, not asserted. For large data use **DVC**
  or **git-lfs**; commit the pointer, not the pixels.
- **Model** — document the trained model with `/model-card` (Model Card + Datasheet); for a
  fine-tune, the pretrained-weight provenance lives in `PRETRAINED.md`
  (see `references/finetuning_guide.md`).

## Environment capture
Pin `requirements.txt` to exact versions before publishing (`pip freeze`, or a `conda env
export`). For a hard reproducibility guarantee, a Dockerfile / container digest removes "works
on my machine". Record the CUDA / driver / GPU — some GPU ops are non-deterministic even with
cuDNN deterministic set, which is why metrics are reported as **mean ± SD over ≥ 3 seeds**, not
a single run.

## Pipeline orchestration — use the framework's, not a new one
For segmentation, **nnU-Net** owns preprocessing → training → inference as a pipeline; build
its `dataset.json` folds from the scaffold's `splits/split_assignment.csv` so the patient-level
split is preserved end to end. **MONAI bundles** package a model + transforms + metadata the
same way. Orchestrate with the framework's own pipeline; do not rebuild one.

## CI for an ML repo (what is worth gating)
CI should gate the **network-free, deterministic** properties — not full training. The scaffold
already ships these: `check_training_hygiene` (seeds, eval-mode inference, train-only loaders,
pretrained provenance) and the split-leakage proof (`/model-validation`). Add a **forward-pass
smoke** (build the model, one batch, check output shape) as a fast job. Do **not** put a real
training run in CI — it is slow, non-deterministic, and not what CI is for.

## What to report (the MLOps reporting checklist)
State, in Methods or a reproducibility appendix: the **compute environment** (framework +
versions, CUDA / driver, GPU), the **seed(s)** and that metrics are mean ± SD over ≥ 3 seeds,
the **config** (as a supplement or a tracker link), the **dataset version** (`/version-dataset`
hash), and the **tracking run** URL / ID. This is the reproducibility half of TRIPOD+AI /
CLAIM 2024; `/check-reporting` covers the items.

## Hand-offs
- Dataset hash / reproducibility-lock → `/version-dataset`.
- Model + dataset documentation → `/model-card`.
- Split / validation-design audit → `/model-validation`.
- Held-out metrics + CIs → `/model-evaluation` → `/analyze-stats`.
- Deployment uncertainty / OOD / monitoring → `/uncertainty-imaging`.
- Reporting fit → `/check-reporting` (TRIPOD+AI / CLAIM / DECIDE-AI).
