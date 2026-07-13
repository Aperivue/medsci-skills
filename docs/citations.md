# Citations & Downstream Use

A running ledger of academic citations and named downstream use of MedSci Skills.
This is the manual companion to the automated metrics in
[`../IMPACT.md`](../IMPACT.md) and [`../metrics/traffic_log.csv`](../metrics/traffic_log.csv).

**How to cite:** see [`../CITATION.cff`](../CITATION.cff) or use the Zenodo DOI
[10.5281/zenodo.20155321](https://doi.org/10.5281/zenodo.20155321).

**Reporting use:** if you used MedSci Skills in your work, open a
["Used in research" issue](https://github.com/Aperivue/medsci-skills/issues/new?template=used-in-research.yml).
With your permission, it will be added below.

---

## How discoveries are tracked

- **Zenodo** automatically lists works that cite the archived DOI.
- **Google Scholar alerts** on the DOI, the title "MedSci Skills", and the
  publisher "Aperivue".
- **Reverse links**: GitHub "Used by" / dependents, and forks with public
  activity.
- **Self-reported**: the "Used in research" issue template.

---

## Peer-reviewed / preprint citations

| Date found | Work (authors, year) | Venue | How it uses MedSci Skills | Link |
|---|---|---|---|---|
| 2026-07-13 | Chen, Wang & Qu (2026), *Recursive Self-Improvement in AI: From Bounded Self-Refinement to Autonomous Research Loops* | arXiv:2607.07663 (survey of 1,250 papers, 2024–2026) | Cites the project's methods paper (arXiv:2606.09500) **twice**, as the reference for what fails when an AI audits its own scientific output: in §5.3 (the self-confirming loop) — *"AI scientists whose self-critique 'inherits the blind spots that produce confident fabrication'"* — and in §6.3, *"In regulated domains, **deterministic integrity gates are interposed** because 'self-critique inherits the blind spots that produce confident fabrication'"*. The toolkit's approach is named as the remedy. | [arXiv](https://arxiv.org/abs/2607.07663) |

---

## Theses, protocols, and registered studies

| Date found | Work | Institution / registry | Use | Link |
|---|---|---|---|---|
| _none recorded yet_ | | | | |

---

## Named downstream tools / forks

| Date found | Project | What it builds on | Link |
|---|---|---|---|
| _none recorded yet_ | | | | |

---

## Community contributions & external verification

Documented independent engagement — external bug reports, fix verifications, and code
contributions — each verified against its public GitHub thread.

| Date | Contributor | Contribution | Link |
|---|---|---|---|
| 2026-07-05 | @Rochelle1995 | Filed a precise bug report for `render-pdf-doc` on Windows (Git Bash could not resolve the MiKTeX PATH; no CJK font fallback), then independently verified the fix on Windows 11 + MiKTeX — all dependency checks pass and both an English and a Korean document (Hangul text + a mixed table) render cleanly with no missing-glyph warnings | [#68](https://github.com/Aperivue/medsci-skills/issues/68) · [#286](https://github.com/Aperivue/medsci-skills/pull/286) |

---

## Media, talks, and listings

| Date | Item | Type | Link |
|---|---|---|---|
| 2026-06-03 | Listed in the **Evidence Synthesis Tools** directory (Workflow & Automation category), added via a maintainer-reviewed PR | Curated directory | [directory](https://evidencesynthesis-tools.github.io/) · [PR](https://github.com/evidencesynthesis-tools/awesome-evidence-synthesis/pull/4) |
| 2026-07-07 | Included by an independent maintainer in **awesome-medical-ai-skills** (juneyaooo), Biomedical Research section — a graded entry ("B-, Active") with an original one-line description | Curated list | [entry](https://github.com/JuneYaooo/awesome-medical-ai-skills/blob/7e395fd600a64234dde74cb3be08710e300c8554/README.md#L424) |
| 2026-07-07 | Included in the Chinese edition, **awesome-medical-ai-skills-cn** (juneyaooo) — with a China-availability note (PubMed / Europe PMC search works domestically) | Curated list | [entry](https://github.com/JuneYaooo/awesome-medical-ai-skills-cn/blob/239471ad76d2d2f88bf1674bd4f3d09e8e06bb03/README.md#L227) |
| 2026-07-07 | Included in **awesome-claude-skills** (Chat2AnyLLM) — an auto-validated table (install path + skill count checked, "ok") | Curated list | [entry](https://github.com/Chat2AnyLLM/awesome-claude-skills/blob/c2b12ff1a87c41045e28a7cc01863511f3654fcf/README.md#L127) |
| 2026-07-07 | Included in **awesome-research-agents** (chrisliu298), CLI-native research-agent suites | Curated list | [entry](https://github.com/chrisliu298/awesome-research-agents/blob/fb32bf2ed19ed37c2ebd944c9bfdcd68d83e1411/README.md#L90) |

---

*Entries are added only when verified against a primary source (the DOI, a
published paper, a public repo, or an explicit user report). Unverified mentions
are not listed.*
