# Exemplar Discussion sections — structure models, not prose to copy

`write-paper` teaches Discussion *rules* (`section_guides/discussion.md`: the 4-paragraph
structure, no new results, no table/figure citations, claim-to-evidence matching) but had no
worked example of what a complete Discussion looks like end to end. This directory completes
the exemplar trio (`exemplar_methods/` → `exemplar_results/` → `exemplar_discussion/`) with
**structure models**: each shows the Discussion paragraph order for a study type and, for
every paragraph, *what it must establish* — with placeholder specifics, never copied text.

These are **authored from scratch as teaching models**, not extracted from any published
paper. Use them to check that a draft's Discussion has every load-bearing paragraph and stays
matched to the evidence; do not copy wording.

## How they are used

In `write-paper` Phase 5 (Discussion), after loading `section_guides/discussion.md`: pick the
exemplar matching the study type and confirm the draft restates the key finding, compares to
prior work without disparagement, gives design-tied limitations, treats generalizability, and
closes with a conclusion matched to the evidence — introducing no new results.

## Contents

- `diagnostic_accuracy_stard.md` — comparison vs prior test, clinical-pathway/threshold,
  spectrum/verification-bias limitations (STARD).
- `ai_validation_tripod_claim.md` — complementary-not-replacement framing, evidence-tier
  separation (discrimination ≠ clinical benefit), optimism/calibration caveats (TRIPOD+AI /
  CLAIM).
- `observational_cohort_strobe.md` — mandatory causal caution, reverse-causation and
  unmeasured-confounding limitations, no care-directive conclusion (STROBE).

## Curator guidelines (for adding more)

- **Synthetic only.** Write the structure with placeholder specifics; never paste a real
  paper's Discussion, use no real citations, no PII, English only.
- **Complete the trio** for the study type (mirror the `exemplar_methods/` + `exemplar_results/`
  siblings), each line stating *what the paragraph must establish*, not finished prose.
- **Enforce claim-to-evidence matching** and **no new results** — the two Discussion failure
  modes; name the study type's most common omission.
- **Anchor to the reporting-guideline** critical items in
  `peer-review/references/reviewer_calibration/compliance_floor.md`.
- Keep each file ~45–75 lines. Cross-reference `section_guides/discussion.md` rather than
  duplicating it.
