# Changelog

## [Unreleased]

### Added — New skill `/academic-aio` + pipeline integration across README, write-paper, orchestrate, PLAN_E2E_PIPELINE

Medical AI paper optimization for AI search engines (Perplexity, ChatGPT web, Elicit,
Consensus, SciSpace) and RAG-based literature tools. Integrates TRIPOD+AI, CLAIM,
STARD-AI, TRIPOD-LLM, and DECIDE-AI reporting anchors with generative-engine-optimization
(GEO) principles from Aggarwal 2024 (arXiv:2311.09735). Scope covers title, abstract,
structured summary boxes (Key Points / Research in Context / Plain-Language Summary),
preprints, GitHub README, `CITATION.cff`, Zenodo, and Hugging Face model / dataset
cards. Explicit defense against LLM citation fabrication (Agarwal 2025, Nat Commun
doi:10.1038/s41467-025-58551-6, which reports up to 78–90% fabricated citations in
medical LLM answers). Produces a visible PASS/PARTIAL/FAIL checklist; never applies
edits silently (Communication Rules).

**Pipeline integration** (added in this release, not in the new skill itself):
- `README.md`: skill-table row added + main pipeline diagram branches
  `humanize → academic-aio` off the self-review / find-journal spine.
- `write-paper/SKILL.md` Skill Interactions table: new rows 7.5 (`/humanize`) and
  7.5a (`/academic-aio` opt-in `--aio`), running after `/self-review` Phase 7.4
  and before DOCX build (Phase 7.6).
- `orchestrate/SKILL.md`: (a) new multi-skill-workflow row "Medical-AI paper,
  AI-search visibility pass" with N4 + N9 nodes; (b) existing "Draft exists,
  prepare for submission" chain extended to `humanize → academic-aio (--aio)`;
  (c) new `--e2e` clause #8 specifying AIO is OFF by default in autonomous
  mode (AI-search visibility is a pre-submission, not a pre-draft, concern and
  autonomous silent rewrites would violate AIO's "never edit silently"
  contract) — opt-in via `--aio`, report always surfaced to user.
- `PLAN_E2E_PIPELINE.md`: new AIO-position section justifying 7.5a placement
  (after `check-reporting` so the Section 1.6 guideline anchor reflects real
  compliance; after `humanize` so the human-readability pass does not erase
  AIO edits; before DOCX build so the optimizations reach the final artifact)
  and documenting the Anti-Hallucination division of labour with
  `search-lit` / `check-reporting` / `write-paper` / `humanize`.

**Anti-Hallucination block added to `/academic-aio` SKILL.md**: bars fabricated
citations / DOIs / arXiv IDs / reporting-guideline item numbers; bars invented
journal-specific summary-box rules (Lancet Digital Health "Research in context",
Radiology "Key Points", npj Digital Medicine); bars fabricated AI-search
discoverability metrics (Perplexity / Elicit / Consensus retrieval scores may
only be reported from recorded probes); bars auto-completion of CITATION.cff
and Zenodo author lists, ORCIDs, and affiliations. This closes the last
validator FAIL from the v2 content-integrity lint rollout.

**Skill count**: 32 → 33. Validator reports 265 PASS / 32 WARN / 0 FAIL after
these changes.

### Changed — Reference split for `/meta-analysis` Phase 4 & Phase 6 (R templates + KM/composite)

`/meta-analysis` SKILL.md had two oversized phases after the earlier Phase 9/10 split:
Phase 6 (Statistical Synthesis) ran 119 lines with full R code for DTA bivariate models,
intervention `metagen`/`metabin`, the dual-approach comparative + single-arm pooled
proportion decision table, practical R notes (method.tau, HK CI, zero-cell correction),
publication-bias test power, and sensitivity-analysis menu; Phase 4 (Data Extraction)
contained two specialised sub-procedures — KM curve reconstruction via WebPlotDigitizer
+ `IPDfromKM` (Guyot 2012) and composite-exposure disaggregation — that together ran
~40 lines. Both were moved to `references/phase6_statistical_synthesis.md` (148 lines)
and `references/phase4_km_composite.md` (58 lines), with SKILL.md bodies retaining a
one-table summary + load-on-demand pointer. Net impact: `/meta-analysis` 594 → 459
lines (−135, cumulative −281 from 740 pre-recovery-loop inlined state).

### Changed — Korean→English prose translation for `/ma-scout`, `/lit-sync`, `/grant-builder`, `/deidentify`

Four skills carried substantial Korean prose body text that tripped rule 9 of the v2
content-integrity lint (Korean outside code/tables/Communication Rules/frontmatter).
Translations preserve Korean domain terms in parenthetical references where they are
literal references to the Korean research system (Korean government agency names in
`/grant-builder`: 복지부=MOHW, 산자부=MOTIE, 중기부=MSS; Korean attachment names:
첨부1-3; Korean vault folder paths in `/lit-sync`: `02 연구/문헌/`, `02 연구/개념노트/`;
Obsidian note template headings in `/lit-sync` that must match the user's existing vault
convention: `## 서지 정보`, `## 핵심 내용`, `## 내 생각`, `## 관련 노트`). `/ma-scout`
also extracted the 72-line bilingual PROSPERO-ready README template block to
`references/project_readme_template.md` (includes Solo-Mode Adaptations for topic-first
mode without supervisor) and replaced the inlined block with a load-on-demand pointer.
Net impact: all four skills now pass lint rule 9 for SKILL.md body text; remaining
Korean is confined to frontmatter triggers (permitted), literal template content, and
Obsidian vault paths (the 32 outstanding WARNs are legitimate Korean-in-parenthesis
references that are not targeted by the rule).

### Changed — Reference split for `/meta-analysis` Phase 9/10, `/check-reporting` Step 4c, `/write-paper` Step 7.4a

The recently added recovery-loop phases were fully inlined in `SKILL.md` bodies,
inflating three skill files beyond what load-on-demand expects. Procedural detail was
extracted to new reference files (`meta-analysis/references/phase9_circulation.md`,
`phase10_recovery.md`, `check-reporting/references/step4c_registration_timing.md`,
`write-paper/references/section_guides/step7_4a_audit_recovery.md`) with SKILL.md bodies
retaining only the trigger table, routing table, and summary paragraph plus a
`Load-on-demand procedural detail` pointer. Net impact: `/meta-analysis` 740 → 594
lines (−146), `/check-reporting` 425 → 376 (−49), `/write-paper` 853 → 829 (−24). Pattern
follows the existing `checklists/QUADAS2.md` load-on-demand convention. All nine
content-integrity lints continue to pass.

### Added — `scripts/validate_skills.sh` v2 content-integrity lints + pre-commit hook

The validator previously checked frontmatter, size tiers, and reference integrity but
could not catch content regressions that had accumulated over prior sessions. v2 adds
four content-integrity rules scoped to shipped skill prose (`SKILL.md` plus
`references/**/*.md`, excluding `HANDOFF.md` and `TODO_*.md` meta-docs):
**Rule 6** blocks project-specific precedent identifiers (`CBCT Ablation MA`,
`Du 2023`, `FD Occlusion AI SR`, `Paper ①/②/③`) from leaking into shipped skills;
**Rule 7** blocks absolute `/Users/eugene/` paths in shipped prose (scripts and
exemplar `.meta.yaml` fixtures are out of scope); **Rule 8** flags dated precedent
blockquotes (`^> ... YYYY-MM-DD`) while allow-listing `Last updated:` / `Created:` /
`Updated:` / `Date:` meta-header prefixes; **Rule 9** warns on Korean prose in
`SKILL.md` body outside fenced code blocks, tables, blockquote examples, the
Communication Rules section, and frontmatter (Korean triggers remain permitted).
Rules 6–8 are FAIL-level; rule 9 is WARN-only pending per-skill translation
decisions. A `.git/hooks/pre-commit` hook runs the validator automatically when any
`skills/**/*.md` or the validator itself is staged, early-exiting otherwise to keep
non-skill commits fast.

### Changed — `/orchestrate` Dialogue Protocol is now the default interactive execution path

The prior interactive flow was a plain bulleted plan followed by "Shall I proceed with
step 1?" — a confirmation that surfaced no lock-in cost. The revised **Workflow Execution
— Dialogue Protocol** section makes per-fork decision-node rendering the primary control
flow: identify the node, render the template (context + numbered options + per-option
`unlocks` / `locks` / `recovery_cost`), wait for a numeric choice or a control word
(`back` / `pause` / `skip`), echo the lock in one line, invoke the matched skill, and
return for the next fork. The Multi-Skill Workflows table gained a **Nodes** column that
maps each scenario to the N1 – N9 node IDs. The `--e2e` Flag section now prescribes
node-by-node default application with per-node logging to `qc/_pipeline_log.md`, and
specifies that the PHI gate (N6) is the sole node that can HALT autonomous mode, while
Audit Recovery (N8) HALTs only when the routed recovery fails validation twice. The
Output Format multi-skill example was replaced with a worked N2 Paper Type rendering to
anchor downstream rendering style.

### Added — `/orchestrate` Dialogue Mode prototype (RPG-style decision nodes)

`/orchestrate` previously executed multi-skill pipelines with plan-then-confirm but
did not surface the downstream cost of each commitment (paper type, study design,
target journal timing, MA synthesis scope, audit recovery branch). The new
**Dialogue Mode** is the interactive default: at each major fork, the orchestrator
renders a decision node (context, numbered options, per-option `unlocks` / `locks` /
`recovery_cost`) and the user picks a number. `--autonomous` / `--e2e` bypasses the
rendering and uses each node's `default`, logging the choice to
`qc/_pipeline_log.md`. The prototype lists 9 primary nodes — entry classification,
paper type, study design (STARD/CONSORT/STROBE/TRIPOD+AI), target-journal timing
(commit-now vs. late-bind), MA synthesis depth (primary / +subgroups / +sensitivity /
+meta-regression), PHI Safety Gate, autonomy flag, Step 7.4a audit recovery branch,
and `/write-paper` section entry on re-entry — with rendering templates and
autonomous-default rationales. Load-on-demand reference at
`skills/orchestrate/references/dialogue_nodes.md`; `SKILL.md` body gains only a
one-paragraph pointer to preserve token economy.

### Added — `/meta-analysis` Phase 9 (Co-author Circulation) + Phase 10 (Self-Audit Recovery)

The pipeline previously stopped at Phase 8 (Reporting & Manuscript), leaving two operational
loops undocumented. **Phase 9** standardizes pre-submission circulation: thread-reply
continuity, attachment scope (body + change summary only; exclude GA / cover letter / COI
until journal is confirmed), recipient structure (corresponding + one senior methodologist
TO, co-authors CC), the 7-day deadline rule, and journal-undetermined framing. **Phase 10**
formalizes the v{N} → v{N+1} rebuild sprint when an audit uncovers structural data or
protocol-application errors — audit log, CSV re-verification, analysis re-run, manuscript
auto-sync, figure regeneration, change summary, protocol-registry amendment in parallel,
and the transparent re-circulation framing. Triggers include extraction ↔ source
mismatch, protocol-analysis disagreement, hand-typed script literal errors, and
consensus-record ↔ locked-dataset disagreement. Anti-patterns (hide & submit, reframe as
"minor revision", cover-letter-only disclosure) are documented as do-not.

### Added — `/write-paper` Step 7.4a Audit Recovery Branch

Phase 7 polish was a linear flow (draft → review → revise → submit) that silently proceeded
past structural self-review findings. Step 7.4a makes the recovery loop explicit: when
Step 7.4 returns a fatal `accuracy`, `data_fidelity`, `protocol_mismatch`, or
`numerical_claim` issue, an unresolved Step 7.3a primary-source disagreement, a persistent
`[VERIFY-CSV]` tag, or a registry ↔ analysis inconsistency, the pipeline halts Steps 7.5 –
7.6 and routes to the appropriate upstream recovery. For MA manuscripts this is
`/meta-analysis` Phase 10; for non-MA manuscripts with extraction errors, back to
`/write-paper` Phase 2; protocol amendments halt for human decision. On re-entry the
pipeline resumes at Step 7.3, not Step 7.1, because recovery may have introduced new
citations. Loop budget: one recovery cycle expected; a second cycle on the same manuscript
prompts a root-cause review of Phase 2 / 6 / 6b.

### Added — `/check-reporting` Step 4c Registration / Protocol Timing Consistency Check

The registration identifier alone is a single checklist item and passes even when the
manuscript is internally inconsistent about registration / amendment timing. Step 4c
audits five consistency items: registration identifier present in Methods/Abstract/
cover letter, registration date ↔ screening/extraction milestone order, amendment date ↔
Methods-described change agreement, cross-artifact agreement between Methods and the
registry record (e.g., PROSPERO PDF), and retrospective-registration disclosure when
the registration date post-dates extraction start. Findings carry the
`[REGISTRATION-TIMING]` label in Part C Action Items, with `fixable_by_ai: false` when
reconciliation requires an external amendment filing. A new `registration_timing` JSON
field is emitted in Part D. Applies to PRISMA 2020, PRISMA-DTA, PRISMA-P, MOOSE, CONSORT,
and SPIRIT. Common Gaps list updated to include amendment-date consistency as item #2.

### Added — Verified neurointervention/cerebrovascular journal profiles

- **JNIS (Journal of NeuroInterventional Surgery)** — compact + detail profiles built from user-supplied author-guidelines PDF (BMJ, SNIS). Covers double-anonymised review, ORCID mandate, BMJ Tier 3 data-sharing policy, Key Messages box requirement, AI policy aligned with BMJ/ICMJE.
- **Journal of Stroke** (Korean Stroke Society) — compact + detail profiles from user-supplied author-guidelines PDF. Full OA CC BY-NC 4.0 with no APC; Vancouver numbered references; structured 250-word abstract for Original Articles; mRS/mTICI/sICH definition requirements; AI policy defaults to ICMJE/WAME (no explicit journal-specific text).
- **Stroke (AHA/ASA)** — compact + detail profiles from user-supplied author-instructions PDFs. ISSN verified against ISSN Portal (print 0039-2499 / online 1524-4628, ISSN-L 0039-2499). Three-category science triage (Basic/Translational, Clinical, Population); structured 300-word abstract; Vancouver references listing first 10 authors + "et al."; 90-day revision window with mandatory Graphic Abstract at revision; explicit AI policy per AHA/ICMJE.

All three profiles follow the two-tier public-library format established by `INSI.md` and include a verification note citing the source author-guidelines PDF.

### Added — `/find-journal` Phase 3.6 Profile Coverage Advisory

Previously, when the public profile library had a known gap for the manuscript's field,
the ranking silently substituted adjacent journals and the user never learned that a
better-fitting target existed. The new Phase 3.6 scans `skills/find-journal/TODO_*_profiles.md`
files, matches their `## Field Keywords` block against the manuscript's themes, and appends
a Coverage Advisory block between the comparison note and the Mandatory Disclaimer when
a relevant TODO has still-missing journals. The advisory names the missing journals,
cites their publisher and 1-line rationale verbatim from the TODO file, and directs the
user to `/add-journal` with a PDF to close the gap per `POLICY.md`. No false alarms when
no TODO is relevant.

`TODO_neurointervention_profiles.md` updated with a `## Field Keywords` section so it
feeds the advisory. Future field TODO files should follow the same convention.

### Added — `/write-paper` Step 7.3a trigger 5 (reporting-quality checklist SRs)

Step 7.3a Numerical Claim Audit previously fired only on pooled estimates, comparative-arm
values, `[VERIFY-CSV]` tags, or post-v1 revisions. It missed the reporting-quality
systematic review pattern, where all headline numbers are derived by counting cells in an
items × studies checklist matrix (TRIPOD+AI, PROBAST+AI, CLAIM, PRISMA, STARD, CHARMS,
ARRIVE). The same failure class applies — hand-tallied totals drift from cell-level truth
while every downstream artifact echoes the wrong number.

Trigger 5 is now mandatory whenever the manuscript reports corpus-level, study-level, or
item-level PRESENT / PARTIAL / ABSENT / compliance counts or percentages from a checklist
synthesis. The procedure adds five steps specific to this pattern: per-study totals
recomputation, corpus-level Σ non-NA denominator, item-level roll-up, 3-way consistency
(manuscript ↔ per-study JSON ↔ summary document), and a reproducible audit script that
emits `numerical_claims_log.csv` and exits non-zero on any mismatch.

A companion rule is recorded in `~/.claude/rules/numerical-safety.md` so the gate
triggers even in non-skill workflows.

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

All four skills reference the revision-era Fisher-exact reversal pattern described above as
a concrete failure mode rather than an abstract risk. Complementary companion rules were
added to `~/.claude/rules/data-integrity.md` and a new `~/.claude/rules/numerical-safety.md`
so the gates trigger even in non-skill workflows.

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
