<!-- AUTO-GENERATED from skills/uncertainty-imaging/SKILL.md by scripts/gen_skill_docs.py. Do not edit by hand. -->

# uncertainty-imaging

> Design or audit the uncertainty-quantification, out-of-distribution (OOD) detection, and selective-prediction layer of a medical-imaging model framed for deployment — so a clinical-use claim carries calibrated per-case uncertainty (MC-dropout / deep ensemble / conformal / Bayesian), an OOD guard validated on a held-out OOD set, an abstention rule at a pre-specified operating point, and uncertainty checked under distribution shift. Emits an uncertainty manifest and a deterministic gate that flags a deployment claim built on point predictions, conformal intervals with unmeasured coverage, and an OOD claim with no held-out OOD data. Integrates MAPIE / captum / pretrained OOD scorers; it does not reimplement them and never runs a model on real patient data.

**Invoke:** `/uncertainty-imaging` · **Tools:** Read, Write, Edit, Bash, Grep, Glob · **Model:** inherit

## When to use

`uncertainty-imaging` activates on requests such as: uncertainty, uncertainty quantification, UQ, epistemic, aleatoric, MC-dropout, monte carlo dropout, deep ensemble, conformal prediction, split conformal, prediction interval, coverage, calibration under shift, out-of-distribution, OOD detection, distribution shift, Mahalanobis, energy score, ODIN, selective prediction, abstention, reject option, deployment safety, DECIDE-AI, predictive uncertainty.

## Quality Card

**Purpose** — Stop a deployment-framed medical-imaging model from shipping point predictions — no per-case uncertainty, conformal coverage never measured, an OOD claim with no held-out OOD data, an ensemble that shares a seed, uncertainty validated only in-distribution — into a clinical manuscript.

**Safety boundaries**

- Advisory plus deterministic-audit only: never alters predictions, coverage, or OOD numbers.
- The reporting verdict is reproduced by a stdlib script (rule on the uncertainty manifest), never asserted from prose.
- Integrates MAPIE / captum / OOD scorers by reference; it does not reimplement them and never runs a model on real patient data.

**Known limitations**

- Audits the declared uncertainty manifest, not the executed code; a mislabelled field (e.g. unvalidated coverage recorded as validated) can hide a real problem — complements, does not replace, model-evaluation's executed calibration.
- A clean uncertainty audit is necessary, not sufficient — prospective deployment monitoring (DECIDE-AI) still governs the clinical claim.

**Validation**

- `python3 scripts/check_uncertainty_reporting.py --manifest <uncertainty_manifest.json> --strict`
- `bash scripts/check_uncertainty_reporting_challenge/verify.sh  # deterministic, network-free`

**Evidence** — `ci_validator`

## Bundled resources

**References** (`skills/uncertainty-imaging/references/`):

- `uncertainty_guide.md`

**Scripts** (`skills/uncertainty-imaging/scripts/`):

- `check_uncertainty_reporting.py`
- `check_uncertainty_reporting_challenge/` (6 files)

## Source

Canonical definition: [`skills/uncertainty-imaging/SKILL.md`](../../skills/uncertainty-imaging/SKILL.md)

---

*Part of [MedSci Skills](../../README.md) — Claude Code skills for the medical research lifecycle. This page is generated from the skill's `SKILL.md`; edit that file and re-run `scripts/gen_skill_docs.py`.*
