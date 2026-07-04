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

## Scope anchor — the target user

The target user is a **clinician-researcher who fine-tunes existing / pretrained models on collected
clinical data to derive clinical results and write papers** — *not* someone developing new
architectures. Every produce path here centres on **adapting an existing model + a clinical outcome +
manuscript rigor**, never architecture innovation. So the lane favours transfer-learning /
fine-tuning of pretrained backbones (timm, MedSAM, nnU-Net), classical ML on radiomics/tabular
features (random forest, XGBoost), and diffusion used off-the-shelf for augmentation — each wrapped
in the leakage / validation / calibration / reporting gates that a solo clinician gets wrong alone.

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

### Item 3 — Radiomics / classical-ML produce path (RF / XGBoost)  ·  clinician-first, do next

- **Why next.** The most common solo-doable clinical-ML workflow (radiomics features → tree
  ensemble → clinical outcome), needs no GPU, and directly serves the target user. The key audit gate
  (`check_cv_leakage`, feature-selection-outside-CV in prose) already exists — only the *produce* path
  and a structural gate are missing.
- **Form.** New skill (`radiomics-ml`) — radiomics + tabular clinical ML with tree ensembles.
- **Produces.** pyradiomics feature-extraction guidance (IBSI settings — by reference), random forest /
  XGBoost / regularised-logistic training with **nested cross-validation**, feature selection **inside
  the fold**, feature-stability (ICC / test-retest) filtering, class-imbalance handling, SHAP,
  calibration, and clinical-utility (decision curve) — integrating scikit-learn / xgboost, not
  reimplementing them.
- **Gate — `check_radiomics_ml`.** Flags (from a declarative pipeline manifest): `NO_NESTED_CV`,
  `HIGH_DIM_LOW_EVENTS`, `SELECTION_OUTSIDE_CV` (Major); `NO_FEATURE_STABILITY`, `NO_CALIBRATION`,
  `NO_EXTERNAL_VALIDATION` (Minor). Complements `check_cv_leakage` (prose audit) at the pipeline-spec
  level.
- **Wiring.** `analyze-stats` calibration / clinical-utility guides; `check-reporting` CLEAR (radiomics)
  + TRIPOD+AI + PROBAST-AI; `self-review` `clinical_prediction_model` probe.
- **Catalog.** +1 skill, +1 detector.

### Item 4 — Fine-tuning scaffold: transfer-learning + SAM/MedSAM adaptation + diffusion augmentation  ·  imaging fine-tune, do fourth

- **Why fourth.** Extends `model-scaffold` from train-from-scratch to the target user's real mode —
  **fine-tune a pretrained model on collected clinical data**: a pretrained timm/MONAI backbone, a
  MedSAM adapter, or nnU-Net fine-tuning; diffusion used off-the-shelf for augmentation, not as a
  novel method.
- **Form.** Extend `model-scaffold` with fine-tuning task modes (`--task finetune` / `--from-pretrained`)
  + a MedSAM-adaptation and a diffusion-augmentation reference — or a thin sibling skill; decide at
  build time. Prefer extending `model-scaffold` (avoids skill-count churn where a mode fits).
- **Produces.** A leakage-safe fine-tuning repo: frozen-vs-unfrozen layer schedule, discriminative
  learning rates, pretrained-weight provenance recorded, small-clinical-dataset regularisation; MedSAM
  prompt/adapter fine-tuning; diffusion augmentation wired to the train-only split (never eval).
- **Gate.** Reuse `check_training_hygiene` + `check_preprocessing_leakage` (augmentation-on-eval already
  caught); add fine-tuning-specific checks only if a gap remains (avoid duplicate detectors).
- **Wiring.** `architecture-zoo` (selection already covers SAM/diffusion) → this (adapt) →
  `model-validation` / `model-evaluation`.
- **Catalog.** +0–1 skill (prefer extend), +0–1 detector.

### Item 5 — Uncertainty / OOD / selective prediction  ·  deployment-safety

- **Why.** Deployment-safety flavored; builds on evaluation + calibration.
- **Form.** New skill (`uncertainty-imaging`) — **decided at build time: new skill**
  (deployment-safety is a distinct concern from held-out metrics; a separate skill is
  more discoverable than a `model-evaluation` mode).
- **Produces.** MC-dropout / deep-ensemble / conformal-prediction intervals, OOD
  detection (energy / Mahalanobis), selective prediction (abstention at a
  coverage target), calibration-under-shift.
- **Gate — `check_uncertainty_reporting`.** Flags: point predictions without
  uncertainty in a deployment-framed claim; conformal intervals without coverage
  validation; an OOD claim without a held-out OOD test set.
- **Wiring.** `model-evaluation` (calibration / subgroup) + `analyze-stats`
  calibration guide; DECIDE-AI monitoring seam in `model-validation`.
- **Catalog.** +1 skill, +1 detector.

### Item 6 — MLOps integration reference (off-moat, reframed thin)  ·  last, reference-only

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
- [x] **Item 3** — radiomics / classical-ML (RF/XGBoost) + `check_radiomics_ml` (skill `radiomics-ml`, PR #276/#277)
- [x] **Item 4** — fine-tuning scaffold: transfer-learning + SAM/MedSAM adaptation + diffusion augmentation
  (`model-scaffold --task finetune` + `--from-pretrained` + `references/finetuning_guide.md`; the
  `PRETRAINED_PROVENANCE_MISSING` verdict added to the existing `check_training_hygiene` — no new
  skill, no new detector). Chosen build-time form: **extend** `model-scaffold` (not a sibling skill).
- [x] **Item 5** — uncertainty/OOD + `check_uncertainty_reporting` (skill `uncertainty-imaging`, PR #279)
- [x] **Item 6** — MLOps integration reference (`model-scaffold/references/mlops_guide.md` — experiment
  tracking / config / data / environment versioning, CI-for-ML, reporting checklist; wiring-only,
  points to MONAI / nnU-Net / W&B / MLflow, reimplements nothing; no skill, no detector). PR #280

*Update the checkboxes and the top-level ROADMAP pointer as items land. Items 1–2
shipped in **v5.15.0**; Items 3–4 (the clinical fine-tuning focus) shipped in **v5.16.0**.
Items 5–6 (deployment safety + the MLOps wiring reference) are staged in `[Unreleased]` for the
next minor (**v5.17.0**) — the full six-item produce-side depth roadmap is now complete; the only
remaining candidate is an `architecture-zoo` graph-neural-net entry (brain connectome).*
