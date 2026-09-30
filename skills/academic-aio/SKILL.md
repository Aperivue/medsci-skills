---
name: academic-aio
description: Medical AI paper optimization for AI search engines (Perplexity, ChatGPT web, Elicit, Consensus, SciSpace) and RAG-based literature tools. Applies when drafting or reviewing titles, abstracts, structured summary boxes (Key Points / Research in Context / Plain-Language Summary), manuscripts for high-impact medical AI journals (Lancet Digital Health, Radiology, Radiology-AI, npj Digital Medicine, Nature Medicine), preprints (medRxiv/arXiv), GitHub README + CITATION.cff + Zenodo archives, and Hugging Face model/dataset cards. Integrates TRIPOD+AI, CLAIM 2024, STARD-AI, TRIPOD-LLM, DECIDE-AI reporting requirements with generative engine optimization (GEO) principles. Produces a visible pass/fail checklist.
triggers: AIO, LLMO, GEO, AI search optimization, discoverability, abstract optimization, structured abstract, Key Points, Research in context, plain-language summary, preprint strategy, GitHub README, CITATION.cff, Zenodo DOI, Hugging Face model card, dataset card, Perplexity, Elicit, Consensus, SciSpace, RAG visibility, reporting guideline compliance, TRIPOD-AI, CLAIM, STARD-AI, taxonomy review paper, Radiology Key Points, Lancet Digital Health Research in context, npj Digital Medicine
tools: Read, Write, Edit, Bash, Grep, Glob
model: inherit
---

# Academic AIO Skill — Medical AI Paper Visibility for AI Search Engines

## Communication Rules

- Surface the checklist in the response. Never apply AIO edits silently.
- When a rule conflicts with journal formatting, defer to the journal and mark the item NA with the reason.
- When introducing a rule, cite its source (TRIPOD+AI, CLAIM, STARD-AI, Agarwal 2025, Algaba 2024, Aggarwal 2024 GEO) by DOI or arXiv ID from External References. Never invent a citation, DOI, arXiv ID, or reporting-guideline item number; mark anything you cannot verify `[VERIFY]`.

## Section 1 — Title and Abstract Optimization

### 1.1 Title three-slot rule
Structure: `[Task] + [Modality or anatomy] + [Model family or method class]`. Include one concrete differentiator (dataset scale, new benchmark, "first …") when defensible. Avoid keyword stuffing (penalized as spam by AI overviews).
- PASS: "Transformer-based segmentation of skull fractures on non-contrast head CT."
- FAIL: "A novel advanced deep-learning AI machine-learning framework for medical image analysis."

### 1.2 Structured abstract
Use the journal-required structure (Background / Methods / Findings / Interpretation for the Lancet family; Background / Purpose / Materials and Methods / Results / Conclusion for the RSNA family; etc.). If the journal allows unstructured, still structure it internally. Each section stands alone as a semantic chunk of ≤ 3 sentences so that RAG chunk-boundary splits do not break the claim.

### 1.3 Opening and closing sentences
- First sentence: the problem AND the contribution in one line. Never open with filler ("In recent years, AI has revolutionized …") — it burns the chunk LLM summarizers extract most.
- Last sentence: explicit interpretation ("we show that …", "this implies …"). No hedging-only closes.

### 1.4 Taxonomy line
Include one sentence that names the field's controlled vocabulary ("diagnostic-accuracy study", "foundation-model evaluation", "LLM-as-judge", "agentic radiology workflow"). Entity linkers in AI indexes use this line.

### 1.5 Quantified claim
Every abstract must contain at least one numeric primary outcome with a confidence interval (for example, "AUC 0.94 [95 % CI 0.91–0.96]").

### 1.6 Reporting-guideline anchor
Name the guideline in the abstract or the opening sentence of Methods: "Reported following TRIPOD+AI (Collins 2024) and CLAIM 2024 (Tejani 2024)". Add STARD-AI 2025, DECIDE-AI, or TRIPOD-LLM when applicable. AIO-rule ↔ guideline-item mapping: `references/reporting_guideline_mapping.md`.

### 1.7 Keyword, MeSH, and RadLex coverage
Title, abstract, and keywords together should cover ≥ 3× the surface area of the concept, without repeating title terms in the keywords (92 % of papers do; Royal Society 2024, doi:10.1098/rspb.2024.1222). Include:
- Core MeSH terms (verify against the NLM MeSH browser) and RadLex terms where applicable.
- Modality synonyms ("chest radiograph (CXR)", "non-contrast CT (NCCT)").
- Both US and UK spellings when relevant.

## Section 2 — Manuscript-Level AIO

### 2.1 Summary box
Include the journal-specific summary box verbatim when supported; it is the fragment AI search engines most often copy or paraphrase:
- Lancet family: "Research in context" (Evidence before this study / Added value / Implications).
- RSNA Radiology and RYAI: "Key Points" — 3 bullets, one claim each.
- npj Digital Medicine: "Plain-language summary" (150–200 words, 8th-grade reading level).
- Nature Medicine: editor's summary (supplied by editorial, but draft one proactively).

Journal-specific templates: `references/journal_summarybox_templates.yaml`. Never invent a summary-box rule: verify each template against the journal's current instructions for authors before applying it.

**Deterministic format check.** Validate the drafted box against its journal spec with `python3 ${CLAUDE_SKILL_DIR}/scripts/check_summary_box.py --manuscript <file> --journal <stem> --strict` (reads `references/summary_box_specs.json`: Key Points bullet count + one-claim-per-bullet, Research-in-context's three sub-blocks, plain-language word band). It catches the wrong-format / wrong-bullet-count box that a production technical check rejects.

### 2.2 Declarative section headings
Headings state a claim, not a generic label: "Model underperforms on rare-finding subset" beats "Subgroup analysis".

### 2.3 Numeric claim compression
In the Methods and in at least one Results paragraph, compress primary-outcome statistics into one sentence:
"On the internal test set (n = 842), the model achieved AUC 0.94 (95 % CI 0.91–0.96), sensitivity 88.2 % (85.1–91.0), specificity 91.4 % (88.7–93.6), at an operating point of 0.37."

### 2.4 Reproducibility block
Include a labeled block (end of Methods or a standalone Data/Code Availability section) listing data availability and license, code availability with DOI, model weights and checkpoints, prompts and configuration files, random seeds, and compute environment. Flag code described only as "available on reasonable request": scrapers read it as not reproducible and AI tools demote the paper.

### 2.4a Citing an AI-assisted tool by use-class
Frame an AI-assisted tool by what it did, not by hiding it: verification/QA and analysis uses go in a **Software / Code-availability statement** (citable); generative drafting or humanizing goes in the journal's **AI-use disclosure field**, not a citation. A self-citation by the tool's author also requires a COI disclosure and should cite only the functions the work used. Use-class table and rules: `${CLAUDE_SKILL_DIR}/references/ai_tool_citation_framing.md`.

### 2.5 Limitations enumeration
List limitations explicitly and name each one (generalizability, spectrum bias, dataset shift, single-center training, label noise). Flag "clinical grade" or "replaces radiologists" overclaims: LLM trust heuristics demote them and they invite reviewer rejection.

### 2.6 Standalone figure captions
Each caption re-states the claim, the dataset, and the metric, because captions survive in vector and image-retrieval indexes when the body text is lost.

## Section 3 — Preprint, Channel, and Indexing Strategy

### 3.1 Preprint versus fast-track
- Default: post to medRxiv (clinical), arXiv (methods, cs.CV / eess.IV), or bioRxiv on the day of journal submission. This puts the paper into Semantic Scholar within 24–72 hours and into Perplexity's web index immediately.
- Exception: if the target journal offers a fast-track review cycle (acceptance → online within roughly 30–60 days) AND the authors prefer a single canonical version, the preprint may be skipped; compensate with aggressive post-acceptance SNS seeding and PMC deposit.
- Never skip both preprint and fast-track — a paywall-only paper is invisible to most RAG pipelines.

### 3.2 Journal preprint policy
Most medical-AI venues allow preprints; a few restrict them or require disclosure. Verify the current policy on Sherpa Romeo or the journal's instructions for authors before posting.

### 3.3 Indexing time-lag
Read `${CLAUDE_SKILL_DIR}/references/launch_sequencing.md` when planning launch timing; it lists how long each index takes to pick a paper up.

### 3.4 Open-access choice
Prefer gold OA with CC-BY when budget allows; otherwise green OA via preprint plus author-accepted manuscript. Closed-access papers without a preprint lose roughly 30–50 % of AI-tool citations because Elicit, Consensus, and Perplexity Academic cannot extract from paywalled PDFs.

Funder OA-policy decision tree (Plan S, NIH, UKRI, Gates, Wellcome, NRF, MoHW): `references/oac_funding_checklist.yaml`.

### 3.5 Post-acceptance channel checklist
- Deposit AAM to PMC or Europe PMC.
- Update ORCID and Google Scholar profile.
- Post to Threads / X / BlueSky with DOI, one-sentence claim, and figure; long-form post on LinkedIn.
- Submit to Papers with Code if the paper reports a benchmark.
- Upload model or dataset to Hugging Face with a model/dataset card.

Section 12 gives the day-by-day order.

## Section 4 — Review-Paper Strategy

Read `${CLAUDE_SKILL_DIR}/references/pre_draft_strategy.md` when the artifact is a review or taxonomy paper, or the phase is `pre-draft`.

## Section 5 — GitHub, CITATION.cff, Zenodo, Hugging Face

Read `${CLAUDE_SKILL_DIR}/references/repository_and_cards.md` when the artifact is a README, `CITATION.cff`, Zenodo record, or Hugging Face model/dataset card (rules 5.1–5.6).

- Embed JSON-LD `ScholarlyArticle` / `SoftwareSourceCode` / `Dataset` / `Person` markup in repository pages and author landing pages — templates in `references/schema_markup_templates/`, validated with `python scripts/validate_schema.py path/to/file.jsonld`.
- Never auto-complete author lists, ORCIDs, or affiliations in `CITATION.cff` or Zenodo metadata; surface the empty slots to the user.

## Section 6 — Authority and E-E-A-T Signals

- Maintain an author landing page (GitHub Pages, personal domain, or institutional page) listing all papers with DOIs and open-access links.
- Use one consistent affiliation string across papers; inconsistency fragments the author entity in knowledge graphs.
- Keep ORCID complete and linked to Google Scholar. Re-run author disambiguation on Semantic Scholar every 6 months.
- Cross-link related papers by the same group in Discussion sections when defensible; within-group citation raises co-retrieval in RAG.
- Refresh repository and model cards quarterly; quarterly-updated articles outperform single-publish ones in AI-overview retention (Conductor 2026 benchmark).

## Section 7 — LLM-Citation Fabrication Defense

Up to 78–90 % of LLM medical citations can be fabricated (Agarwal et al., Nat Commun 2025, doi:10.1038/s41467-025-58551-6). Defend the paper's identifiers:

- Surface DOI and PMID in copy-friendly text at the top of the paper's landing page and README (for example, `DOI: 10.xxxx/yyyy • PMID: 12345678`).
- Add a "How to cite" section with BibTeX, APA, Vancouver, and the plain-text line in one place.
- Monitor incorrect citations: a Google Scholar alert for the paper's title variant, plus periodic Perplexity and ChatGPT web queries that record hallucinated bibliographic errors. Report discoverability (Perplexity / Elicit / Consensus retrieval) only from a recorded probe; never estimate it.
- When a reviewer cites an LLM-generated reference, verify the DOI and PMID yourself before accepting it.

## Section 9 — Per-Project Application and Pipeline Integration

When invoked, run in this order:

1. Read the target artifact (title, abstract, manuscript section, README, or card) and **identify its lifecycle phase**: `pre-draft` / `drafting` / `pre-submission` / `post-acceptance` / `post-publication`.
2. Apply Sections 1–5 and 10 relevant to that artifact, **filtering each rule by its `applies_to_phase` field in `references/checklists/AIO_GENERAL.md`**. Out-of-phase rules become NA rather than FAIL (e.g., do not surface §11.5 multi-disciplinary roster or §12 launch sequencing as FAIL on a `pre-submission` audit). Produce a PASS / PARTIAL / FAIL table, one-line reason and concrete fix per item, **sorted by `expected_lift` (high → medium → low)**, in the output template of `references/checklists/AIO_GENERAL.md`. Render via `templates/aio_audit_checklist.md.j2` when programmatic.
3. **Honour `defers_to` annotations to avoid duplicate audits.** Items annotated with a `defers_to` field record only present/absent status here; item-level detail belongs to the linked skill or reference (§1.6 → `/check-reporting`; §3.4 / §11.3 → `references/oac_funding_checklist.yaml`). When the manuscript has not had a reporting-guideline audit, invoke `/check-reporting` first; the AIO ↔ guideline-item mapping is in `references/reporting_guideline_mapping.md`.
4. Apply the Section 6 author-authority audit once per submission cycle, and Sections 11–12 as the `applies_to_phase` filter allows.
5. Surface Section 7 citation-defense recommendations at `post-acceptance` time. For multi-repo or Hugging-Face-card team audits, run `scripts/batch_metadata_audit.py`.
6. Output:
   - The phase-filtered checklist (visible).
   - A short deferred-item list with one-line status per `defers_to` rule.
   - At most 5 concrete edits **ranked by `expected_lift`** (high first, then medium, then low). A `low`-lift edit enters the Top 5 only when no `high` / `medium` item remains open.

### Integration with other skills
- Run after `/self-review` and `/humanize`, so QC-confirmed claims and the final human-readable text anchor the checklist.
- Within `/write-paper`: apply Section 1 while drafting the title and abstract, Sections 2.5 and 6 (cross-linking) while drafting the Discussion, and the full checklist at QC, after the reporting-guideline check and numerical-claim audit.

## Section 10 — Q&A and Entity-Extraction Optimization

### 10.1 Four-question Q&A block (Discussion or Appendix)
Add a labeled Q&A block, either as the closing subsection of Discussion or as a Supplementary Box:
- **What was known before this study?** — two-sentence restatement of the prior state.
- **What does this study add?** — two-sentence statement of the contribution.
- **How might this change clinical practice or research?** — one-sentence interpretation; avoid overclaim.
- **Why does this matter?** — one-sentence "so what" framing for non-specialists.

Lancet Digital Health "Research in context" already encodes the first two questions; the block extends them.

### 10.2 Glossary block with entity IDs
Define each domain-specific acronym inline on first use AND list them in a Glossary subsection at the end of Methods or in the Supplement, with the canonical entity ID where possible: MeSH term ID (clinical concepts), RadLex ID (radiology terms), UMLS CUI (cross-vocabulary mapping), Hugging Face model ID (named models), arXiv ID (cited methods).

### 10.3 Inline citation anchor text
Avoid bare reference numbers; bind each citation to its specific claim:
- WEAK: "Prior work [12] showed efficacy."
- STRONG: "Smith et al. (DOI: 10.xxxx/yyyy) reported a 12 % accuracy gain on the MIMIC-CXR test set [12]."

When citing one's own prior work, name the cohort or dataset explicitly to enable cross-paper retrieval.

### 10.4 Explicit challenge statement
Beyond the 2.5 limitations list, include a single-paragraph "Why this is hard" statement near the start of Discussion:

"Building accurate [task] for [modality/anatomy] is constrained by [data scarcity / label noise / dataset shift / regulatory uncertainty / interpretability]. Each of these has been documented [refs], and our results address [subset]."

LLM web-search systems quote challenge statements as authoritative summaries of field state (worked case: `references/case_studies/kjr_mllm_2025.md`).

## Section 11 — First-Mover Timing and Citation-Graph Density

Rules 11.1 (topic-peak detection), 11.2 (editorial-board leverage), and 11.5 (multi-disciplinary author roster) are in `${CLAUDE_SKILL_DIR}/references/pre_draft_strategy.md`; read it at `pre-draft`.

### 11.3 PMC-auto-deposit journal preference
OA journals that auto-deposit to PubMed Central reach LLM crawlers within 4–6 weeks of publication; non-PMC OA journals can take 3–6 months. When all else is equal, prefer a PMC-auto-deposit journal. Radiology/medical-AI examples (verify per submission; policies change):
- Korean Journal of Radiology (KJR) — auto-deposit confirmed.
- Lancet Digital Health — author-funded green OA, PMC-eligible after embargo.
- Radiology and Radiology: AI — selected articles auto-deposit.
- npj Digital Medicine — auto-deposit (Nature OA).
- JAMIA — author-funded OA route.
- JMIR — auto-deposit (PMC-indexed).

### 11.4 Citation-graph anchor strategy
Anchor the Discussion in 5–10 high-visibility prior works that LLM training corpora already index well, so the paper is retrieved when users query those works.
- Identify seminal references via Semantic Scholar's "Highly Influential Citations" filter for the topic.
- Cite them with semantic predicates (Section 10.3), not as bare lists.
- Mix recent preprints (currency) with 2018–2022 seminal papers (graph anchoring); a 2024–2025-only citation profile has low LLM retrieval weight because of corpus cutoffs.

## Section 12 — Cross-Platform Launch Sequencing

At `post-acceptance` / `post-publication`, read `${CLAUDE_SKILL_DIR}/references/launch_sequencing.md` for the Day 0 → Month 1 sequence (rules 12.1–12.5).

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
