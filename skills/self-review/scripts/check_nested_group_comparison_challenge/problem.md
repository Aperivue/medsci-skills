# Challenge card — nested-group-comparison gate (self-review)

## Problem
Answering a selection-bias comment, authors add a "representativeness" table that
compares the analysed subset (n=33) against the "full cohort" (n=132) *containing*
those 33 patients, with P values. The groups are nested, so the two-group test is
invalid — not merely uninformative. The correct contrast is subset vs remainder
(n=99). The column headers announce both n's and their labels verbatim, so the
defect is deterministically visible.

## What the gate does
`check_nested_group_comparison.py` scans GFM tables for two `n = N` column headers,
one labelled subset/sub-cohort/correlated/analysed/surgical/pathology and the other
labelled full/total/overall/entire/whole cohort, together with a P-value column, and
flags `NESTED_GROUP_TEST` when the subset n is smaller than the cohort that names it.
A "remainder" label is excluded so a valid subset-vs-remainder table does not fire.

## Fixture (synthetic only — no real manuscript, no PII)
- `fixture/nested.md` — full cohort (n=132) vs pathology-correlated subset (n=33) + P.
- `fixture/clean.md` — disjoint randomised arms (n=66 / n=66) and a valid
  subset-vs-remainder table (n=33 / n=99), both with P columns; neither fires.

## Expected
- `expected/nested.txt` — `NESTED_GROUP_TEST`; exit 1 under `--strict`.
- `expected/clean.txt` — `OK`; exit 0.

`verify.sh` diffs both outputs and asserts the exit-code contract. Network-free, stdlib-only.
