# Challenge card — self-review coverage ledger (PASS over an unworked category)

## Problem
The Phase 3c self-review JSON recorded what the review FOUND (`issues[]`) and nothing about what
it LOOKED AT. A review that never reached category C (validation & statistics) and a review that
worked C and found nothing produced the same `"verdict": "PASS"`, and `/write-paper` Phase 7 stops
its fix loop on that PASS. "Not checked" read as "no problem".

## What the tool does
`scripts/check_review_coverage.py` reads `qc/self_review.json` and its `coverage` ledger: one entry
per category A–L and per loaded domain-probe module, each `assessed` (with evidence references),
`not_applicable` (with a one-line reason) or `not_assessed`. It enforces one rule: the review
cannot return PASS while any applicable entry is `not_assessed`.

- `COVERAGE_GAP_PASS` (Major) — PASS with a `not_assessed` entry. Certain from the input: the JSON
  states both facts itself.
- `COVERAGE_GAP` (Minor) — a `not_assessed` entry under REVISE; reported so the gap is visible.
- `COVERAGE_NOT_RECORDED` (Minor) — no `coverage` object (JSON written before the ledger existed).
  Legacy, not a failure: the run still reports `OK` and exits 0 under `--strict`.

A malformed ledger (a missing letter, `assessed` without evidence, `not_applicable` without a
reason, an unknown probe module, an unknown verdict, NaN) is an input error: exit 2 naming the field.

## Fixture (synthetic only — no real manuscript, no PII)
- `fixture/pass_gap.json` — PASS, category C `not_assessed` → `COVERAGE_GAP_PASS`, exit 1 under `--strict`.
- `fixture/pass_complete.json` — the same review with C assessed (K not_applicable with a reason)
  → silent, exit 0. Same verdict, same issues, opposite outcome: the ledger is what the gate reads.
- `fixture/revise_gap.json` — REVISE with category I and the observational-confounding probe
  `not_assessed` → two `COVERAGE_GAP` Minors, exit 0 under `--strict`.
- `fixture/legacy_no_coverage.json` — PASS with no `coverage` object → `COVERAGE_NOT_RECORDED`
  Minor, verdict `OK`, exit 0 under `--strict`.

## Expected
- `expected/<fixture>.txt` — stdout for each fixture (golden diff).
