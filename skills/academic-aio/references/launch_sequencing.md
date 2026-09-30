# Launch Sequencing and Indexing Windows

Load from `SKILL.md` Section 3.3 or Section 12 when the lifecycle phase is `post-acceptance` or
`post-publication`. Section numbers match `SKILL.md` and `checklists/AIO_GENERAL.md`.

## Section 3.3 — Indexing time-lag (2025 baseline)

- Perplexity Academic / ChatGPT web: real-time web crawl, citable on publication day.
- Semantic Scholar: 24–72 hours from DOI or preprint.
- Google Scholar: 1–7 days.
- PMC (NIH deposit): 2–6 weeks for accepted manuscripts; longer for CC-BY-NC.
- Elicit and Consensus: follow Semantic Scholar / OpenAlex.
- LLM training corpora (next model generation): 6–18 months.

Plan launch activities around these windows.

## Section 12 — Cross-Platform Launch Sequencing

`SKILL.md` Section 3.5 (post-acceptance channel checklist) is unordered; Section 12 prescribes the
timing. The first 30 days after publication are the primary discoverability window for AI-search
engines and LLM training-data harvesters.

### 12.1 Day 0 — publication day (execute simultaneously)

- GitHub release (tag a stable version; let Zenodo mint a version-specific DOI).
- Hugging Face model card + dataset card (if applicable); link arXiv ID and DOI.
- Twitter/X + Threads + Bluesky: 1-sentence claim + key figure + DOI in copy-friendly format.
- LinkedIn announcement (long-form): hook line + structured claim block + DOI.
- Author landing-page update with PDF link (OA) or AAM.

### 12.2 Day 1 — propagation

- Update ORCID with DOI, abstract, and authorship role.
- Update Google Scholar (verify auto-detection within 24h; manual add if delayed).
- Update preprint server with "Accepted" version note + link to published version.
- Update institutional profile / department news page.

### 12.3 Week 1 — depth posts

- LinkedIn second post: long-form interpretation or methods spotlight.
- Papers with Code submission (if benchmark or model with public weights).
- ResearchGate upload of AAM (per journal policy).
- Reddit/Hacker News post if the work has broad appeal (assess fit honestly).

### 12.4 Weeks 2–4 — refresh signals

- README and HF card minor update (new badges, new FAQ entries).
- Follow-up blog or Substack post expanding on one figure or limitation.
- Respond to reader questions on social platforms — those answers themselves become indexed
  content.

### 12.5 Month 1 — monitoring

- Google Scholar alert for the paper title.
- Semantic Scholar / Scite citation alerts.
- Quarterly probe: query Perplexity, ChatGPT web, Elicit, Consensus, SciSpace with 3–5 expected
  discovery queries; record retrieval position and any hallucinated bibliographic errors.
- If a fabricated citation appears, update the README "How to cite" block (`SKILL.md` Section 7)
  to maximize copy-friendliness of the correct identifier.
