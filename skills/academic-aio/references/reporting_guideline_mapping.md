# Reporting-Guideline ↔ AIO Rule Mapping

This table maps each AIO rule (sections 1-12 of `SKILL.md`) to the corresponding item(s) in the major medical-AI reporting guidelines. Use it to align the `/check-reporting` audit with the `/academic-aio` audit so the same evidence covers both.

## Core mapping

| AIO rule | TRIPOD+AI 2024 | CLAIM 2024 | STARD-AI 2025 | TRIPOD-LLM 2024 | DECIDE-AI 2022 | Notes |
|----------|----------------|-------------|----------------|-----------------|----------------|-------|
| §1.1 Title three-slot | item 1 (title) | item 1 (title and abstract) | item 1 (title) | item 1a (title) | — | All require keyword presence and study-type identification. |
| §1.2 Structured abstract | item 2 (abstract) | item 1 (title and abstract) | item 2 (abstract) | item 1b (abstract) | — | Each guideline mandates structured form. |
| §1.5 Quantified primary outcome with CI | item 16 (model performance) | items 28-30 (performance metrics) | items 23-26 (diagnostic estimates) | item 17 (performance with CI) | item 8 (clinical effect) | CI mandatory for all. |
| §1.6 Reporting-guideline anchor | (compliance declaration) | (compliance declaration) | (compliance declaration) | (compliance declaration) | (compliance declaration) | Cite guideline + checklist in Methods or supplement. |
| §2.4 Reproducibility block | item 24 (data sharing) + item 25 (code sharing) | items 33-34 (data and code availability) | item 28 (data and code) | items 22-23 (artifacts) | item 12 (artifacts) | All require explicit data/code statement. |
| §2.5 Limitations enumeration | item 23 (limitations) | item 41 (limitations) | item 27 (limitations) | item 19 (limitations) | item 11 (limitations) | Enumerate, do not narrate generally. |
| §10.4 Challenge statement | (implicit in Background) | item 4 (rationale) | item 5 (rationale) | item 4 (rationale) | item 4 (rationale) | "Why this is hard" overlaps with rationale items. |

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

Item numbers above are derived from the most recent published version of each guideline. Verify against the EQUATOR Network entry before citing item numbers in a manuscript — guideline updates renumber items.
