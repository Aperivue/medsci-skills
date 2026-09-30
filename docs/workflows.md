# Workflows and skill boundaries

How the skills combine into workflows, which skill to use when two look alike, and the
cross-skill checks that run along the way. Moved here from the README in v6.0; phase and step
numbers refer to each skill's `SKILL.md`, and each skill's [reference page](skills/README.md) is
the current description.

- [Start here: three workflows](#start-here-three-workflows)
- [Common tasks, step by step](#common-tasks-step-by-step)
- [Skill boundaries — which to use, and in what order](#skill-boundaries--which-to-use-and-in-what-order)
- [How the skills connect](#how-the-skills-connect)
- [Integrity checks that span skills](#integrity-checks-that-span-skills)

## Start here: three workflows

New users don't need all the skills at once. Most work starts as one of three
workflows. Each runs through `/orchestrate` or by invoking the named skills in
order; all outputs require human-expert review.

**Workflow A — Manuscript pre-submission audit.** *Use when* a manuscript is nearly
ready and you want it checked before a reviewer sees it. *Skills:* `/self-review` →
`/check-reporting` → `/verify-refs` → `/sync-submission`. *In:* your manuscript
(+ `refs.bib`, tables/figures). *Out:* anticipated reviewer comments, an item-by-item
reporting-guideline audit, a citation-integrity report, and a submission-package
drift check. *Safety:* it flags issues; you fix and verify them.

**Workflow B — Data to manuscript package.** *Use when* you have a cleaned dataset
and need a full draft. *Skills:* `/clean-data` → `/analyze-stats` → `/make-figures` →
`/write-paper` → `/check-reporting` → `/find-journal`. *In:* a cleaned CSV/parquet
+ a research question. *Out:* reproducible analysis code, publication-ready figures,
an IMRaD draft, a reporting checklist, and a journal shortlist. *Safety:* statistics
and claims must be verified against your data; the toolkit never fabricates numbers
or references.

**Workflow C — Systematic review / meta-analysis.** *Use when* you are running an
SR/MA. *Skills:* `/meta-analysis` (with `/search-lit`, `/make-figures`,
`/check-reporting`). *In:* a research question + search strategy. *Out:* PROSPERO-style
protocol scaffolding, screening/extraction structure, PRISMA-consistent counts and
diagram, pooled-estimate figures, and a manuscript draft. *Safety:* screening and
extraction decisions stay with the human review team.

## Common tasks, step by step

**"I have data and want a complete manuscript with zero manual steps."**
```
/orchestrate --e2e      # Autonomous: analyze → figures → write → QC → DOCX
```
Or equivalently: `/write-paper --autonomous` if analysis and figures already exist.

**"I have a diagnostic accuracy study draft and need to check compliance."**
```
/design-study          # Review study design for leakage and bias
/analyze-stats         # Generate DTA statistics (sensitivity, specificity, AUC with CIs)
/make-figures          # Create ROC curve + STARD flow diagram
/check-reporting       # Audit against STARD checklist
```

**"I'm starting a meta-analysis and need to find relevant studies."**
```
/search-lit            # Systematic search across PubMed + Semantic Scholar
/fulltext-retrieval    # Batch download open-access PDFs for included studies
/meta-analysis         # Full DTA or intervention MA pipeline
/make-figures          # Forest plot + PRISMA flow diagram
/check-reporting       # Audit against PRISMA-DTA checklist
```

**"I need to present a paper at journal club."**
```
/present-paper         # Analyze paper, find supporting refs, draft speaker script
```

**"I need to submit an IRB protocol for a new study."**
```
/search-lit            # Background literature for rationale
/design-study          # Validate study design, identify bias risks
/calc-sample-size      # Power analysis with IRB justification text
/write-protocol        # Generate 4 core sections + 6 skeleton sections
```

**"I have an interesting case to publish."**
```
/write-paper           # Case report mode (CARE 2016, 1000-word short-form)
/self-review           # Pre-submission self-check
/find-journal          # Which journal accepts case reports in this field?
```

**"My paper was rejected. Where else should I submit?"**
```
/find-journal          # Exclude rejected journal, recommend alternatives
/write-paper           # Generate new cover letter (Phase 8+)
```

**"I have messy clinical data that needs cleaning before analysis."**
```
/deidentify            # Remove PHI from clinical data (standalone Python, no LLM)
/clean-data            # Profile dataset, flag issues, generate cleaning code
/analyze-stats         # Run statistics on cleaned data
/make-figures          # Publication-ready figures
```

**"I want to write a grant proposal for a radiology AI project."**
```
/design-study          # Validate study design before writing
/grant-builder         # Structure significance, innovation, approach
/search-lit            # Find supporting literature with verified citations
```

## Skill boundaries — which to use, and in what order

The skill set is deliberately *specialized, not consolidated* — each skill owns a distinct artifact or lifecycle step, so the routing stays precise. The boundaries that are easy to confuse:

- **Reference pipeline** — `search-lit` (discover candidates) → `lit-sync` (sole writer of `refs.bib`, syncs Zotero/Obsidian) → `manage-refs` (render CSL / inject CWYW / cross-ref QC, sole writer of the rendered DOCX) → `verify-refs` (read-only audit; never edits `refs.bib`). They are one pipeline, not four overlapping tools.
- **Language passes run in order** — `humanize` (remove AI-writing tells) → `polish-language` (deterministic ESL/house-style consistency: abbreviations, spelling, en-dashes, p-value case) → `academic-aio` (AI-search/GEO visibility). Three sequential passes with non-overlapping jobs.
- **Manuscript type picks the skill** — `write-paper` (original/IMRAD articles, case reports, MAs) vs `review-paper` (narrative / scoping / systematic literature reviews) vs `revise` (reviewer-response + tracked changes). Different structures and reporting guidelines.
- **Author vs external reviewer** — `self-review` is your own pre-submission check (anticipated comments); `peer-review` drafts a journal-facing review as an external reviewer. Same domain probes, different user and output.
- **Project entry** — `intake-project` classifies and scaffolds a *new or messy folder*; `orchestrate` routes a *goal or task* ("help me write a paper"). Start with `intake-project` when you have files but no structure, `orchestrate` when you have a task but no plan.
- **Study design** — `design-study` covers general validity (analysis unit, leakage, comparator, validation) **and** carries a design-stage ceiling gate for perceptual / observer / reader / visual-Turing-test / image-provenance studies; `design-ai-benchmarking` specializes in AI-vs-human-expert evaluation (rubrics, calibration probes, LLM-as-judge).
- **Content vs template** — `write-protocol` drafts IRB/ethics scientific content; `fill-protocol` renders that content into an institutional Word template without breaking its formatting.

## How the skills connect

### Autonomous end-to-end pipeline

`orchestrate --e2e` or `write-paper --autonomous` runs the full pipeline from data to submission-ready DOCX with bounded validation. Skills pass outputs via structured manifests (`_analysis_outputs.md`, `_figure_manifest.md`) and project artifacts (`project.yaml`, `artifact_manifest.json`, `qc/status.json`). If a skill fails to produce expected outputs, the pipeline halts rather than proceeding with missing data. Phase 7 enforces a strict QC chain: AI pattern removal → reporting compliance check → `/verify-refs` citation audit → numerical claim audit → self-review with auto-fix (max 2 iterations) → DOCX/submission build.

### IRB protocol to submission in one pipeline

`design-study` -> `calc-sample-size` -> `write-protocol` gives you an IRB-ready protocol. After data collection: `clean-data` -> `analyze-stats` -> `write-paper` -> `self-review` -> `find-journal` -> cover letter. Every transition is a defined skill handoff.

### Skills work together

Skills call each other. `check-reporting` invokes `make-figures` for PRISMA diagrams. `write-paper` calls `search-lit` for citation verification. `self-review` delegates reporting compliance to `check-reporting`. `calc-sample-size` output feeds directly into `write-protocol`'s IRB justification section.

### Skill flow diagram

A v5-era overview; it predates the model-engineering skills, which are listed in the
[README skill map](../README.md#skills).

```
                              ┌─────────────────────────────────┐
                              │  orchestrate: single entry point │
                              │  classifies intent, routes to    │
                              │  the right skill or chains them  │
                              └───────────────┬─────────────────┘
                                              │
                  ┌───────────────────────────┼───────────────────────────┐
                  │                           │                           │
            intake-project              (main pipeline)             grant-builder
            (new/messy projects)              │                    (proposals)
                  │                           │
                  ▼                           ▼
                                    ┌── calc-sample-size ──┐
                                    │                      ▼
ma-scout -> search-lit -> fulltext-retrieval -> design-study ──> write-protocol -> manage-project
   │            │
   │            └── find-cohort-gap (DB variables → literature gap → ranked topic proposals)
   │                                    │
   │                                    ▼
   │                         deidentify -> clean-data -> analyze-stats -> make-figures -> write-paper
   │                                                        │                                │
   │                                           replicate-study (paper → new DB)         humanize
   │                                           cross-national (parallel survey)              │
   │                                           batch-cohort (N × M matrix)                   ▼
   │                                                                          find-journal <── self-review
   │                                                                               │                    │
   │                                                                               │                    ▼
   │                                                                               │          humanize -> academic-aio (AI-search visibility)
   │                                                                               ▼
   │                                                    [cover-letter] -> check-reporting -> revise -> present-paper
   │                                                                                                       │
   └── meta-analysis                                                                                  peer-review
                         lit-sync (Zotero + Obsidian sync)     author-strategy (PubMed profile analysis)

                              ┌─────────────────────────────────────────────┐
                              │  publish-skill: package any skill above for │
                              │  open-source distribution (PII audit,       │
                              │  license check, generalization)             │
                              └─────────────────────────────────────────────┘
                              ┌─────────────────────────────────────────────┐
                              │  add-journal: add new journal profiles to   │
                              │  the database (write-paper + find-journal   │
                              │  dual profile generation with quality gates)│
                              └─────────────────────────────────────────────┘
```

## Integrity checks that span skills

### Anti-hallucination citations

Every reference produced by `search-lit` is verified against PubMed, Semantic Scholar, or CrossRef APIs. Existing manuscripts should then run `/verify-refs`, which writes a visible reference audit and blocks fabricated references before submission. No citation is ever generated from memory alone. API errors are batched silently -- no token waste from repeated failure messages.

### Anti-hallucination numerical claims

`/meta-analysis` Phase 6b, `/self-review` Phase 2.5a, `/revise` Step 2.5, and `/write-paper`
Step 7.3a enforce a common 3-layer audit (CSV ↔ analysis script ↔ manuscript) with primary-
source back-checking for pooled estimates and revision-era numbers. Hand-typed numerical
matrices without CSV-coordinate comments are flagged as structural risks even when the values
are currently correct, since the next revision will re-introduce the same failure mode.

### Reference safety (Phase 1)

Projects declare their source-of-truth layout in `SSOT.yaml`, and a `qc/migration_complete` marker gates strict enforcement. `/verify-refs` is the sole writer of `qc/reference_audit.json`. The `MEDSCI_VERIFY_REFS_MODE` env var (`auto` default, `warn`, `enforce`, `off`) controls behavior — `auto` blocks only when both SSOT.yaml and the migration marker are present, otherwise warns. Legacy projects freeze as warn-only; new projects opt in via `scripts/migrate_project_to_ssot.py`. An optional PostToolUse hook (not shipped in this repo — document only) can invoke `/verify-refs` automatically on manuscript saves for users who install it locally at `~/.claude/hooks/verify-refs-guard.sh`; the regression suite (`tests/test_phase1c_hooks.sh`) runs end-to-end only when that local hook is present and is skipped otherwise. The hook gates saves under `*/submission/*/manuscript/*.{docx,md}` and `*/revision/R*/…circulation….docx` (enforce-eligible), and — added for issue #14 — also **warn-only** on pre-submission and mentor-circulation drafts that previously skipped the audit entirely: `*/outgoing/*.{docx,md}`, `*/8_Review_Comments/*/outgoing/*.{docx,md}`, and any `*/circulation/*.{docx,md}`. Warn-only patterns surface a missing audit without blocking rapid iteration and never enforce, regardless of SSOT/migration state.

### Meta-analysis failure modes

`/meta-analysis` ships empirical failure-mode references (data integrity, review orchestration, submission package drift, post-submission release ops) with four automation hooks: `scripts/prisma_5way_consistency.py` (DI-6 PRISMA number consistency), `scripts/extraction_consensus_log_init.py` (DI-1 dual-extraction scaffold), `scripts/tag_cleanup_gate.sh` (DI-8 placeholder tag gate), and `/sync-submission`'s `scripts/verify_package_integrity.py` (SPD SHA-256 manifest for submission bundles).

### Per-skill features

Reporting-guideline and risk-of-bias checklists, publication-ready tables and figures, and the
Results/Discussion boundary rules are described on the reference pages for
[`check-reporting`](skills/check-reporting.md), [`analyze-stats`](skills/analyze-stats.md),
[`make-figures`](skills/make-figures.md) and [`write-paper`](skills/write-paper.md).
What the deterministic detectors cover, and which have been formally evaluated, is in
[`MEDSCI_AUDIT.md`](../MEDSCI_AUDIT.md).
