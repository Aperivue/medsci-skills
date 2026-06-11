# Compliance floor — critical-item presence over headline percentage

A reporting-compliance percentage is a coarse summary. Two manuscripts at the same
percentage can differ enormously in reviewability, because **not all items carry equal
weight**. Calibrate the reviewer comment to *which* items are missing, not just how many.

## The principle

1. **Critical items are pass/fail.** For each study type there is a small set of items that
   a methods reviewer or editor treats as non-waivable. If one is MISSING, raise it as a
   Major comment **regardless of the overall percentage** — an otherwise 90%-compliant paper
   that cannot be reproduced or whose ground truth is undefined is not "90% acceptable."
2. **The overall percentage is a secondary signal**, useful for "is the reporting broadly
   thorough or broadly thin," not for a desk-reject line. Do not assert a numeric floor a
   journal has not published.
3. **The journal's own required elements are hard.** A missing structured-abstract heading,
   a missing required panel (e.g., Key Points / Summary Statement), or the wrong reporting
   checklist for the study type is a concrete, citable gap — but those facts live in
   `reviewer_profiles/` and the author guidelines; verify there, never invent them.

## Critical items by guideline (MISSING → Major / reject-risk)

These are the items most consistently treated as non-waivable. Phrase the comment as the
specific missing item, anchored to where it should appear.

| Guideline (study type) | Critical items (raise as Major if MISSING) |
|---|---|
| **CLAIM** (AI in medical imaging) | Model architecture + training procedure; ground-truth/reference-standard definition; data-partition method (train/val/test, leakage control); evaluation metrics with uncertainty |
| **TRIPOD+AI** (prediction model) | Source and types of input data; outcome definition and timing; how the model was developed and validated; performance with **calibration**, not discrimination only |
| **STARD-AI / STARD** (diagnostic accuracy) | Reference standard and its rationale; blinding of index-test vs reference readers; participant flow (2×2 recoverable); handling of indeterminate results |
| **STROBE** (observational) | Eligibility criteria and selection; outcome/exposure definitions; **how missing data were handled**; participant flow (cascade reconciles) |
| **PRISMA / PRISMA-DTA** (systematic review) | Full search strategy (≥1 database verbatim); flow diagram that reconciles; per-study risk-of-bias; pre-registration/protocol reference |

Extensions name the base instrument too (e.g., STARD **and** STARD-AI) — a manuscript that
cites only the extension and skips the base items is itself an item to flag.

## Desk-rejection-risk signals (weigh, don't over-assert)

- A **critical item is MISSING** (above) — the strongest single signal.
- The manuscript uses the **wrong reporting guideline** for its design (e.g., a prediction
  model reported only against STROBE).
- A journal **required element is absent** (per `reviewer_profiles/` + author guidelines).
- The **reporting checklist is not uploaded** or references a stale manuscript version.

When several co-occur, say so in the Confidential Comments to the Editor as a coherent
"reporting readiness" concern, not as a list of nitpicks.

## Integration

Run `/check-reporting` first for the item-by-item table, then apply this file:
- `/peer-review` Phase 2 (reporting-guideline check) and Phase 4 self-QC.
- `/self-review` category G — flag MISSING critical items as Anticipated Major Comments.
