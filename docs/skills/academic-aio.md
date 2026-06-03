<!-- AUTO-GENERATED from skills/academic-aio/SKILL.md by scripts/gen_skill_docs.py. Do not edit by hand. -->

# academic-aio

> Medical AI paper optimization for AI search engines (Perplexity, ChatGPT web, Elicit, Consensus, SciSpace) and RAG-based literature tools. Applies when drafting or reviewing titles, abstracts, structured summary boxes (Key Points / Research in Context / Plain-Language Summary), manuscripts for high-impact medical AI journals (Lancet Digital Health, Radiology, Radiology-AI, npj Digital Medicine, Nature Medicine), preprints (medRxiv/arXiv), GitHub README + CITATION.cff + Zenodo archives, and Hugging Face model/dataset cards. Integrates TRIPOD+AI, CLAIM 2024, STARD-AI, TRIPOD-LLM, DECIDE-AI reporting requirements with generative engine optimization (GEO) principles. Produces a visible pass/fail checklist.

**Invoke:** `/academic-aio` · **Tools:** Read, Write, Edit, Grep, Glob · **Model:** inherit

## When to use

`academic-aio` activates on requests such as: AIO, LLMO, GEO, AI search optimization, discoverability, abstract optimization, structured abstract, Key Points, Research in context, plain-language summary, preprint strategy, GitHub README, CITATION.cff, Zenodo DOI, Hugging Face model card, dataset card, Perplexity, Elicit, Consensus, SciSpace, RAG visibility, reporting guideline compliance, TRIPOD-AI, CLAIM, STARD-AI, taxonomy review paper, Radiology Key Points, Lancet Digital Health Research in context, npj Digital Medicine.

## Quality Card

**Purpose** — Make a medical-AI manuscript discoverable and citable by AI search/RAG tools without sacrificing reporting-guideline compliance.

**Safety boundaries**

- Off by default in autonomous pipelines; rewrites require user review (no silent rewrite).
- Reporting-guideline claims are checked, never asserted without the underlying item being present.

**Known limitations**

- GEO/AIO heuristics evolve with each engine; recommendations are point-in-time.
- Does not draft new scientific content; optimizes existing approved text only.

**Validation**

- `python3 scripts/validate_schema.py <summary-box-file>`

**Evidence** — `bundled_script`

## Bundled resources

**References** (`skills/academic-aio/references/`):

- `case_studies/` (1 file)
- `checklists/` (1 file)
- `journal_summarybox_templates.yaml`
- `oac_funding_checklist.yaml`
- `reporting_guideline_mapping.md`
- `schema_markup_templates/` (5 files)

**Scripts** (`skills/academic-aio/scripts/`):

- `batch_metadata_audit.py`
- `validate_schema.py`

**Templates** (`skills/academic-aio/templates/`):

- `aio_audit_checklist.md.j2`

## Source

Canonical definition: [`skills/academic-aio/SKILL.md`](../../skills/academic-aio/SKILL.md)

---

*Part of [MedSci Skills](../../README.md) — Claude Code skills for the medical research lifecycle. This page is generated from the skill's `SKILL.md`; edit that file and re-run `scripts/gen_skill_docs.py`.*
