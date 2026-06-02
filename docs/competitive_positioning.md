# Competitive Positioning

> **MedSci Skills is a submission-grade clinical manuscript workflow, not a generic biomedical skill catalog.**
> **It competes on clinical submission reliability, not skill count.**

This page explains where MedSci Skills sits relative to broad agent-skill catalogs, and where it deliberately does **not** compete. It is intentionally narrow: one physician-researcher's medical-manuscript pipeline, biased toward radiology, diagnostic accuracy, observational EMR studies, and systematic review / meta-analysis.

## What it is

A connected pipeline from research question to journal submission: topic discovery → literature search → full-text retrieval → study design → sample size → protocol → de-identification → data cleaning → statistics → figures → writing → humanize → reporting compliance → reference verification → journal selection → peer review → revision → submission drift control.

The differentiated strength is **submission reliability**, not breadth:

- **Reference-verification gates and citation-audit workflows.** References pass PubMed / Semantic Scholar / CrossRef verification (including full-author cross-checks) before inclusion, rather than being generated from model memory.
- **Reporting-guideline compliance.** Item-by-item audits against EQUATOR-network checklists (STROBE, CONSORT, STARD, TRIPOD+AI, PRISMA, and risk-of-bias tools).
- **Drift guards.** Numerical, reference, and submission-package consistency checks across the manuscript lifecycle.
- **Cross-skill chaining.** Skills call each other in defined chains (for example, `design-study` → `calc-sample-size` → `write-protocol`), rather than standing alone.
- **Reproducible demos.** End-to-end demo projects on public datasets with manifest-locked outputs.

## How it differs from broad skill catalogs

Broad catalogs optimize for **coverage** — hundreds of skills spanning many scientific domains. MedSci Skills optimizes for **curation and reliability** within a single clinical-manuscript domain: fewer skills, each with bundled reference material, validators, explicit usage boundaries, and tested behavior on real publication workflows.

Skill count is not the axis of comparison. A larger catalog does not make a manuscript more likely to pass desk review; reference integrity, reporting compliance, and consistency control do.

## Comparable repositories

These are larger-scope catalogs that serve adjacent needs. Skill counts drift; the figures below are point-in-time and should be re-checked at the source.

| Repository | Scope | Skill count (as of 2026-06-03; verify at source) |
|---|---|---|
| [K-Dense scientific-agent-skills](https://github.com/K-Dense-AI/scientific-agent-skills) | Multi-disciplinary science (cheminformatics, structural biology, genomics) | ~140 (verify at source) |
| [OpenClaw Medical Skills](https://github.com/FreedomIntelligence/OpenClaw-Medical-Skills) | Broad biomedical aggregation across many source repos | ~870 (verify at source) |
| [AIPOCH medical-research-skills](https://github.com/aipoch/medical-research-skills) | Medical research, with a published skill-audit framing | varies (verify at source) |
| [Orchestra AI Research Skills](https://github.com/Orchestra-Research/AI-Research-SKILLs) | AI/ML research lifecycle | varies (verify at source) |

If you need wet-lab protocols, drug discovery, single-cell genomics, broad bioinformatics, or generic AI/ML engineering, those catalogs are better fits.

## What MedSci Skills does not do

- No skill-count race.
- No omics / single-cell / broad bioinformatics.
- No drug discovery or cheminformatics.
- No generic AI/ML engineering.
- No hundreds of thin skills.

## Host compatibility

MedSci Skills targets Claude Code today. A cross-agent host-compatibility roadmap (Codex, Cursor, and the generic Agent Skills standard) is planned; host support will be stated only where install and discovery have been verified against official documentation.

---

*Part of [MedSci Skills](../README.md). For the per-skill reference, see [`docs/skills/`](skills/).*
