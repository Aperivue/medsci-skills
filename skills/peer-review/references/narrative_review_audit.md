# Narrative / Review-Article Audit — Reference Material

Supporting material for the Phase 2D (RV1–RV9) review-article audit in `SKILL.md`. It collects (1) the SANRA appraisal items, (2) a consolidated evaluation checklist, and (3) a candidate-additions list for AI/LLM-in-radiology reviews. Nothing here is a hard requirement; it is an appraisal aid for a *narrative* (non-systematic) review.

## 1. SANRA appraisal items (paraphrased)

SANRA (Scale for the Assessment of Narrative Review Articles) is a brief **critical-appraisal tool, not a reporting guideline** — it scores narrative-review quality and is not meant to be enforced like PRISMA. Six items, each scored 0–2 (paraphrased; see source for exact wording):

1. **Importance** — the review explains why the topic matters to the readership.
2. **Aims** — the review states its aims/questions.
3. **Literature search** — the review describes how sources were identified (databases, terms, time window). For a narrative review this is a transparency *suggestion*, not a systematic-search requirement.
4. **Referencing** — claims are supported by appropriate, accurate, primary-source citations.
5. **Scientific reasoning** — evidence is appraised and synthesized critically rather than selectively reported.
6. **Endpoint data** — relevant data are presented appropriately (tables, figures, summary elements).

Source: Mertens S, Goldbeck-Wood S, Baethge C. *SANRA — a scale for the quality assessment of narrative review articles.* Research Integrity and Peer Review (2019). https://doi.org/10.1186/s41073-019-0064-8

> Mapping to Phase 2D probes: RV2 ↔ items 1–2; RV3 ↔ item 3 (suggestion-level); RV6 ↔ items 4–5. RV1 (novelty) and RV7 (load-bearing figures/tables) are **editorial value-add axes**, not SANRA items — keep them separate so SANRA is not over-applied.

## 2. Consolidated evaluation checklist

Structural / appraisal (SANRA-aligned):
1. Importance and knowledge gap are established.
2. Aims and scope boundaries are explicit (what is in/out).
3. Evidence-gathering is transparent enough to judge balance (suggestion for narrative reviews).
4. Citations are accurate and primary-source-weighted.
5. Evidence is appraised critically; conflicting findings are handled fairly.
6. Key data are summarized in tables/figures/summary elements.

Content / rigor:
7. Coverage is comprehensive and current for the field.
8. Treatment is balanced and objective (no cherry-picking toward a predetermined conclusion).
9. Novelty / value-add over existing reviews is articulated.
10. Findings are attributed to primary sources (no propagation of secondary-source errors).

Accessibility / utility:
11. Clear for the target audience; jargon is explained.
12. Actionable takeaways (clinical implications, future directions).
13. Logical organization and flow.

Domain-specific (AI/LLM reviews):
14. Technical and medical claims are accurate.
15. Relevant frameworks/standards are acknowledged where they support the argument.

## 3. Candidate additions for AI/LLM-in-radiology reviews

These are **candidate additions** a reviewer may raise with "consider adding X because it directly supports Y" phrasing — never "must cite," and proportionate to length. Items are tiered by publication status so a preprint is not equated with a peer-reviewed guideline. Verify each against the manuscript's existing coverage before suggesting it (do not request additions already present).

**Reporting frameworks (peer-reviewed):**
- TRIPOD-LLM — reporting for studies using large language models (Nature Medicine).
- MI-CLAIM-GEN — minimum-information checklist for generative clinical AI (Nature Medicine).
- STARD-AI — diagnostic-accuracy reporting for AI (Nature Medicine).
- CLAIM (2024 update) — checklist for AI in medical imaging (Radiology: Artificial Intelligence).

**Reporting frameworks (preprint — label as such):**
- Treat any not-yet-peer-reviewed arXiv/medRxiv checklist as a preprint and label it as such; do not equate it with a peer-reviewed guideline. Verify status before citing, since such items are frequently published later (the example above, MI-CLAIM-GEN, first appeared on arXiv and was subsequently published in Nature Medicine).

**Concepts and tooling commonly expected in a hallucination-in-radiology review:**
- Hallucination taxonomy: intrinsic vs extrinsic; faithfulness vs factuality.
- Retrieval-augmented generation (RAG): shifts the dominant failure mode from fabrication toward retrieval error rather than eliminating hallucination.
- Uncertainty / confidence calibration for clinical decision support.
- Radiology-specific evaluation: report-level metrics (e.g., RadGraph, CheXbert/CheXpert-F1) and hallucination-detection work for generated reports.
- Regulatory and deployment context: FDA 510(k) / CE pathways; deployment-assessment rubrics (e.g., RADAR).

## Principle

For a narrative review, error-spotting (RV4/RV5/RV6) is necessary but not sufficient. Identifying thematic gaps and proportionately suggesting missing literature/topics (RV8) is an expected part of the reviewer's role — the inverse of the scope-creep restraint applied to original research. New *studies* are still not requested; only missing *literature/topics* are.
