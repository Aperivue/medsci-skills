# Challenge card — test statistic vs reported P (self-review)

## Problem
A results sentence such as `t(28) = 1.50, P = .03` carries everything needed to recompute its
own P: the statistic and its degrees of freedom. A P the printed statistic cannot produce is a
transcription or analysis error; one on the other side of alpha changes the conclusion. Nobody
recomputes it at review time.

## What the gate does
`check_test_statistic_p.py` finds `t(df) = x`, `F(df1, df2) = x`, `χ2(df) = x` and `z = x` with
a P in the same sentence, recomputes the two-sided (t, z) or upper-tail (F, χ2) P with a
pure-Python regularized incomplete beta / gamma function, and reads both numbers as intervals at
their printed precision. It fires only when no statistic in the statistic's rounding interval
gives a P inside the reported P's interval (`P_STAT_INCONSISTENT`, Minor), and calls it Major
(`P_STAT_DECISION_ERROR`) only when the two ranges also lie on opposite sides of alpha.

## Fixture (synthetic only — no real manuscript, no PII)
- `fixture/stat_bad.md` — `t(48) = 2.10, P = .041` (consistent) and `t(28) = 1.50, P = .03`
  (two-sided P 0.144–0.146 over [1.495, 1.505]).
- `fixture/stat_ok.md` — the same with the second P corrected to `.14`.

## Expected
- `expected/bad.txt` — one `P_STAT_DECISION_ERROR`; exit 1 under `--strict`.
- `expected/ok.txt` — `OK`; exit 0.

Reference values come from scipy 1.17.1 (`2*scipy.stats.t.sf(x, df)`), recorded in `verify.sh`.
`verify.sh` diffs both outputs and asserts the exit-code contract. Network-free, stdlib-only.
