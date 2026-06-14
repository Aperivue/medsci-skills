# Critical-item floor — presence outranks the headline percentage

A compliance percentage is a coarse summary: two manuscripts at the same percentage can
differ enormously in reviewability because **not all items carry equal weight**. After the
item-by-item table (Step 4), use this floor so a MISSING **critical** item is surfaced as a
headline gap regardless of the overall percentage.

## The principle

1. **Critical items are pass/fail.** For each study type a small set of items is treated as
   non-waivable by methods reviewers/editors. If one is MISSING, surface it as a **Critical
   gap** even when the overall percentage is high — a 90%-compliant manuscript whose ground
   truth is undefined or which cannot be reproduced is not "90% acceptable."
2. **The percentage is a secondary signal** ("broadly thorough vs broadly thin"), not a
   desk-reject line. Do not assert a numeric floor a journal has not published.
3. **The journal's own required elements are hard** (a missing required panel, the wrong
   checklist for the design) — verify against the author guidelines, never invent them.

## Critical items by guideline (MISSING → Critical gap)

| Guideline (study type) | Critical items |
|---|---|
| **CLAIM / STARD-AI** (imaging AI / AI diagnostic) | Ground-truth/reference-standard definition; data-partition with leakage control; evaluation metrics with uncertainty; model + training procedure (when a model is developed — for a locked/already-trained model evaluated as a diagnostic test, the version/provenance instead) |
| **TRIPOD+AI** (prediction model) | Input data + outcome definition/timing; development and validation; performance with **calibration**, not discrimination only |
| **STARD** (diagnostic accuracy) | Reference standard + rationale; reader blinding (index vs reference); participant flow (2×2 recoverable); indeterminate-result handling |
| **STROBE** (observational) | Eligibility/selection; exposure/outcome definitions; **missing-data handling**; participant flow that reconciles |
| **PRISMA / PRISMA-DTA** (systematic review) | Full search strategy (≥1 database verbatim); flow diagram that reconciles; per-study risk of bias; registration/protocol **status or reference** (an explicit "not registered / no protocol" satisfies this — a reference is not mandatory) |

Where an extension genuinely extends a base instrument (e.g., STARD-AI extends STARD), a
manuscript that names only the extension and skips the base items is a gap — but defer this
to Step 4e (framework naming), which already distinguishes true extensions from standalone
rewrites (TRIPOD+AI is a complete rewrite, not an add-on to TRIPOD 2015, so it implies no
separate TRIPOD-2015 floor). Do not manufacture a base-citation Critical gap here.

## AI / radiomics: appraisal is separate from reporting

The checklists above answer "was it **reported**?" For AI/ML and radiomics, also confirm the
manuscript's chosen **methodological-quality / risk-of-bias** instrument and its non-waivable
concerns — a fully *reported* paper can still be at high risk of bias.

| Appraisal / RoB instrument | Non-waivable concerns |
|---|---|
| **PROBAST+AI** (prediction-model RoB, regression or ML/AI) | Train/test independence + leakage; sample size / overfitting-and-optimism control; calibration, not discrimination only |
| **METRICS / RQS** (radiomics methodological quality, EuSoMII) | Feature reproducibility/stability (test–retest, segmentation, ICC); internal–external validation + multiplicity; calibration |
| **APPRAISE-AI** (clinical-AI study quality) | Independent/external validation; robustness / error analysis; reproducibility (data + code) |

Keep these distinct from their **reporting** counterparts — **CLEAR** (radiomics reporting)
and **DECIDE-AI** (early clinical-evaluation reporting) are reporting guidelines, not RoB
tools; route them through the normal checklist flow, not this appraisal note.

## How to use in the report

- After the item table, list **Critical items: X / Y present**, naming each MISSING critical
  item and the section where it should appear.
- If any critical item is MISSING, the report's headline is the **Critical gap**, not the
  percentage. (This floor complements the reviewer-side judgment layer; it does not assert a
  journal desk-reject threshold.)
