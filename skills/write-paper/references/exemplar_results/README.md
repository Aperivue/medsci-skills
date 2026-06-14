# Exemplar Results sections — structure models, not prose to copy

`write-paper` teaches Results *rules* (`section_guides/results.md`: mirror-symmetry with
Methods, the flow diagram, no interpretation) but had no worked example of what a complete,
well-ordered Results section looks like end to end. This directory fills that gap with
**structure exemplars** that follow the `exemplar_methods/` siblings in Methods order: each
shows the Results paragraph order for a study type and, for every paragraph, *what it must
establish* — with placeholder specifics, never copied text.

These are **authored from scratch as teaching models**, not extracted from any published
paper. Use them to check that a draft's Results presents every load-bearing element in the
same order as its Methods; do not copy wording.

## How they are used

In `write-paper` Phase 4 (Results), after loading `section_guides/results.md`: pick the
exemplar matching the study type and confirm the draft presents each element in Methods order
(flow → baseline/prevalence → primary estimate with CIs → calibration/agreement →
subgroups/comparator → sensitivity/missing-data). A missing element is a gap to fix; an
element that interprets rather than reports belongs in the Discussion.

## Contents

- `diagnostic_accuracy_stard.md` — flow, prevalence, sensitivity/specificity (+ PPV/NPV) with
  CIs at a fixed operating point, agreement, comparator (STARD).
- `ai_validation_tripod_claim.md` — partition/flow, per-set discrimination with CIs,
  calibration, operating point, clinical utility (TRIPOD+AI / CLAIM).
- `observational_cohort_strobe.md` — assembly, Table 1 by exposure, crude-then-adjusted
  estimate with CIs, subgroups, sensitivity analyses (STROBE).

## Curator guidelines (for adding more)

- **Synthetic only.** Write the structure with placeholder specifics (`[N]`, `[YYYY–YYYY]`,
  `[metric]`); never paste a real paper's Results, use no real citations, no PII, English only.
- **Follow the matching `exemplar_methods/` file in Methods order** (same study type), so
  Results and Methods read in the same sequence.
- **One study type per file**, each line stating *what the paragraph must establish* (not
  finished prose), and report-only — flag interpretation as belonging to the Discussion.
- **Name the common omission** for each study type, and anchor to the reporting-guideline
  critical items in `peer-review/references/reviewer_calibration/compliance_floor.md`.
- Keep each file ~50–90 lines. Cross-reference `section_guides/results.md` rather than
  duplicating it.
