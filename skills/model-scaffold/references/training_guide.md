# Training guide (model-scaffold)

Load-on-demand notes for taking a scaffolded repo to a trained, publishable model. The
scaffold gives you a leakage-safe, reproducible skeleton; this guide covers the
decisions it deliberately leaves to you.

## Swap the model for a production backbone
The emitted `model.py` is a small, CPU-runnable U-Net for the forward-pass smoke test.
For real work, integrate (do not reimplement):
- **MONAI** — `monai.networks.nets.UNet` / `SegResNet`, plus `monai.transforms` and
  `monai.metrics` (DiceMetric, HausdorffDistanceMetric, SurfaceDiceMetric). Keep the
  scaffold's `dataset.py` split-reading contract; replace the model + transforms.
- **nnU-Net (v2)** — for many segmentation tasks the strongest baseline. Use the
  scaffold's `splits/split_assignment.csv` to build the nnU-Net `dataset.json` folds so
  the patient-level split is preserved end to end.
- **3-D** — for volumetric CT/MR, switch to a 3-D U-Net / `SegResNet` and 3-D patches;
  use **TorchIO** for spatial/intensity augmentation.

## Augmentation — train split only
Apply augmentation to the **training** split only, never to val/test. Watch
modality-specific traps: do not horizontal-flip when laterality is a label; window CT
to a clinically sensible HU range before normalising; consider bias-field simulation
for MR. Fit any normalisation statistics on the **training** fold only (fitting on the
whole cohort is preprocessing-before-split leakage — see `/model-validation` MD1).

## Optimisation defaults that travel well
AdamW + a cosine or warmup schedule; gradient clipping for unstable losses; early
stopping / best-checkpoint on the **validation** split (never the test set); automatic
mixed precision (AMP) for speed. Report the metric as **mean ± SD over ≥ 3 seeds**, not
a single run (deep metrics move with seed/init; some GPU ops are non-deterministic even
with cuDNN deterministic set).

## Reproducibility record
Before publishing, complete `REPRODUCIBILITY.md`: pinned `requirements.txt`
(torch/monai/... exact versions), CUDA/driver, GPU model, the git commit of the repo,
and the seed. Pair with `/version-dataset` to hash the exact dataset the model trained
on. For reproducibility-safe wiring of experiment tracking (W&B / MLflow), config / data
/ environment versioning, CI-for-ML, and the MLOps reporting checklist, see
`mlops_guide.md`.

## Hand-offs
- Split / validation-design audit → `/model-validation` (run `check_split_leakage.py`
  on `splits/split_assignment.csv`).
- Held-out metrics (Dice + HD95/NSD, AUROC/AUPRC, calibration, CIs) → `/model-evaluation`
  then `/analyze-stats`.
- Figures (training curve, overlay, confusion) → `/make-figures`.
- Methods + reporting → `/write-paper` (fill the `[VERIFY]` placeholders) and
  `/check-reporting` (CLAIM 2024 / TRIPOD+AI / STARD-AI).
