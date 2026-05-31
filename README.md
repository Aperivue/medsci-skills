<div align="center">

# MedSci Skills

**40 skills that actually work.** Built by a physician-researcher, tested on real publications.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
![Skills](https://img.shields.io/badge/Skills-40-brightgreen?style=flat-square)
![Platform](https://img.shields.io/badge/Platform-Claude_Code-blueviolet?style=flat-square)
![Built by](https://img.shields.io/badge/Built_by-Physician--Researcher-blue?style=flat-square)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20155321.svg)](https://doi.org/10.5281/zenodo.20155321)
[![Citation](https://img.shields.io/badge/Cite-CITATION.cff-blue?style=flat-square)](CITATION.cff)

![MedSci Skills](assets/social-preview.png)

*Topic Discovery &rarr; Literature Search &rarr; Full-Text Retrieval &rarr; Study Design &rarr; Sample Size &rarr; Protocol &rarr; De-identification &rarr; Data Cleaning &rarr; Statistics &rarr; Figures &rarr; Writing &rarr; Humanize &rarr; Compliance &rarr; Journal Selection &rarr; Peer Review &rarr; Revision &rarr; Presentation*

</div>

![check-reporting demo](demo.gif)

---

## What's New

The v2.10 cycle expands the public workflow surface while tightening release hygiene:

- `/peer-review` v2.10 adds the Phase 2A SR-MA 8-probe extension (P1-P8) for systematic review meta-analyses (PR #22).
- `/verify-refs` v1.2.0 adds Gate 5 PMID/DOI duplicate detection plus synchronous `submission_safe` / `fully_verified` propagation (PR #23).
- `/meta-analysis` adds SR-MA dual-extractor workflow support, cohort overlap detection, and a supplementary 8-file pack (PR #24).
- Validator coverage now enforces the PII blocklist across `templates/` and `scripts/` as well as skill documentation.

---

## Live Demos: Three Study Types, Three Full Pipelines

Three public datasets. Three study types. Each produces a complete manuscript, publication-ready figures, reporting compliance audit, and presentation slides.

| Demo | Dataset | Study Type | Compliance |
|------|---------|------------|------------|
| [Demo 1: Wisconsin BC](demo/01_wisconsin_bc/) | `sklearn` built-in | Diagnostic accuracy | STARD 2015 |
| [Demo 2: BCG Vaccine](demo/02_metafor_bcg/) | `metafor::dat.bcg` (13 RCTs) | Meta-analysis | PRISMA 2020 |
| [Demo 3: NHANES Obesity](demo/03_nhanes_obesity/) | CDC NHANES 2017-18 | Epidemiology (survey) | STROBE |

### Demo 1: Diagnostic Accuracy — Wisconsin Breast Cancer

```python
from sklearn.datasets import load_breast_cancer
data = load_breast_cancer()  # 569 samples, zero download
```

**Output from `orchestrate --e2e`** ([see full demo](demo/01_wisconsin_bc/)):

| Output | Description |
|--------|-------------|
| [Manuscript](demo/01_wisconsin_bc/manuscript/manuscript.md) | IMRAD draft, ~1,900 words |
| [Title Page](demo/01_wisconsin_bc/manuscript/title_page.md) | STARD title page with key points |
| [DOCX](demo/01_wisconsin_bc/manuscript/manuscript_final.docx) | Submission-ready Word document |
| [ROC Curve](demo/01_wisconsin_bc/analysis/figures/roc_curve.png) | 3-model comparison with DeLong 95% CIs |
| [STARD Flow](demo/01_wisconsin_bc/analysis/figures/stard_flow.svg) | D2-generated STARD 2015 flow diagram |
| [Reporting Checklist](demo/01_wisconsin_bc/qc/reporting_checklist.md) | STARD 2015 — 82.1% compliance (23/28 PRESENT) |
| [Self-Review](demo/01_wisconsin_bc/qc/self_review.md) | Score 83/100 (2 fix iterations; initial 74), 4 major / 5 minor |
| [Pipeline Log](demo/01_wisconsin_bc/qc/_pipeline_log.md) | 7-step E2E execution trace |
| [Presentation](demo/01_wisconsin_bc/presentation/presentation.pptx) | 12 slides with speaker notes |
| [Cover Letter](demo/01_wisconsin_bc/submission/radiology_ai/cover_letter.md) | Example submission cover letter |

**Pipeline:** `analyze-stats` &rarr; `make-figures` &rarr; `write-paper` &rarr; AI pattern scan &rarr; `check-reporting` (STARD) &rarr; `self-review` &rarr; DOCX build &rarr; `present-paper`

### Demo 2: Meta-Analysis — BCG Vaccine Efficacy

```r
library(metafor)
data(dat.bcg)  # 13 RCTs, 357,347 participants (Colditz et al. 1994)
```

**Output from `orchestrate --e2e`** ([see full demo](demo/02_metafor_bcg/)):

| Output | Description |
|--------|-------------|
| [Manuscript](demo/02_metafor_bcg/manuscript/manuscript.md) | Pooled RR = 0.489 (95% CI: 0.344–0.696), ~2,600 words |
| [Title Page](demo/02_metafor_bcg/manuscript/title_page.md) | PRISMA title page with key points |
| [DOCX](demo/02_metafor_bcg/manuscript/manuscript_final.docx) | Submission-ready Word document |
| [Forest Plot](demo/02_metafor_bcg/analysis/figures/forest_plot.png) | 13 studies, RE model (REML), 300 dpi |
| [Bubble Plot](demo/02_metafor_bcg/analysis/figures/bubble_plot.png) | Meta-regression: latitude vs. RR (R² = 75.6%) |
| [PRISMA Flow](demo/02_metafor_bcg/analysis/figures/prisma_flow.svg) | D2-generated PRISMA 2020 flow diagram |
| [Reporting Checklist](demo/02_metafor_bcg/qc/reporting_checklist.md) | PRISMA 2020 — 77.8% compliance (21/27 PRESENT) |
| [Self-Review](demo/02_metafor_bcg/qc/self_review.md) | Score 82/100 (2 fix iterations; initial 72), 4 major / 5 minor |
| [Pipeline Log](demo/02_metafor_bcg/qc/_pipeline_log.md) | 7-step E2E execution trace |
| [Presentation](demo/02_metafor_bcg/presentation/presentation.pptx) | 12 slides with speaker notes |

**Pipeline:** `analyze-stats` (R metafor) &rarr; `make-figures` &rarr; `write-paper` &rarr; AI pattern scan &rarr; `check-reporting` (PRISMA 2020) &rarr; `self-review` &rarr; DOCX build &rarr; `present-paper`

### Demo 3: Epidemiology — NHANES Obesity & Diabetes

```python
# Pre-processed NHANES 2017-2018 CSV included
# 4,866 US adults after exclusions
```

**Output from `orchestrate --e2e`** ([see full demo](demo/03_nhanes_obesity/)):

| Output | Description |
|--------|-------------|
| [Manuscript](demo/03_nhanes_obesity/manuscript/manuscript.md) | Adjusted OR = 4.50 (95% CI: 3.23–6.27), ~2,800 words |
| [Title Page](demo/03_nhanes_obesity/manuscript/title_page.md) | STROBE title page with key points |
| [DOCX](demo/03_nhanes_obesity/manuscript/manuscript_final.docx) | Submission-ready Word document |
| [Prevalence Chart](demo/03_nhanes_obesity/analysis/figures/prevalence_by_bmi.png) | Diabetes prevalence by BMI with Wilson 95% CIs |
| [OR Forest Plot](demo/03_nhanes_obesity/analysis/figures/or_forest_plot.png) | Adjusted odds ratios for 7 variables |
| [Study Flow](demo/03_nhanes_obesity/analysis/figures/strobe_flow.svg) | D2-generated participant flow diagram |
| [Reporting Checklist](demo/03_nhanes_obesity/qc/reporting_checklist.md) | STROBE — 81.8% compliance (18/22 PRESENT) |
| [Self-Review](demo/03_nhanes_obesity/qc/self_review.md) | Score 85/100 PASS (2 fix iterations; initial 75), 4 major / 5 minor |
| [Pipeline Log](demo/03_nhanes_obesity/qc/_pipeline_log.md) | 7-step E2E execution trace |
| [Presentation](demo/03_nhanes_obesity/presentation/presentation.pptx) | 12 slides with speaker notes |

**Pipeline:** `analyze-stats` &rarr; `make-figures` &rarr; `write-paper` &rarr; AI pattern scan &rarr; `check-reporting` (STROBE) &rarr; `self-review` &rarr; DOCX build &rarr; `present-paper`

### Project Folder Structure

Each demo (and real project) follows this role-based folder layout:

```
project/
├── data/                          # Input data
│   └── raw_data.csv
├── analysis/                      # /analyze-stats + /make-figures outputs
│   ├── tables/
│   ├── figures/
│   │   └── _figure_manifest.md
│   ├── _analysis_outputs.md
│   └── analyze.py
├── manuscript/                    # /write-paper outputs
│   ├── manuscript.md
│   ├── manuscript_final.docx
│   └── title_page.md
├── qc/                            # Quality verification
│   ├── reporting_checklist.md     # /check-reporting
│   ├── self_review.md             # /self-review
│   └── _pipeline_log.md
├── submission/                    # Post-journal-selection (manual trigger)
│   └── {journal_short}/
│       ├── cover_letter.md
│       ├── checklist.md
│       └── peer_review.md
└── presentation/
    └── presentation.pptx
```

The E2E pipeline (`orchestrate --e2e`) produces everything up to `qc/`. The `submission/` directory is created after journal selection via `/find-journal`.

---

## Why This Repo?

| | MedSci Skills | Aggregator repos (400-900 skills) |
|---|---|---|
| **Citation quality** | Every reference verified via PubMed / Semantic Scholar / CrossRef API. Zero hallucinated citations. | No verification -- citations generated from model memory |
| **Pipeline integration** | Skills call each other in defined chains. `design-study` -> `calc-sample-size` -> `write-protocol`. | Standalone stubs with no cross-skill interaction |
| **End-to-end coverage** | From IRB protocol to journal submission: sample size, data cleaning, analysis, writing, compliance, journal selection, cover letter. | Gaps at every transition -- no protocol, no journal matching, no cover letter |
| **Battle-tested** | Used on real manuscript submissions by a practicing physician-researcher | Unknown provenance and validation |
| **Depth per skill** | 150-600 lines of documentation + bundled reference files (curated journal profile library, checklists, formula sheets, code templates) | Typically thin SKILL.md templates |

---

## What This Is NOT

This is **not** a broad scientific-tooling library — for cheminformatics, structural biology, or genomics pipelines, see [K-Dense scientific-agent-skills](https://github.com/K-Dense-AI/scientific-agent-skills) (135 skills). It is **not** a biomedical-skill aggregator — for the largest curated collection mirroring 12+ source repos, see [OpenClaw Medical Skills](https://github.com/FreedomIntelligence/OpenClaw-Medical-Skills) (869 skills).

MedSci Skills is **opinionated and narrow on purpose**: a single physician-researcher's medical-manuscript pipeline, biased toward radiology, diagnostic accuracy, observational EMR studies, and systematic review / meta-analysis. If you write IMRAD manuscripts for clinical journals, audit reporting compliance against EQUATOR guidelines, or run SR/MA workflows end-to-end, this is built for you. For wet-lab protocols, drug discovery, or single-cell genomics, the repos above are better fits.

---

## Skills

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

### Available Now

| Skill | What It Does |
|-------|-------------|
| **orchestrate** | Single entry point for the full bundle. Classifies your request and routes to the right skill -- or chains multiple skills for multi-step workflows. Full Pipeline Mode runs `analyze-stats` → `make-figures` → `write-paper` → `check-reporting` → `self-review` end-to-end. **New:** `--e2e` flag for fully autonomous execution with post-skill validation and halt-on-failure. |
| **find-cohort-gap** | Research gap finder for longitudinal cohort databases. Profiles cohort strengths, matches PI expertise, scans literature saturation via 6-Pattern scoring, and outputs ranked topic proposals with comparison tables and one-pagers. Works with any cohort: NHIS, UK Biobank, institutional EMR, health checkup registries. |
| **search-lit** | PubMed + Semantic Scholar + bioRxiv search with anti-hallucination citation verification. Token-efficient error handling -- CrossRef failures are silently batched, not repeated. **New:** BibTeX output tags each entry with `verified`/`verified_by`/`verified_on` fields so downstream skills can trust the citation provenance. |
| **verify-refs** | Pre-submission reference audit for `.md`, `.docx`, `.bib`, or `.tsv` inputs. Extracts references, verifies DOI/PMID via CrossRef/PubMed when available, and writes `qc/reference_audit.json` as the sole output — row-level status (OK / MISMATCH / UNVERIFIED / FABRICATED) lives inside the JSON `records[]` block. `/search-lit` produces candidate BibTeX; `/lit-sync` owns `manuscript/_src/refs.bib`. |
| **fulltext-retrieval** | Batch open-access PDF downloader. Unpaywall → PMC → OpenAlex → CrossRef pipeline. OA-only -- no paywall bypass. Input: DOI list or TSV. Optional PDF→Markdown conversion via [pymupdf4llm](https://pymupdf.readthedocs.io/en/latest/pymupdf4llm/) for token-efficient LLM analysis of academic papers. |
| **check-reporting** | Manuscript compliance audit against 32 reporting guidelines and risk of bias tools (STROBE, STARD, STARD-AI, TRIPOD, TRIPOD+AI, PRISMA, PRISMA-DTA, PRISMA-P, MOOSE, ARRIVE, CONSORT, CARE, SPIRIT, CLAIM, SQUIRE 2.0, CLEAR, GRRAS, MI-CLEAR-LLM, SWiM, AMSTAR 2, QUADAS-2, QUADAS-C, RoB 2, ROBINS-I, ROBINS-E, ROBIS, ROB-ME, PROBAST, PROBAST+AI, NOS, COSMIN, RoB NMA). **New:** Machine-readable JSON summary with `compliance_pct` and `fixable_by_ai` flags for automated pipeline integration. |
| **analyze-stats** | Statistical analysis code generation (Python/R) for diagnostic accuracy, DTA meta-analysis (bivariate/HSROC), inter-rater agreement, survival analysis, demographics tables, regression (logistic/linear), propensity score (matching/IPTW/overlap weighting), and repeated measures (RM ANOVA/GEE/mixed models). Calibration mandatory for prediction models. |
| **meta-analysis** | Full systematic review and meta-analysis pipeline (8 phases). DTA (bivariate/HSROC) and intervention meta-analysis. Protocol to submission-ready manuscript with PRISMA-DTA compliance. |
| **make-figures** | Publication-ready figures and visual abstracts: ROC curves, forest plots, PRISMA/CONSORT/STARD flow diagrams, Kaplan-Meier curves, Bland-Altman plots, confusion matrices, and journal-specific visual/graphical abstracts (python-pptx template-based). **New (v1.1.0):** communication-first design principles (Nat Hum Behav 2026 — key message, audience, cognitive load, figure-vs-table decision) and five flow-diagram production lessons (official-template fidelity, VML fallback PDF export, docx XML escape, sequential placeholder mapping, version freeze); critic rubric Section G adds 5 communication-first checks. `--study-type` auto-generates the full required figure set; structured `_figure_manifest.md` output for downstream pipeline consumption; D2 enforced as default for flow diagrams. |
| **design-study** | Study design review: identifies analysis unit, cohort logic, data leakage risks, comparator design, validation strategy, and reporting guideline fit. |
| **intake-project** | Classifies new research projects, summarizes current state, identifies missing inputs, and recommends next steps. |
| **grant-builder** | Structures grant proposals: significance, innovation, approach, milestones, and consortium roles. |
| **present-paper** | Academic presentation preparation: paper analysis, supporting research, speaker scripts, slide note injection, and Q&A prep. |
| **publish-skill** | Convert personal Claude Code skills into distributable, open-source-ready packages. PII audit, license compatibility check, generalization, and packaging workflow. |
| **write-paper** | Full IMRAD manuscript pipeline (8 phases). Outline to submission-ready manuscript with critic-fixer loops, AI pattern avoidance, and journal compliance. Anti-interpretation guardrails in Results; interactive Discussion planning with anchor paper input. Case report mode (CARE 2016, 1000-word short-form). Optional cover letter generation (Phase 8+). LLM Disclosure: auto-generates disclosure statements in Methods, Acknowledgments, and Cover Letter (opt-out via `--no-llm-disclosure`). **New:** `--autonomous` flag skips all user gates for fully automated manuscript generation; Phase 2 auto-calls `/make-figures --study-type` with manifest verification; Phase 7 enforces strict sequential QC chain (check-reporting → search-lit → self-review fix loop → DOCX build). |
| **self-review** | Pre-submission self-review from reviewer perspective. 10 categories with research-type branching (AI, observational, educational, meta-analysis, case report, surgical). Anticipated Major/Minor format with severity framing and optional R0 numbering for `/revise` pipeline. **New:** `--json` structured output with `fixable_by_ai` flags; `--fix` mode auto-applies text fixes (max 2 iterations). |
| **revise** | Response to reviewers with tracked changes. Parses decision letters, classifies comments as MAJOR/MINOR/REBUTTAL, generates point-by-point responses and cover letter. |
| **sync-submission** | SSOT-to-submission drift audit and journal package helper. Treats `submission/{journal}/` as derived output, records source hashes in `.journal_meta.json`, and blocks freezing drifted packages. |
| **manage-project** | Research project scaffolding and progress tracking. Commands: init, status, sync-memory, checklist, timeline. Backwards submission timelines and pre-submission checklists. **New:** `init --zotero-collection NAME` auto-creates the Zotero collection via pyzotero and wires the `library_id`/`collection_key` into the project contract. |
| **calc-sample-size** | Interactive sample size calculator with decision-tree guided test selection. Covers 11 designs (diagnostic accuracy, t-test, ANOVA, chi-square, McNemar, logistic regression, Cox regression EPV, survival, ICC, kappa, non-inferiority/equivalence). Generates reproducible R/Python code and IRB-ready justification text. |
| **find-journal** | Journal recommendation engine. 2-pass matching: compact profiles for scoring, write-paper profiles for top-5 enrichment. Covers 30+ medical specialties, with a user-local private tier for personal-use profiles. No cached IF/APC -- you verify current metrics at journal sites. Post-rejection re-targeting mode. |
| **add-journal** | Add new journal profiles to the database. Extracts metadata from author guidelines, generates both write-paper (detailed) and find-journal (compact) profiles in canonical format with quality gates. Batch mode for adding multiple journals in one session. |
| **deidentify** | De-identify clinical research data before LLM-assisted analysis. Standalone Python CLI (no LLM) with 10 country locale packs (kr, us, jp, cn, de, uk, fr, ca, au, in). Detects PHI via regex + heuristics. Interactive terminal review, pseudonymization, date shifting, mapping file generation. Custom locale support via `--locale-file`. |
| **clean-data** | Interactive data profiling and cleaning assistant. Three-stage workflow: profile your CSV/Excel data, flag issues (missing values, outliers, duplicates, type mismatches), then generate cleaning code for approved actions only. PHI/PII safety warnings built-in. |
| **write-protocol** | IRB/ethics protocol generator. Produces 4 core sections (Background, Study Design, Sample Size Justification, Statistical Plan) with full prose. 6 remaining sections provided as structured skeletons with TODO markers for institution-specific content. Korea/US/EU regulatory guidance. |
| **replicate-study** | Replicate an existing cohort study on a different database. Extracts methodology from a source paper, maps variables via harmonization table, generates analysis code, and produces a replication difference report. Validated on KNHANES/NHANES cross-national replication. |
| **cross-national** | End-to-end cross-national comparison study. Variable harmonization, parallel weighted survey analysis (no data pooling), and country-stratified comparison tables. Built-in KNHANES + NHANES coding references. |
| **batch-cohort** | Generate N analysis scripts from one validated template × multiple exposure/outcome combinations. The "80-person team" pattern: same method, swap variables only. Self-adjustment prevention, EPV checks, Bonferroni correction, and summary heatmaps. Validated with 18 combinations on KNHANES 2018. |
| **humanize** | Detect and remove AI writing patterns from academic manuscripts. Scans for 18 common patterns (significance inflation, AI vocabulary, copula avoidance, etc.) and rewrites flagged passages while preserving technical accuracy. Density target: <2.0 instances per 1000 words. |
| **author-strategy** | PubMed author profile analysis. Fetches publication data via E-utilities, classifies study types (GBD, SR/MA, NHIS, AI/ML, etc.), generates 7 visualizations, and produces a strategy report with replication opportunities. |
| **peer-review** | Structured peer review drafting for medical journals. Systematic manuscript analysis, journal-specific formatting (RYAI, INSI, EURE, AJR, KJR), conciseness targets (500-800 words), and pre-submission QC checklist. Constructive developmental tone. |
| **ma-scout** | Meta-analysis topic discovery and feasibility assessment. Two modes: (A) Professor-first — profile → pillar analysis → MA gaps, (B) Topic-first — question → landscape scan → co-author matching. Multi-source validation (PubMed, PROSPERO, bioRxiv) with realistic k estimation (15-30% discount). |
| **lit-sync** | Sync research references from .bib files to Zotero library + Obsidian literature notes. Concept extraction from 10+ literature notes with cross-cutting theme discovery. Works after `/search-lit` or standalone. |
| **academic-aio** | AI search engine (Perplexity / ChatGPT web / Elicit / Consensus / SciSpace) and RAG visibility checklist for medical AI papers. Integrates TRIPOD+AI, CLAIM, STARD-AI, TRIPOD-LLM, DECIDE-AI reporting anchors with generative-engine-optimization (GEO) principles. Covers title, abstract, structured summary boxes (Key Points / Research in Context / Plain-Language Summary), preprints, GitHub README, `CITATION.cff`, Zenodo, and Hugging Face model/dataset cards. Explicit defense against LLM citation fabrication (Agarwal 2025, Nat Commun). Produces a visible PASS/PARTIAL/FAIL checklist; never applies edits silently. Pairs with `write-paper` Phase 4/6/7, runs after `self-review` + `humanize`. |
| **manage-refs** | Reference lifecycle as a single skill: citekey ↔ `.bib` validation, journal-CSL pandoc rendering (`render_pandoc.sh`), manuscript ↔ rendered DOCX cross-reference QC (`check_xref.py --strict` is the submission gate), `[N]` ↔ `[@key]` marker conversion, and native Zotero CWYW field-code injection for co-author Word workflows. Hybrid 3-phase strategy (pandoc draft → CWYW transition → Zotero CWYW for circulation/revision/submission). Sole writer of `manuscript_final.docx` and `qc/xref_audit.json`. **New:** split out of `write-paper` Phase 7.6 in 2026-05-01 release so `revise`, `peer-review`, `sync-submission`, and `find-journal` can render directly without depending on a sibling skill. |
| **render-pdf-doc** | Render non-bibliography academic markdown (proposal, briefing handout, anchor doc, IRB cover, reference table) to publication-quality PDF via `pandoc + xelatex` with CJK font fallback (Apple SD Gothic Neo on macOS, Noto Sans CJK KR on Linux) and content-proportional pipe-table column widths. Boundary opposite of `manage-refs` (bibliography-driven). **New:** spun off from `write-paper` Phase 7.6 in 2026-05-01. |
| **define-variables** | Literature-grounded variable operationalization for observational research. Turns a data dictionary plus research question into a citation-backed table of exposure / outcome / covariate definitions, cutoffs, and DB-variable mappings. Tier 0 dictionary-first rule prevents ad-hoc phenotype definitions that invite reviewer rejection. Bridges `/search-lit` output into `/write-protocol` Methods. |
| **fill-protocol** | Fill institutional Word form templates (`.doc` / `.docx`) for IRB protocols, ethics applications, grant proposals, and other structured research documents while preserving the original styles, table layouts, fonts, and page geometry. Korean-aware (CJK eastAsia font enforcement, table cantSplit) but works for any-language template. Pairs with `write-protocol` (content) — fill-protocol renders the content into the institutional template. |
| **fill-icmje-coi** | Batch-generate per-author ICMJE Conflict of Interest Disclosure Forms (`coi_disclosure.docx`) for manuscript submission. Pre-fills all 13 disclosure items as "☒ None" plus the final certification using a synthetic seed template, then clones the seed per author with Date / Name / Manuscript Title replaced. Designed for the common case of hospital-based observational research where no author has real financial conflicts; circulated forms become "reply 변경 없음 + sign" for most authors and only flag those who need to amend. |

## Installation

> **No terminal?** Use the classroom installer ZIP. Download, unzip, double-click the installer, then restart your desktop agent app.

### Option 1: Classroom installer (recommended for non-programmers)

Windows:

```text
https://github.com/Aperivue/medsci-skills/releases/latest/download/medsci-skills-classroom-windows.zip
```

macOS:

```text
https://github.com/Aperivue/medsci-skills/releases/latest/download/medsci-skills-classroom-macos.zip
```

After unzipping:

- Windows: double-click `installers/install-windows.cmd`
- macOS: double-click `installers/install-macos.command`

Then restart Claude Code Desktop, Codex Desktop, or Cursor and test with:

```text
MedSci Skills가 설치됐는지 확인하고, 오늘 실습에 쓸 대표 스킬 5개만 보여줘.
```

### Option 2: Install all skills manually

```bash
git clone https://github.com/Aperivue/medsci-skills.git
cp -r medsci-skills/skills/* ~/.claude/skills/
```

### Option 3: Install individual skills manually

```bash
git clone https://github.com/Aperivue/medsci-skills.git
cp -r medsci-skills/skills/check-reporting ~/.claude/skills/
```

### Platform notes

- Claude Code: skills are copied to `~/.claude/skills/`.
- Codex: skills are copied to `~/.agents/skills/`.
- Cursor: use a project rule in `.cursor/rules/` that points Cursor to the skill files.
- Windows users do not need WSL for the basic classroom workflow. Use WSL only for advanced reproducible Linux toolchains.

See [docs/classroom_distribution_plan.md](docs/classroom_distribution_plan.md) and [docs/classroom_materials.md](docs/classroom_materials.md) for instructor distribution, email templates, and first-class exercises.

> **Tip:** Not sure which skill to use? Start with `/orchestrate` -- it will classify your request and route you to the right tool.

## Key Features

### Autonomous E2E Pipeline (v2.3)
`orchestrate --e2e` or `write-paper --autonomous` runs the full pipeline from data to submission-ready DOCX with bounded validation. Skills pass outputs via structured manifests (`_analysis_outputs.md`, `_figure_manifest.md`) and project artifacts (`project.yaml`, `artifact_manifest.json`, `qc/status.json`). If a skill fails to produce expected outputs, the pipeline halts rather than proceeding with missing data. Phase 7 enforces a strict QC chain: AI pattern removal → reporting compliance check → `/verify-refs` citation audit → numerical claim audit → self-review with auto-fix (max 2 iterations) → DOCX/submission build.

### Anti-Hallucination Citations
Every reference produced by `search-lit` is verified against PubMed, Semantic Scholar, or CrossRef APIs. Existing manuscripts should then run `/verify-refs`, which writes a visible reference audit and blocks fabricated references before submission. No citation is ever generated from memory alone. API errors are batched silently -- no token waste from repeated failure messages.

### Anti-Hallucination Numerical Claims (v2.3)
`/meta-analysis` Phase 6b, `/self-review` Phase 2.5a, `/revise` Step 2.5, and `/write-paper`
Step 7.3a enforce a common 3-layer audit (CSV ↔ analysis script ↔ manuscript) with primary-
source back-checking for pooled estimates and revision-era numbers. Hand-typed numerical
matrices without CSV-coordinate comments are flagged as structural risks even when the values
are currently correct, since the next revision will re-introduce the same failure mode.

### Reference Safety (Phase 1)
Projects declare their source-of-truth layout in `SSOT.yaml`, and a `qc/migration_complete` marker gates strict enforcement. `/verify-refs` is the sole writer of `qc/reference_audit.json`. The `MEDSCI_VERIFY_REFS_MODE` env var (`auto` default, `warn`, `enforce`, `off`) controls behavior — `auto` blocks only when both SSOT.yaml and the migration marker are present, otherwise warns. Legacy projects freeze as warn-only; new projects opt in via `scripts/migrate_project_to_ssot.py`. An optional PostToolUse hook (not shipped in this repo — document only) can invoke `/verify-refs` automatically on manuscript saves for users who install it locally at `~/.claude/hooks/verify-refs-guard.sh`; the regression suite (`tests/test_phase1c_hooks.sh`) runs end-to-end only when that local hook is present and is skipped otherwise.

### Meta-Analysis Failure Modes
`/meta-analysis` ships empirical failure-mode references (data integrity, review orchestration, submission package drift, post-submission release ops) with four automation hooks: `scripts/prisma_5way_consistency.py` (DI-6 PRISMA number consistency), `scripts/extraction_consensus_log_init.py` (DI-1 dual-extraction scaffold), `scripts/tag_cleanup_gate.sh` (DI-8 placeholder tag gate), and `scripts/verify_package_integrity.py` (SPD SHA-256 manifest for submission bundles).

### 33 Reporting Guidelines & RoB Tools Built-in
`check-reporting` includes bundled checklists for 32 guidelines and risk-of-bias tools: STROBE, STARD, STARD-AI, TRIPOD, TRIPOD+AI, PRISMA 2020, PRISMA-DTA, PRISMA-P, MOOSE, ARRIVE, CONSORT, CARE, SPIRIT, CLAIM, SQUIRE 2.0, CLEAR, GRRAS, MI-CLEAR-LLM, SWiM, AMSTAR 2, QUADAS-2, QUADAS-C, RoB 2, ROBINS-I, ROBINS-E, ROBIS, ROB-ME, PROBAST, PROBAST+AI, NOS, COSMIN, RoB NMA. Includes Results/Discussion section boundary checks and machine-readable JSON summary for pipeline integration.

### Publication-Ready Output
`analyze-stats` generates reproducible Python/R code for 13 analysis types -- including regression, propensity score, and repeated measures -- with mandatory calibration for prediction models. `make-figures` produces journal-specification figures (300 DPI, colorblind-safe palettes, proper dimensions), visual/graphical abstracts, and a tool selection guide (D2 for flow diagrams, matplotlib for data plots). `--study-type` auto-generates the complete figure set for each study design.

### Results/Discussion Boundary Enforcement
`write-paper` enforces strict separation: Results contain only factual findings (no interpretation, no "why"), Discussion uses interactive anchor-paper scaffolding. The critic rubric includes a dedicated Section Boundaries pass/fail gate.

### IRB Protocol to Submission in One Pipeline
`design-study` -> `calc-sample-size` -> `write-protocol` gives you an IRB-ready protocol. After data collection: `clean-data` -> `analyze-stats` -> `write-paper` -> `self-review` -> `find-journal` -> cover letter. Every transition is a defined skill handoff.

### Skills Work Together
Skills call each other. `check-reporting` invokes `make-figures` for PRISMA diagrams. `write-paper` calls `search-lit` for citation verification. `self-review` delegates reporting compliance to `check-reporting`. `calc-sample-size` output feeds directly into `write-protocol`'s IRB justification section.

## Setup

**New to Python, R, or the command line?** The full step-by-step guide for clinicians is in [`docs/setup/`](docs/setup/README.md):

- [Mac setup](docs/setup/mac.md) — Homebrew → Python 3.11 → R → Node → Claude Code (~30 min)
- [Windows setup](docs/setup/windows.md) — winget-based, no WSL required
- [MCP server setup](docs/setup/mcp-setup.md) — Zotero, Google Drive, PubMed integration
- [Common issues](docs/setup/common-issues.md) — top 10 fixes (PATH, Apple Silicon, antivirus, JSON syntax)

**Verify your environment** with the diagnostic skill (read-only, installs nothing):
```
/setup-medsci
```
Prints a checklist showing which components are present, which are missing, and which doc to follow for any gap.

## Requirements

- [Claude Code](https://claude.ai/code) CLI or IDE extension
- Python 3.9+ (for statistical analysis and figure generation)
- R 4.0+ with `meta` (>=7.0), `metafor` (>=4.0), `mada` (>=0.5.11) packages (for meta-analysis)

## Use Cases

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

## Disclaimer

These skills are research productivity tools. They do **not** provide clinical decision support, medical advice, or diagnostic recommendations. All outputs should be reviewed by qualified researchers before use in any publication or clinical context.

## Acknowledgements

- `make-figures` Critic Loop is inspired by [PaperBanana](https://github.com/dwzhu-pku/PaperBanana) (Zhu et al., *Automating Academic Illustration for AI Scientists*, arXiv:2601.23265, 2025) and by prior self-refinement research — Self-Refine (Madaan et al., 2023), Reflexion (Shinn et al., 2023), and Constitutional AI (Anthropic, 2022). The implementation in this repository is a clean-room reconstruction specialized for medical publication figures; no code, prompts, or configurations are derived from PaperBanana's repository.
- Reporting-guideline checklists bundled with `check-reporting` are redistributed under their original Creative Commons licenses (see each checklist for attribution).
- Wong colorblind-safe palette: Wong B. *Points of view: Color blindness.* Nature Methods 8:441 (2011).

## License

MIT License. See [LICENSE](LICENSE) for details.

Bundled reporting guideline checklists retain their original Creative Commons licenses. See each checklist file for attribution.

Optional dependency: `pdf_to_md.py` uses [pymupdf4llm](https://pymupdf.readthedocs.io) (AGPL-3.0). Not bundled -- installed separately by the user via `pip install pymupdf4llm`.

## About

Built by [Aperivue](https://aperivue.com) -- tools for medical AI research and education.

If you find this useful, consider giving it a star. It helps other researchers discover these tools.
