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
- Primary estimates report effect size with 95% CI and exact p-values.

**Known limitations**

- Correctness depends on a correct analysis plan and clean data (use design-study / clean-data first).
- Does not adjudicate clinical validity of the chosen test.

**Validation**

- `re-run the emitted script and diff results`
- `/self-review`

**Evidence** — `demo`

## Bundled resources

**References** (`skills/analyze-stats/references/`):

- `analysis_guides/` (7 files)
- `style/` (2 files)
- `table-standards/` (13 files)
- `templates/` (14 files)

## Source

Canonical definition: [`skills/analyze-stats/SKILL.md`](../../skills/analyze-stats/SKILL.md)

---

*Part of [MedSci Skills](../../README.md) — Claude Code skills for the medical research lifecycle. This page is generated from the skill's `SKILL.md`; edit that file and re-run `scripts/gen_skill_docs.py`.*
