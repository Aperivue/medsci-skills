# Changelog

## [Unreleased]

### Added — Verified neurointervention/cerebrovascular journal profiles

- **JNIS (Journal of NeuroInterventional Surgery)** — compact + detail profiles built from user-supplied author-guidelines PDF (BMJ, SNIS). Covers double-anonymised review, ORCID mandate, BMJ Tier 3 data-sharing policy, Key Messages box requirement, AI policy aligned with BMJ/ICMJE.
- **Journal of Stroke** (Korean Stroke Society) — compact + detail profiles from user-supplied author-guidelines PDF. Full OA CC BY-NC 4.0 with no APC; Vancouver numbered references; structured 250-word abstract for Original Articles; mRS/mTICI/sICH definition requirements; AI policy defaults to ICMJE/WAME (no explicit journal-specific text).

Both profiles follow the two-tier public-library format already established by `INSI.md` and include a verification note citing the 2026-04-19 user-supplied PDF as source.

## [2.3.0] - 2026-04-19

### Added — Numerical Hallucination Prevention Layer

A real incident during a revision run exposed that the citation-safety pipeline did not have
a symmetric counterpart for numerical claims. Citations were verified end-to-end against
PubMed (0 fabricated refs), while a hand-typed `matrix()` in a revision-era R script silently
reversed a Fisher exact 2x2 ("3/45 vs 0/56, p=0.085" where the source said "0/45 vs 1/56,
p=0.37"). Every internal consistency check passed because every artifact echoed the same
wrong number. Detection required an explicitly requested second-pass audit with random
sampling against the primary paper.

To close that gap, four skills now enforce a common 3-layer (CSV ↔ analysis script ↔
manuscript) audit, with additional back-checking against the primary paper for revisions and
pooled estimates:

- **`/meta-analysis` Phase 6b — Post-Analysis Source Fidelity Audit (new).** After Phase 6
  statistical synthesis, mandates no hand-typed numerical matrices when a CSV exists,
  separate consensus-log rows for comparative-arm subsets, and a random 3-claim back-check
  (manuscript → R output → primary-source Table/Figure) before advancing to GRADE. A single
  mismatch is a P0 blocker.
- **`/self-review` Phase 2.5a — Numerical Source-Fidelity Audit (new).** Complements the
  existing Phase 2.5 internal consistency check with external validation: stratified random
  sampling of 5 claims, 3-layer traversal (manuscript ↔ CSV ↔ primary paper), and escalation
  of any mismatch to Major Comment. Revision-introduced numbers and comparative-arm specific
  values are the two highest-yield strata and are always sampled.
- **`/revise` Step 2.5 — Revision Numerical Lineage Check (new).** Any `/analyze-stats`
  re-run during revision must tag new numerical claims with `[VERIFY-CSV]`, read inputs from
  the locked extraction CSV, and maintain a response-document audit table that maps each new
  number to its source script:line + CSV coordinate + primary-source location. Prose
  generation is gated on the audit clearing.
- **`/write-paper` Step 7.3a — Numerical Claim Audit (new).** Sits alongside the existing
  citation verification step. Triggered whenever the manuscript contains pooled estimates,
  comparative-arm values, `[VERIFY-CSV]` tags, or is a post-v1 revision. Greps all analysis
  scripts for hand-typed numerical literals without CSV-coordinate comments and flags them
  as structural risks regardless of current correctness.

All four skills cite the CBCT Ablation MA-2 Du 2023 incident as precedent to make the
failure mode concrete rather than abstract. Complementary companion rules were added to
`~/.claude/rules/data-integrity.md` and a new `~/.claude/rules/numerical-safety.md` so the
gates trigger even in non-skill workflows.

## [2.2.1] - 2026-04-18

### Added

- **`/meta-analysis` Phase 3 multi-round screening structure**: Phase 3a now distinguishes Round 1 (single-reviewer initial screen), Round 2 (dual independent screen with Cohen's kappa), Round 3 (first-reviewer adjudication of disagreements), Round 4 (full-text), and PRISMA flow.
- **AI-assisted pre-screening template** (`meta-analysis/references/ai_pre_screening_template.py`): reusable script for compressing R3 adjudication. Generates AI suggestions only; first reviewer must independently confirm or overturn each. Includes Methods boilerplate citing model name and version. Companion priority-sort logic built in.

### Changed

- **`/meta-analysis` SKILL.md**: Phase 3 expanded from 17 to 39 lines (3a–3e). Maintains kappa requirement and adds explicit guidance for handling MAYBE-tagged records.

## [2.2.0] - 2026-04-18

### Added

- **5 new skills** (32 total): `humanize`, `author-strategy`, `peer-review`, `ma-scout`, `lit-sync`
  - **humanize**: 18-pattern AI writing detection and removal for academic manuscripts
  - **author-strategy**: PubMed author profile analysis with study type classification and strategy report
  - **peer-review**: Structured peer review drafting with journal-specific formatting (RYAI, INSI, EURE, AJR, KJR)
  - **ma-scout**: Meta-analysis topic discovery — professor-first or topic-first modes with PubMed E-utilities, PROSPERO check, and PICO scaffolding (732 lines, largest new skill)
  - **lit-sync**: Zotero + Obsidian reference sync pipeline with cross-cutting concept note extraction
- **Anti-hallucination clauses** added to all 32 skills. Domain-specific rules prevent fabricated variables, effect sizes, citations, and clinical definitions.
- **SKILL_TEMPLATE.md** (`docs/`) — canonical template for new skill creation with quality tier requirements
- **validate_skills.sh** (`scripts/`) — automated skill linter checking frontmatter, anti-hallucination, gates, line count tier, and reference integrity
- **3-country harmonization CSV** (`replicate-study/references/harmonization_3country.csv`) — KNHANES+NHANES+CHNS variable mapping (45 rows)

### Changed

- **cross-national**: Expanded from 2-country to 3-country support (KNHANES+NHANES+CHNS). Added ~100 lines of validated variable codings for KNHANES, NHANES, and CHNS with specific warnings (BMI cutoffs, hemoglobin units, survey weight handling). Added composite score replication warnings from LE8 validation.
- **batch-cohort**: Added physician-diagnosis requirement for outcome definitions (rule 8) and full 8-covariate default (rule 9). Expanded self-adjustment removal for education/income/MetS.
- **replicate-study**: Added 3-country harmonization reference.
- **fulltext-retrieval**: Fixed frontmatter (added missing `tools` and `model` fields).

### Infrastructure

- All 32 skills now pass `validate_skills.sh` with 0 FAIL.
- Quality tier distribution: 15 HIGH (300+ lines), 14 MID (150-300), 3 THIN (<150).

## [2.1.0] - 2026-04-15

### Added

- **find-cohort-gap**: New skill for systematic research gap discovery from cohort databases. 6-phase pipeline (cohort intake → PI profiling → intersection matrix → literature saturation scan → 6-Pattern scoring with comparison tables → feasibility gate → ranked one-pager proposals). Works with any cohort: NHIS, UK Biobank, institutional EMR, health checkup registries. Includes 4 reference files (pattern scoring rubric, cohort profile template, one-pager template, saturation query templates). Integrates with `/search-lit` for PubMed searches and feeds into `/design-study` → `/write-paper` pipeline.

## [2.0.0] - 2026-04-14

### Changed

- **Demos regenerated with `orchestrate --e2e` pipeline.** All 3 demos now produce a consistent artifact set: `analyze.{py,R}`, `_analysis_outputs.md`, `_pipeline_log.md`, `manuscript.md`, `manuscript_final.docx`, `reporting_checklist.md`, `review_comments.md`, `figures/_figure_manifest.md`, and study-type-specific tables and figures.
- Demo output structure flattened: `tables/` replaces `output/` for CSV files; manuscript and QC artifacts live at demo root.
- Previous demo scripts and outputs archived to `demo/_archive/` for reference.

### Added

- **Demo 1 (Wisconsin BC, STARD):** 19 artifacts. STARD flow diagram (D2), reporting checklist (82.1% compliance), self-review (74/100), submission-ready DOCX.
- **Demo 2 (BCG Vaccine, PRISMA):** 24 artifacts. R metafor analysis with forest plot, funnel plot, bubble plot, PRISMA flow diagram (D2), reporting checklist (77.8% compliance), self-review (72/100), submission-ready DOCX.
- **Demo 3 (NHANES Obesity, STROBE):** 23 artifacts. Python analysis with prevalence chart, OR forest plot, HbA1c distribution, age x BMI subgroup plot, STROBE flow diagram (D2), reporting checklist (81.8% compliance), self-review (75/100), submission-ready DOCX.
- `CHANGELOG.md` (this file).

### Pipeline artifacts (new in each demo)

| Artifact | Description |
|----------|-------------|
| `_pipeline_log.md` | 7-step execution trace with pass/fail status |
| `_figure_manifest.md` | Structured figure inventory for downstream consumption |
| `reporting_checklist.md` | Item-by-item guideline compliance assessment |
| `review_comments.md` | Self-review with Major/Minor classification and scores |
| `manuscript_final.docx` | Pandoc-built submission-ready Word document |

## [1.0.0] - 2026-04-08

Initial release with 22 skills and 3 demo pipelines.
