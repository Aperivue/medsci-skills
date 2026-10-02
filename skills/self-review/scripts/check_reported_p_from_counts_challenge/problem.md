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
≤ 1e-3 (the family is only named in the message), and flags a row
(`P_NOT_REPRODUCIBLE`) when, under **every** family, the reported P differs by more
than one order of magnitude, sits on the other side of alpha (default 0.05; a printed
value whose rounding interval straddles alpha is not judged), or is an upper bound
(`<0.001`) the computed P exceeds. Continuous rows (mean ± SD, median [IQR]) are
skipped. A single-row table is checked. A P printed on the first level of a
multi-level variable (next row: counts, empty P) is an omnibus P and is not judged by
the alpha or bound rules. When no count row with a P is found the report says
`NOT CHECKED` instead of claiming every P reproduces.

## Fixture (synthetic only — no real manuscript, no PII)
- `fixture/p_bad.md` — Male 79/132 vs 16/33 (reproduces at 0.237) and Adenocarcinoma
  5/132 vs 4/33 reporting `P<0.001` (true ≈ 0.06).
- `fixture/p_ok.md` — same table with the Adenocarcinoma P corrected to 0.060.
- `fixture/p_cross.md` — 40/100 vs 30/100 printed `0.04` (true ≈ 0.18: crosses
  alpha), 45/100 vs 25/100 printed `<0.001` (true ≈ 0.005: bound exceeded), and a
  single-row table 60/100 vs 30/100 printed `0.90` (true ≈ 3e-05).
- `fixture/p_cross_ok.md` — the same rows with correct P values, plus a `0.05` whose
  rounding interval straddles alpha, a `0.046` that only one family reproduces, and a
  three-level Stage variable with one omnibus P on its first level.
- `fixture/p_none.md` — prose only, no table.

## Expected
- `expected/bad.txt` — one `P_NOT_REPRODUCIBLE`; exit 1 under `--strict`.
- `expected/ok.txt` — `OK`; exit 0.
- `expected/cross.txt` — three `P_NOT_REPRODUCIBLE`; exit 1 under `--strict`.
- `expected/cross_ok.txt` — `OK`; exit 0.
- `expected/none.txt` — `NOT CHECKED`; exit 0.

`verify.sh` diffs both outputs and asserts the exit-code contract. Network-free, stdlib-only.
