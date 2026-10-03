# Reporting-Guideline ↔ AIO Rule Mapping

This table maps each AIO rule (sections 1-12 of `SKILL.md`) to the corresponding item(s) in the major medical-AI reporting guidelines. Use it to align the `/check-reporting` audit with the `/academic-aio` audit so the same evidence covers both.

## Core mapping

Cells name the reporting-guideline **item by its topic**, not by number. Item numbers live in one
place: the `/check-reporting` checklists in `skills/check-reporting/references/checklists/`
(`TRIPOD_AI.md`, `CLAIM_2024.md`, `STARD_AI.md`, `TRIPOD_LLM.md`, `DECIDE_AI.md`). Look the item up
there by its topic name; do not copy a number from this file. "No matching item" means the
check-reporting checklist has no item on that topic; check the source guideline before assuming
the guideline has none.

| AIO rule | TRIPOD+AI 2024 | CLAIM 2024 | STARD-AI 2025 | TRIPOD-LLM 2024 | DECIDE-AI 2022 | Notes |
|----------|----------------|-------------|----------------|-----------------|----------------|-------|
| §1.1 Title three-slot | Title | Title | Title | Title | — | All require keyword presence and study-type identification. |
| §1.2 Structured abstract | Abstract | Abstract | Abstract | Abstract | — | Each guideline mandates structured form. |
| §1.5 Quantified primary outcome with CI | Model performance | Performance metrics; Uncertainty | Accuracy estimates | Performance | No matching item | CI mandatory for all. |
| §1.6 Reporting-guideline anchor | (compliance declaration) | (compliance declaration) | (compliance declaration) | (compliance declaration) | (compliance declaration) | Cite guideline + checklist in Methods or supplement. |
| §2.4 Reproducibility block | Data sharing; Code sharing | Availability | Data and code availability | Data availability; Code / prompt availability | Data availability | All require explicit data/code statement. |
| §2.5 Limitations enumeration | Limitations | Limitations | Study limitations | Limitations | No matching item | Enumerate, do not narrate generally. |
| §10.4 Challenge statement | Background | Background | Scientific background | Background — context | No matching item | "Why this is hard" overlaps with background/rationale items. |

## Workflow

1. Run `/check-reporting` first — produces a PRESENT/PARTIAL/MISSING audit per guideline item.
2. Run `/academic-aio` — produces the AIO PASS/PARTIAL/FAIL checklist.
3. For each AIO FAIL or PARTIAL row, check this mapping. If the underlying reporting-guideline item is also MISSING/PARTIAL, fix it once and both audits update.
4. Items present in `/check-reporting` audit but not in this mapping (e.g., randomization details for RCTs, domain-specific safety items) do not have an AIO consequence and can be addressed independently.

## When the two audits disagree

- AIO PASS + reporting-guideline MISSING — the manuscript looks discoverable but is not formally compliant. Reviewers may still reject. Always fix the reporting-guideline gap.
- AIO FAIL + reporting-guideline PRESENT — a rule was recorded in compliance form but rendered in a way that LLM extractors cannot parse (e.g., reporting CIs in supplementary instead of inline in the abstract). Move the content into a chunk-friendly location.

## Source

- TRIPOD+AI: Collins et al. BMJ 2024.
- CLAIM 2024: Tejani et al. Radiology: AI 2024, doi:10.1148/ryai.240300.
- STARD-AI 2025: Sounderajah et al. Nat Med 2025, doi:10.1038/s41591-025-03953-8.
- TRIPOD-LLM 2024: Gallifant et al. Nat Med 2024, doi:10.1038/s41591-024-03425-5.
- DECIDE-AI 2022: Vasey et al. Nat Med 2022, doi:10.1038/s41591-022-01772-9.

## Anti-hallucination

This file carries no item numbers on purpose: an earlier version restated them by hand and they
disagreed with the check-reporting checklists. Take item numbers from the check-reporting
checklist, and verify them against the EQUATOR Network entry before citing them in a manuscript —
guideline updates renumber items.
