---
title: "MedSci Skills: Deterministic Integrity Gates and an Agent-Skill Toolkit for the Medical Research Lifecycle"
tags:
  - medical research
  - research integrity
  - reporting guidelines
  - systematic review
  - reproducibility
  - research software
authors:
  - name: Yoojin Nam
    orcid: 0000-0001-8565-1360
    affiliation: 1
affiliations:
  - name: "Department of Radiology and Research Institute of Radiology, University of Ulsan College of Medicine, Asan Medical Center, Seoul, Republic of Korea"
    index: 1
date: 12 July 2026
bibliography: paper.bib
---

# Summary

MedSci Skills is an open-source toolkit that pairs LLM-assisted medical research workflows with a **deterministic verification layer**. Its core is a suite of 79 stdlib-only detectors that *recompute* what a manuscript already asserts rather than asking a language model to judge it: reference records are checked against PubMed and CrossRef, printed percentages against their column denominators, reported *P* values against the cell counts they were computed from, sensitivity and specificity denominators against the reference-standard counts in the characteristics table, and reporting compliance against 46 vendored checklists (STROBE, PRISMA, STARD, CONSORT, TRIPOD+AI, and others). Each detector ships a synthetic challenge card — a positive case and a negative control — that runs in continuous integration, so a clean result is meaningful and a flagged defect is reproducible.

Around that verification core, the toolkit exposes 56 task-bounded skills spanning the manuscript lifecycle: literature search and reference management, study design and sample-size planning, de-identification and data cleaning, statistical analysis and publication figures, drafting, reporting-guideline audits, peer review, revision, and submission hygiene — together with a medical-AI model-engineering lane covering architecture selection, reproducible training scaffolds, validation, evaluation, explainability, and model documentation. The skills are agent-agnostic: a single transactional installer targets Claude Code [@anthropic_claude_code], Codex, Cursor, and GitHub Copilot, and skills interoperate with external tools such as reference managers through the Model Context Protocol [@model_context_protocol]. Four end-to-end demonstrations on public data — diagnostic accuracy, meta-analysis, epidemiology, and a medical-AI model — produce complete, inspectable outputs.

# Statement of Need

LLM assistance in clinical manuscript preparation fails less often at generation than at **verification**. References drift from the records they claim to cite, printed percentages disagree with their denominators, reporting checklists are applied after the analysis is frozen, and submission bundles accumulate stale artifacts. These are quality-control failures rather than model-capability failures, and they are precisely the class of error a language model is least reliable at catching in its own output.

A companion evaluation of this architecture, conducted on an earlier release of the toolkit [@nam2026gates], found that deterministic gates detected 27 of 27 seeded defects with zero false positives, while a single-prompt LLM reviewer detected 11 of 27. MedSci Skills operationalizes that result as a design rule: work that can be settled by recomputation is routed to a deterministic script, and the language model is used for synthesis, drafting, and procedural coordination — never as the final arbiter of a verifiable fact. The evaluation and the current catalog are deliberately reported as separate facts: detectors added since that benchmark are covered by their own continuous-integration challenge cards, not by a re-run of it.

The intended users are clinician-researchers, research assistants, medical-AI teams, and methods collaborators who already keep analysis and writing in a local repository, and who need an auditable, re-executable trail rather than an opaque assistant.

# State of the Field

General LLM agent frameworks and prompt libraries provide broad orchestration patterns, but they rarely encode the domain constraints that decide whether a medical manuscript survives peer review: EQUATOR reporting guidelines [@equator_network] — for example PRISMA [@page2021prisma], STARD [@bossuyt2015stard], STROBE [@vonelm2007strobe], TRIPOD+AI [@collins2015tripod], and CLAIM [@mongan2020claim] — PubMed-backed reference verification, staged systematic-review screening, and submission-bundle hygiene. Medical-AI software ecosystems, in turn, emphasize models, datasets, and training libraries.

MedSci Skills targets the research-production workflow that surrounds those analyses, complementing rather than replacing statistical packages, reference managers, and reporting-guideline templates. It routes deterministic work to scripts or external tools wherever a check can be decided by recomputation, and uses agent behavior only for synthesis, review, and procedural coordination.

# Software Design

The repository is organized as a modular skill library over a deterministic audit layer.

- **Bounded skills.** Each skill owns one research task and declares when it should *and should not* be used, keeping procedural context next to the task instead of centralizing every rule in a single orchestrator. Higher-level skills such as `/orchestrate`, `/self-review`, and `/revise` coordinate downstream checks without hiding the underlying artifacts.
- **Deterministic detectors.** Checks that must not depend on model judgment are implemented as stdlib-only Python scripts with explicit verdicts and non-zero exit codes, so they compose into halt-on-failure gates and can be re-executed independently by a reviewer.
- **Challenge cards and continuous integration.** Every detector is paired with synthetic fixtures — a positive case and a negative control — that run on each push, alongside catalog-consistency, routing-reachability, and public-claim gates that keep the documentation and the code from drifting apart.
- **Reproducible demonstrations.** The demos use openly available datasets and content-hash manifests, so complete outputs — manuscripts, figures, compliance audits, and model-evaluation tables — can be inspected without private data.
- **Release hygiene.** Repository validators enforce public-release constraints, including project-identifier blocklists and metadata checks, before a release is cut.

The toolkit is archived with a citable Zenodo DOI and a public version history, and is distributed through npm and a plugin marketplace in addition to the source repository.

# Example

A detector recomputes a claim rather than judging it. Consider a baseline table in which a categorical comparison reports a *P* value that its own cell counts do not support:

```
| Characteristic | Full cohort (n = 132) | Subset (n = 33) | P       |
| -------------- | --------------------- | --------------- | ------- |
| Adenocarcinoma | 5 (4)                 | 4 (12)          | <0.001  |
```

Running the reported-*P* detector on the manuscript:

```
$ python3 check_reported_p_from_counts.py --manuscript table3.md

[MAJOR] P_NOT_REPRODUCIBLE  row 'Adenocarcinoma' (5/132 vs 4/33)
  reports P<0.001, but recomputes to Fisher 0.0799 / Yates 0.145 /
  uncorrected 0.0594 (closest Pearson chi-square (uncorrected))
```

The detector reconstructs the 2×2 table from the printed counts, recomputes the test with a standard-library Fisher exact test and a Pearson chi-square, and reports the discrepancy with an explicit verdict and a non-zero signal — so it can halt a submission gate or be re-run by a reviewer. A correct table returns `OK` and passes silently. The same pattern underlies the other detectors: references are re-resolved against PubMed and CrossRef, printed percentages are re-divided by their denominators, and reporting compliance is re-scored against the vendored checklists.

# AI Usage Disclosure

Generative AI tools, including Claude Code and Codex, were used to draft, revise, and audit skill documentation, scripts, validators, release notes, and this paper. The author made the core design decisions, reviewed all AI-assisted output, ran the repository validation suite, and is responsible for the accuracy, originality, licensing, and research-integrity compliance of the work.

# Competing Interests

The author is the founder of Aperivue (Incheon, Republic of Korea), which hosts the MedSci Skills repository. The software is released under the MIT license and is freely available. The author reports no other competing interests.

# Acknowledgements

The author thanks Jinhoon Jeong and Namkug Kim for their collaboration on the companion evaluation of this architecture [@nam2026gates], and the public reporting-guideline communities and open-source manuscript-production ecosystems on whose work this toolkit builds. No specific external funding supported the development of this software.

# References
