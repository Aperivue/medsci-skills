# Methods structure — diagnostic-accuracy study (STARD)

A structure model for an index-test-vs-reference-standard accuracy study. Each heading is a
paragraph; each bullet is *what the paragraph must establish*. Placeholders in `[brackets]`
stand for the study's real specifics — fill them; do not copy this text.

## Study design and oversight
- State the design (prospective / retrospective, consecutive / case-control sampling — and
  why; case-control sampling inflates accuracy and must be named).
- Setting and dates: `[single/multi-center]`, `[YYYY–YYYY]`, recruitment source.
- Ethics approval + consent (or waiver) and registration if applicable.

## Participants and eligibility
- Eligibility as a numbered list: inclusion `(1)…(2)…`, exclusion `(1)…(2)…`.
- The clinical question and the intended-use population the index test is meant to serve.
- Flow that lets the reader rebuild a 2×2 (enrolled → tested → analyzed; exclusions with
  reasons) — this is what the STARD diagram renders.

## Index test
- What it is, who performed/read it, their experience, and blinding to the reference
  standard and to clinical data.
- Acquisition specifics: `[scanner/vendor/field strength]`, protocol, software/version.
- The positivity threshold/criterion and whether it was pre-specified or data-derived.

## Reference standard
- The reference standard and its rationale (the validity hierarchy: pathology > imaging
  panel consensus > clinical follow-up at `[interval]`).
- Who applied it, their blinding to the index test, and the index↔reference time interval
  (verification timing).
- How indeterminate/non-diagnostic results were handled (ITD vs per-protocol — state which).

## Sample size
- The accuracy target and precision (expected sensitivity/specificity + CI half-width) or
  the available-sample justification; the prevalence assumed.

## Statistical analysis
- Sensitivity/specificity with 95% CIs; PPV/NPV with the prevalence they assume.
- Comparison method if two tests (paired McNemar / difference in AUC with a test of the
  difference — not two standalone AUCs), and any subgroup/multiplicity handling.
- Missing/indeterminate handling and any sensitivity analysis.
- Software + version.

## Reporting-guideline fit
- STARD 2015 (or STARD-AI for an AI index test — name BOTH base and extension). Critical
  items: reference standard + rationale, reader blinding, participant flow, indeterminate
  handling (see `peer-review/references/reviewer_calibration/compliance_floor.md`).

## Common omission
- Reader **blinding** to the reference standard and the **index↔reference time interval**
  — the two details most often missing, and both bias the headline accuracy if unaddressed.
