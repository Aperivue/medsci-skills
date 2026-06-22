<div align="center">

# MedSci Skills

**45 skills that actually work.** Built by a physician-researcher, tested on real publications.

*MedSci Skills is a submission-grade clinical manuscript workflow, not a generic biomedical skill catalog. Its moat is the compliance layer — 36 reporting guidelines and risk-of-bias tools, reference/citation verification, and deterministic integrity gates, before peer review sees the manuscript. It competes on clinical submission reliability, not skill count.*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Release](https://img.shields.io/github/v/release/Aperivue/medsci-skills?style=flat-square&color=blue)](https://github.com/Aperivue/medsci-skills/releases/latest)
[![CI](https://img.shields.io/github/actions/workflow/status/Aperivue/medsci-skills/validate.yml?branch=main&style=flat-square&label=CI)](https://github.com/Aperivue/medsci-skills/actions/workflows/validate.yml)
![Skills](https://img.shields.io/badge/Skills-45-brightgreen?style=flat-square)
[![npm](https://img.shields.io/npm/v/medsci-skills?style=flat-square&label=npm&color=cb3837)](https://www.npmjs.com/package/medsci-skills)
[![good first issues](https://img.shields.io/github/issues/Aperivue/medsci-skills/good%20first%20issue?style=flat-square&label=good%20first%20issues&color=7057ff)](https://github.com/Aperivue/medsci-skills/contribute)

[![Agent Skills](https://img.shields.io/badge/Agent_Skills-standard-blue?style=flat-square)](https://agentskills.io)
[![Claude Code](https://img.shields.io/badge/Claude_Code-supported-success?style=flat-square)](docs/host_compatibility.md)
[![Codex](https://img.shields.io/badge/Codex-supported-success?style=flat-square)](docs/host_compatibility.md)
[![Cursor](https://img.shields.io/badge/Cursor-supported-success?style=flat-square)](docs/host_compatibility.md)
[![GitHub Copilot](https://img.shields.io/badge/GitHub_Copilot-supported-success?style=flat-square)](docs/host_compatibility.md)

[![DOI](https://img.shields.io/badge/DOI-10.5281%2Fzenodo.20155321-blue?style=flat-square)](https://doi.org/10.5281/zenodo.20155321)
[![arXiv](https://img.shields.io/badge/arXiv-2606.09500-b31b1b?style=flat-square)](https://arxiv.org/abs/2606.09500)
[![Citation](https://img.shields.io/badge/Cite-CITATION.cff-blue?style=flat-square)](CITATION.cff)
![Built by](https://img.shields.io/badge/Built_by-Physician--Researcher-blue?style=flat-square)

![MedSci Skills](https://raw.githubusercontent.com/Aperivue/medsci-skills/main/assets/social-preview.png)

*Topic Discovery &rarr; Literature Search &rarr; Full-Text Retrieval &rarr; Study Design &rarr; Sample Size &rarr; Protocol &rarr; De-identification &rarr; Data Cleaning &rarr; Statistics &rarr; Figures &rarr; Writing &rarr; Humanize &rarr; Compliance &rarr; Journal Selection &rarr; Peer Review &rarr; Revision &rarr; Presentation*

**Created & maintained by [Yoojin Nam, MD](https://orcid.org/0000-0001-8565-1360)**
<br>
<sub>Department of Radiology and Research Institute of Radiology, University of Ulsan College of Medicine, Asan Medical Center, Seoul, Republic of Korea</sub>

</div>

![check-reporting demo](demo.gif)

---

## What is MedSci Skills?

MedSci Skills is an open-source Claude Code skill collection for **clinical
manuscript preparation**. It helps physician-researchers and biomedical
investigators move from literature search, study design, statistics, and figures to
reporting-guideline compliance, citation/reference auditing, numerical-consistency
checks, and response-to-reviewer workflows — combining agentic writing with
**deterministic integrity gates** for submission-grade biomedical research. It is
**not** a diagnostic tool, an autonomous author, or a general AI-scientist platform;
every output requires human-expert verification. New here? See the
[3 workflows below](#start-here-3-workflows), the [FAQ](docs/faq.md), and the
[scope boundary](ROADMAP.md#not-planned--explicitly-out-of-scope).

---

## Quick Start

**No terminal?** Use the classroom installer ZIP — download, unzip, double-click the installer, then restart your agent app (see [Installation](#installation)).

**Have a terminal?** Fastest path — one command, nothing to clone:

```bash
npx medsci-skills install        # copies every skill into your agent's folder
```

**Have git?** Install every skill in three commands:

```bash
git clone https://github.com/Aperivue/medsci-skills.git
mkdir -p ~/.claude/skills
cp -r medsci-skills/skills/* ~/.claude/skills/
```

Restart Claude Code, then start with **`/orchestrate`** — it classifies your request and routes you to the right skill. Full install options (Codex, Cursor, individual skills) are in [Installation](#installation).

### Install as a Claude Code plugin

Prefer plugins? One line adds the marketplace; `/plugin` then lets you browse eight category plugins and enable the ones you want:

```text
/plugin marketplace add Aperivue/medsci-skills
/plugin            # browse eight category plugins; enable the ones you want
```

| Plugin | Covers |
|--------|--------|
| `medsci-literature` | Literature search, full-text retrieval, Zotero sync, reference-integrity audits |
| `medsci-data` | Study design, variable operationalization, sample size, data cleaning, de-identification, codebooks, dataset versioning |
| `medsci-analysis` | Statistics, figures, batch/cross-national/replication analysis, meta-analysis |
| `medsci-writing` | IMRAD & protocol drafting, AI-pattern removal, AI-search optimization, reviewer responses |
| `medsci-review` | Self-review, peer review, reporting-guideline compliance |
| `medsci-submission` | Submission packaging, journal selection, ICMJE/IRB form filling, grant proposals |
| `medsci-project` | Orchestration, project intake/management, gap & topic discovery, author strategy |
| `medsci-presentation` | Presentations/PPTX, PDF/document rendering, environment setup, skill publishing |

Install a single category and invoke its skills under that namespace:

```text
/plugin install medsci-analysis@medsci-skills
/medsci-analysis:analyze-stats
```

All eight plugins share the same repository source, so this groups and enables skills by category — it is not a partial download. The marketplace tracks `main`, so a plugin's version is its git commit.

**Want just one capability?** Two skills are also published as focused standalone repos (generated mirrors; this repo stays the source of truth), each installable on its own with `/plugin marketplace add Aperivue/<repo>`:

- [`Aperivue/verify-refs`](https://github.com/Aperivue/verify-refs) — catch fabricated/mismatched citations (PubMed + CrossRef).
- [`Aperivue/check-reporting`](https://github.com/Aperivue/check-reporting) — audit a manuscript against the bundled EQUATOR reporting guidelines and risk-of-bias tools.

---

## Start here: 3 workflows

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

## Live Demos: Three Study Types, Three Full Pipelines

Three public datasets. Three study types. Each produces a complete manuscript, publication-ready figures, and a reporting compliance audit.

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

<details>
<summary>Full output list — manuscript, figures, STARD flow, checklist (click to expand)</summary>

| Output | Description |
|--------|-------------|
| [Manuscript](demo/01_wisconsin_bc/manuscript/manuscript.md) | IMRAD draft, ~1,800 words |
| [Title Page](demo/01_wisconsin_bc/manuscript/title_page.md) | STARD title page with key points |
| [DOCX](demo/01_wisconsin_bc/manuscript/manuscript_final.docx) | Submission-ready Word document |
| [ROC Curve](demo/01_wisconsin_bc/analysis/figures/roc_curve.png) | 3-model comparison with DeLong 95% CIs |
| [Confusion Matrices](demo/01_wisconsin_bc/analysis/figures/confusion_matrices.png) | Per-model confusion matrices at threshold 0.5 |
| [STARD Flow](demo/01_wisconsin_bc/figures/stard_flow.svg) | D2-generated STARD 2015 flow diagram |
| [Reporting Checklist](demo/01_wisconsin_bc/qc/reporting_checklist.md) | STARD 2015 — 60.9% compliance (14/23 applicable) |
| [Self-Review](demo/01_wisconsin_bc/qc/self_review.md) | Initial 82 (REVISE) → 88 (PASS) after 1 fix iteration; final 0 major / 1 minor |
| [Pipeline Log](demo/01_wisconsin_bc/qc/_pipeline_log.md) | 7-step E2E execution trace |

</details>

**Pipeline:** `analyze-stats` &rarr; `make-figures` &rarr; `write-paper` &rarr; AI pattern scan &rarr; `check-reporting` (STARD) &rarr; `self-review` &rarr; DOCX build &rarr; `present-paper`

### Demo 2: Meta-Analysis — BCG Vaccine Efficacy

```r
library(metafor)
data(dat.bcg)  # 13 RCTs, 357,347 participants (Colditz et al. 1994)
```

**Output from `orchestrate --e2e`** ([see full demo](demo/02_metafor_bcg/)):

<details>
<summary>Full output list — manuscript, forest/funnel plots, PRISMA flow, checklist (click to expand)</summary>

| Output | Description |
|--------|-------------|
| [Manuscript](demo/02_metafor_bcg/manuscript/manuscript.md) | Pooled RR = 0.489 (95% CI: 0.344–0.696), ~2,200 words |
| [Title Page](demo/02_metafor_bcg/manuscript/title_page.md) | PRISMA title page with key points |
| [DOCX](demo/02_metafor_bcg/manuscript/manuscript_final.docx) | Submission-ready Word document |
| [Forest Plot](demo/02_metafor_bcg/analysis/figures/forest.png) | 13 studies, RE model (REML), 300 dpi |
| [Funnel Plot](demo/02_metafor_bcg/analysis/figures/funnel.png) | Small-study / publication-bias visual |
| [PRISMA Flow](demo/02_metafor_bcg/analysis/figures/prisma_flow.svg) | D2-generated PRISMA 2020 flow diagram |
| [Reporting Checklist](demo/02_metafor_bcg/qc/reporting_checklist.md) | PRISMA 2020 — 57.1% (24/42) at check-reporting → 61.9% (26/42) after self-review fix |
| [Self-Review](demo/02_metafor_bcg/qc/self_review.md) | Initial 78 → 82 (REVISE) after 1 fix iteration; 3 major / 4 minor (majors are out-of-scope RoB/GRADE/references) |
| [Pipeline Log](demo/02_metafor_bcg/qc/_pipeline_log.md) | 7-step E2E execution trace |

</details>

**Pipeline:** `analyze-stats` (R metafor) &rarr; `make-figures` &rarr; `write-paper` &rarr; AI pattern scan &rarr; `check-reporting` (PRISMA 2020) &rarr; `self-review` &rarr; DOCX build &rarr; `present-paper`

### Demo 3: Epidemiology — NHANES Obesity & Diabetes

```python
# Pre-processed NHANES 2017-2018 CSV included
# 5,010 US adults after exclusions
```

**Output from `orchestrate --e2e`** ([see full demo](demo/03_nhanes_obesity/)):

<details>
<summary>Full output list — manuscript, OR forest plot, STROBE flow, checklist (click to expand)</summary>

| Output | Description |
|--------|-------------|
| [Manuscript](demo/03_nhanes_obesity/manuscript/manuscript.md) | Adjusted OR = 3.03 (95% CI: 2.29–4.02), ~1,850 words |
| [Title Page](demo/03_nhanes_obesity/manuscript/title_page.md) | STROBE title page with key points |
| [DOCX](demo/03_nhanes_obesity/manuscript/manuscript_final.docx) | Submission-ready Word document |
| [OR Forest Plot](demo/03_nhanes_obesity/analysis/figures/forest_or.png) | Adjusted odds ratios for 7 variables |
| [Study Flow](demo/03_nhanes_obesity/analysis/figures/strobe_flow.svg) | D2-generated participant flow diagram |
| [Reporting Checklist](demo/03_nhanes_obesity/qc/reporting_checklist.md) | STROBE — 83.3% compliance (25/30 applicable) |
| [Self-Review](demo/03_nhanes_obesity/qc/self_review.md) | ACCEPT-WITH-NOTES after 1 fix iteration; 0 genuine majors remaining |
| [Pipeline Log](demo/03_nhanes_obesity/qc/_pipeline_log.md) | 7-step E2E execution trace |

</details>

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

## What's New

**v4.7** is the **self-update foundation** — physician-researchers stay current without GitHub, git, or a terminal. Additive and backward-compatible; still 45 skills / 36 guidelines / 30 detectors:

- **Transactional, crash-recoverable installer.** Each install runs through a durable journal state machine recovered on the next run (roll back / forward-clean / fail-closed), with per-target SHA-256 inventories — your modified or third-party skills are backed up and never clobbered or auto-deleted.
- **One-click self-updater** (`~/.medsci-skills/updater/`, `install.py --check-update`). Verifies the download against the github.com API digest and **never `extractall()`s** (per-entry rejection of traversal / symlink / duplicate / zip-bomb + an allowlist & per-file hash). The release pipeline injects a verified `provenance.json`, attests build provenance, runs on a protected `release` environment, and verifies each ZIP round-trips through the updater's own safe-extract before publishing.
- **Opt-in update notice (off by default):** `install.py --enable-update-notify` shows a one-line "update available" message at Claude Code session start — no telemetry, reads nothing about your session, installs nothing. `--disable-update-notify` / `MEDSCI_NO_UPDATE_CHECK=1` turn it off. *(Honest scope: the digest/attestation detect transport tampering, not a compromised publisher account — see `SECURITY.md`.)*

**v4.6** is a maintainability, governance, and review-depth release — still 45 skills / 36 guidelines; analysis-integrity detectors **28 → 30**, domain probes 11 → 12:

- **Fairness / equity / subgroup-performance probe (EQ0–EQ6)** for AI/prediction/diagnostic studies that claim cross-population performance, plus two new detectors: an **AI-disclosure + data/code-availability** check (`/sync-submission`) and a **structured-summary-box conformance** check (`/academic-aio`).
- **Governance + answer-engine layer:** `ROADMAP.md`, `MAINTAINERS.md`, `SECURITY.md`, a maintainer workflow + release checklist, an AEO/GEO `docs/faq.md`, a "Start here: 3 workflows" + "Validation status" section in this README, and a new `maturity` field (official / experimental / community) on every skill.
- **Token diet (pilot):** `write-paper` Phase 7 integrity audits moved to a load-on-demand reference (~2,559 tokens saved per invocation). Positioning now leads with the compliance moat rather than skill count.

**v4.5** deepens the review + submission surface with no new skill or reporting-guideline count (still 45 skills / 36 guidelines); analysis-integrity detectors **27 → 28**:

- **`/clean-data` + `/analyze-stats` — reverse-coded-item / negative-alpha detector.** A multi-item Likert scale with a negatively-worded item must be recoded `(min+max) − x` before the scale total or Cronbach's alpha is computed; left un-recoded, the item correlates negatively with the rest of the scale and alpha collapses (often negative). A negative alpha is a coding bug, not a "multidimensional construct." New stdlib-only `check_reverse_coding.py` returns `REVERSE_CODING_LIKELY` / `REVERSE_CODING_SUSPECT` / `OK` from per-item item-rest correlations + raw alpha; the Likert summary template gains a `--reverse-items` recode flag.
- **`/peer-review` + `/self-review` — SR/MA + DTA + prediction-model probe batch.** `sr_ma.md` **P12** risk-of-bias table row-sum ↔ traffic-light figure-matrix reconciliation and **P13** included-study ↔ reference-list completeness; `diagnostic_accuracy.md` **D7** index-test-as-enrollment-criterion circularity; `clinical_prediction_model.md` **CP5** intended-use horizon leakage and **CP6** development/CV vs held-out/external validation-nomenclature conflation. Vendored byte-identical into `/self-review`.
- **`/sync-submission` — embedded absolute-path leak scan.** A `word/*.xml` attribute (e.g. a pandoc-embedded image's `<pic:cNvPr descr="…">`) carrying an absolute home-dir path (`/Users/…`, `/home/…`) is a username leak invisible to a rendered-text scan; now flagged as `docx_embedded_abs_path` under `check_asset_anonymization.py`.

**v4.4** adds reviewer/analysis depth with no new skill or reporting-guideline count (still 45 skills / 36 guidelines / 27 detectors):

- **`/author-strategy` — trajectory-archetype classification (optional).** Classifies a queried author's PubMed trajectory into abstract career archetypes (A1 infrastructure builder, A2 methodology rule-maker, A3 clinical→AI hybrid, A4 SR/MA volume engine, A5 large-consortium participation, A6 device/technique depth, + a computed composite) as an **explainable, multi-label, confidence-scored heuristic — not an objective verdict**. The rubric is a single canonical YAML (the narrative doc is generated from it); scores exclude `unavailable` signals (h-index/citation/venue-tier → `[VERIFY]`, never fabricated); a **disambiguation gate** binds an approved `corpus_manifest.json` to the CSV (csv + PMID-set hashes) so a surname alone never classifies, and target-author attribution never borrows a co-author's ORCID/affiliation.
- **`/peer-review` + `/self-review` — Image-Synthesis / cross-modality probe (IS1–IS4)** for studies that synthesize one imaging modality from another and claim the output carries the target's information, plus a reviewer-side reference-integrity spot-check.
- **`/verify-refs` — OpenAlex tertiary index** recovers conference-proceedings / non-DOI citations (NeurIPS/ICLR/ACL) that fall through PubMed and CrossRef, the free analogue of a portal's second index.

**v4.3** hardens the **cross-sectional / observational cohort** review surface end-to-end, much of it reverse-engineered from real CC-BY cohort papers (learn-only under the license firewall) — no new skill or reporting-guideline count (still 45 skills / 36 guidelines); analysis-integrity detectors **25 → 27**:

- **Observational probes O1 → O14** (`/peer-review` + `/self-review`, vendored) — over-adjustment / analysis-unit clustering / outcome construct-validity (O7–O9), overlapping-subset gradient (O10), **complex-survey design & weighting** for NHANES/KNHANES (O11), **data-driven threshold / "inflection-point" mining** (O12), **cross-sectional mediation** temporal-order & sequential-ignorability (O13), and **interaction scale** — additive RERI/AP/S vs multiplicative (O14). Plus a new **clinical-prediction-model** probe module **CP1–CP4** and survival **S9** (panel-data / multistate variance).
- **Two new detectors (25 → 27)** — `check_wordcount_cap.py` (the revision-inflation trap: body vs journal cap) and `check_paren_spans.py` (em-dash→paren conversions that wrap a whole sentence). Plus a `check_confounding_completeness.py` upgrade (DB-code↔prose alias map, SMD-from-mean±SD, exposure-defining-covariate exemption), a `check_cohort_arithmetic.py` `ANALYSIS_UNIT_UNDISCLOSED` check, a `check_scope_coherence.py` cross-sectional-yield lexicon, and a verify-refs corporate/collective-author render-abort fix.
- **Analysis & submission tooling** — `/analyze-stats` gains **mediation** and **interaction & effect-modification** guides; `/sync-submission` gains `assemble_supplement.py` (S{N} index↔file integrity) and a `/revise` body-word-count exit gate; `/render-pdf-doc` gains a `scan_glyph_coverage.py` xelatex silent-glyph-drop scan.

**v4.2** builds out the case-report capability end-to-end, grounded in real CC-BY case reports (learn-only under the license firewall) — no new skill or reporting-guideline count (still 45 skills / 36 guidelines); journal profiles **68 → 73**:

- **Case-report + case-series writing** — `/write-paper` gains a CARE narrative + 150-word-abstract case-report exemplar, a **case-series** paper type (methods-light mini-cohort, all-cases summary table, counts-not-rates), and **adverse-event/pharmacovigilance** (Naranjo/WHO-UMC causality) and **diagnostic-pitfall/mimic** subtypes.
- **Radiology / imaging-led track** — a dedicated `exemplar_case_report_radiology.md` (per-modality technique→findings→impression, structured-reporting lexicons BI-RADS/LI-RADS/PI-RADS/TI-RADS/Lung-RADS/O-RADS, quantitative threshold honesty, an interventional-radiology procedure/complication subtype, DICOM de-identification) plus a `/make-figures` annotated multimodality imaging-panel exemplar.
- **Case-report reviewer probe** — `/peer-review` + `/self-review` ship a vendored case-report domain probe **CR1–CR9** (novelty/consent/n=1 causality, case-series design, adverse-event causality, imaging-led discipline).
- **Where to submit** — compact `/find-journal` profiles for Journal of Medical Case Reports, Cureus, Radiology Case Reports, BMJ Case Reports, and BJR Case Reports, and `/check-reporting` CARE notes for adverse-event and case-series subtypes.

**v4.1** ships distribution levers and a submission pre-flight gate — analysis-integrity detectors **24 → 25** (still 43 skills):

- **Claude Code plugin marketplace** — `/plugin marketplace add Aperivue/medsci-skills`, then `/plugin` discovery of eight `medsci-*` category plugins generated from the catalog SSOT (`.claude-plugin/marketplace.json`).
- **MedSci-Audit detector registry** — the deterministic verification layer is now a named, enumerated, citable suite ([`MEDSCI_AUDIT.md`](MEDSCI_AUDIT.md) + generated `metadata/detectors_catalog.json`, six audit families).
- **Hero-skill standalone mirrors** — `scripts/sync_hero_skill.py` mirrors a focused skill to its own star-funnel repo; first two live: [`Aperivue/verify-refs`](https://github.com/Aperivue/verify-refs) and [`Aperivue/check-reporting`](https://github.com/Aperivue/check-reporting).
- **Placeholder/marker gate** — `check_placeholders.py` flags leftover `[@NEW:]` / `[version]` / `TODO` / template-URL markers before submission (the 25th detector).
- **Submission pre-flight gate** — `preflight_gate.py` bundles the existing detectors + `/verify-refs` into one halt-on-failure command (`qc/preflight_gate_report.json`, non-zero exit on any blocker) — the single last step before freeze.

**v4.0** extends the project's own deterministic, no-drift SSOT discipline to the public storefront and finishes the detector backlog — bringing the analysis-integrity detector count in `skills/` to **24** (still 43 skills):

- **SSOT to the storefront** — a generated, machine-readable `metadata/skills_catalog.json` (slug + research-lifecycle category + one-line description per skill) is now the source the [aperivue.com](https://aperivue.com/en/skills) storefront vendors, gated offline so the public site can never silently drift behind the repo (`gen_skills_catalog_json.py --check`).
- **Asset/figure anonymization** — `/sync-submission` scans figure-generating scripts, figure-PDF rendered text, and docx/PDF metadata authors for the institution/author leaks a body-text scan misses (`check_asset_anonymization.py`).
- **Cross-artifact staleness** — flags supplement values that disagree with the corrected body, and reporting checklists built against an older manuscript version (`check_cross_artifact_stale.py`; `check_checklist_version.py` with a `target_manuscript`/`source_sha256` checklist contract).
- **Survival reporting** — `/analyze-stats` emits median survival with its 95% CI, a Cox events-per-variable gate, and cluster-robust SE for nested observation units.

**v3.8.0** adds an `evaluation/` harness suite that validates the instrument itself — deterministic detector recall on programmatically seeded defects (E1), fresh-clone manifest reproducibility (E4), claim audit-trail completeness (E5), host-portability and metadata-drift checks (E6/E7/E8), and a cost/time table (E3) — each writing a self-describing, reproducible run package. An LLM-comparator (E2) and a self-review convergence harness (E9) ship runnable but are NOT executed in this release. This release also reconciles the README Live-Demos numbers with the v3.7.0 clean-room demo artifacts. Catalog unchanged (still 43 skills, 21 detectors).

**v3.7.0** adds three deterministic, stdlib-only detectors on top of the v3.6.0 panel-derived gates — bringing the analysis-integrity detector count in `skills/` to **21** — without broadening the catalog (still 43 skills):

- **Reference adequacy** — `/self-review` and `/write-paper` now check that a draft cites *enough* references in the *right* sections and that *every named method* (a competing-risk model, multiple imputation, the E-value, an eGFR equation) carries a citation — the adequacy layer that complements `/verify-refs`'s integrity layer (`check_reference_adequacy.py`).
- **Panel lens-diversity** — `/self-review --panel` post-processes its reviewers so the cost buys breadth, not a louder echo (`check_panel_diversity.py`).
- **Generated-code quality** — `/analyze-stats` lints emitted analysis scripts for reproducibility slop (missing seed, hard-coded data literals, absolute paths, in-place source overwrite) (`check_generated_code.py`).

Plus a publish-time skill-worthiness gate (`/publish-skill`) and public adoption/impact tracking (`IMPACT.md`).

**v3.6.0** lands 18 gates from a 13-project panel self-review (158 traces → 12 recurring defect patterns), without broadening the catalog (still 43 skills). Six new stdlib detectors join the existing trio — deterministic where a grep is clean, prose/probe where the call needs a human:

- **Cohort & pool arithmetic** — `/self-review` recomputes incidence rates from events ÷ person-years, balances STROBE exclusion cascades, and checks ordinal tier/stratum partitions for disjointness (`check_cohort_arithmetic.py`); `/meta-analysis` locks patient/lesion aggregate totals and requires re-run evidence for any "fixed" audit note.
- **Claim ↔ artifact ↔ scope** — Methods ↔ Results ↔ disk coverage (a run-but-unreported analysis is flagged), an endpoint ↔ conclusion scope gate (a cross-sectional design cannot license a surveillance claim; a binary surrogate is not a care directive), and a reviewer-team 3-way that makes an LLM-as-reviewer fatal.
- **Statistical & reporting contracts** — a CI/estimand output contract (quantile/proportion/sHR must carry a 95% CI; Cox EPV gate; proportion-MA Egger ban + prediction interval), interval-censoring / PH-violation / CIF-horizon survival rules, reporting-framework base+extension naming, a classical-style body lint, a PROSPERO ID format gate, and a pagination-placeholder citation gate.

Earlier in this series: analysis-integrity guards (confounding completeness, claim-vs-artifact, structural-zero handling), a multi-agent `/self-review --panel` mode, and shared domain-probe modules vendored byte-identical into `/peer-review` and `/self-review` with a CI drift gate.

---

## Why This Repo?

| | MedSci Skills | Broad skill aggregators |
|---|---|---|
| **Citation quality** | Every reference passes reference-verification gates (PubMed / Semantic Scholar / CrossRef) and citation-audit workflows before inclusion. | No verification -- citations generated from model memory |
| **Pipeline integration** | Skills call each other in defined chains. `design-study` -> `calc-sample-size` -> `write-protocol`. | Standalone stubs with no cross-skill interaction |
| **End-to-end coverage** | From IRB protocol to journal submission: sample size, data cleaning, analysis, writing, compliance, journal selection, cover letter. | Gaps at every transition -- no protocol, no journal matching, no cover letter |
| **Battle-tested** | Used on real manuscript submissions by a practicing physician-researcher | Unknown provenance and validation |
| **Depth per skill** | 150-600 lines of documentation + bundled reference files (curated journal profile library, checklists, formula sheets, code templates) | Typically thin SKILL.md templates |

**MedSci-Audit** — the verification edge in the first rows above is a named suite of **28 deterministic detectors** (citation & reference integrity, cohort & pool arithmetic, scope/estimand contracts, reporting compliance, and more) that catch fabricated or drifted content before a manuscript reaches a reviewer. See **[`MEDSCI_AUDIT.md`](MEDSCI_AUDIT.md)** for the suite, its six families, and its evaluation evidence.

---

## What This Is NOT

This is **not** a broad scientific-tooling library — for cheminformatics, structural biology, or genomics pipelines, see [K-Dense scientific-agent-skills](https://github.com/K-Dense-AI/scientific-agent-skills). It is **not** a biomedical-skill aggregator — for a broad curated collection, see [OpenClaw Medical Skills](https://github.com/FreedomIntelligence/OpenClaw-Medical-Skills). For how MedSci Skills compares to these catalogs, see [`docs/competitive_positioning.md`](docs/competitive_positioning.md). For verified cross-agent install paths (Claude Code, Codex, Cursor, GitHub Copilot), see [`docs/host_compatibility.md`](docs/host_compatibility.md).

MedSci Skills is **opinionated and narrow on purpose**: a single physician-researcher's medical-manuscript pipeline, biased toward radiology, diagnostic accuracy, observational EMR studies, and systematic review / meta-analysis. If you write IMRAD manuscripts for clinical journals, audit reporting compliance against EQUATOR guidelines, or run SR/MA workflows end-to-end, this is built for you. For wet-lab protocols, drug discovery, or single-cell genomics, the repos above are better fits.

---

## Skills

📖 **Per-skill reference:** [`docs/skills/`](docs/skills/) — one page per skill (what it does, when it activates, its Quality Card — purpose, safety boundaries, known limitations, validation, evidence — and bundled resources), generated from each `SKILL.md` + `skill.yml`. See [`docs/skills/AUDIT.md`](docs/skills/AUDIT.md) for how the skills are validated.

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
| **orchestrate** | Single entry point for the full bundle. Classifies your request and routes to the right skill -- or chains multiple skills for multi-step workflows. Full Pipeline Mode runs `analyze-stats` → `make-figures` → `write-paper` → `check-reporting` → `self-review` end-to-end. `--e2e` flag for fully autonomous execution with post-skill validation and halt-on-failure. |
| **find-cohort-gap** | Research gap finder for longitudinal cohort databases. Profiles cohort strengths, matches PI expertise, scans literature saturation via 6-Pattern scoring, and outputs ranked topic proposals with comparison tables and one-pagers. Works with any cohort: NHIS, UK Biobank, institutional EMR, health checkup registries. |
| **search-lit** | PubMed + Semantic Scholar + bioRxiv search with anti-hallucination citation verification. Token-efficient error handling -- CrossRef failures are silently batched, not repeated. BibTeX output tags each entry with `verified`/`verified_by`/`verified_on` fields so downstream skills can trust the citation provenance. |
| **verify-refs** | Pre-submission reference audit for `.md`, `.docx`, `.bib`, or `.tsv` inputs. Extracts references, verifies DOI/PMID via CrossRef/PubMed when available, and writes `qc/reference_audit.json` as the sole output — row-level status (OK / MISMATCH / UNVERIFIED / FABRICATED) lives inside the JSON `records[]` block. `/search-lit` produces candidate BibTeX; `/lit-sync` owns `manuscript/_src/refs.bib`. |
| **fulltext-retrieval** | Batch open-access PDF downloader. Unpaywall → PMC → OpenAlex → CrossRef pipeline. OA-only -- no paywall bypass. Input: DOI list or TSV. Optional PDF→Markdown conversion via [pymupdf4llm](https://pymupdf.readthedocs.io/en/latest/pymupdf4llm/) for token-efficient LLM analysis of academic papers. |
| **check-reporting** | Manuscript compliance audit against 36 reporting guidelines and risk of bias tools (STROBE, STARD, STARD-AI, TRIPOD, TRIPOD+AI, TRIPOD-LLM, PRISMA, PRISMA-DTA, PRISMA-P, MOOSE, ARRIVE, CONSORT, CONSORT-AI, CARE, SPIRIT, SPIRIT-AI, CLAIM, DECIDE-AI, SQUIRE 2.0, CLEAR, GRRAS, MI-CLEAR-LLM, SWiM, AMSTAR 2, QUADAS-2, QUADAS-C, RoB 2, ROBINS-I, ROBINS-E, ROBIS, ROB-ME, PROBAST, PROBAST+AI, NOS, COSMIN, RoB NMA). Machine-readable JSON summary with `compliance_pct` and `fixable_by_ai` flags for automated pipeline integration. |
| **analyze-stats** | Statistical analysis code generation (Python/R) for diagnostic accuracy, DTA meta-analysis (bivariate/HSROC), inter-rater agreement, survival analysis, demographics tables, regression (logistic/linear), propensity score (matching/IPTW/overlap weighting), and repeated measures (RM ANOVA/GEE/mixed models). Calibration mandatory for prediction models. |
| **meta-analysis** | Full systematic review and meta-analysis pipeline (8 phases). DTA (bivariate/HSROC) and intervention meta-analysis. Protocol to submission-ready manuscript with PRISMA-DTA compliance. |
| **make-figures** | Publication-ready figures and visual abstracts: ROC curves, forest plots, PRISMA/CONSORT/STARD flow diagrams, Kaplan-Meier curves, Bland-Altman plots, confusion matrices, and journal-specific visual/graphical abstracts (python-pptx template-based). Communication-first design principles (Nat Hum Behav 2026 — key message, audience, cognitive load, figure-vs-table decision) and five flow-diagram production lessons (official-template fidelity, VML fallback PDF export, docx XML escape, sequential placeholder mapping, version freeze); critic rubric Section G adds 5 communication-first checks. `--study-type` auto-generates the full required figure set; structured `_figure_manifest.md` output for downstream pipeline consumption; D2 enforced as default for flow diagrams. |
| **design-study** | Study design review: identifies analysis unit, cohort logic, data leakage risks, comparator design, validation strategy, and reporting guideline fit. |
| **design-ai-benchmarking** | Design and validity review for benchmarking AI system(s) against a human-expert panel: evaluation-question and arm definition, decoupled multi-dimensional rubrics with anchors, planted calibration probes (positive-control / known-bad / instability / mechanism-contradiction), reviewer-panel construction with per-reviewer randomization, inter-rater reliability targets with separate control-item reliability, LLM-as-judge vs human-as-judge adjudication, construct-independence guards, and a structured JSON rating-export schema. Locks the rubric before data collection. |
| **intake-project** | Classifies new research projects, summarizes current state, identifies missing inputs, and recommends next steps. |
| **grant-builder** | Structures grant proposals: significance, innovation, approach, milestones, and consortium roles. |
| **present-paper** | Academic presentation preparation: paper analysis, supporting research, speaker scripts, slide note injection, and Q&A prep. |
| **publish-skill** | Convert personal Claude Code skills into distributable, open-source-ready packages. PII audit, license compatibility check, generalization, and packaging workflow. |
| **write-paper** | Full IMRAD manuscript pipeline (8 phases). Outline to submission-ready manuscript with critic-fixer loops, AI pattern avoidance, and journal compliance. Anti-interpretation guardrails in Results; interactive Discussion planning with anchor paper input. Case report mode (CARE 2016, 1000-word short-form). Optional cover letter generation (Phase 8+). LLM Disclosure: auto-generates disclosure statements in Methods, Acknowledgments, and Cover Letter (opt-out via `--no-llm-disclosure`). `--autonomous` flag skips all user gates for fully automated manuscript generation; Phase 2 auto-calls `/make-figures --study-type` with manifest verification; Phase 7 enforces strict sequential QC chain (check-reporting → search-lit → self-review fix loop → DOCX build). |
| **review-paper** | Scaffold and draft a literature review — narrative (SANRA), scoping (PRISMA-ScR + JBI), or systematic (PRISMA 2020). Asks for the spine axis (modality / task / lifecycle), builds a 7-part skeleton with a required Intro scope/non-overlap block, per-section summary-table stubs, and an evaluation-metrics critique subsection, then wires reporting/registration and hands off to `/self-review` (RV1-RV8) → `/check-reporting` → `/verify-refs` → `/humanize`. Never invents citations. |
| **self-review** | Pre-submission self-review from reviewer perspective. 10 categories with research-type branching (AI, observational, educational, meta-analysis, case report, surgical). Anticipated Major/Minor format with severity framing and optional R0 numbering for `/revise` pipeline. `--json` structured output with `fixable_by_ai` flags; `--fix` mode auto-applies text fixes (max 2 iterations). |
| **revise** | Response to reviewers with tracked changes. Parses decision letters, classifies comments as MAJOR/MINOR/REBUTTAL, generates point-by-point responses and cover letter. |
| **sync-submission** | SSOT-to-submission drift audit and journal package helper. Treats `submission/{journal}/` as derived output, records source hashes in `.journal_meta.json`, and blocks freezing drifted packages. |
| **manage-project** | Research project scaffolding and progress tracking. Commands: init, status, sync-memory, checklist, timeline. Backwards submission timelines and pre-submission checklists. `init --zotero-collection NAME` auto-creates the Zotero collection via pyzotero and wires the `library_id`/`collection_key` into the project contract. |
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
| **polish-language** | Academic English consistency linting and non-native (ESL) clarity polish. A deterministic linter (`lint_consistency.py`) flags abbreviation define-once violations, US/UK spelling drift, hyphen-vs-en-dash numeric ranges, `P`/`p` case and impossible `P = 0.000`, hyphenation variants, small-number style, and value/unit spacing — then a gated, style-only clarity pass fixes wording without ever changing numbers, citations, or scientific meaning. Distinct from `humanize` (AI-tell removal) and `check-reporting` (guideline items); bundles a reproducible challenge card. |
| **manage-refs** | Reference lifecycle as a single skill: citekey ↔ `.bib` validation, journal-CSL pandoc rendering (`render_pandoc.sh`), manuscript ↔ rendered DOCX cross-reference QC (`check_xref.py --strict` is the submission gate), `[N]` ↔ `[@key]` marker conversion, and native Zotero CWYW field-code injection for co-author Word workflows. Hybrid 3-phase strategy (pandoc draft → CWYW transition → Zotero CWYW for circulation/revision/submission). Sole writer of `manuscript_final.docx` and `qc/xref_audit.json`. Split out of `write-paper` Phase 7.6 so `revise`, `peer-review`, `sync-submission`, and `find-journal` can render directly without depending on a sibling skill. |
| **render-pdf-doc** | Render non-bibliography academic markdown (proposal, briefing handout, anchor doc, IRB cover, reference table) to publication-quality PDF via `pandoc + xelatex` with CJK font fallback (Apple SD Gothic Neo on macOS, Noto Sans CJK KR on Linux) and content-proportional pipe-table column widths. Boundary opposite of `manage-refs` (bibliography-driven). Spun off from `write-paper` Phase 7.6. |
| **define-variables** | Literature-grounded variable operationalization for observational research. Turns a data dictionary plus research question into a citation-backed table of exposure / outcome / covariate definitions, cutoffs, and DB-variable mappings. Tier 0 dictionary-first rule prevents ad-hoc phenotype definitions that invite reviewer rejection. Bridges `/search-lit` output into `/write-protocol` Methods. |
| **generate-codebook** | Generate a citable data dictionary / codebook from a tabular dataset (CSV/TSV/Excel/Parquet/Stata/SAS). Profiles every variable — role, type, level frequencies, range/quantiles, missingness — into `codebook.md` + `codebook.json`. Flags coded variables whose level meanings are unknown as `[NEEDS DICTIONARY]` rather than guessing them, feeding `/define-variables` and the dictionary-first workflow. |
| **version-dataset** | Dataset version control for reproducibility. Builds a deterministic content-hash manifest (file SHA-256 + tabular schema + per-column value hashes), verifies a later copy to detect drift (schema / row-count / value changes), and diffs two manifests. Locks "which version of the data the results came from"; also reproducibility-locks the bundled demos. |
| **fill-protocol** | Fill institutional Word form templates (`.doc` / `.docx`) for IRB protocols, ethics applications, grant proposals, and other structured research documents while preserving the original styles, table layouts, fonts, and page geometry. Korean-aware (CJK eastAsia font enforcement, table cantSplit) but works for any-language template. Pairs with `write-protocol` (content) — fill-protocol renders the content into the institutional template. |
| **fill-icmje-coi** | Batch-generate per-author ICMJE Conflict of Interest Disclosure Forms (`coi_disclosure.docx`) for manuscript submission. Pre-fills all 13 disclosure items as "☒ None" plus the final certification using a synthetic seed template, then clones the seed per author with Date / Name / Manuscript Title replaced. Designed for the common case of hospital-based observational research where no author has real financial conflicts; circulated forms become "reply 변경 없음 + sign" for most authors and only flag those who need to amend. |
| **setup-medsci** | Diagnostic checklist for the MedSci Skills runtime. Verifies Python, R, Node, the agent host, Git, Zotero, and configured MCP servers, then prints a pass/fail table with links to the right setup doc for any missing component. Read-only — installs nothing. |

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

### Option 4: npm / npx (terminal-friendly shortcut)

A convenience wrapper for terminal users — it copies the same skills via the
dependency-free Python installer. The canonical install paths remain the plugin
marketplace (Option 1's sibling above) and the git clone above; npm is just a shortcut.

```bash
npx medsci-skills install            # all hosts (Claude, Codex, Cursor)
npx medsci-skills install --target claude
npx medsci-skills list               # list bundled skills
npx medsci-skills doctor             # quick Node/Python/skill-folder check
```

Requires Node 18+ and (for `install`/`doctor`) `python3` on your PATH.

### Platform notes

- Claude Code: skills are copied to `~/.claude/skills/` (also read by GitHub Copilot and Cursor).
- Codex: skills are copied to `~/.agents/skills/` (also read by Cursor and GitHub Copilot).
- Cursor: no separate step needed — Cursor reads `~/.claude/skills/` and `~/.agents/skills/` directly. The installer can still write an optional `.cursor/rules/` steering rule with `--cursor-project`.
- See [`docs/host_compatibility.md`](docs/host_compatibility.md) for the verified per-host install paths and their official sources.
- Windows users do not need WSL for the basic classroom workflow. Use WSL only for advanced reproducible Linux toolchains.

See [docs/classroom_distribution_plan.md](docs/classroom_distribution_plan.md) and [docs/classroom_materials.md](docs/classroom_materials.md) for instructor distribution, email templates, and first-class exercises.

> **Tip:** Not sure which skill to use? Start with `/orchestrate` -- it will classify your request and route you to the right tool.

## Updating

MedSci Skills updates often. You do **not** need GitHub, git, or the command line to stay current.

- **One click (recommended for the classroom install).** After installing, an updater is placed at
  `~/.medsci-skills/updater/` (and, if you chose `--desktop-launcher`, an **"Update MedSci Skills"**
  icon on your Desktop). Double-click it: it downloads the latest release from GitHub, verifies it,
  and re-installs — transactionally, so an interrupted update never corrupts your install.
- **Already installed an old copy?** Re-download the latest classroom ZIP **once** and double-click
  the installer; from then on the one-click updater is in place for every future update.
- **Terminal users:** `npx medsci-skills@latest install` always installs the latest.
- **Just checking:** `python3 installers/install.py --check-update` reports whether a newer version
  is available and installs nothing.
- **Get reminded (opt-in, Claude Code):** `python3 installers/install.py --enable-update-notify`
  shows a one-line *"update available"* notice when a Claude Code session starts. It is **off by
  default**, checks at most once a day, reads nothing about your session, and never installs
  anything. Turn it off with `--disable-update-notify`, or silence it with `MEDSCI_NO_UPDATE_CHECK=1`.
- **Claude Code plugin marketplace:** third-party marketplace **auto-update is off by default** —
  enable it in Claude Code or run a manual plugin update.

Updates connect only to GitHub, send no information about your machine or work, and create no
telemetry or tracking. Modified skills are backed up before an update and never auto-deleted. See
the [update privacy & data notice](docs/update_privacy.md).

## Key Features

### Autonomous E2E Pipeline

`orchestrate --e2e` or `write-paper --autonomous` runs the full pipeline from data to submission-ready DOCX with bounded validation. Skills pass outputs via structured manifests (`_analysis_outputs.md`, `_figure_manifest.md`) and project artifacts (`project.yaml`, `artifact_manifest.json`, `qc/status.json`). If a skill fails to produce expected outputs, the pipeline halts rather than proceeding with missing data. Phase 7 enforces a strict QC chain: AI pattern removal → reporting compliance check → `/verify-refs` citation audit → numerical claim audit → self-review with auto-fix (max 2 iterations) → DOCX/submission build.

### Anti-Hallucination Citations
Every reference produced by `search-lit` is verified against PubMed, Semantic Scholar, or CrossRef APIs. Existing manuscripts should then run `/verify-refs`, which writes a visible reference audit and blocks fabricated references before submission. No citation is ever generated from memory alone. API errors are batched silently -- no token waste from repeated failure messages.

### Anti-Hallucination Numerical Claims

`/meta-analysis` Phase 6b, `/self-review` Phase 2.5a, `/revise` Step 2.5, and `/write-paper`
Step 7.3a enforce a common 3-layer audit (CSV ↔ analysis script ↔ manuscript) with primary-
source back-checking for pooled estimates and revision-era numbers. Hand-typed numerical
matrices without CSV-coordinate comments are flagged as structural risks even when the values
are currently correct, since the next revision will re-introduce the same failure mode.

### Reference Safety (Phase 1)
Projects declare their source-of-truth layout in `SSOT.yaml`, and a `qc/migration_complete` marker gates strict enforcement. `/verify-refs` is the sole writer of `qc/reference_audit.json`. The `MEDSCI_VERIFY_REFS_MODE` env var (`auto` default, `warn`, `enforce`, `off`) controls behavior — `auto` blocks only when both SSOT.yaml and the migration marker are present, otherwise warns. Legacy projects freeze as warn-only; new projects opt in via `scripts/migrate_project_to_ssot.py`. An optional PostToolUse hook (not shipped in this repo — document only) can invoke `/verify-refs` automatically on manuscript saves for users who install it locally at `~/.claude/hooks/verify-refs-guard.sh`; the regression suite (`tests/test_phase1c_hooks.sh`) runs end-to-end only when that local hook is present and is skipped otherwise.

### Meta-Analysis Failure Modes
`/meta-analysis` ships empirical failure-mode references (data integrity, review orchestration, submission package drift, post-submission release ops) with four automation hooks: `scripts/prisma_5way_consistency.py` (DI-6 PRISMA number consistency), `scripts/extraction_consensus_log_init.py` (DI-1 dual-extraction scaffold), `scripts/tag_cleanup_gate.sh` (DI-8 placeholder tag gate), and `scripts/verify_package_integrity.py` (SPD SHA-256 manifest for submission bundles).

### 36 Reporting Guidelines & RoB Tools Built-in
`check-reporting` includes bundled checklists for 36 guidelines and risk-of-bias tools: STROBE, STARD, STARD-AI, TRIPOD, TRIPOD+AI, TRIPOD-LLM, PRISMA 2020, PRISMA-DTA, PRISMA-P, MOOSE, ARRIVE, CONSORT, CONSORT-AI, CARE, SPIRIT, SPIRIT-AI, CLAIM, DECIDE-AI, SQUIRE 2.0, CLEAR, GRRAS, MI-CLEAR-LLM, SWiM, AMSTAR 2, QUADAS-2, QUADAS-C, RoB 2, ROBINS-I, ROBINS-E, ROBIS, ROB-ME, PROBAST, PROBAST+AI, NOS, COSMIN, RoB NMA. Includes Results/Discussion section boundary checks and machine-readable JSON summary for pipeline integration.

### Publication-Ready Output
`analyze-stats` generates reproducible Python/R code for 13 analysis types -- including regression, propensity score, and repeated measures -- with mandatory calibration for prediction models. `make-figures` produces journal-specification figures (300 DPI, colorblind-safe palettes, proper dimensions), visual/graphical abstracts, and a tool selection guide (D2 for flow diagrams, matplotlib for data plots). `--study-type` auto-generates the complete figure set for each study design.

### Results/Discussion Boundary Enforcement
`write-paper` enforces strict separation: Results contain only factual findings (no interpretation, no "why"), Discussion uses interactive anchor-paper scaffolding. The critic rubric includes a dedicated Section Boundaries pass/fail gate.

### IRB Protocol to Submission in One Pipeline
`design-study` -> `calc-sample-size` -> `write-protocol` gives you an IRB-ready protocol. After data collection: `clean-data` -> `analyze-stats` -> `write-paper` -> `self-review` -> `find-journal` -> cover letter. Every transition is a defined skill handoff.

### Skills Work Together
Skills call each other. `check-reporting` invokes `make-figures` for PRISMA diagrams. `write-paper` calls `search-lit` for citation verification. `self-review` delegates reporting compliance to `check-reporting`. `calc-sample-size` output feeds directly into `write-protocol`'s IRB justification section.

### Validation status — available vs CI-gated vs evaluated
Be precise about what "validated" means here — the three tiers are different facts:
- **Available** — every bundled skill and deterministic detector. The current totals are the single source of truth in [`metadata/catalog_counts.json`](metadata/catalog_counts.json) and [`MEDSCI_AUDIT.md`](MEDSCI_AUDIT.md).
- **CI-gated** — detectors with a committed challenge/regression test that runs on every push via [`validate.yml`](.github/workflows/validate.yml).
- **Formally evaluated** — the subset measured by the canonical evaluation harness **E1** in [`evaluation/`](evaluation/), which is v3.8-era and validates the then-current detector subset; detectors added since are **CI-tested, not yet E1-evaluated** (the size of the catalog and the size of the evaluated subset are deliberately reported as separate facts — see `MEDSCI_AUDIT.md`).

The toolkit is *designed to reduce common manuscript-preparation errors*; it does **not** guarantee correctness and is **not** clinically validated.

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

- An [Agent Skills](https://agentskills.io)-compatible host — [Claude Code](https://claude.ai/code) (primary), or Codex / Cursor / GitHub Copilot (see [`docs/host_compatibility.md`](docs/host_compatibility.md); some live-data workflows rely on Claude MCP servers)
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

## Contributing

Contributions are welcome — and most are **one small, self-contained file** that a
template walks you through. You do not need to understand the whole pipeline to add value.
Pick a [**good first issue**](https://github.com/Aperivue/medsci-skills/contribute), or start
from one of these:

| Want to add… | How | Issue |
|---|---|---|
| **A journal profile** (submission rules for a journal we don't cover) | `/add-journal`, or copy an existing `journal_profiles/*.md` | [#115](https://github.com/Aperivue/medsci-skills/issues/115) |
| **A figure exemplar** (ROC, KM, forest, Bland–Altman, confusion matrix…) | one `make-figures/references/exemplar_plots/*.md` anatomy model | [#118](https://github.com/Aperivue/medsci-skills/issues/118) |
| **A CSL citation style** for a journal that lacks one | drop a `.csl` into `manage-refs/citation_styles/` | [#117](https://github.com/Aperivue/medsci-skills/issues/117) |
| **A de-identification locale pack** for one more country | add patterns to `deidentify/` | [#116](https://github.com/Aperivue/medsci-skills/issues/116) |
| **A reporting checklist or peer-review exemplar** | one reference file in the matching skill | [#120](https://github.com/Aperivue/medsci-skills/issues/120) |
| **A README translation** (e.g., zh-CN) | a translated `README` | [#119](https://github.com/Aperivue/medsci-skills/issues/119) |

Every contribution is gated the same way the maintainers are: it must be a self-contained
file, pass the CI (`validate.yml` — PII scan, structure, catalog consistency), and carry no
patient or author identifiers. See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the PR checklist
and the PII/publication hygiene rules. New ideas that don't fit a template? Open a
[skill request](https://github.com/Aperivue/medsci-skills/issues/new?template=skill_request.yml)
or a [detector request](https://github.com/Aperivue/medsci-skills/issues/new?template=detector_request.yml).

**Governance:** [`ROADMAP.md`](ROADMAP.md) (priorities + scope boundary),
[`MAINTAINERS.md`](MAINTAINERS.md) (roles — clinical authority stays with the founder),
[`docs/maintainer_workflow.md`](docs/maintainer_workflow.md) (review + release process),
and [`SECURITY.md`](SECURITY.md) (vulnerability reporting + the medical-scope boundary).
A change that touches a medical/research claim needs Clinical-Lead review.

## In the Wild

Adoption is tracked openly in [`IMPACT.md`](IMPACT.md) (stars, forks, traffic,
release downloads — snapshotted weekly into [`metrics/traffic_log.csv`](metrics/traffic_log.csv))
and academic use is logged in [`docs/citations.md`](docs/citations.md).

**Used MedSci Skills in your research?** Please
[let us know](https://github.com/Aperivue/medsci-skills/issues/new?template=used-in-research.yml).
It helps other researchers find the toolkit — and we list it (with your permission).

## Citation

If you use MedSci Skills in your research, please cite the software via
[`CITATION.cff`](CITATION.cff) (Zenodo concept DOI
[10.5281/zenodo.20155321](https://doi.org/10.5281/zenodo.20155321)).

The design and evaluation of the toolkit are described in a preprint:

> Nam Y, Kim N. *Agentic Skills for Auditable and Reproducible Medical Research
> Writing: An Integrity-gated Architecture for LLM-Assisted Clinical Manuscripts.*
> arXiv:2606.09500 (2026). https://arxiv.org/abs/2606.09500

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
