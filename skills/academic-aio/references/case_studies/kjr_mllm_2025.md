# Case Study — KJR Multimodal LLM Review (2025)

> Post-mortem of an unexpectedly high-engagement medical-AI review. Used to validate Sections 10–12 of the academic-aio skill. Identifying co-author and institutional details are abstracted; the paper itself is publicly indexed.

## Paper

- **Title**: Multimodal Large Language Models in Medical Imaging: Current State and Future Directions
- **Venue**: Korean Journal of Radiology, Vol 26, Issue 10, pp. 900–923 (October 2025)
- **DOI**: 10.3348/kjr.2025.0599
- **PMC ID**: PMC12479233
- **OA status**: Creative Commons (gold OA), KJR + PMC dual indexing
- **Author roster**: 15-author multi-disciplinary team — resident + medical-AI researcher (first author), software engineer, medical student, faculty across 5 Asian academic medical institutions and one university computational biology department, anchored by a mid-career corresponding author who serves on the target journal's editorial board (Technology section).
- **Timeline**: Received 2025-05-14 → revised 2025-07-03 → accepted 2025-07-08 → published October 2025 (~5 months end-to-end, fast for a review article).

## Engagement metrics (May 2026, ~7 months post-publication)

- Page views: 3,016
- PDF downloads: 628
- Citations: 64
- First-author Google Scholar impact (since 2021): h-index 4, i10-index 2, total 101 citations — of which ~63 % are attributable to this single review.

These figures place the paper in the top decile of KJR articles by 12-month citation accrual.

## Driver analysis (which AIO levers actually operated)

The author's initial hypothesis space included (a) journal visibility, (b) hot topic, (c) corresponding author's reach, (d) multi-disciplinary team, (e) fast turnaround, (f) OA + PMC indexing, and (g) early SNS exposure. Post-hoc evidence:

| Hypothesis | Verdict | Notes |
|------------|---------|-------|
| AI-search retrievability (Perplexity / ChatGPT web / Elicit / Consensus / SciSpace) | **Strong (primary driver)** | Paper appears at #3–4 for "MLLM medical imaging review 2025" on Google web; Perplexity preferentially cites it for queries on multimodal radiology AI. |
| OA + PMC dual indexing | Strong | Full text crawled by AI agents within 4–6 weeks; corresponds to Section 11.3. |
| Topic peak timing | Strong | Submitted shortly after GPT-4o and Claude 3.5 multimodal launches; published at the peak of the 2025 MLLM hype cycle. Corresponds to Section 11.1. |
| First-mover review | Strong | Competing reviews (in JBI, Archives of Comp Methods, ScienceDirect) appeared later or in less-discoverable venues. |
| Editorial-board signal | Moderate | Corresponding author's editorial role plausibly accelerated review and raised editor's-pick probability. Corresponds to Section 11.2. |
| Multi-disciplinary 15-author team | Moderate | Author-entity diversification across institutions multiplied Google Scholar entry points. Corresponds to Section 11.5. |
| Early SNS exposure | Weak | No clear evidence that SNS drove the bulk of traffic; KJR/PMC pathway dominated. |

## Structural features that AI-search systems extracted

The article body exhibits several patterns that map to Sections 10–11 of this skill:

1. **Explicit taxonomy** (2D vs 3D MLLM; Applications vs Barriers) — RAG systems chunk-cite each branch independently.
2. **Verbatim challenge statements** — phrases such as "lack of large-scale high-quality multimodal datasets" and "hallucinated findings" are quoted by Perplexity and ChatGPT web as authoritative summaries of field state. Corresponds to Section 10.4.
3. **Declarative subsection headings** — claim-style rather than generic labels (Section 2.2).
4. **10 figures + 5 tables** — rich pull-quotable structures for retrieval.
5. **DOI + PMID surfaced cleanly** in KJR landing page header — minimizes citation fabrication (Section 7).

## Lessons codified into the skill

| Skill update | Source observation |
|--------------|---------------------|
| §10.4 Explicit challenge statement | Field-state quotes were the most common Perplexity extraction. |
| §11.1 Topic peak detection | Submission timing aligned with model-release shockwave. |
| §11.2 Editorial-board leverage | Review-process speed plausibly editor-mediated. |
| §11.3 PMC-auto-deposit preference | KJR-PMC pathway delivered LLM crawl in 4–6 weeks. |
| §11.4 Citation-graph anchor | Discussion seeded with a mix of seminal multimodal-LLM works. |
| §11.5 Multi-disciplinary roster | 15-author 5-institution composition multiplied entry points. |

## Replication checklist (apply to next medical-AI review)

- [ ] Identify a topic 6–12 months ahead of expected peak using Section 11.1 signals.
- [ ] Recruit a corresponding author with editorial-board affiliation at a PMC-auto-deposit OA journal (Section 11.2 + 11.3).
- [ ] Assemble a 10–15 author team spanning ≥ 3 institutions and ≥ 2 disciplines (Section 11.5).
- [ ] Draft taxonomy headings as declarative claims (Section 2.2) with explicit 2D-vs-3D-style subdivisions.
- [ ] Insert a "Why this is hard" challenge paragraph at the start of Discussion (Section 10.4).
- [ ] Add a four-question Q&A block in Discussion or Appendix (Section 10.1).
- [ ] Anchor Discussion in 5–10 highly-cited prior works (Section 11.4).
- [ ] Execute Day-0/Day-1/Week-1 launch sequencing (Section 12).
- [ ] Probe Perplexity / ChatGPT web / Elicit / Consensus / SciSpace at +30, +60, +90 days post-publication; correct any fabricated citations encountered (Section 7).

## Caveats

- Single-paper case study — not a controlled experiment. Hot-topic timing alone could explain a large fraction of the engagement; the AIO mechanisms identified here are necessary but not provably sufficient.
- Citation accrual at 7 months is a leading indicator, not a final one. A second readout at 24 months will distinguish landscape-review citation behavior from short-term hype.
- Editorial-board involvement is institution-specific. Replicating Section 11.2 requires evaluating the target journal's recusal policy and disclosing it appropriately.

## References

- KJR landing page: `https://www.kjronline.org/DOIx.php?id=10.3348/kjr.2025.0599`
- PMC full text: `https://pmc.ncbi.nlm.nih.gov/articles/PMC12479233/`
- GEO framework: Aggarwal et al., KDD 2024, arXiv:2311.09735.
- LLM medical citation fabrication: Agarwal et al., Nat Commun 2025, doi:10.1038/s41467-025-58551-6.
