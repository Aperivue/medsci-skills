# Frequently asked questions

A plain-language reference for researchers evaluating MedSci Skills, and a
search/answer-engine-friendly summary of what it is and is not.

## What is MedSci Skills?

MedSci Skills is an open-source Claude Code skill collection for **clinical
manuscript preparation**. It helps physician-researchers and biomedical
investigators move from literature search, study design, statistics, and figures to
reporting-guideline compliance, citation/reference auditing, numerical-consistency
checks, and response-to-reviewer workflows. It combines agentic writing workflows
with **deterministic integrity gates** for submission-grade biomedical research.

## Who should use it?

Physician-researchers, biomedical investigators, and research teams writing
clinical, diagnostic-accuracy, observational, or systematic-review/meta-analysis
manuscripts — especially in radiology and medical AI, where the bundled reporting
guidelines and journal profiles are deepest.

## Is MedSci Skills a "medical writing AI"? Does it replace human authors?

No. It is workflow tooling with deterministic checks, not an autonomous author. It
**does not replace** authors, statisticians, reviewers, IRBs, or journal
requirements, and every output **requires human-expert verification**. Its goal is
to make manuscripts more auditable and reproducible and to reduce common
preparation errors — not to write the paper for you.

## Is it clinically validated? Is it a clinical/diagnostic tool?

No. MedSci Skills is **not** a clinical-decision-support or diagnostic tool and
makes no clinical-validation claim about itself. It supports manuscript and research
**workflow** only (see [`SECURITY.md`](../SECURITY.md) for the scope boundary).

## Does it check STROBE, PRISMA, STARD (and other guidelines)?

Yes. It bundles a set of EQUATOR-network reporting checklists and risk-of-bias /
appraisal tools (STROBE, CONSORT and CONSORT-AI, STARD and STARD-AI, PRISMA and
PRISMA-DTA, TRIPOD and TRIPOD+AI, QUADAS-2, RoB 2, ROBINS-I, AMSTAR 2, and more) and
audits a manuscript item by item. The authoritative current list and count are in
[`metadata/catalog_counts.json`](../metadata/catalog_counts.json) and the
[README](../README.md).

## Can it verify references and citations?

Yes. References are checked against PubMed / CrossRef / OpenAlex (including
first-author and full-author cross-checks) before they are trusted; the toolkit
never writes references from model memory. See `/verify-refs`.

## Can it detect numerical inconsistencies?

Yes. Deterministic detectors check numerical and cohort arithmetic, pooled-estimate
consistency, and cross-artifact drift across the manuscript, tables, figures, and
submission package. These are part of the **MedSci-Audit** detector layer
(see [`MEDSCI_AUDIT.md`](../MEDSCI_AUDIT.md)).

## How is it different from a general AI writing assistant?

A general assistant drafts prose. MedSci Skills adds the clinical-submission layer a
generic tool lacks: reporting-guideline audits, reference verification, numerical /
cross-artifact consistency gates, journal-specific profiles, and ICMJE/IRB form
support — deterministic checks that run before a reviewer sees the manuscript.

## How is it different from a general "AI scientist" agent?

It is intentionally narrow. It does not span chemistry, drug discovery, or bench
biology, and it is not an autonomous research agent. It is one physician-researcher's
clinical-manuscript pipeline with integrity gates (see
[`ROADMAP.md`](../ROADMAP.md) for the scope boundary).

## Why is my slash command `/medsci-analysis:analyze-stats` instead of `/analyze-stats`?

Because the install path decides the name. Skills installed **as a plugin** are prefixed
with their plugin's name; skills installed into the **skills folder** (`npx medsci-skills
install`, `gh skill install`, the classroom installer, or `installers/install.py`) are
invoked bare. Both run the same skill. See
[common setup issues](setup/common-issues.md#11-a-skills-slash-command-is-longer-than-the-docs-show-or-a-plain-prompt-starts-no-skill)
for how to switch, and what to do when a plain-language request starts no skill at all.

## Is it free and open-source?

Yes — MIT licensed (see [`LICENSE`](../LICENSE); note any per-file carve-outs noted
in the file headers).

## How widely adopted is it?

It has **early community adoption signals** (stars, forks, and a few named uses) for
a niche biomedical-workflow repository — not widespread adoption. The honest,
continuously updated record is in [`IMPACT.md`](../IMPACT.md).

## How do I cite MedSci Skills?

Use [`CITATION.cff`](../CITATION.cff) or the archived Zenodo DOI listed in the
[README](../README.md).
