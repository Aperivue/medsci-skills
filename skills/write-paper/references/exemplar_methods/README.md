# Exemplar Methods sections — structure models, not prose to copy

`write-paper` teaches Methods *structure* (PICO, the reporting-guideline cross-reference,
the backbone-article strategy) but had no worked example of what a complete, well-ordered
Methods section looks like end to end. This directory fills that gap with **structure
exemplars**: each shows the paragraph order for a study type and, for every paragraph, *what
it must establish* — with placeholder specifics, never copied text.

These are **authored from scratch as teaching models**, not extracted from any published
paper. Use them to check that a draft's Methods has every load-bearing paragraph in a sane
order; do not copy wording.

## How they are used

In `write-paper` Phase 3 (Methods), after loading `section_guides/methods.md`: pick the
exemplar matching the study type and confirm the draft establishes each element the
exemplar lists (design, setting/dates, eligibility, the index test/exposure, the reference
standard/outcome, sample-size justification, the statistical plan, and the reporting-guideline
fit). A missing element is a gap to fill before drafting Results.

## Contents

- `diagnostic_accuracy_stard.md` — an index-test vs reference-standard accuracy study (STARD).
- `ai_validation_tripod_claim.md` — an AI/ML model development + validation study (TRIPOD+AI / CLAIM).
- `observational_cohort_strobe.md` — an exposure→outcome observational cohort (STROBE).

## Curator guidelines (for adding more)

- **Synthetic only.** Write the structure with placeholder specifics (`[scanner/vendor]`,
  `[N]`, `[YYYY–YYYY]`); never paste a real paper's Methods, and use no real citations, no
  PII, English only.
- **One study type per file**, paragraph by paragraph, each line stating *what the paragraph
  must establish* (not finished prose).
- **Anchor to the reporting guideline** the study type maps to, naming the critical items
  (see `peer-review/references/reviewer_calibration/compliance_floor.md`).
- **Name the common omission** for each study type (the paragraph drafts most often skip).
- Keep each file ~50–90 lines. Cross-reference `section_guides/methods.md` and the relevant
  `paper_types/` template rather than duplicating them.
