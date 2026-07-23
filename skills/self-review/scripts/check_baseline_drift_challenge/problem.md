# Challenge card — baseline drift (self-review)

## Problem
Self-review is run in a loop (review → revise → review). The hazard is not any single
pass but the *anchor*: each pass takes the previous **AI output** as its baseline, so a
small framing bias introduced in one pass becomes the starting point for the next and
compounds — claims strengthen, scope inflates, caveats accrete — while every individual
pass looks locally reasonable. Nothing measured how far the manuscript had drifted from
the last version a human actually approved.

## What the gate does
`scripts/check_baseline_drift.py` compares the current manuscript against a **baseline** —
the last human-approved / circulated version (the frozen v_N of manuscript-versioning),
not the last AI output — and reports lexical framing drift via fixed, word-boundary
lexicons: `STRENGTH_INFLATION` (certainty markers up while hedges fall),
`SIGNIFICANCE_INFLATION_DRIFT` (novel / pivotal / unprecedented … tokens up),
`SCOPE_INFLATION_DRIFT` (generalization phrases the baseline lacked), and `HEDGE_ACCRETION`
(hedge density up — the cumulative form of over-hardening). It is advisory: framing is a
judgment call, so every finding is Minor and the gate never blocks. With no `--baseline`
there is nothing to anchor against and it emits zero findings.

## Fixture (synthetic only — no real manuscript, no PII)
One approved `baseline.md` plus three revisions of it:
- `fixture/drifted.md` — assertions replace hedges, three significance tokens and four
  scope phrases added → `STRENGTH_INFLATION` + `SIGNIFICANCE_INFLATION_DRIFT` +
  `SCOPE_INFLATION_DRIFT`.
- `fixture/overhedged.md` — caveats piled on, claim strength unchanged → `HEDGE_ACCRETION`
  only.
- `fixture/stable.md` — a legitimate reword at the same strength → **clean** (the
  false-positive control).
- `baseline.md` alone (no `--baseline`) — **clean** (the crossfire path passes only
  `--manuscript`).

## Expected
- `expected/<scenario>.txt` — the drift summary for each run.
- Every scenario exits 0, even under `--strict` (advisory). The JSON artifact carries the
  same verdicts; the drifted draft carries all three inflation verdicts, the reword and
  the no-baseline path carry none.

`verify.sh` diffs each stdout against `expected/`, asserts the always-exit-0 contract, and
checks the JSON verdicts. Network-free, stdlib-only.
