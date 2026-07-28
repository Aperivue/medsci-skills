# Challenge card — refinement regression axis (self-review)

## Problem
Self-review is stateless: each run reports the manuscript's *current* findings, but nothing
compares one run to the last. So when the author revises to fix finding X, the gate
pass-rate goes up ("X resolved") and no one measures whether the fix **introduced** a new
finding Y — the loop looks like it is improving while quietly accumulating new problems.
Worse, a finding that was fixed can reappear a round later (the "Mirror Loop"): the loop is
churning, not converging.

## What the tool does
`scripts/refinement_regression.py` is a loop controller, not a detector — it finds no defect
and carries no `check_` prefix. It reads a small run-history **ledger** (one line per run,
each line the `verdict@where` fingerprints of that run's findings) plus the current run's
`qc/*.json`, and reports the regression axis *alongside* the pass-rate axis: `resolved`
(fixed), `carried` (still open), `new` (**broke**), and `churn` (a previously-resolved
finding that resurfaced). Verdict: `PROGRESSING` (fixed, nothing new), `REGRESSION` (a new
finding introduced), `CHURNING` (Mirror Loop — stop), `CONVERGED` (done), or `INDETERMINATE`
(first run). Advisory: it never blocks. By default it only classifies; with `--append` it
records the current run as the next ledger entry.

## Fixture (synthetic only — no real manuscript, no PII)
Five scenarios, each a `ledger.jsonl` (prior runs) plus a `qc/` dir (the current run):
- `progressing/` — one finding resolved, none new → `PROGRESSING`.
- `regression/` — `RATE_BACKCALC@Methods` appears that the prior run lacked → `REGRESSION`.
- `churning/` — `HEDGE_ACCRETION` was present two runs back, resolved, and is back → `CHURNING`.
- `converged/` — the last finding resolved, nothing carried or new → `CONVERGED`.
- `firstrun/` — an empty ledger → `INDETERMINATE`.

## Expected
- `expected/<scenario>.txt` — the regression summary for each run.
- Every scenario exits 0, even under `--strict` (advisory). The JSON artifact carries the
  same verdict and names the offending key. `--append` adds exactly one ledger line and the
  committed fixture ledgers stay immutable under the classify-only runs.

`verify.sh` diffs each stdout against `expected/`, checks the JSON verdicts, exercises
`--append` on a temp copy, and asserts the fixtures were not mutated. Network-free,
stdlib-only.
