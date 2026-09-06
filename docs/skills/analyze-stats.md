<!-- AUTO-GENERATED from skills/analyze-stats/SKILL.md by scripts/gen_skill_docs.py. Do not edit by hand. -->

# analyze-stats

> Statistical analysis for medical research papers. Generates reproducible Python/R code with publication-ready tables and figures. Supports diagnostic accuracy, inter-rater agreement, meta-analysis, survival analysis, survey data, group comparisons, regression, propensity score, and repeated measures.

**Invoke:** `/analyze-stats` · **Tools:** Read, Write, Edit, Bash, Grep, Glob · **Model:** inherit

## When to use

`analyze-stats` activates on requests such as: statistics, statistical analysis, analyze data, run stats, table 1, demographics table, ROC curve, agreement analysis, ICC, kappa, survival analysis, Kaplan-Meier, group comparison, logistic regression, linear regression, regression, propensity score, PSM, IPTW, SIPTW, overlap weighting, repeated measures, mixed model, GEE, longitudinal, survey weighted, KNHANES, NHANES, NHIS cohort, complex survey, wOR, weighted odds ratio, claims-based, ICD-10.

## Quality Card

**Purpose** — Produce reproducible statistical code and publication-ready output for a specified design (DTA, agreement, survival, regression, survey, etc.).

**Safety boundaries**

- All numbers come from executed code on the supplied data; never hand-typed (seed-fixed transforms).
- Primary estimates report 95% CIs; planned hypothesis tests also report effect sizes and exact p-values.

**Known limitations**

- Correctness depends on a correct analysis plan and clean data (use design-study / clean-data first).
- Does not adjudicate clinical validity of the chosen test.
- The bound binary workflow requires declared independent units and fixed 0/1 predictions; hashes do not establish design validity or data rights.

**Validation**

- `python3 tests/test_analysis_run.py`
- `python3 scripts/demo_analysis_run.py --out demo-project`
- `re-run the emitted script and diff results`
- `/self-review`

**Evidence** — `demo`

## Bundled resources

**References** (`skills/analyze-stats/references/`):

- `analysis_guides/` (18 files)
- `analysis_run_workflow.md`
- `style/` (2 files)
- `table-standards/` (17 files)
- `templates/` (14 files)

**Scripts** (`skills/analyze-stats/scripts/`):

- `analysis_run_challenge/` (2 files)
- `check_generated_code.py`
- `check_separation.py`
- `demo_analysis_run.py`
- `rating_monotonicity.py`
- `run_analysis.py`

## Source

Canonical definition: [`skills/analyze-stats/SKILL.md`](../../skills/analyze-stats/SKILL.md)

---

*Part of [MedSci Skills](../../README.md) — Claude Code skills for the medical research lifecycle. This page is generated from the skill's `SKILL.md`; edit that file and re-run `scripts/gen_skill_docs.py`.*
