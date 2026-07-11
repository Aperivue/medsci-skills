# Challenge card — DTA-denominator gate (self-review)

## Problem
Sensitivity is a/(a+c) over disease-positive patients and specificity d/(b+d) over
disease-negative patients, so those denominators must equal the reference-standard
positive / negative counts in the characteristics table. When they disagree while
the grand total still matches (table 14/19, Results 15/18, both = 33), a totals-only
check passes and the split-level error — under an Abstract headline — survives
multiple review rounds. It is present from the first submission, not introduced by a
revision.

## What the gate does
`check_dta_denominators.py` recovers the reference-standard negative / positive
counts from the characteristics table (pN0 vs pN1+pN2; node-negative vs -positive;
absent vs present) and the sensitivity / specificity denominators from the Results
prose, and asserts each denominator equals its category count — explicitly noting
when the grand totals agree, because that is what hides it. It also checks a staging
breakdown sums (`STAGE_ROWSUM`: correct + over + under == n).

## Fixture (synthetic only — no real manuscript, no PII)
- `fixture/dta_bad.md` — table pN0=14 / pN1+pN2=19; Results specificity 14/15 and
  sensitivity 13/18; grand totals both 33.
- `fixture/dta_ok.md` — Results 14/14 and 13/19 match the table.

## Expected
- `expected/bad.txt` — two `DTA_DENOMINATOR_MISMATCH` + `GRAND_TOTAL_AGREES`; exit 1 under `--strict`.
- `expected/ok.txt` — `OK`; exit 0.

`verify.sh` diffs both outputs and asserts the exit-code contract. Network-free, stdlib-only.
