# Pipeline log — Demo 4 (PneumoniaMNIST CNN, model-engineering lane)

The lane run end to end on a laptop. Unlike Demos 1–3 this is not `orchestrate --e2e`; it is the
model-engineering lane, whose stages are architecture choice → scaffold → gates → training →
evaluation → calibration → interpretability → write-up.

| Step | Skill / script | Output | Result |
|---|---|---|---|
| Architecture choice | `/architecture-zoo` | — | small CNN, the scaffold default; chosen because the point is the pipeline, not the leaderboard |
| Scaffold | `/model-scaffold` (task: classification) | `pipeline/` | runnable repo with seeding, eval-mode inference and split construction baked in |
| Split | `pipeline/build_split.py` | `splits/split_assignment.csv` (regenerated, not vendored) | MedMNIST's official image-level split |
| **Split-leakage gate** | `/model-validation` `check_split_leakage.py --strict` | `qc/split_leakage.json` | **OK** — partitions disjoint by set arithmetic, seed recorded |
| **Training-hygiene gate** | `/model-scaffold` `check_training_hygiene.py --strict` | `qc/training_hygiene.json` | **OK** — every RNG seeded, cuDNN deterministic, inference under `eval()` + `no_grad()`, train loader from the train split only |
| Training | `pipeline/experiment.py` | `results/results.json`, `results/predictions_seed4{2,3,4}.csv` | 3 seeds × 20 epochs, best checkpoint on validation, MPS |
| Evaluation | same | `results/results.json`, `results/predictions_ensemble.csv` | AUROC 0.964 ± 0.004 over seeds; ensemble 0.969 (95% CI 0.956–0.980), AUPRC 0.980 (0.970–0.988); bootstrap 2000 replicates |
| Calibration | `pipeline/explain.py` | `results/calibration.json` | ECE 0.127, Brier 0.103 — **the gate's most useful output**: a 0.969-AUROC classifier is over-confident, and the write-up says so instead of burying it |
| Interpretability | `pipeline/explain.py` (captum LayerGradCam) | `results/explainability.json` | Grad-CAM with **both Adebayo sanity checks** quantified: model-randomisation r −0.07, label-permutation r −0.03 |
| **Explainability gate** | `/explainability` `check_explainability_report.py` | `qc/explainability_report.json` | **OK** — and it forced the maps to be reported as *attribution*, not localisation, because the benchmark has no lesion masks |
| Figures | `pipeline/make_figs.py` | `figures/fig1–fig4` | every value read from `results/` at build time |
| Write-up | `/write-paper` | `manuscript/writeup.md`, `manuscript/title_page.md` | |
| Self-review | `/self-review` (single pass) | `qc/self_review.md` | 2 Major, 4 Minor; RM2/Rm1/Rm2 applied at the time |

## Closed later (2026-07-31)

- **RM1 — references unverified.** The self-review had left this as an open blocker. `/verify-refs
  --strict` was run against `manuscript/refs.bib`: **8 of 9 OK, 0 fabricated, 0 duplicates,
  `submission_safe: true`** (`qc/reference_audit.json`). The ninth (`paszke2019pytorch`) is
  **UNVERIFIED and stays that way** — NeurIPS 2019 proceedings carry no CrossRef DOI and no PubMed
  record, so no registry can confirm it. UNVERIFIED is not FABRICATED. RM1 is now closed in
  `qc/self_review.md` rather than left dangling.
- **CLAIM 2024 assessment added** (`qc/reporting_checklist.md`): 44 items, 27 PRESENT / 6 PARTIAL /
  7 MISSING / 4 N/A. It surfaced a defect nothing else had: **the manuscript states package versions
  that no shipped artifact records**, while `pipeline/REPRODUCIBILITY.md` and
  `pipeline/requirements.txt` both say no version set was captured, and `results/results.json` has no
  environment block. The versions are kept but flagged in the manuscript as the one number a reader
  cannot re-derive; the Reproducibility section no longer claims they are captured.
- **`manuscript_final.docx` rendered** — pandoc **without** `--citeproc`, because the write-up carries
  a hand-numbered References section and citeproc would append a second bibliography. The rendered
  file was checked for that duplication and has none.
- **`manifest.lock.json` added** — 11 artifacts fingerprinted (`version_dataset.py verify --strict`:
  11/11 match). Not yet wired into CI: the repository's demo-manifest step covers Demos 1–3 only, and
  extending it is a gate change left for the maintainer.

## What is not here

No external validation — deliberately. That is Demo 5's job, and this note names the gap rather than
implying it was covered. No presentation, no submission packaging.
