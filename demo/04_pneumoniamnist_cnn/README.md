# Demo 4 — PneumoniaMNIST CNN (model-engineering lane, end to end)

A worked example of the MedSci Skills **model-engineering lane** — the deep-learning counterpart to
Demos 1–3 (which cover the classical-stats / manuscript pipeline). It runs the lane end to end on a public
benchmark: **architecture choice → scaffold → data-stage & split & hygiene gates → 3-seed training →
held-out evaluation → calibration → Grad-CAM interpretability → write-up**. Every number is produced by an
executed run; none is hand-entered. **Tooling demonstration, not a clinical claim.**

## Dataset
PneumoniaMNIST (MedMNIST v2, CC BY 4.0; Yang et al. 2023), 28×28 chest-radiograph images, official
image-level split. Auto-downloaded by the `medmnist` package — no data is vendored here.

## Results (from `results/results.json`)
| Metric | Value |
|---|---|
| Test AUROC (3 seeds) | **0.964 ± 0.004** |
| Ensemble AUROC (95% CI) | **0.969 (0.956–0.980)** |
| Ensemble AUPRC (95% CI) | 0.980 (0.970–0.988) |
| ECE / Brier | 0.127 / 0.103 |
| Grad-CAM Adebayo sanity | model-rand r −0.07, label-perm r −0.03 (pass) |

Gates (outputs in `qc/`): split-leakage **OK**, training-hygiene **OK**, explainability-report **OK**.

## Layout
- `pipeline/` — the scaffolded, hygiene-clean code (dataset, model, losses, train, experiment, evaluate,
  explain, make_figs, build_split, config, requirements).
- `results/` — `results.json` (SSOT) + per-seed / ensemble predictions + calibration + explainability.
- `figures/` — training curve, ROC (+CI), reliability, Grad-CAM panel.
- `manuscript/` — `writeup.md` + `title_page.md` + `refs.bib` (references verified via `/verify-refs`).
- `qc/` — gate outputs (`split_leakage.json`, `training_hygiene.json`, `explainability_report.json`),
  `self_review.md`, `reference_audit.json`.

## Reproduce
```bash
python3 -m venv .venv && . .venv/bin/activate     # Python 3.11–3.13 (torch has no 3.14 wheel yet)
pip install -r pipeline/requirements.txt matplotlib captum
bash reproduce.sh                                  # gates → 3-seed train → evaluate → calibration/XAI → figures
```
Runs in minutes on a laptop GPU (CUDA or Apple MPS) or on CPU. Results reproduce up to backend
non-determinism (bounded by the reported seed SD).
