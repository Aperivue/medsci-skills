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
  - name: "Department of Radiology and Research Institute of Radiology, University of Ulsan College of Medicine, Asan Medical Center, Seoul, Republic of Korea"
    index: 1
date: 5 July 2026
bibliography: paper.bib
---

# Summary

MedSci Skills is a collection of Claude Code [@anthropic_claude_code] skills for medical researchers who need repeatable support across the manuscript lifecycle. The repository currently contains 55 skills covering topic discovery, literature search, full-text retrieval, study design, sample size planning, protocol drafting, de-identification, data cleaning, statistical analysis, publication figures, manuscript writing, reporting-guideline checks, reference verification, peer review, revision, presentation, and submission hygiene, together with a medical-AI model-engineering lane (architecture selection, reproducible training scaffolds, validation, evaluation, and model documentation).

The software is organized as auditable workflow modules rather than as single-use prompts. Each skill encodes task boundaries, anti-hallucination checks, deterministic script hooks where appropriate, and routing guidance for adjacent skills. Four public end-to-end demos illustrate diagnostic accuracy, meta-analysis, epidemiology, and medical-AI model-engineering workflows using public datasets.

# Statement of Need

Medical manuscript work often fails at handoff points: references drift from PubMed records, reporting checklists are applied too late, figures and manuscript counts disagree, and submission packages accumulate stale files. These failures are not primarily model-capability problems. They are workflow and quality-control problems.

MedSci Skills addresses this by packaging medical-research procedures as reusable agent skills with validators, checklists, and explicit downstream boundaries. The target audience is clinician-researchers, research assistants, medical AI teams, and manuscript-methods collaborators who already use local repositories for analysis and writing.

# State of the Field

General LLM agent frameworks and prompt libraries provide broad orchestration patterns, but they rarely encode domain-specific medical manuscript constraints such as EQUATOR reporting guidelines [@equator_network] — for example PRISMA [@page2021prisma], STARD [@bossuyt2015stard], STROBE [@vonelm2007strobe], TRIPOD+AI [@collins2015tripod], and CLAIM [@mongan2020claim] — PubMed-backed reference checks, systematic-review screening stages, and submission-bundle hygiene. Existing medical AI resources emphasize models, datasets, or application libraries; MedSci Skills focuses on the research-production workflow that surrounds those analyses.

The repository complements rather than replaces statistical packages, reference managers, and reporting-guideline templates. It routes deterministic work to scripts or external tools where possible and uses agent behavior for synthesis, review, and procedural coordination.

# Software Design

The system is a modular skill library. Each skill owns a bounded research task and declares when it should or should not be used. Higher-level skills such as `/orchestrate`, `/self-review`, and `/revise` coordinate downstream checks without hiding the underlying artifacts. Skills run within Claude Code and can interoperate with external tools, such as reference managers, through the Model Context Protocol [@model_context_protocol].

Design trade-offs:

- Skills keep procedural context close to the task instead of centralizing all rules in one large orchestrator.
- Validators enforce public-release hygiene, including project-identifier blocklists and metadata checks.
- Deterministic scripts are used for checks that should not depend on language-model judgment.
- Public demos use accessible datasets so users can inspect complete outputs without private data.

# Research Applications

MedSci Skills is archived with a citable Zenodo DOI and a public version history, and ships four reproducible end-to-end demonstrations — diagnostic accuracy, meta-analysis, epidemiology, and medical-AI model engineering — built on openly available datasets, so that complete outputs can be inspected without private data. It is most useful to groups that need a structured manuscript workflow with built-in checks for references, reporting-guideline compliance, meta-analysis artifacts, and submission-package consistency.

# AI Usage Disclosure

Generative AI tools including Claude Code and Codex were used to draft, revise, and audit skill documentation, scripts, validators, release notes, and this paper outline. Human authors made the core design decisions, reviewed AI-assisted outputs, ran repository validation checks, and remain responsible for accuracy, originality, licensing, and research-integrity compliance.

# Competing Interests

The author is the founder and CEO of Aperivue (Incheon, Republic of Korea), which hosts the MedSci Skills repository. The software is released under the MIT license and is freely available, and the author reports no other competing interests.

# Acknowledgements

This project builds on public reporting-guideline communities, open-source statistical and manuscript-production tooling, and the broader Claude Code skill ecosystem. No specific external funding supported the development of this software.

# References

References are managed in `paper.bib`.
