---
title: "MedSci Skills: Claude Code Skills for the Medical Research Lifecycle"
tags:
  - medical research
  - systematic review
  - meta-analysis
  - reporting guidelines
  - research software
authors:
  - name: Yoojin Nam
    orcid: 0000-0001-8565-1360
    affiliation: 1
affiliations:
  - name: University of Ulsan College of Medicine, Seoul, Republic of Korea
    index: 1
date: 23 May 2026
bibliography: paper.bib
---

# Summary

MedSci Skills is a collection of Claude Code skills for medical researchers who need repeatable support across the manuscript lifecycle. The repository currently contains 40 skills covering topic discovery, literature search, full-text retrieval, study design, sample size planning, protocol drafting, de-identification, data cleaning, statistical analysis, publication figures, manuscript writing, reporting-guideline checks, reference verification, peer review, revision, presentation, and submission hygiene.

The software is organized as auditable workflow modules rather than as single-use prompts. Each skill encodes task boundaries, anti-hallucination checks, deterministic script hooks where appropriate, and routing guidance for adjacent skills. Three public end-to-end demos illustrate diagnostic accuracy, meta-analysis, and epidemiology workflows using public datasets.

# Statement of Need

Medical manuscript work often fails at handoff points: references drift from PubMed records, reporting checklists are applied too late, figures and manuscript counts disagree, and submission packages accumulate stale files. These failures are not primarily model-capability problems. They are workflow and quality-control problems.

MedSci Skills addresses this by packaging medical-research procedures as reusable agent skills with validators, checklists, and explicit downstream boundaries. The target audience is clinician-researchers, research assistants, medical AI teams, and manuscript-methods collaborators who already use local repositories for analysis and writing.

# State of the Field

General LLM agent frameworks and prompt libraries provide broad orchestration patterns, but they rarely encode domain-specific medical manuscript constraints such as EQUATOR reporting guidelines, PubMed-backed reference checks, systematic-review screening stages, and submission-bundle hygiene. Existing medical AI resources emphasize models, datasets, or application libraries; MedSci Skills focuses on the research-production workflow that surrounds those analyses.

The repository complements rather than replaces statistical packages, reference managers, and reporting-guideline templates. It routes deterministic work to scripts or external tools where possible and uses agent behavior for synthesis, review, and procedural coordination.

# Software Design

The system is a modular skill library. Each skill owns a bounded research task and declares when it should or should not be used. Higher-level skills such as `/orchestrate`, `/self-review`, and `/revise` coordinate downstream checks without hiding the underlying artifacts.

Design trade-offs:

- Skills keep procedural context close to the task instead of centralizing all rules in one large orchestrator.
- Validators enforce public-release hygiene, including project-identifier blocklists and metadata checks.
- Deterministic scripts are used for checks that should not depend on language-model judgment.
- Public demos use accessible datasets so users can inspect complete outputs without private data.

# Research Impact Statement

MedSci Skills has a citable Zenodo DOI, a public GitHub history, three reproducible demonstration pipelines, and active repository traffic from developer and research communities. The near-term research significance is strongest for groups that need a structured manuscript workflow with built-in checks for references, reporting guidelines, meta-analysis artifacts, and submission package drift.

Before JOSS submission, this section should be strengthened with concrete adoption evidence, citations, external issues, or documented reuse by researchers outside the maintainer's own workflow.

# AI Usage Disclosure

Generative AI tools including Claude Code and Codex were used to draft, revise, and audit skill documentation, scripts, validators, release notes, and this paper outline. Human authors made the core design decisions, reviewed AI-assisted outputs, ran repository validation checks, and remain responsible for accuracy, originality, licensing, and research-integrity compliance.

# Acknowledgements

This project builds on public reporting-guideline communities, open-source statistical and manuscript-production tooling, and the broader Claude Code skill ecosystem. Funding and institutional acknowledgements should be added before submission if applicable.

# References

References are managed in `paper.bib`.
