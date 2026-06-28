---
name: model-validation
description: >
  Design or audit the clinical-validation study for an engineer-built medical-imaging model
  (segmentation, classification, or detection) before the validation report or manuscript is written.
  Covers patient-level split disjointness and the data-leakage taxonomy, tuning-on-test, internal
  versus genuine external validation, comparator design, single-run versus multi-seed variance,
  task-correct metric selection, test-set sizing, and CLAIM 2024 / TRIPOD+AI / STARD-AI reporting fit.
  Ships a deterministic split-leakage gate that proves patient disjointness by set arithmetic on the
  emitted split-assignment table. Does not build or train models — it integrates with MONAI / nnU-Net,
  it does not replace them.
triggers: model validation, validate AI model, imaging model validation, data leakage, split leakage, train test split, patient-level split, internal validation, external validation, validation design, leakage audit, segmentation model validation, classification model validation, detection model validation, nnU-Net validation, deep learning validation, CLAIM 2024, generalizability, held-out test set
tools: Read, Write, Edit, Bash, Grep, Glob
model: inherit
---

# Model-Validation Skill

## Purpose

This skill pressure-tests the **validation study for an engineer-built medical-imaging model** — the
common case where a clinical team receives a trained segmentation / classification / detection model
from an engineering collaborator and must validate it and write it up. It is the imaging-model
specialization of `/design-study`: where `design-study` covers general validity and
`design-ai-benchmarking` covers AI-versus-human-expert reader studies, this skill owns the
**partition, leakage, reproducibility, and metric-selection mechanics** that decide whether a reported
Dice / AUROC / sensitivity is trustworthy.

It is **advisory and deterministic-audit only**. It writes decision notes and runs a stdlib gate on the
split table; it never builds, trains, or alters the model, and it never replaces MONAI / nnU-Net /
TorchIO — those produce the model, this validates and publishes it.

## When to use
- A trained imaging model (in-house, vendor, or open-weights) needs a clinical-validation study designed
  or audited before submission.
- You have, or can produce, the **split-assignment table** (which patient went to train / val / test).

## When NOT to use
- Building or training the model → out of scope (integrate MONAI / nnU-Net).
- AI-versus-human-expert reader study → `/design-ai-benchmarking`.
- LLM / MLLM evaluation → `/mllm-eval` (when available).
- General study/validity review → `/design-study`.
- Statistical execution (DeLong, ICC, bootstrap CIs, calibration tables) → `/analyze-stats`.
- Item-by-item reporting-guideline audit of a finished manuscript → `/check-reporting`.
- Reviewing a finished manuscript → `/self-review` or `/peer-review` (which load the MD0–MD8
  reviewer-side probe).

## Workflow

### Phase 1 — Reconstruct the task, the intended-use horizon, and the analysis unit
State the model's task (segmentation / classification / detection), its **intended-use horizon**
(screening, triage, pre-procedure, post-hoc), the **single headline metric** the conclusion leans on,
and the **analysis unit** the metric must respect (per-patient vs per-lesion vs per-image). Everything
downstream is read against this.

### Phase 2 — Leakage audit (the deterministic gate, run first)
The most metric-inflating defect is a split that is **not disjoint at the patient level**. Produce the
emitted split-assignment table (`patient_id,split`) and run the gate:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/check_split_leakage.py \
  --splits <split_assignment.csv> --out qc/split_leakage.json --strict
```

`PATIENT_OVERLAP` (a patient in ≥ 2 partitions) and `MISSING_SEED` (an unreproducible split) are
proven by set arithmetic — not heuristics. Then walk the rest of the **leakage taxonomy** (Kapoor &
Narayanan, *Patterns* 2023) that the table cannot show: **preprocessing-before-split** (normalisation,
resampling, foundation-model embeddings, or ComBat harmonisation fit on the whole cohort before
partitioning), **site / scanner / burned-in-label shortcuts**, and **temporal leakage** (a random split
where future and past coexist). The decisive question: *could any value used in training have been
computed only with knowledge of a test case?*

### Phase 3 — Validation tier (internal split vs genuine external)
Classify the evidence honestly: apparent → internal random split → cross-validation → temporal →
geographic / external (different site, scanner, vendor) → multi-site external. Cross-validation and
bootstrap are development-time optimism corrections, **not** external validation. Flag a generalisability
or deployment claim that outruns an internal-only design, and "developed with external validation" where
the single external set was used for tuning. Also confirm the test set was touched **once** — no
architecture search, hyperparameter sweep, early-stopping, or operating-point / threshold choice read
the test set.

### Phase 4 — Comparator design
Decide what the model is compared against: clinical-only baseline, incremental value over an existing
score, or reader comparison. For a reader comparison, hand the rubric / inter-rater design to
`/design-ai-benchmarking`.

### Phase 5 — Metric selection (task-correct, prevalence-aware)
Match the metric to the task and the prevalence (Metrics Reloaded — Maier-Hein & Reinke et al.,
*Nat Methods* 2024): **segmentation** pairs an overlap metric (Dice / IoU) with a **boundary metric**
(HD95 / Normalised Surface Distance), per-structure not only global; **classification under imbalance**
reports **AUROC and AUPRC with CIs** plus sensitivity / specificity and prevalence-dependent PPV / NPV,
never bare accuracy on a balanced set; **detection** reports FROC / mAP with the IoU match criterion
stated. Require the headline metric as **mean ± SD across ≥ 3 seeds / runs**, or a fixed reported seed
with the determinism caveat. The per-case metric computation + the deterministic metric-reporting gate
live in `/model-evaluation` (which emits the per-case table for `/analyze-stats`).

### Phase 6 — Test-set sizing
Check the **events per class** in the test set, not the cohort total — a metric on a sparse positive set
has a confidence interval spanning much of the usable range, and calibration needs roughly ≥ 100 events.
Hand the formal sizing (diagnostic-accuracy / AUC precision / agreement) to `/calc-sample-size`.

### Phase 7 — Reporting-guideline fit
Map the study to its reporting standard via `/check-reporting`: **CLAIM 2024** (diagnostic imaging AI),
**TRIPOD+AI** (prediction model), **STARD-AI** (diagnostic accuracy), **PROBAST+AI** (risk of bias).

### Phase 8 — Handoffs
Carry the audited design into `/write-paper` (Methods), `/calc-sample-size` (sizing), `/check-reporting`
(compliance), and — for the reviewer-side audit of the finished draft — `/self-review`, which loads the
`model_development.md` (MD0–MD8) probe.

## Deterministic gate

`scripts/check_split_leakage.py` — proves patient-level split disjointness + seed presence on the emitted
split-assignment table (stdlib, network-free). Verdicts: `PATIENT_OVERLAP` (Major), `MISSING_SEED`
(Major), `SINGLE_PARTITION` (Minor). Reproducible challenge:
`bash ${CLAUDE_SKILL_DIR}/scripts/check_split_leakage_challenge/verify.sh`.

## Anti-Hallucination

- **Never fabricate performance metrics, split assignments, event counts, or seeds.** Every number comes
  from the engineer's executed code, the supplied split table, or a re-run of the deterministic gate —
  never invented. A reported Dice / AUROC / overlap count with no underlying record is the failure mode
  this skill exists to prevent.
- **Never report a split-audit "pass" without running `check_split_leakage.py`.** The patient-disjointness
  verdict is proven by the script, not asserted from prose.
- **Never invent references, reporting-guideline items, or metric-selection rules.** Verify citations via
  `/search-lit` (confirmed DOI / PMID); mark unverified ones `[UNVERIFIED - NEEDS MANUAL CHECK]`. If a
  CLAIM 2024 / TRIPOD+AI / Metrics-Reloaded item is uncertain, flag `[VERIFY]` and ask the user rather
  than guessing.
- **Do not claim external validation, generalisability, or deployment readiness the design does not
  support** — classify the validation tier honestly and let the evidence cap the claim.

## Boundaries — which skill to use, in what order

```
design-study (general validity)
  └─ model-validation (this skill: leakage, split, comparator, metric, sizing handoff)
       ├─ check_split_leakage.py  (deterministic patient-disjointness gate)
       ├─ calc-sample-size        (test-set / event sizing)
       ├─ design-ai-benchmarking  (reader-comparison rubric / IRR)
       ├─ check-reporting         (CLAIM 2024 / TRIPOD+AI / STARD-AI)
       └─ write-paper -> self-review / peer-review (MD0–MD8 reviewer probe)
```

It does not build the model (integrate MONAI / nnU-Net), compute publication statistics (`/analyze-stats`
owns DeLong / ICC / calibration tables), or evaluate an LLM / MLLM (`/mllm-eval`).
