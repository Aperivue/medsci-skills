# Challenge card — reported-P-from-counts gate (self-review)

## Problem
A baseline table comparing two groups prints a count per group and a P value per
row. That P is fully determined by the four cell counts, yet a wrong one — a
reported `p<0.001` whose true value is ~0.06 — survives review because no one
recomputes it. The test family is identifiable from the rows that *do* reproduce
(here a sex row reproduces exactly at 0.237 under uncorrected Pearson), which
calibrates the check for the rest.

## What the gate does
`check_reported_p_from_counts.py` rebuilds the 2x2 table for every integer-count
row (from the two `n = N` group headers), recomputes Fisher's exact test and
Pearson's chi-square with and without Yates' correction in pure stdlib
(`math.comb` / `math.erfc`), calibrates the family on the rows that reproduce to
≤ 1e-3, and flags any row whose reported P differs by more than one order of
magnitude under **every** family (`P_NOT_REPRODUCIBLE`). Continuous rows (mean ± SD,
median [IQR]) are skipped and a single-row table never fires.

## Fixture (synthetic only — no real manuscript, no PII)
- `fixture/p_bad.md` — Male 79/132 vs 16/33 (reproduces at 0.237) and Adenocarcinoma
  5/132 vs 4/33 reporting `P<0.001` (true ≈ 0.06).
- `fixture/p_ok.md` — same table with the Adenocarcinoma P corrected to 0.060.

## Expected
- `expected/bad.txt` — one `P_NOT_REPRODUCIBLE`; exit 1 under `--strict`.
- `expected/ok.txt` — `OK`; exit 0.

`verify.sh` diffs both outputs and asserts the exit-code contract. Network-free, stdlib-only.
