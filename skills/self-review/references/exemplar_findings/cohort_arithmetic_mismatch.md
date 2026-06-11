# Exemplar — cohort arithmetic does not reconcile

**Fired:** `check_cohort_arithmetic.py` — `CASCADE_SUM` (the STROBE flow does not balance:
start N − Σ(exclusions) ≠ final analytic N) and/or `RATE_BACKCALC` (a reported incidence
rate does not reproduce from numerator/person-time).
**Severity:** Fatal → Anticipated **Major**. **Category:** A. Study Design & Data Integrity.

## Anticipated Major Comment (how a reviewer will put it)

> The participant flow does not add up. The Methods report 1,000 screened and exclusions of
> 120 + 60 + 40, which leaves 780, but the analytic cohort is given as 800 (Figure 1 vs
> Results, first paragraph). Please reconcile the flow diagram, the text, and Table 1 so the
> numbers are internally consistent, and state which figure is correct.
>
> Relatedly, the incidence rate of 12.0 per 1,000 person-years with 9,800 person-years
> implies ~118 events, but 96 events are reported (Table 2). Please confirm the numerator,
> denominator, and rate.

## Severity / category rationale

This is **Fatal** because the cohort size and the event/person-time are the denominators of
every downstream estimate — if they are inconsistent, the reader cannot trust any rate or
effect size. It is **category A** (data integrity), not a wording issue.

## Fix

Recompute the cascade and the rate from the source data (never hand-retype), correct the
diagram/text/table to a single set of numbers, and add a one-line reconciliation note if a
late exclusion was applied. `fixable_by_ai: false` — the numbers must come from the data,
not be guessed; the author re-derives from the CSV.

## R0-ready line

> R0-A1 (Major, Fatal): STROBE flow and the incidence rate do not reconcile (Figure 1 /
> Results / Table 2); re-derive from source and unify. [gate: check_cohort_arithmetic]
