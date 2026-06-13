<!-- AUTO-GENERATED from skills/meta-analysis/SKILL.md by scripts/gen_skill_docs.py. Do not edit by hand. -->

# meta-analysis

> Systematic review and meta-analysis pipeline for medical research. Covers protocol registration (PROSPERO), search strategy, screening, data extraction, risk of bias assessment (QUADAS-2/ROBINS-I), statistical synthesis (bivariate/HSROC for DTA, random-effects for intervention), and PRISMA-compliant reporting. Supports both DTA and intervention meta-analyses.

**Invoke:** `/meta-analysis` · **Tools:** Read, Write, Edit, Bash, Grep, Glob · **Model:** inherit

## When to use

`meta-analysis` activates on requests such as: meta-analysis, systematic review, PROSPERO, forest plot, funnel plot, PRISMA, QUADAS, ROBINS, HSROC, bivariate model, pooled sensitivity, pooled specificity, search strategy, study selection, data extraction form.

## Quality Card

**Purpose** — Run the SR/MA pipeline: PROSPERO registration, search, screening, extraction, risk of bias, synthesis (bivariate/HSROC or random-effects), and PRISMA reporting.

**Safety boundaries**

- Study counts are never reported without ID-level receipts; halts on a P0 reconciliation mismatch.
- Pool composition is locked to a single source of truth; downstream counts are re-derived, not copied.

**Known limitations**

- Synthesis validity depends on correct extraction; the skill enforces process, not clinical correctness.
- DTA pooling assumes adequate per-study 2x2 / threshold data.

**Validation**

- `python3 scripts/screening_reconcile.py`
- `python3 scripts/check_pool_consistency.py`

**Evidence** — `demo`

## Bundled resources

**References** (`skills/meta-analysis/references/`):

- `LICENSES.md`
- `PROSPERO_template.md`
- `ai_pre_screening_template.py`
- `checklists/` (7 files)
- `data_integrity_checklist.md`
- `icmje_coi_guide.md`
- `phase10_recovery.md`
- `phase4_km_composite.md`
- `phase6_statistical_synthesis.md`
- `phase9_circulation.md`
- `post_submission_release_ops.md`
- `r_templates.md`
- `review_orchestration.md`
- `single_arm_proportion_ma.md`
- `submission_package_drift.md`

**Scripts** (`skills/meta-analysis/scripts/`):

- `check_pool_consistency.py`
- `cohort_overlap_check.py`
- `dta_extraction_qc.py`
- `screening_reconcile.py`

**Templates** (`skills/meta-analysis/templates/`):

- `FINAL_POOL_LOCK.yaml.template`
- `extraction_form_v2.md`
- `supplementary_8file_checklist.md`

## Source

Canonical definition: [`skills/meta-analysis/SKILL.md`](../../skills/meta-analysis/SKILL.md)

---

*Part of [MedSci Skills](../../README.md) — Claude Code skills for the medical research lifecycle. This page is generated from the skill's `SKILL.md`; edit that file and re-run `scripts/gen_skill_docs.py`.*
