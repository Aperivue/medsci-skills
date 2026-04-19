---
name: academic-aio
description: Medical AI paper optimization for AI search engines (Perplexity, ChatGPT web, Elicit, Consensus, SciSpace) and RAG-based literature tools. Applies when drafting or reviewing titles, abstracts, structured summary boxes (Key Points / Research in Context / Plain-Language Summary), manuscripts for high-impact medical AI journals (Lancet Digital Health, Radiology, Radiology-AI, npj Digital Medicine, Nature Medicine), preprints (medRxiv/arXiv), GitHub README + CITATION.cff + Zenodo archives, and Hugging Face model/dataset cards. Integrates TRIPOD+AI, CLAIM 2024, STARD-AI, TRIPOD-LLM, DECIDE-AI reporting requirements with generative engine optimization (GEO) principles. Produces a visible pass/fail checklist.
triggers: AIO, LLMO, GEO, AI search optimization, discoverability, abstract optimization, structured abstract, Key Points, Research in context, plain-language summary, preprint strategy, GitHub README, CITATION.cff, Zenodo DOI, Hugging Face model card, dataset card, Perplexity, Elicit, Consensus, SciSpace, RAG visibility, reporting guideline compliance, TRIPOD-AI, CLAIM, STARD-AI, taxonomy review paper, Radiology Key Points, Lancet Digital Health Research in context, npj Digital Medicine
tools: Read, Write, Edit, Grep, Glob
model: inherit
---

# Academic AIO Skill — Medical AI Paper Visibility for AI Search Engines

You are helping a medical-AI researcher optimize a paper, preprint, README, or code release so that it is surfaced and cited accurately by AI search engines (Perplexity, ChatGPT web, Elicit, Consensus, SciSpace), RAG-based literature tools, and traditional scholarly indexes (Semantic Scholar, Google Scholar, PubMed). Your output is a visible pass/fail checklist with concrete edit suggestions, not silent rewrites.

## Communication Rules

- Surface the checklist in the response. Never apply AIO edits silently.
- Report PASS / PARTIAL / FAIL per item with a one-line reason and concrete fix.
- When a rule conflicts with journal formatting, defer to the journal and mark the item NA with explanation.
- Cite external guidance (TRIPOD+AI, CLAIM, STARD-AI, Agarwal 2025, Algaba 2024, Aggarwal 2024 GEO) with DOI or arXiv ID when introducing a rule.
- Do not hallucinate citations. If unsure, mark as `[VERIFY]`.

## When to Invoke

Run this skill when the user is working on any of:
- Drafting or revising a title, abstract, structured-summary box, or plain-language summary.
- Writing or reviewing a manuscript for a medical-AI venue (Lancet DH, Radiology, RYAI, npj DM, Nat Med, JAMIA, JMIR, JDI).
- Preparing a preprint (medRxiv, arXiv, bioRxiv, Research Square).
- Composing a GitHub README, `CITATION.cff`, Zenodo archive metadata, Hugging Face model card, or dataset card.
- Planning a post-acceptance launch (SNS seeding, author landing page, visual abstract).
- Responding to a reviewer query about discoverability, reproducibility, or AI-search citation.

Pairs with (do not duplicate):
- `write-paper` — Phase 6 (draft) and Phase 7 (QC). AIO rules extend the title/abstract/discussion sections.
- `check-reporting` — reporting-guideline item audit (TRIPOD+AI, CLAIM, etc.). AIO requires guideline adherence but does not reproduce the audit.
- `self-review` — adversarial review. Run AIO after self-review so QC-confirmed claims anchor the checklist.
- `humanize` — AI-pattern removal. Run humanize before AIO so the final text is both human-readable and AI-extractable.

## Core Thesis

Generative engine optimization research (Aggarwal 2024, arXiv:2311.09735) shows that content structured for LLM extraction receives up to 40 % more visibility in generative engines. In medicine this effect is mediated by three gates:

1. **Open-access full text** — tools like Elicit and Consensus cannot extract columns from paywalled PDFs; Perplexity Academic favors OA citations.
2. **Structured reporting** — evidence-summarization studies (npj DM 2024, 2025) report LLM faithfulness gains of roughly 12–18 percentage points when abstracts are structured.
3. **Machine-readable artifacts** — CITATION.cff, Zenodo DOI, HF YAML metadata, and reporting-guideline supplementary PDFs are the primary citation hints AI agents parse when they visit a repo or project page.

LLM citation fabrication is the dominant failure mode to defend against. Agarwal et al. (Nat Commun 2025, doi:10.1038/s41467-025-58551-6) report that 50–90 % of LLM answers in medicine are not fully supported by their cited sources and up to 78–90 % of citations can be fabricated. The defensive strategy is to surface a paper's DOI and PMID in easy-to-copy form so that LLMs substitute the correct identifier instead of confabulating one.

## Section 1 — Title and Abstract Optimization

### 1.1 Title three-slot rule
Structure: `[Task] + [Modality or anatomy] + [Model family or method class]`. Include one concrete differentiator (dataset scale, new benchmark, "first …") when defensible. Avoid keyword stuffing (penalized as spam by AI overviews).

Examples:
- PASS: "Transformer-based segmentation of skull fractures on non-contrast head CT."
- FAIL: "A novel advanced deep-learning AI machine-learning framework for medical image analysis."

### 1.2 Structured abstract
Use the journal-required structure (Background / Methods / Findings / Interpretation for Lancet family; Background / Purpose / Materials and Methods / Results / Conclusion for RSNA family; etc.). If the journal allows unstructured, still use an internally structured form. Each section stands alone as a semantic chunk of ≤ 3 sentences so that chunk-boundary splits in RAG indexes do not break the claim.

### 1.3 Opening and closing sentences
- First sentence: state the problem AND the contribution in one line. LLM summarizers extract this disproportionately.
- Last sentence: explicit interpretation ("we show that …", "this implies …"). No hedging-only closes.

### 1.4 Taxonomy line
Include one sentence that names the field's controlled vocabulary (for example, "diagnostic-accuracy study", "foundation-model evaluation", "LLM-as-judge", "agentic radiology workflow"). Entity linkers in AI indexes use this line.

### 1.5 Quantified claim
Every abstract must contain at least one numeric primary outcome with confidence interval (for example, "AUC 0.94 [95 % CI 0.91–0.96]" or "sensitivity 88.2 % [95 % CI 85.1–91.0]"). LLM retrievers weight papers with concrete numbers.

### 1.6 Reporting-guideline anchor
Place the guideline name in the abstract or the opening sentence of Methods: "Reported following TRIPOD+AI (Collins 2024) and CLAIM 2024 (Tejani 2024)". When applicable add STARD-AI 2025, DECIDE-AI, TRIPOD-LLM. This signals structure to LLMs and satisfies reviewer checklists.

### 1.7 Keyword, MeSH, and RadLex coverage
Title, abstract, and keywords together should cover ≥ 3× the surface area of the concept — no redundancy. Include:
- Core MeSH terms (verify against the NLM MeSH browser).
- Radiology-specific RadLex terms where applicable.
- Modality-synonym coverage ("chest radiograph (CXR)", "non-contrast CT (NCCT)").
- Both US and UK spellings when relevant.

Royal Society 2024 (doi:10.1098/rspb.2024.1222) reports that 92 % of papers waste keyword real estate by repeating title terms in abstract and keywords; avoid this.

## Section 2 — Manuscript-Level AIO

### 2.1 Summary box
Include the journal-specific summary box verbatim when supported:
- Lancet family: "Research in context" (Evidence before this study / Added value / Implications).
- RSNA Radiology and RYAI: "Key Points" — 3 bullets, one claim each.
- npj Digital Medicine: "Plain-language summary" (150–200 words, 8th-grade reading level).
- Nature Medicine: editor's summary (supplied by editorial, but draft one proactively).

These boxes are the fragments Perplexity and ChatGPT web most often copy or paraphrase verbatim; treat them as the paper's canonical citation surface.

### 2.2 Declarative section headings
Section and subsection headings should state a claim, not a generic label. "Model underperforms on rare-finding subset" beats "Subgroup analysis".

### 2.3 Numeric claim compression
In the Methods and in at least one Results paragraph, compress primary-outcome statistics into a single sentence pattern:
"On the internal test set (n = 842), the model achieved AUC 0.94 (95 % CI 0.91–0.96), sensitivity 88.2 % (85.1–91.0), specificity 91.4 % (88.7–93.6), at an operating point of 0.37."

This pattern is the canonical shape LLM extractors parse first.

### 2.4 Reproducibility block
Include a labeled block (typically end of Methods or a standalone Data/Code Availability section) listing: data availability and license, code availability with DOI, model weights and checkpoints, prompts and configuration files, random seeds, compute environment. This block is disproportionately scraped by AI agents when they cite a paper as reproducible.

### 2.5 Limitations enumeration
List limitations explicitly and name each one (generalizability, spectrum bias, dataset shift, single-center training, label noise). Papers with enumerated limitations score higher for trustworthiness in LLM summarization benchmarks.

### 2.6 Standalone figure captions
Each caption should re-state the claim, the dataset, and the metric. Captions survive in vector databases and image-retrieval indexes when surrounding body text is lost.

## Section 3 — Preprint, Channel, and Indexing Strategy

### 3.1 Preprint versus fast-track
- Default: post to medRxiv (clinical), arXiv (methods, cs.CV / eess.IV), or bioRxiv on the day of journal submission. Rapid preprinting puts the paper into Semantic Scholar within 24–72 hours and into Perplexity's web index immediately.
- Exception: if the target journal offers a fast-track review cycle (acceptance → online within roughly 30–60 days) AND the authors prefer a single canonical version, a preprint may be skipped. In that case, compensate by aggressive post-acceptance SNS seeding and PMC deposit.
- Never skip preprint AND fast-track — this is the discoverability deadzone.

### 3.2 Journal preprint-policy table (verify before submission)
Most medical-AI venues allow preprints (Radiology, RYAI, Lancet DH, npj DM, Nature Medicine, JAMIA, JMIR, Cell Reports Medicine, Cell Patterns). A few have restrictions or require disclosure. Always verify the current policy on Sherpa Romeo or the journal's instructions-for-authors page before posting.

### 3.3 Indexing time-lag (2025 baseline)
- Perplexity Academic / ChatGPT web: real-time web crawl, citable on publication day.
- Semantic Scholar: 24–72 hours from DOI or preprint.
- Google Scholar: 1–7 days.
- PMC (NIH deposit): 2–6 weeks for accepted manuscripts; longer for CC-BY-NC.
- Elicit and Consensus: follow Semantic Scholar / OpenAlex.
- LLM training corpora (next model generation): 6–18 months.

Plan launch activities around these windows.

### 3.4 Open-access choice
Prefer gold OA with CC-BY when budget allows. If not, green OA via preprint plus author-accepted manuscript is acceptable. Closed-access papers without preprint lose roughly 30–50 % of AI-tool citations because Elicit, Consensus, and Perplexity Academic cannot extract from paywalled PDFs.

### 3.5 Post-acceptance channel checklist
- Deposit AAM to PMC or Europe PMC.
- Update ORCID and Google Scholar profile.
- Post to Threads / X / BlueSky with DOI, one-sentence claim, and figure.
- Long-form post on LinkedIn (targets different LLM training corpora).
- Submit to Papers with Code if the paper reports a benchmark.
- Upload model or dataset to Hugging Face with a model/dataset card.

## Section 4 — Review-Paper Strategy

Review articles function as hub nodes in knowledge graphs and accrue "lookup citations" when readers need a canonical reference for a taxonomy. For researchers building a portfolio in medical AI:

- Target at least one review or taxonomy paper per year in a top-tier venue.
- Include 5 or more taxonomy tables (model class, dataset, task type, evaluation metric, failure mode). Each table becomes a lookup target.
- Cite 100 or more primary references for breadth; 150+ for canonical status.
- Co-author with a consortium of 10+ investigators from multiple institutions when possible — this multiplies social-network reach and citation dispersal.
- Pair the review with a companion dataset, benchmark, or code artifact on Zenodo or Hugging Face to anchor AI-tool citations.

Empirically, review papers with these properties outperform original research on short-term FWCI while feeding traffic to the authors' original papers through reverse citation.

## Section 5 — GitHub, CITATION.cff, Zenodo, Hugging Face

### 5.1 README canonical 10-slot order
1. Title + one-line description + badges (license, DOI, arXiv, Hugging Face, paper link).
2. Paper reference block — BibTeX + APA + two-sentence abstract.
3. TL;DR — at most 5 bullets: problem, approach, key result, intended users.
4. Quickstart — `pip install` or `git clone && make demo`. Should work in under 5 minutes.
5. Reproducibility — exact commands that regenerate every figure and table. Pin package versions.
6. Project structure — a tree with one-line folder descriptions.
7. Data access — license, download scripts, DUA notes.
8. FAQ — "How is this different from X?", "Can this be used clinically?", "How do I cite this?". High-value retrieval content.
9. Acknowledgements, funding, and COI.
10. License (prefer Apache-2.0 for research code).

### 5.2 CITATION.cff
Add a `CITATION.cff` file at repository root. GitHub renders it as a "Cite this repository" button, and AI agents treat it as the primary citation hint. Include authors with ORCID, title, version, DOI (post-Zenodo-archive), repository URL, and license.

### 5.3 Zenodo DOI
Enable GitHub–Zenodo integration for each release. Cite the version-specific DOI in the paper's Data/Code Availability section. Zenodo deposits appear in Google Scholar and OpenAlex, creating an independent citable artifact.

### 5.4 Hugging Face model card YAML
Required keys: `license`, `library_name`, `tags`, `datasets`, `base_model` (when fine-tuning), `pipeline_tag`. Required prose sections: Intended use, Training data, Evaluation, Limitations, Ethical considerations, and a clinical-use disclaimer ("This model is not approved for clinical diagnostic use; it is provided for research purposes only").

### 5.5 Hugging Face dataset card
Required prose: license, PHI and re-identification risk, task, language, splits, annotation process, known biases, ethical review status.

### 5.6 Web-crawler-friendly formatting
- Markdown headings are declarative claims.
- Code blocks are fenced and language-tagged.
- Tables are plain Markdown, not HTML (survive Markdown-to-vector chunking).
- Images have descriptive alt text (vision-LLMs read alt text when image retrieval fails).
- Each README section is under about 300 words to survive fixed-size chunking.
- Use question-style subheadings when natural ("Why another benchmark?", "How fast is inference?").

## Section 6 — Authority and E-E-A-T Signals

- Maintain a personal author landing page (GitHub Pages, personal domain, or institutional page) that lists all papers with DOIs and open-access links. AI indexes weight author-entity pages.
- Use one consistent affiliation string across papers. Inconsistency fragments the author entity in knowledge graphs and loses citation velocity.
- Keep ORCID complete and linked to Google Scholar. Re-run author-disambiguation on Semantic Scholar every 6 months.
- Cross-link related papers by the same group in Discussion sections when defensible. Within-group self-citation increases co-retrieval probability in RAG.
- Refresh repository and model cards quarterly — articles updated quarterly outperform single-publish articles in AI-overview retention (Conductor 2026 benchmark).

## Section 7 — LLM-Citation Fabrication Defense

Given Agarwal et al. Nat Commun 2025 (doi:10.1038/s41467-025-58551-6) findings that up to 78–90 % of LLM medical citations can be fabricated, take the following defensive steps:

- Surface DOI and PMID in copy-friendly text at the top of the paper's landing page and README (for example, `DOI: 10.xxxx/yyyy • PMID: 12345678`).
- Add a "How to cite" section with BibTeX, APA, Vancouver, and the plain-text line in one place.
- Monitor incorrect citations. Set a Google Scholar alert for the paper's title variant; periodically query Perplexity and ChatGPT web for the paper and record hallucinated bibliographic errors.
- When responding to a reviewer who cites an LLM-generated reference, verify the DOI and PMID yourself before accepting.

## Section 8 — Red Flags

- Closed code described as "available on reasonable request" — scrapers treat this as "not reproducible" and AI tools demote the paper.
- Paywall-only with no preprint and no fast-track — invisible to most RAG pipelines.
- Keyword-stuffed titles ("A deep-learning artificial-intelligence machine-learning system for …") — penalized as spam.
- Abstracts opening with filler ("In recent years, AI has revolutionized …") — burns the chunk most likely to be extracted.
- Walls of theory before the README quickstart.
- "Clinical grade" or "replaces radiologists" overclaims — demoted by LLM trust heuristics and may trigger reviewer rejection.
- PHI leakage in Hugging Face dataset samples.
- Inconsistent author affiliations across co-authored papers.

## Section 9 — Per-Project Application and Pipeline Integration

When invoked, run in this order:

1. Read the target artifact (title, abstract, manuscript section, README, or card).
2. Apply Sections 1–5 relevant to that artifact; produce a PASS / PARTIAL / FAIL table.
3. Cross-check reporting-guideline anchor (Section 1.6) by invoking `check-reporting` if the user has not already done so.
4. Apply Section 6 author-authority audit once per submission cycle.
5. Surface Section 7 citation-defense recommendations at post-acceptance time.
6. Output: the checklist (visible), then at most 5 concrete edits ranked by expected visibility impact.

### Integration with `write-paper`
- Phase 4 (Title and abstract drafting) → apply Section 1 as an inline filter.
- Phase 6 (Discussion) → apply Section 2.5 (limitations) and Section 6 (cross-linking).
- Phase 7 (QC) → run AIO after reporting-guideline check and numerical-claim audit.

### Output template

```
## Academic AIO Checklist — [Artifact type]

| # | Item | Status | Note |
|---|------|--------|------|
| 1.1 | Title three-slot | PASS/PARTIAL/FAIL | … |
| 1.2 | Structured abstract | PASS/PARTIAL/FAIL | … |
| ... | ... | ... | ... |

## Top 5 suggested edits
1. …
2. …
```

## External References

- GEO: Generative Engine Optimization — Aggarwal et al., KDD 2024, arXiv:2311.09735.
- LLM medical citation fabrication — Agarwal et al., Nat Commun 2025, doi:10.1038/s41467-025-58551-6.
- LLM citation bias — Algaba et al., 2024, arXiv:2405.15739.
- ExpertQA attribution — Malaviya et al., 2024, arXiv:2309.07852.
- TRIPOD+AI — Collins et al., BMJ 2024. EQUATOR Network.
- CLAIM 2024 — Tejani et al., Radiology: AI 2024, doi:10.1148/ryai.240300.
- STARD-AI — Sounderajah et al., Nat Med 2025, doi:10.1038/s41591-025-03953-8.
- TRIPOD-LLM — Gallifant et al., Nat Med 2024, doi:10.1038/s41591-024-03425-5.
- DECIDE-AI — Vasey et al., Nat Med 2022, doi:10.1038/s41591-022-01772-9.
- Title, abstract, keywords guide — Royal Society Proc B 2024, doi:10.1098/rspb.2024.1222.
- GitHub repository citation advantage — Yan et al., Inf Process Manag 2024, doi:10.1016/j.ipm.2023.103569.
- Semantic Scholar Open Data Platform — Kinney et al., arXiv:2301.10140.

## Anti-Hallucination

- **Never fabricate citations, DOIs, arXiv IDs, or reporting-guideline item numbers.** Every cited reporting framework (TRIPOD+AI, CLAIM, STARD-AI, TRIPOD-LLM, DECIDE-AI) must map to a verifiable DOI or EQUATOR Network entry. Mark unverified items as `[UNVERIFIED - NEEDS MANUAL CHECK]`.
- **Never invent journal-specific summary-box rules** (Lancet Digital Health "Research in context", Radiology "Key Points", npj Digital Medicine). Verify current instructions-to-authors from the journal's website before applying.
- **Never fabricate discoverability metrics** (Perplexity/Elicit/Consensus retrieval scores) — only report observed behavior from a recorded probe.
- **Never auto-complete author lists, ORCIDs, or affiliations** in CITATION.cff or Zenodo metadata; surface empty slots to the user.
- If a compliance item, journal policy, or AI-search platform behavior is uncertain, state the uncertainty rather than guessing.
