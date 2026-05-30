# Regression fixture: pre_submission_gate.sh

End-to-end test for the four-stage chain
`check_citation_keys` → `verify_refs --strict` → `render_pandoc` (optional) → `check_xref --strict`.

## Layout

- `manuscript.md` — minimal IMRAD-shaped markdown with 3 valid `[@key]` cites, a Figure 1 mention, and a Table 1 mention.
- `refs.bib` — 3 real entries (Rinella 2023 MASLD multisociety consensus, Vandenbroucke 2007 STROBE E&E, Fine–Gray 1999) all with verifiable DOI + PMID.
- `run.sh` — invokes `pre_submission_gate.sh` in two modes and asserts the expected exit code and `submission_safe` value for each.
- `expected/pre_submission_gate.pass.summary.json` — golden minimal summary for the `--allow-separate-attachments` PASS path (compared as JSON, not byte-for-byte; timestamps and full per-stage logs are excluded from the comparison).

## What is verified

- Stage 1 passes: `[@key]` ↔ `.bib` keys all resolve.
- Stage 2 passes: `verify_refs.py --strict` reports OK for the 3 real DOIs (requires network).
- Stage 3 is SKIPPED because the harness supplies a pre-rendered DOCX placeholder.
- Stage 4 default mode FAILS with `MISSING_DOCX > 0` (Figure 1 + Table 1 are cited but not in the placeholder DOCX).
- Stage 4 `--allow-separate-attachments` mode PASSES with the same DOCX (MISSING_DOCX downgraded to WARN).

## Running

```bash
bash run.sh
```

Exit code 0 = both invariants hold; non-zero = regression.

## What is NOT verified by this fixture

- The full `verify_refs.py` per-entry record schema is deferred to the verify-refs unit tests.
- Network failures during stage 2 are reported as a fixture skip, not a regression (the test runner is expected to be offline-tolerant for CI environments without network).
