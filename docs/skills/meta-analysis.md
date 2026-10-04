<!-- AUTO-GENERATED from skills/meta-analysis/SKILL.md by scripts/gen_skill_docs.py. Do not edit by hand. -->

# meta-analysis

> Use when running a systematic review and meta-analysis, DTA or intervention. Covers PROSPERO protocol, search, screening, extraction, risk of bias (QUADAS-3, RoB 2, ROBINS-I), bivariate/HSROC or random-effects pooling, forest plots, heterogeneity and PRISMA reporting. Topic scouting is /ma-scout.

**Invoke:** `/meta-analysis`

## When to use

`meta-analysis` activates on requests such as: meta-analysis, systematic review, PROSPERO, QUADAS-3, forest plot, funnel plot, PRISMA, QUADAS, ROBINS, HSROC, bivariate model, pooled sensitivity, pooled specificity, search strategy, study selection, data extraction form.

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
- `bash scripts/extract_assist_challenge/verify.sh  # deterministic, network-free`
- `bash scripts/check_exclusion_code_validity_challenge/verify.sh  # deterministic, network-free`
- `bash scripts/check_ratio_ci_symmetry_challenge/verify.sh  # deterministic, network-free`

**Evidence** — `demo`

## Bundled resources

**References** (`skills/meta-analysis/references/`):

- `LICENSES.md`
- `PROSPERO_template.md`
- `ai_pre_screening_template.py`
- `checklists/` (8 files)
- `data_integrity_checklist.md`
- `empirical_lessons.md`
- `icmje_coi_guide.md`
- `phase10_recovery.md`
- `phase3_screening_detail.md`
- `phase4_extraction_detail.md`
- `phase4_km_composite.md`
- `phase6_statistical_synthesis.md`
- `phase9_circulation.md`
- `post_submission_release_ops.md`
- `r_templates.md`
- `review_orchestration.md`
- `single_arm_proportion_ma.md`
- `submission_package_drift.md`

**Scripts** (`skills/meta-analysis/scripts/`):

- `check_exclusion_code_validity.py`
- `check_exclusion_code_validity_challenge/` (6 files)
- `check_pool_consistency.py`
- `check_ratio_ci_symmetry.py`
- `check_ratio_ci_symmetry_challenge/` (4 files)
- `cohort_overlap_check.py`
- `dta_extraction_qc.py`
- `extract_assist.py`
- `extract_assist_challenge/` (6 files)
- `extraction_consensus_log_init.py`
- `prisma_5way_consistency.py`
- `screening_reconcile.py`
- `tag_cleanup_gate.sh`

**Templates** (`skills/meta-analysis/templates/`):

- `FINAL_POOL_LOCK.yaml.template`
- `extraction_form_v2.md`
- `supplementary_8file_checklist.md`

## Source

Canonical definition: [`skills/meta-analysis/SKILL.md`](../../skills/meta-analysis/SKILL.md)

---

*Part of [MedSci Skills](../../README.md) — Claude Code skills for the medical research lifecycle. This page is generated from the skill's `SKILL.md`; edit that file and re-run `scripts/gen_skill_docs.py`.*
