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
than one order of magnitude, or is an upper bound (`<0.001`) the computed P exceeds.
A reported P on the other side of alpha (default 0.05; a printed value whose rounding
interval straddles alpha is not judged) under every family is a MINOR advisory,
`P_ALPHA_CROSSING`, that never fails `--strict`: the table cannot prove the P is a crude
2x2 P, so it may be adjusted or use a different denominator. Continuous rows (mean ± SD, median [IQR]) are
skipped. A single-row table is checked. A P printed on the first level of a
multi-level variable (next row: counts, empty P) is an omnibus P and is not judged by
the alpha or bound rules. The alpha, bound and single-row rules need the crude 2x2 to be the
row's own table: both cells must print a % equal to count / header n at its printed
precision (a smaller missing-data denominator fails this), and the P must not be
model-based (an adjusted / multivariable / model / regression / weighted P header, an
OR / HR / RR / beta / estimate column, or adjusted / multivariable / regression /
weighted in the table's caption or footnotes). Other rows keep only the order-of-magnitude rule (tables with >= 2
count rows) and the report adds a `LIMITED` line counting them. When no count row with a P is found the report says
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
- `fixture/p_adjusted.md` — 20/100 vs 31/100 with an adjusted OR and an adjusted P of
  0.03 (crude Fisher ≈ 0.10), the same with an OR column and a plain P header, and a
  multivariable P header -> not judged by the crude alpha rule.
- `fixture/p_missing_denom.md` — 20 (33.3) vs 32 (53.3) under n = 100 per group with a
  footnote giving 60 per group with BMI, P 0.03 (true for 20/60 vs 32/60) -> not judged
  against the header n; a count row with no % likewise.

- `fixture/p_adjusted_context.md` — 20/100 vs 30/100 at P 0.03 (crude Fisher ≈ 0.14) under a
  `P*` header whose footnote says adjusted (logistic regression); the same under a plain
  `P value` header with the adjustment in the caption; and `<0.001` against a crude ≈ 0.005
  under an inverse-probability-weighted footnote -> not judged by the boundary rules.
- `fixture/p_alpha_only.md` — 40/100 vs 30/100 printed `0.04` (true ≈ 0.18) and nothing else
  wrong -> MINOR advisory only.
- `fixture/p_footnote_crude.md` — a `P value*` header whose footnote names Fisher's exact
  test, 45/100 vs 25/100 printed `<0.001` (true ≈ 0.005), then a prose paragraph that
  mentions an adjusted analysis -> the bound rule still fires.

## Expected
- `expected/bad.txt` — one `P_NOT_REPRODUCIBLE`; exit 1 under `--strict`.
- `expected/ok.txt` — `OK`; exit 0.
- `expected/cross.txt` — two `P_NOT_REPRODUCIBLE` and one MINOR `P_ALPHA_CROSSING`; exit 1
  under `--strict`.
- `expected/cross_ok.txt` — `OK`; exit 0.
- `expected/none.txt` — `NOT CHECKED`; exit 0.
- `expected/adjusted.txt`, `expected/missing_denom.txt`, `expected/adjusted_context.txt` — `OK`
  with a `LIMITED` line; exit 0.
- `expected/alpha_only.txt` — `OK` with one MINOR `P_ALPHA_CROSSING`; exit 0 under `--strict`.
- `expected/footnote_crude.txt` — one `P_NOT_REPRODUCIBLE`; exit 1 under `--strict`.

`verify.sh` diffs both outputs and asserts the exit-code contract. Network-free, stdlib-only.
