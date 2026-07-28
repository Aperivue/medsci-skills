# Challenge card — refinement terminal-state (self-review loop controller)

## Problem
Self-review is run in a loop — review, revise, review again. The floor gates
(numerical, citation, cross-reference, leakage) converge to a fixed point of zero
Major findings, but nothing declares the loop *done*. Because every additive gate can
always surface one more caveat, an ungrounded loop drifts: the manuscript over-hardens,
the same findings get re-raised in new words (the "Mirror Loop"), and "no edit needed"
is never treated as a valid outcome. `check_editorial_impression.py` (the ceiling pass)
*detects* over-hardening, but nothing turns the floor + ceiling state into a reproducible
STOP signal the harness cannot rationalize away, and nothing legitimizes a zero-edit PASS.

## What the tool does
`scripts/refinement_stop.py` is a loop controller, not a detector — it finds no defect,
carries no `check_` prefix, and is not counted in the detector catalog. It reads the
`qc/*.json` artifacts the other gates already wrote and classifies the loop's terminal
state: `CONTINUE` (a floor Major remains), `STOP_OVERHARDENING` (floor clean but the
ceiling pass flags accumulation), `STOP_MINOR_OPTIONAL` (only optional Minor polish
left), `STOP_ZERO_EDIT` (floor at fixed point, ceiling clean — submission-ready as-is),
or `INDETERMINATE` (no gate artifacts yet). A floor gate is recognised by a
`summary.n_major`; the ceiling pass by a `summary.by_action`. It is advisory and never
blocks — it must not double-gate the floor detectors, which already exit non-zero on
their own Majors — so every run exits 0.

## Fixture (synthetic only — no real manuscript, no PII)
Five `qc/` directories of synthetic gate envelopes:
- `fixture/zero_edit/` — floor 0 Major/0 Minor + ceiling 0 → `STOP_ZERO_EDIT`.
- `fixture/overhardening/` — floor 0 Major + ceiling 2 findings → `STOP_OVERHARDENING`.
- `fixture/minor_optional/` — floor 0 Major/1 Minor + ceiling 0 → `STOP_MINOR_OPTIONAL`.
- `fixture/continue/` — floor 1 Major → `CONTINUE`.
- `fixture/empty/` — no `*.json` → `INDETERMINATE`.

## Expected
- `expected/<scenario>.txt` — the terminal-state summary for each directory.
- Every scenario exits 0, even under `--strict` (advisory; the controller informs, it
  never blocks). The JSON artifact carries the same `verdict` + `stop` flag.

`verify.sh` diffs each stdout against `expected/`, asserts the always-exit-0 contract,
and checks the JSON verdict. Network-free, stdlib-only.
