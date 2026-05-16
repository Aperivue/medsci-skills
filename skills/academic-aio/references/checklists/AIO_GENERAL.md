# Academic AIO General Checklist

> Machine-readable checklist mirroring `SKILL.md` sections 1–12. Use as the canonical pass/fail audit table for any medical-AI artifact (manuscript, preprint, README, CITATION.cff, HF card). Each item maps to a SKILL.md section so audit findings can be traced back to the rule.

## How to use

1. Copy this checklist into the working artifact directory as `qc/aio_audit.md`.
2. Determine the artifact's **lifecycle phase** (`pre-draft`, `drafting`, `pre-submission`, `post-acceptance`, `post-publication`) and filter rules whose `applies_to_phase` does not include the current phase — those become NA (do not surface as FAIL).
3. Mark each remaining item PASS / PARTIAL / FAIL with a one-line reason.
4. For FAIL items, generate a concrete edit suggestion ranked by `expected_lift` (`high` first, then `medium`, then `low`).
5. Re-run after edits until ≥ 90 % of applicable items pass.
6. Where an item carries a `defers_to` link, item-level detail belongs to the linked skill — record only the high-level status here to avoid duplicate audits.

## Schema (v2)

```
items[].id              : §-numbered rule id
items[].rule            : one-line description
items[].applies_to      : artifact types where the rule fires
items[].applies_to_phase: lifecycle phases where the rule is actionable
items[].priority        : H | M | L  (severity if missing)
items[].expected_lift   : high | medium | low  (KJR-case-validated visibility gain)
items[].defers_to       : optional skill / file owning item-level detail
```

## Checklist

```yaml
checklist:
  schema_version: 2
  last_updated: "2026-05-11"

  metadata:
    artifact_path: ""
    artifact_type: ""        # manuscript | preprint | readme | citation_cff | hf_card | dataset_card
    artifact_phase: ""       # pre-draft | drafting | pre-submission | post-acceptance | post-publication
    journal_target: ""
    audit_date: ""           # YYYY-MM-DD
    reviewer: ""

  items:
    # Section 1 — Title and Abstract Optimization
    - id: 1.1
      rule: Title three-slot ([Task] + [Modality/anatomy] + [Model class])
      applies_to: [title]
      applies_to_phase: [drafting, pre-submission]
      priority: H
      expected_lift: high
    - id: 1.2
      rule: Structured abstract per journal template; chunk-friendly ≤3-sentence sub-blocks
      applies_to: [abstract]
      applies_to_phase: [drafting, pre-submission]
      priority: H
      expected_lift: high
    - id: 1.3
      rule: First sentence states problem + contribution; last sentence is explicit interpretation
      applies_to: [abstract]
      applies_to_phase: [drafting, pre-submission]
      priority: H
      expected_lift: high
    - id: 1.4
      rule: Taxonomy line names controlled vocabulary (e.g., DTA, foundation-model evaluation)
      applies_to: [abstract]
      applies_to_phase: [pre-submission]
      priority: M
      expected_lift: low
    - id: 1.5
      rule: Quantified primary outcome with 95 % CI in abstract
      applies_to: [abstract]
      applies_to_phase: [drafting, pre-submission]
      priority: H
      expected_lift: high
    - id: 1.6
      rule: Reporting-guideline anchor present (TRIPOD+AI / CLAIM / STARD-AI / TRIPOD-LLM / DECIDE-AI / PRISMA-DTA)
      applies_to: [abstract, methods]
      applies_to_phase: [drafting, pre-submission]
      priority: H
      expected_lift: high
      defers_to: /check-reporting   # item-level audit; AIO records anchor-present status only
    - id: 1.7
      rule: MeSH and RadLex coverage; consistent UK/US spelling; no abstract-keyword redundancy
      applies_to: [keywords, abstract]
      applies_to_phase: [pre-submission]
      priority: M
      expected_lift: medium

    # Section 2 — Manuscript-Level
    - id: 2.1
      rule: Journal-specific summary box present (Research in context / Key Points / PLS / Main Points)
      applies_to: [manuscript]
      applies_to_phase: [drafting, pre-submission]
      priority: H
      expected_lift: high   # KJR case: top extracted fragment by AI overviews
    - id: 2.2
      rule: Section headings are declarative claims, not generic labels
      applies_to: [manuscript]
      applies_to_phase: [drafting, pre-submission]
      priority: M
      expected_lift: medium
    - id: 2.3
      rule: Numeric claim compression sentence in Methods and Results
      applies_to: [methods, results]
      applies_to_phase: [drafting, pre-submission]
      priority: M
      expected_lift: medium
    - id: 2.4
      rule: Reproducibility block (data, code, weights, prompts, seeds, env)
      applies_to: [methods, data_availability]
      applies_to_phase: [pre-submission]
      priority: H
      expected_lift: high
    - id: 2.5
      rule: Limitations enumerated and named
      applies_to: [discussion]
      applies_to_phase: [drafting, pre-submission]
      priority: M
      expected_lift: medium
    - id: 2.6
      rule: Standalone figure captions restate claim, dataset, and metric
      applies_to: [figures]
      applies_to_phase: [pre-submission]
      priority: M
      expected_lift: low

    # Section 3 — Preprint, Channel, Indexing
    - id: 3.1
      rule: Preprint posted on submission day, OR fast-track justified
      applies_to: [submission_strategy]
      applies_to_phase: [pre-submission]
      priority: H
      expected_lift: high
    - id: 3.2
      rule: Journal preprint policy verified (Sherpa Romeo or IFA)
      applies_to: [submission_strategy]
      applies_to_phase: [pre-submission]
      priority: H
      expected_lift: medium
    - id: 3.4
      rule: Open-access route selected (gold OA preferred; green OA acceptable)
      applies_to: [submission_strategy]
      applies_to_phase: [pre-draft, pre-submission]
      priority: H
      expected_lift: high
      defers_to: references/oac_funding_checklist.yaml
    - id: 3.5
      rule: Post-acceptance channel checklist scheduled (PMC, ORCID, Scholar, SNS, HF)
      applies_to: [post_acceptance]
      applies_to_phase: [post-acceptance]
      priority: M
      expected_lift: high

    # Section 5 — GitHub / CITATION.cff / Zenodo / HF
    - id: 5.1
      rule: README follows 10-slot canonical order
      applies_to: [readme]
      applies_to_phase: [post-acceptance, post-publication]
      priority: H
      expected_lift: medium
    - id: 5.2
      rule: CITATION.cff present at repo root with ORCID, DOI, version
      applies_to: [citation_cff]
      applies_to_phase: [post-acceptance, post-publication]
      priority: H
      expected_lift: medium
    - id: 5.3
      rule: Zenodo DOI minted via GitHub integration; cited in paper
      applies_to: [zenodo, manuscript]
      applies_to_phase: [pre-submission, post-acceptance]
      priority: H
      expected_lift: high
    - id: 5.4
      rule: Hugging Face model card YAML keys + required prose sections complete
      applies_to: [hf_card]
      applies_to_phase: [post-acceptance, post-publication]
      priority: H
      expected_lift: medium
    - id: 5.5
      rule: Hugging Face dataset card includes PHI/re-identification disclosure
      applies_to: [dataset_card]
      applies_to_phase: [post-acceptance, post-publication]
      priority: H
      expected_lift: medium
    - id: 5.6
      rule: Web-crawler-friendly markdown (declarative headings, alt text, fenced code, JSON-LD)
      applies_to: [readme, hf_card]
      applies_to_phase: [post-acceptance, post-publication]
      priority: M
      expected_lift: medium

    # Section 6 — Authority / E-E-A-T
    - id: 6.1
      rule: Personal author landing page lists all papers with DOIs
      applies_to: [author_profile]
      applies_to_phase: [pre-draft, drafting, pre-submission, post-acceptance, post-publication]
      priority: M
      expected_lift: medium
    - id: 6.2
      rule: Affiliation string consistent across papers
      applies_to: [author_profile]
      applies_to_phase: [drafting, pre-submission]
      priority: H
      expected_lift: high
    - id: 6.3
      rule: ORCID complete and linked to Google Scholar
      applies_to: [author_profile]
      applies_to_phase: [pre-draft, drafting, pre-submission, post-acceptance, post-publication]
      priority: H
      expected_lift: high

    # Section 7 — LLM-Citation Fabrication Defense
    - id: 7.1
      rule: DOI + PMID surfaced in copy-friendly text on landing page and README
      applies_to: [readme, manuscript]
      applies_to_phase: [post-acceptance, post-publication]
      priority: H
      expected_lift: high
    - id: 7.2
      rule: "How to cite" section with BibTeX, APA, Vancouver, plain-text
      applies_to: [readme]
      applies_to_phase: [post-acceptance, post-publication]
      priority: H
      expected_lift: medium
    - id: 7.3
      rule: Scholar alert configured; Perplexity / ChatGPT probes scheduled
      applies_to: [post_acceptance]
      applies_to_phase: [post-publication]
      priority: M
      expected_lift: low

    # Section 10 — Q&A and Entity-Extraction
    - id: 10.1
      rule: Four-question Q&A block (What was known / What this adds / How this changes practice / Why it matters)
      applies_to: [discussion, supplement]
      applies_to_phase: [drafting, pre-submission]
      priority: H
      expected_lift: high   # KJR case: directly correlated with AI-overview extraction
    - id: 10.2
      rule: Glossary block with MeSH / RadLex / UMLS / arXiv IDs
      applies_to: [methods, supplement]
      applies_to_phase: [pre-submission]
      priority: L
      expected_lift: low   # over-engineering for non-NLP / non-foundation-model papers; apply selectively
    - id: 10.3
      rule: Inline citation anchor text uses semantic predicates, not bare numbers
      applies_to: [manuscript]
      applies_to_phase: [drafting, pre-submission]
      priority: M
      expected_lift: medium
    - id: 10.4
      rule: Explicit "Why this is hard" challenge statement at start of Discussion
      applies_to: [discussion]
      applies_to_phase: [drafting, pre-submission]
      priority: H
      expected_lift: high   # KJR case: top quoted fragment by Perplexity / ChatGPT web

    # Section 11 — First-Mover Timing and Citation-Graph
    - id: 11.1
      rule: Topic-peak signals checked before submission timing decision
      applies_to: [submission_strategy]
      applies_to_phase: [pre-draft]
      priority: H
      expected_lift: high
    - id: 11.2
      rule: Editorial-board leverage considered (corresponding author affiliation)
      applies_to: [submission_strategy]
      applies_to_phase: [pre-draft]
      priority: M
      expected_lift: medium
    - id: 11.3
      rule: Target journal verified as PMC-auto-deposit when applicable
      applies_to: [submission_strategy]
      applies_to_phase: [pre-draft, pre-submission]
      priority: H
      expected_lift: high
      defers_to: references/oac_funding_checklist.yaml
    - id: 11.4
      rule: Discussion anchored in 5–10 high-visibility seminal works
      applies_to: [discussion]
      applies_to_phase: [drafting]
      priority: M
      expected_lift: medium
    - id: 11.5
      rule: Author roster spans ≥ 3 institutions and ≥ 2 disciplines (review papers)
      applies_to: [authorship]
      applies_to_phase: [pre-draft]
      priority: M
      expected_lift: medium   # not actionable once drafting begins; auto-NA in later phases

    # Section 12 — Cross-Platform Launch Sequencing
    - id: 12.1
      rule: Day-0 simultaneous launch (GitHub release, HF card, X/Threads, LinkedIn, landing page)
      applies_to: [post_acceptance]
      applies_to_phase: [post-acceptance]
      priority: H
      expected_lift: high
    - id: 12.2
      rule: Day-1 propagation (ORCID, Scholar, preprint update, institutional page)
      applies_to: [post_acceptance]
      applies_to_phase: [post-acceptance]
      priority: M
      expected_lift: medium
    - id: 12.3
      rule: Week-1 depth posts (LinkedIn long-form, Papers with Code, ResearchGate)
      applies_to: [post_acceptance]
      applies_to_phase: [post-acceptance]
      priority: M
      expected_lift: medium
    - id: 12.4
      rule: Weeks 2–4 refresh signals scheduled
      applies_to: [post_acceptance]
      applies_to_phase: [post-publication]
      priority: L
      expected_lift: low
    - id: 12.5
      rule: Month-1 monitoring (alerts + AI-search probes)
      applies_to: [post_acceptance]
      applies_to_phase: [post-publication]
      priority: M
      expected_lift: medium
```

## Output template (paste into qc/aio_audit.md)

```markdown
# AIO Audit — {artifact_path}

**Phase**: {pre-draft | drafting | pre-submission | post-acceptance | post-publication}
**Top 5 ranked by expected_lift (high → medium → low):**

| Rank | ID | Rule | Status | Reason | Suggested edit |
|------|----|------|--------|--------|----------------|
| 1 | {id} | … | FAIL | … | … |
| ... |

## Full table (applicable items only — out-of-phase rules auto-NA)

| ID | Rule | Lift | Status | Reason | Suggested edit |
|----|------|------|--------|--------|----------------|
| ... |

## Deferred items (audit elsewhere)

- §1.6 → run `/check-reporting`
- §3.4 / §11.3 → see `references/oac_funding_checklist.yaml`

## Summary

- PASS: X / Y applicable items
- High-lift fixes pending: …
```

## Migration from schema v1

If a prior `qc/aio_audit.md` was generated under schema v1 (no `applies_to_phase` / `expected_lift`), regenerate from this v2 file. The id list is unchanged so prior PASS/FAIL state can be re-imported by id.
