# Reviewer calibration — turning a compliance % into a judgment

`/check-reporting` reports how many guideline items are PRESENT / PARTIAL / MISSING and a
compliance percentage. A percentage alone does not answer the reviewer's actual question:
**is this manuscript reporting-complete enough, and which gaps are serious?** This directory
holds that judgment layer.

It is deliberately **not** in `reviewer_profiles/` — that directory is "form fields, not
opinions" (the scorecard a journal's editorial system shows). Calibration is opinion, so it
lives here, as the reviewer's own guideline.

## What it provides

- `compliance_floor.md` — the principle that **critical-item presence outranks the overall
  percentage**, a per-guideline list of items that are reject-risk when MISSING regardless
  of the headline %, a companion table of **AI/radiomics methodological-quality & risk-of-bias
  instruments** (PROBAST+AI, METRICS/RQS, APPRAISE-AI — kept distinct from their reporting
  counterparts CLEAR and DECIDE-AI) whose concerns can fail even a fully-reported paper, and
  the desk-rejection-risk signals to weigh.

## How it is used

In `/peer-review` Phase 2 (reporting-guideline check) and `/self-review` (category G), after
`/check-reporting` produces its table: don't stop at the percentage. Check that each
**critical item** for the study type is PRESENT; a 90%-compliant manuscript that is missing
a critical item is weaker than an 80%-compliant one that has them all.

## Boundaries (read before adding)

- **No fabricated thresholds.** This file does not assert "journal X desk-rejects below
  Y%." Journals rarely publish a numeric floor. The *only* hard signals are (a) a missing
  critical item and (b) the journal's own stated required elements (which live in
  `reviewer_profiles/` and the author guidelines — verify there, do not invent).
- **Critical-item lists are methodological judgment**, grounded in the guideline's own item
  set (public), not in any single manuscript or review.
- Keep it general and study-type-keyed; per-journal specifics belong in `reviewer_profiles/`
  and are cited, not duplicated here.
