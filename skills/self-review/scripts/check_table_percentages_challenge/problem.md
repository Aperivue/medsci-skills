# Challenge card — table-percentage gate (self-review)

## Problem
A characteristics table prints `79 (63%)` and `53 (37%)` under a stated denominator
of 132. The true percentages are 59.8% and 40.2% — both cells are wrong. This is
pure arithmetic with no judgement, yet it routinely survives multiple review rounds
because it is present verbatim from the first submission and no prior gate recomputed
a printed percentage against its own column count. `check_cohort_arithmetic.py` covers
rate back-calculation, exclusion cascades, and tier-partition disjointness, but not a
single `n (%)` cell versus its denominator.

## What the gate does
`scripts/check_table_percentages.py` parses GFM pipe tables from the manuscript,
recovers each column's denominator (a `n = N` header, a Total row, or the column's
counts summing), and recomputes `100·n/denominator` for every count/percentage cell,
flagging any that differs from the printed value by more than 0.5 pp (configurable).
A column is treated as percentages only when a cell carries an explicit `%` OR its
parenthetical values sum to ~100 (a partition) — so `mean (SD)` cells, whose SDs
carry no `%` and do not sum to 100, are never misread as percentages.

## Fixture (synthetic only — no real manuscript, no PII)
- `fixture/table_bad.md` — `79 (63)` / `53 (37)` under `n = 132`; both wrong
  (59.8% / 40.2%). Detected via the partition path (63 + 37 = 100), so the gate
  fires even though *both* cells are wrong and neither reproduces.
- `fixture/table_ok.md` — a correct percentage column (`16 (48%)` / `17 (52%)` under
  `n = 33`) plus a `mean (SD)` table (`45 (12)` / `24 (3)`); the gate must clear the
  correct column and must not false-positive on the standard deviations.

## Expected
- `expected/bad.txt` — `MISMATCH FOUND`, two `PERCENT_MISMATCH` rows; exit 1 under `--strict`.
- `expected/ok.txt` — `OK`, zero findings; exit 0 under `--strict`.

`verify.sh` diffs both stdout outputs against `expected/` and asserts the exit-code
contract (bad → 1, ok → 0). Network-free, stdlib-only.
