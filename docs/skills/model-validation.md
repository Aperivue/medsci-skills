<!-- AUTO-GENERATED from skills/model-validation/SKILL.md by scripts/gen_skill_docs.py. Do not edit by hand. -->

# model-validation

> Design or audit the clinical-validation study for an engineer-built medical-imaging model (segmentation, classification, or detection) before the validation report or manuscript is written. Covers patient-level split disjointness and the data-leakage taxonomy, tuning-on-test, internal versus genuine external validation, comparator design, single-run versus multi-seed variance, task-correct metric selection, test-set sizing, and CLAIM 2024 / TRIPOD+AI / STARD-AI reporting fit. Ships a deterministic split-leakage gate that proves patient disjointness by set arithmetic on the emitted split-assignment table. Does not build or train models — it integrates with MONAI / nnU-Net, it does not replace them.

**Invoke:** `/model-validation` · **Tools:** Read, Write, Edit, Bash, Grep, Glob · **Model:** inherit

## When to use

`model-validation` activates on requests such as: model validation, validate AI model, imaging model validation, data leakage, split leakage, train test split, patient-level split, internal validation, external validation, validation design, leakage audit, segmentation model validation, classification model validation, detection model validation, nnU-Net validation, deep learning validation, CLAIM 2024, generalizability, held-out test set.

## Quality Card

**Purpose** — Catch the structural validity failures of an engineer-built imaging model's evaluation — patient-level leakage, tuning on the test set, an internal split sold as external validation, a single-run headline metric, and metric-on-imbalanced — before they reach a clinical-validation manuscript.

**Safety boundaries**

- Advisory plus deterministic-audit only: never alters predictions, splits, or metrics.
- The leakage verdict is reproduced by a stdlib script (set arithmetic on the patient IDs), never asserted from prose.

**Known limitations**

- Audits the evaluation design, not the model's clinical safety; a clean audit is necessary, not sufficient.
- The split-leakage gate sees only the split table it is given; it cannot detect leakage hidden in upstream preprocessing it never sees.

**Validation**

- `python3 scripts/check_split_leakage.py --splits <split_assignment.csv> --strict`
- `bash scripts/check_split_leakage_challenge/verify.sh  # deterministic, network-free`

**Evidence** — `ci_validator`

## Bundled resources

**References** (`skills/model-validation/references/`):

- `validation_design.md`

**Scripts** (`skills/model-validation/scripts/`):

- `check_split_leakage.py`
- `check_split_leakage_challenge/` (7 files)

## Source

Canonical definition: [`skills/model-validation/SKILL.md`](../../skills/model-validation/SKILL.md)

---

*Part of [MedSci Skills](../../README.md) — Claude Code skills for the medical research lifecycle. This page is generated from the skill's `SKILL.md`; edit that file and re-run `scripts/gen_skill_docs.py`.*
