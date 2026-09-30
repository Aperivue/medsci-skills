<div align="center">

# MedSci Skills

English | [简体中文](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/README.zh-CN.md)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/LICENSE)
[![Release](https://img.shields.io/github/v/release/Aperivue/medsci-skills?style=flat-square&color=blue)](https://github.com/Aperivue/medsci-skills/releases/latest)
[![CI](https://img.shields.io/github/actions/workflow/status/Aperivue/medsci-skills/validate.yml?branch=main&style=flat-square&label=CI)](https://github.com/Aperivue/medsci-skills/actions/workflows/validate.yml)
![Skills](https://img.shields.io/badge/Skills-59-brightgreen?style=flat-square)
[![npm](https://img.shields.io/npm/v/medsci-skills?style=flat-square&label=npm&color=cb3837)](https://www.npmjs.com/package/medsci-skills)
[![DOI](https://img.shields.io/badge/DOI-10.5281%2Fzenodo.20155321-blue?style=flat-square)](https://doi.org/10.5281/zenodo.20155321)
[![arXiv](https://img.shields.io/badge/arXiv-2606.09500-b31b1b?style=flat-square)](https://arxiv.org/abs/2606.09500)

**Created & maintained by [Yoojin Nam, MD](https://orcid.org/0000-0001-8565-1360)**
<br>
<sub>Department of Radiology and Research Institute of Radiology, University of Ulsan College of Medicine, Asan Medical Center, Seoul, Republic of Korea</sub>

</div>

<a id="what-is-medsci-skills"></a>
MedSci Skills is a set of [Agent Skills](https://agentskills.io) for clinical research: literature and references, study design, statistics, figures, manuscript drafting, reporting-guideline checks and journal submission, plus a lane for building and validating medical-imaging AI models.
It is for physicians and biomedical or medical-engineering researchers who work in Claude Code, Codex, Cursor or GitHub Copilot.
The skills draft and check, bundled scripts recompute what can be recomputed, and every output still needs review by a qualified researcher; it is not a diagnostic tool or an autonomous author.

## Installation

<a id="quick-start"></a><a id="install-with-gh-skill"></a><a id="install-as-a-claude-code-plugin"></a><a id="option-1-classroom-installer-recommended-for-non-programmers"></a><a id="option-2-install-all-skills-manually"></a><a id="option-3-install-individual-skills-manually"></a><a id="option-4-npm--npx-terminal-friendly-shortcut"></a><a id="option-5-github-cli-gh-skill"></a><a id="platform-notes"></a><a id="optional-let-plain-language-requests-find-the-skills"></a><a id="updating"></a><a id="setup"></a><a id="requirements"></a>
In a terminal, with Node 18+ and Python 3.9+ installed:

```bash
npx medsci-skills install
```

This copies every skill into `~/.claude/skills/` (read by Claude Code, Cursor and GitHub Copilot) and `~/.agents/skills/` (read by Codex, Cursor and GitHub Copilot).
Restart your agent, type `/orchestrate`, and describe what you want to do; it routes the request to the right skill.
To be told when a new version ships, add `--enable-update-notify`: a one-line notice at Claude Code session start, off by default, no telemetry.

Other ways to install, each described in [docs/install.md](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/docs/install.md):

- **No terminal:** the [classroom installer](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/docs/install.md#classroom-installer-no-terminal) for Windows or macOS — download, unzip, double-click.
- **Claude Code plugin:** [`/plugin marketplace add Aperivue/medsci-skills`](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/docs/install.md#claude-code-plugin-marketplace), then enable the plugins you want; skills are then namespaced, e.g. `/medsci-analysis:analyze-stats`.
- **GitHub CLI 2.90+:** [`gh skill install --all Aperivue/medsci-skills`](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/docs/install.md#github-cli-gh-skill), or name a single skill.
- **git:** [clone the repository](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/docs/install.md#git-clone) and copy `skills/*` into `~/.claude/skills/`.

[Updating](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/docs/install.md#updating), [what individual skills need](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/docs/install.md#requirements) (pandoc, R, PyTorch), [where the files go](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/docs/install.md#where-the-skills-go) and the [optional routing block](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/docs/install.md#optional-let-plain-language-requests-find-the-skills) for plain-language requests are on the same page.

## Three workflows to start with

<a id="start-here-3-workflows"></a><a id="use-cases"></a>
Call a skill by name, or describe the task to `/orchestrate`.

**Check a manuscript against its reporting guideline — `/check-reporting`**
- You give: your manuscript and, if you know it, the guideline — it covers 49 reporting guidelines and risk-of-bias tools, from STROBE, STARD and CONSORT to PRISMA 2020 and TRIPOD+AI.
- You get: an item-by-item audit (PRESENT, PARTIAL, MISSING or N/A, with where each item was found), a list of fixes, and a JSON summary in `qc/`; it is a working audit, not the checklist you upload to the journal.

**Analyse a dataset — `/analyze-stats`**
- You give: a de-identified data file (CSV, Excel or TSV) and your research question.
- You get: an analysis plan to approve, then Python (or R) code that it runs, tables as CSV and Markdown, figures as PDF and 300-dpi PNG, and a manifest that `/make-figures` and `/write-paper` read.

**Verify references — `/verify-refs`**
- You give: a manuscript or bibliography (`.md`, `.docx`, `.bib`, `.txt` or `.tsv`).
- You get: `qc/reference_audit.json`, marking each reference OK, MISMATCH, UNVERIFIED or FABRICATED after lookup in PubMed, CrossRef and OpenAlex; it reports and never edits your references.

Longer chains (pre-submission audit, data to manuscript, systematic review) and step-by-step command lists for common tasks are in [docs/workflows.md](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/docs/workflows.md).

### Demos

<a id="live-demos-five-study-types-five-full-pipelines"></a><a id="demo-1-diagnostic-accuracy--wisconsin-breast-cancer"></a><a id="demo-2-meta-analysis--bcg-vaccine-efficacy"></a><a id="demo-3-epidemiology--nhanes-obesity--diabetes"></a><a id="demo-5-external-validation--msd--amos-spleen-segmentation"></a><a id="project-folder-structure"></a>
Five worked examples on public datasets, with their code, outputs and QC reports committed to the repository:

| Demo | Data | What it shows |
|------|------|---------------|
| [Diagnostic accuracy](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/demo/01_wisconsin_bc) | Wisconsin breast cancer (`sklearn`) | Analysis to manuscript draft, STARD 2015 audit |
| [Meta-analysis](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/demo/02_metafor_bcg) | BCG vaccine trials (`metafor::dat.bcg`) | Pooled analysis to manuscript draft, PRISMA 2020 audit |
| [Survey epidemiology](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/demo/03_nhanes_obesity) | NHANES 2017–18 | Weighted survey analysis to manuscript draft, STROBE audit |
| [Model engineering](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/demo/04_pneumoniamnist_cnn/README.md) | PneumoniaMNIST | CNN scaffold, leakage gates, training, evaluation, Grad-CAM |
| [External validation](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/demo/05_msd_amos_spleen/README.md) | MSD spleen, then AMOS CT and MRI | 3-D segmentation tested on an external cohort, including where it failed |

What each demo produced, and how to rerun it: [docs/demos.md](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/docs/demos.md).

## Skills

<a id="by-research-stage"></a><a id="available-now"></a>
All 59 skills, by research stage. Each name links to its reference page (what it does, when to use it, its known limits). `npx medsci-skills list` prints the same groups, and with the plugin install each row is one plugin.

| Stage | Plugin | Skills |
|-------|--------|--------|
| Project & Workflow | `medsci-project` | [`author-strategy`](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/docs/skills/author-strategy.md) · [`find-cohort-gap`](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/docs/skills/find-cohort-gap.md) · [`intake-project`](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/docs/skills/intake-project.md) · [`ma-scout`](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/docs/skills/ma-scout.md) · [`manage-project`](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/docs/skills/manage-project.md) · [`orchestrate`](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/docs/skills/orchestrate.md) |
| Literature & References | `medsci-literature` | [`fulltext-retrieval`](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/docs/skills/fulltext-retrieval.md) · [`lit-sync`](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/docs/skills/lit-sync.md) · [`manage-refs`](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/docs/skills/manage-refs.md) · [`obsidian-paper-vault`](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/docs/skills/obsidian-paper-vault.md) · [`search-lit`](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/docs/skills/search-lit.md) · [`verify-refs`](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/docs/skills/verify-refs.md) |
| Data & Study Design | `medsci-data` | [`calc-sample-size`](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/docs/skills/calc-sample-size.md) · [`clean-data`](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/docs/skills/clean-data.md) · [`define-variables`](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/docs/skills/define-variables.md) · [`deidentify`](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/docs/skills/deidentify.md) · [`design-ai-benchmarking`](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/docs/skills/design-ai-benchmarking.md) · [`design-study`](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/docs/skills/design-study.md) · [`generate-codebook`](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/docs/skills/generate-codebook.md) · [`version-dataset`](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/docs/skills/version-dataset.md) |
| Analysis & Figures | `medsci-analysis` | [`analyze-stats`](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/docs/skills/analyze-stats.md) · [`batch-cohort`](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/docs/skills/batch-cohort.md) · [`cross-national`](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/docs/skills/cross-national.md) · [`make-figures`](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/docs/skills/make-figures.md) · [`meta-analysis`](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/docs/skills/meta-analysis.md) · [`replicate-study`](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/docs/skills/replicate-study.md) |
| Model Engineering & Validation | `medsci-modeling` | [`architecture-zoo`](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/docs/skills/architecture-zoo.md) · [`explainability`](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/docs/skills/explainability.md) · [`mllm-eval`](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/docs/skills/mllm-eval.md) · [`model-card`](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/docs/skills/model-card.md) · [`model-evaluation`](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/docs/skills/model-evaluation.md) · [`model-scaffold`](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/docs/skills/model-scaffold.md) · [`model-sourcing`](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/docs/skills/model-sourcing.md) · [`model-validation`](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/docs/skills/model-validation.md) · [`preprocess-imaging`](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/docs/skills/preprocess-imaging.md) · [`profile-imaging`](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/docs/skills/profile-imaging.md) · [`radiomics-ml`](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/docs/skills/radiomics-ml.md) · [`uncertainty-imaging`](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/docs/skills/uncertainty-imaging.md) |
| Writing & Manuscript | `medsci-writing` | [`academic-aio`](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/docs/skills/academic-aio.md) · [`humanize`](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/docs/skills/humanize.md) · [`polish-language`](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/docs/skills/polish-language.md) · [`review-paper`](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/docs/skills/review-paper.md) · [`revise`](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/docs/skills/revise.md) · [`write-paper`](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/docs/skills/write-paper.md) · [`write-protocol`](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/docs/skills/write-protocol.md) |
| Review & Compliance | `medsci-review` | [`check-reporting`](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/docs/skills/check-reporting.md) · [`peer-review`](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/docs/skills/peer-review.md) · [`self-review`](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/docs/skills/self-review.md) |
| Submission & Journals | `medsci-submission` | [`add-journal`](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/docs/skills/add-journal.md) · [`fill-icmje-coi`](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/docs/skills/fill-icmje-coi.md) · [`fill-protocol`](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/docs/skills/fill-protocol.md) · [`find-journal`](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/docs/skills/find-journal.md) · [`grant-builder`](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/docs/skills/grant-builder.md) · [`sync-submission`](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/docs/skills/sync-submission.md) |
| Presentation & Tooling | `medsci-presentation` | [`contribute`](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/docs/skills/contribute.md) · [`present-paper`](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/docs/skills/present-paper.md) · [`publish-skill`](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/docs/skills/publish-skill.md) · [`render-pdf-doc`](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/docs/skills/render-pdf-doc.md) · [`setup-medsci`](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/docs/skills/setup-medsci.md) |

Not sure which one fits? Start with `/orchestrate`.

## Patient data and safety

<a id="disclaimer"></a><a id="validation-status--available-vs-ci-gated-vs-evaluated"></a>
Do not give an agent identifiable patient data. `/deidentify` runs locally with no network or AI calls: it detects protected health information with regex and heuristics (locale packs for ten countries) and pseudonymises it after an interactive review, and `/analyze-stats` asks whether a raw data file contains patient identifiers before using it. These are research productivity tools, not clinical decision support: they are not clinically validated and do not replace expert review, so a qualified researcher must check every output before it is used in a publication or clinical context. The 90 deterministic detectors recompute or cross-check specific things (reference metadata, arithmetic, checklist items, data leakage); a clean run means those checks found nothing, not that the manuscript is correct. [MEDSCI_AUDIT.md](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/MEDSCI_AUDIT.md) lists each detector and which have been formally evaluated; reference lookups use the public, keyless APIs in [docs/connectors.md](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/docs/connectors.md).

## Citation

If MedSci Skills helped produce your manuscript, protocol, or analysis, please cite it —
software citation is how a tool like this earns academic recognition, and it takes one line.

**In your manuscript** (Methods or Acknowledgements — cite the version you actually used):

> Reporting-guideline compliance, reference verification, and pre-submission integrity checks
> were assisted by MedSci Skills (version X.Y.Z; https://github.com/Aperivue/medsci-skills;
> archived at Zenodo, https://doi.org/10.5281/zenodo.20155321).

**BibTeX** (the software, and the preprint describing its design):

```bibtex
@software{nam_medsci_skills,
  author    = {Nam, Yoojin},
  title     = {{MedSci Skills: Claude Code Skills for the Medical Research Lifecycle}},
  year      = {2026},
  publisher = {Zenodo},
  doi       = {10.5281/zenodo.20155321},
  url       = {https://github.com/Aperivue/medsci-skills}
}

@article{nam2026agentic,
  author  = {Nam, Yoojin and Jeong, Jinhoon and Kim, Namkug},
  title   = {{Deterministic Integrity Gates for LLM-Assisted Clinical Manuscript
             Preparation: An Auditable Biomedical Informatics Architecture}},
  year    = {2026},
  journal = {arXiv preprint arXiv:2606.09500},
  url     = {https://arxiv.org/abs/2606.09500}
}
```

The Zenodo **concept DOI** [10.5281/zenodo.20155321](https://doi.org/10.5281/zenodo.20155321)
always resolves to the latest release; [`CITATION.cff`](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/CITATION.cff) carries the machine-readable
metadata (GitHub's "Cite this repository" button reads it).

**Used it in published or in-review work?** Tell us via the
["Used in research" issue template](https://github.com/Aperivue/medsci-skills/issues/new?template=used-in-research.yml)
— with your permission it is added to [`docs/citations.md`](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/docs/citations.md).

## License

MIT License. See [LICENSE](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/LICENSE) for details.

Some bundled material is **not** ours and is not MIT: the official guideline templates, the CSL citation styles, and a few checklist summaries carry their own terms — including CC BY-NC, which restricts commercial use. Those are indexed in [THIRD-PARTY-NOTICES.md](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/THIRD-PARTY-NOTICES.md), which ships with every copy and is checked against the tree on every build.

Bundled reporting guideline checklists retain their original Creative Commons licenses. See each checklist file for attribution.

Optional dependency: `pdf_to_md.py` uses [pymupdf4llm](https://pymupdf.readthedocs.io) (AGPL-3.0). Not bundled -- installed separately by the user via `pip install pymupdf4llm`.

### Acknowledgements

- `make-figures` Critic Loop is inspired by [PaperBanana](https://github.com/dwzhu-pku/PaperBanana) (Zhu et al., *Automating Academic Illustration for AI Scientists*, arXiv:2601.23265, 2025) and by prior self-refinement research — Self-Refine (Madaan et al., 2023), Reflexion (Shinn et al., 2023), and Constitutional AI (Anthropic, 2022). The implementation in this repository is a clean-room reconstruction specialized for medical publication figures; no code, prompts, or configurations are derived from PaperBanana's repository.
- Reporting-guideline checklists bundled with `check-reporting` are redistributed under their original Creative Commons licenses (see each checklist for attribution).
- Wong colorblind-safe palette: Wong B. *Points of view: Color blindness.* Nature Methods 8:441 (2011).

## More

<a id="whats-new"></a><a id="key-features"></a><a id="autonomous-e2e-pipeline"></a><a id="anti-hallucination-citations"></a><a id="anti-hallucination-numerical-claims"></a><a id="reference-safety-phase-1"></a><a id="meta-analysis-failure-modes"></a><a id="49-reporting-guidelines--rob-tools-built-in"></a><a id="publication-ready-output"></a><a id="resultsdiscussion-boundary-enforcement"></a><a id="irb-protocol-to-submission-in-one-pipeline"></a><a id="skills-work-together"></a><a id="skill-boundaries--which-to-use-and-in-what-order"></a><a id="contributing"></a><a id="in-the-wild"></a><a id="cited-in-the-literature"></a><a id="adoption"></a><a id="star-history"></a><a id="why-this-repo"></a><a id="what-this-is-not"></a><a id="about"></a>

- [Release notes](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/CHANGELOG.md) — what changed in each version.
- [Workflows and skill boundaries](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/docs/workflows.md) — skill chains, which skill to use when two look alike, and checks that span skills.
- [Skill reference](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/docs/skills/README.md) and [FAQ](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/docs/faq.md).
- [Host compatibility](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/docs/host_compatibility.md) — verified install paths for Claude Code, Codex, Cursor and GitHub Copilot.
- [How it differs from other skill collections](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/docs/competitive_positioning.md) and the [scope boundary](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/ROADMAP.md#not-planned--explicitly-out-of-scope).
- [Contributing](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/CONTRIBUTING.md) — most contributions are one file; `/contribute` sends a change from your installed copy after scanning it for patient data. [Good first issues](https://github.com/Aperivue/medsci-skills/contribute).
- [Adoption](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/IMPACT.md) (stars, forks, downloads) and [citations](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/docs/citations.md).
- Governance: [ROADMAP](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/ROADMAP.md), [MAINTAINERS](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/MAINTAINERS.md), [SECURITY](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/SECURITY.md), [CONTRIBUTORS](https://github.com/Aperivue/medsci-skills/blob/v6.0.0/CONTRIBUTORS.md).

Built by [Aperivue](https://aperivue.com).
