# Model-Engineering Lane — Produce-Side Depth Roadmap

A sequenced build plan for deepening the **produce** side of the medical-AI
model-engineering lane. This is a working checklist, executed one item at a time;
it is a companion to the top-level [`ROADMAP.md`](../ROADMAP.md) (§ Research
throughput), not a delivery commitment.

## Where the lane stands

The lane today is a **design → scaffold → validate → evaluate → document** loop:

| Stage | Skill(s) |
|-------|----------|
| Choose architecture | `architecture-zoo` |
| Scaffold training repo | `model-scaffold` (+ `check_training_hygiene`) |
| Validate | `model-validation` (+ `check_split_leakage`) |
| Evaluate | `model-evaluation` (+ `check_metric_reporting`) |
| Document | `model-card` (+ `check_model_card_complete`) |
| LLM/MLLM eval | `mllm-eval` (+ `check_mllm_eval_completeness`) |
| AI-vs-expert design | `design-ai-benchmarking` |

Plus an **audit companion** in `self-review` domain-probes (`model_development`,
`clinical_prediction_model`, `ai_overclaiming`, `image_synthesis`).

By design this is a *rigor / reproducibility / reporting* lane — it **integrates**
MONAI / nnU-Net / timm and never reimplements a training framework. Three
produce-side stages are genuinely thin; this roadmap fills them, in order.

## Guardrails (every item)

- **On-moat only.** Rigor / reproducibility / reporting for medical imaging —
  never generic MLOps. Training loops, hyperparameter search, and experiment
  tracking stay with MONAI / nnU-Net / timm / W&B; we wire and report, not rebuild
  (this is the [ROADMAP out-of-scope clause](../ROADMAP.md)).
- **Human-in-loop.** Nothing trains, tunes, or claims a result autonomously.
- **Every addition ships a deterministic gate + a network-free challenge card +
  a CI-wired test** (the reproducible-challenge pattern), and no fabricated
  numbers (VERIFY placeholders where a real run is required).
- **Wire bidirectionally.** Each produce skill pairs with its `self-review`
  audit probe and, where relevant, a `check-reporting` item (CLAIM 2024 /
  TRIPOD+AI).
- **Catalog discipline.** A new skill bumps `metadata/catalog_counts.json`
  (skills) + the README tagline + the four count-claim files; a new detector
  bumps the detectors-catalog family map + count. Run `gen_*` `--check` +
  `validate_catalog_consistency.py` before every push.
- **Batched release.** Merge each item to `[Unreleased]`; release the lane as
  **one** user-noticeable batch once ≥2 items land (per the
  [release-cadence policy](maintainer_workflow.md#release-cadence)) — not per skill.

## Sequence

### Item 1 — Imaging data pipeline + data-stage leakage  ·  foundation, do first

- **Why first.** Everything downstream depends on leakage-safe, correctly
  preprocessed data. It extends the existing split-leakage moat
  (`model-validation`) **upstream** to the data-preparation stage.
- **Form.** New skill (`preprocess-imaging`) — a distinct produce stage that
  `model-scaffold` consumes; not an extension.
- **Produces.** DICOM/NIfTI I/O, resampling / spacing normalization, intensity
  windowing/normalization, a patient-level split at slice/volume granularity, and
  augmentation-appropriateness guidance per modality (physiology-preserving vs
  breaking) — integrating MONAI transforms / TorchIO, not reimplementing them.
- **Gate — `check_preprocessing_leakage`.** Flags: (a) normalization/scaler
  statistics fit on full data or the test split (train-only fit required);
  (b) augmentation or resampling applied before the split; (c) patient IDs
  crossing train/val/test at the slice level (set-arithmetic on the
  slice→patient map, extending `check_split_leakage`); (d) test-time augmentation
  folded into training metrics.
- **Wiring.** Feeds `model-scaffold`'s split; `self-review` `model_development`
  probe gains a data-leakage audit back-link; CLAIM data-preprocessing item.
- **Catalog.** +1 skill, +1 detector.

### Item 2 — Interpretability / explainability (produce + pitfalls)  ·  reviewer-demand, do second

- **Why second.** Highest reviewer-demand and adoption pull; independent of Item 1.
  Currently only *audited* in `self-review`, never produced.
- **Form.** New skill (`explainability`).
- **Produces.** Grad-CAM / Grad-CAM++ / attention-rollout / saliency wired to a
  trained model (integrating captum / pytorch-grad-cam), quantitative
  localization metrics (pointing game, IoU with ground-truth masks), and
  **mandatory sanity checks** (Adebayo et al. model-parameter and data
  randomization tests).
- **Gate — `check_explainability_report`.** Flags: saliency presented as causal
  or as validation of correctness; missing sanity check; no quantitative
  localization metric; single cherry-picked example without a cohort-level result.
- **Wiring.** `self-review` `ai_overclaiming` / `image_synthesis` probes (audit)
  ↔ produce; CLAIM / TRIPOD+AI explainability items in `check-reporting`.
- **Catalog.** +1 skill, +1 detector.

### Item 3 — Uncertainty / OOD / selective prediction  ·  deployment-safety, do third

- **Why third.** Deployment-safety flavored; builds on evaluation + calibration.
- **Form.** New skill (`uncertainty-imaging`) — decide vs extending
  `model-evaluation` at build time (lean new skill for discoverability).
- **Produces.** MC-dropout / deep-ensemble / conformal-prediction intervals, OOD
  detection (energy / Mahalanobis), selective prediction (abstention at a
  coverage target), calibration-under-shift.
- **Gate — `check_uncertainty_reporting`.** Flags: point predictions without
  uncertainty in a deployment-framed claim; conformal intervals without coverage
  validation; an OOD claim without a held-out OOD test set.
- **Wiring.** `model-evaluation` (calibration / subgroup) + `analyze-stats`
  calibration guide; DECIDE-AI monitoring seam in `model-validation`.
- **Catalog.** +1 skill, +1 detector.

### Item 4 — MLOps integration reference (off-moat, reframed thin)  ·  last, reference-only

- **Why last / reframed.** Honors "grow all of it" without scope creep. **Not** a
  training-loop or experiment-tracking reimplementation. A reference that
  documents reproducibility-safe wiring of MONAI / nnU-Net / timm + W&B / MLflow,
  seed discipline, and what to report — pointing to the frameworks, never
  replacing them, bounded by the ROADMAP out-of-scope clause.
- **Form.** Reference extension of `model-scaffold` (`training_guide.md`), not a
  new skill → **no count bump**.

## Progress

- [x] **Item 1** — imaging data pipeline + `check_preprocessing_leakage` (skill `preprocess-imaging`, PR #274)
- [x] **Item 2** — interpretability/explainability + `check_explainability_report` (skill `explainability`, PR #275)
- [ ] **Item 3** — uncertainty/OOD + `check_uncertainty_reporting`
- [ ] **Item 4** — MLOps integration reference (`model-scaffold/training_guide.md`)

*Update the checkboxes and the top-level ROADMAP pointer as items land. Release
the lane as one batch (e.g. a `model-engineering produce-side depth` minor) once
Items 1–2 are merged.*
