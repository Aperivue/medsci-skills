---
name: medsci
description: MedSci skills bundle — medical research workflow skills (study design, statistics, writing, reporting, peer review). See capabilities.yml for the master index and skills/ for individual skills.
---

# MedSci Skills Bundle

This directory is a bundle of medical-research workflow skills, intended for use
with [opencode](https://opencode.ai) agent skill discovery.

## Structure

- `capabilities.yml` — master capability index. **Start here** to find the right
  skill for a given research phase.
- `skills/<name>/SKILL.md` — individual skills, each loadable via the `skill`
  tool. Examples: `design-study`, `analyze-stats`, `write-paper`,
  `check-reporting`, `search-lit`, `meta-analysis`.
- `scripts/` — supporting Python/Bash scripts invoked by the skills.

## Usage

Load a skill by name via the `skill` tool, e.g. `skill("write-paper")`. Each
skill's `SKILL.md` describes its workflow and prerequisites. The
`orchestrate` skill routes multi-step or ambiguous research goals to the
appropriate skill(s) from this bundle.

## Scope

Covers the full medical-research lifecycle: literature search, study design,
sample-size calculation, data cleaning, statistical analysis, manuscript
writing, reporting-guideline compliance, figure generation, journal selection,
peer review, and revision. Includes specialized tracks for medical-imaging AI
(model scaffolding, validation, explainability, uncertainty quantification)
and for clinical-radiomics / tabular ML.
