<!-- Domain probe module — shared, vendored BYTE-IDENTICAL by /peer-review and /self-review.
     Severity words below (MAJOR / MINOR / major / minor) denote finding severity, NOT a journal
     recommendation. Each consuming skill maps findings to its own output:
       - peer-review: Major / Minor comments + Confidential Comments to the Editor; a task- or
         design-level flaw is placed as Major #1.
       - self-review: Anticipated Major / Minor Comments (Fatal / Fixable) mapped to category letters.
     Do NOT edit one copy only — run `python3 scripts/check_domain_probe_sync.py --sync`. -->

# Model-Development / Validation-Integrity probes (MD0–MD8)

A checklist for **engineer-built medical-imaging models** — a segmentation, classification, or detection model (CNN / U-Net / nnU-Net / transformer) that a clinical team received from an engineering collaborator and is now validating and writing up. This probe owns the **partition, leakage, reproducibility, and metric-selection mechanics** of the model's evaluation. It is the imaging-model counterpart to `clinical_prediction_model.md` (tabular TRIPOD prediction models) and `radiomics.md` (hand-crafted feature pipelines), and it complements `ai_overclaiming.md` (which owns the *claim*, MD owns the *mechanism behind the number*). Route here when the manuscript develops, validates, or reports the performance of a deep-learning imaging model. Author-side study design for such a model is `/model-validation`; this module is the reviewer-side audit.

**MD0 — Locate the deployment task and the evaluation it rests on (gate; run first)**:
- State the model's task (segmentation / classification / detection), its **intended-use horizon** (screening, triage, pre-procedure, post-hoc), and the **single number the conclusion leans on** (Dice, AUROC, sensitivity at an operating point, FROC). Then find the partition that produced it: which data trained the model, which tuned it, and which was touched once for the final estimate.
- An integrity finding is a **lead until the metric and the partition that produced it are read together** — do not escalate a clean number whose provenance is simply not yet described; ask for it first.
- Boundary with neighbours: `ai_overclaiming.md` AO5 = the *claim/metric is optimistic*; `clinical_prediction_model.md` CP = a *tabular TRIPOD model*; MD = the *partition, leakage, reproducibility, and metric mechanics of an engineer-built imaging model*.

**MD1 — Partition disjointness and the leakage taxonomy**:
- Confirm the split is at the **patient level**, not the image / series / slice level — the same patient contributing slices to both train and test inflates every metric, because the model can memorise patient-specific anatomy rather than pathology (CLAIM 2024 data-partition items; Varoquaux & Cheplygina, *npj Digit Med* 2022).
- Walk the leakage taxonomy (Kapoor & Narayanan, *Patterns* 2023): (a) **same-patient / near-duplicate** records across splits; (b) **preprocessing-before-split** — any normalisation, intensity scaling, resampling, feature selection, foundation-model embedding, or ComBat-style harmonisation **fit on the whole cohort** before partitioning leaks test statistics into training; (c) **site / scanner / label shortcut** — a model that separates classes by acquisition site or a burned-in annotation rather than by pathology; (d) **temporal leakage** — a random split in which future and past coexist.
- The decisive test: *could any value used in training have been computed only with knowledge of a test case?* → MAJOR (often Fatal) when a leakage path is present and the headline metric depends on it; a clarify-request when the split is clean but its level or ordering is simply undescribed.

**MD2 — Tuning, threshold, and model selection on the test set**:
- The test set must be touched **once**, for the final estimate. Flag any architecture search, hyperparameter sweep, early-stopping criterion, **operating-point / threshold** choice (Youden, F1-max), or "best checkpoint" selection that reads the test set — each is a form of tuning-on-test that makes the reported number optimistic and non-reproducible.
- Require an explicit statement that the threshold and the final model were fixed on training / tuning folds only. A test set reused across multiple model variants (model-selection leakage) → MAJOR; a tuning step whose data source is unstated → PARTIAL pending clarification. (Cross-link `ai_overclaiming.md` on threshold provenance.)

**MD3 — Internal split vs genuine external validation (and the nomenclature conflation)**:
- Classify the evidence honestly: apparent → internal random split → cross-validation → **temporal** (later time window) → **geographic / external** (different site, scanner, vendor) → **multi-site external**. Cross-validation and bootstrap are development-time optimism corrections, **not** external validation (cross-link `clinical_prediction_model.md` CP6).
- Flag "developed **with external validation**" when the single external set was used for tuning or feature selection, and flag a single external site propping up a broad generalisability claim (cross-link `ai_overclaiming.md`). A geographically or temporally external test of adequate size is the strongest single lever for a deployment-readiness claim — its absence caps the claim to internal performance. → MAJOR when an external / generalisability claim outruns an internal-only design.

**MD4 — Seed, run-to-run variance, and single-run reporting**:
- A deep model's metric varies with random seed, initialisation, augmentation order, and (for non-deterministic GPU operations) hardware. A single-run headline number with no spread overstates precision and is unreproducible.
- Require the metric as **mean ± SD (or 95% CI) across ≥3 seeds / runs**, or — minimally — a fixed, reported seed with the determinism caveat, and confirm the reported figure is not a cherry-picked best run or epoch. Single-run headline with no variance and no fixed seed → MAJOR; variance unreported but a fixed seed is stated → MINOR.

**MD5 — Test-set size and event count for the headline metric (and for calibration)**:
- A metric is only as stable as its denominator. Check the **test-set events per class**, not the cohort total: an AUROC of 0.92 on 18 positive cases has a confidence interval spanning much of the usable range, and a calibration claim needs roughly ≥100 events to be meaningful (Riley et al., prediction-model sample-size work; CLAIM 2024 asks that the test size be justified).
- Segmentation / detection: confirm the number of **lesions / structures**, not just patients, supports the per-structure metric. Sparse-test headline metric with no precision statement → MAJOR (route the sizing to `/calc-sample-size`); adequate n but the CI omitted → MINOR.

**MD6 — Metric selection and the imbalanced-data pitfalls**:
- Match the metric to the task and the prevalence (Metrics Reloaded — Maier-Hein & Reinke et al., *Nat Methods* 2024; pitfalls companion Reinke et al., *Nat Methods* 2024). (a) **Segmentation**: Dice / IoU alone is shape-insensitive — pair an **overlap metric with a boundary metric** (HD95 / Normalised Surface Distance), report **per-structure** rather than only a global mean, and beware Dice instability on small structures. (b) **Classification under imbalance**: **accuracy is misleading** — report threshold-independent discrimination with CIs (**AUROC and AUPRC**, since AUPRC tracks the minority class), plus sensitivity / specificity and prevalence-dependent **PPV / NPV at the deployment base rate**, not on an artificially balanced set. (c) **Detection**: report **FROC / sensitivity-per-false-positive or mAP with the IoU match criterion stated**, not patient-level accuracy.
- A headline that is accuracy-on-imbalanced, Dice-only, or a metric whose match / operating criterion is unstated → MAJOR; a sound metric missing only its CI or a secondary boundary metric → MINOR.

**MD7 — Reproducibility and provenance of the engineer-built artifact**:
- The clinician inherits a model and must be able to say where it came from and rebuild the evaluation. Require: model **provenance** (in-house / vendor / open-weights + version), architecture, all hyperparameters, framework + **library versions**, the **preprocessing pipeline in order**, hardware, the **random seed**, and **code + weights + data availability** (or a stated reason) — the standard ML-reproducibility set (Pineau et al., ML Reproducibility Checklist; CLAIM 2024; TRIPOD+AI).
- For a **vendor / closed** model, state the access limits explicitly (training-data composition unknown, results not independently reproducible) rather than implying full transparency. Missing the items needed to reproduce the headline result → MAJOR; a few secondary items absent → MINOR.

**MD8 — Label quality and the reference standard behind the engineer's metrics**:
- A model is bounded by its labels. Check who produced the reference standard, the **number of annotators, the consensus / adjudication rule, blinding, and reported inter-reader agreement** (κ / ICC), and whether any labels are **automated / "silver" or model-derived** (NLP-mined report labels, prior model outputs) — label noise caps achievable performance and silent self-labelling is circular (CLAIM 2024 reference-standard items; cross-link self-review circularity checks).
- For subgroup / fairness, defer to `equity_fairness.md` rather than re-deriving it here. An undefined reference standard, or model-derived labels feeding the same model's evaluation → MAJOR (Fatal when circular); agreement simply unreported → MINOR.

**Output template (MD1 / MD6 example)**:
> "The split appears to be at the image level (Methods, Data partitions) while the claim is patient-level, and intensity normalisation is described before the split — either path lets test statistics into training, so I would ask for a patient-level partition with all preprocessing fit on the training fold only and the metrics re-reported. Separately, segmentation quality is reported as mean Dice alone; because Dice is insensitive to boundary error and unstable on small structures, I would add a boundary metric (HD95 or NSD) and per-structure values with 95% confidence intervals. As written, the headline understates uncertainty and cannot be reproduced."
