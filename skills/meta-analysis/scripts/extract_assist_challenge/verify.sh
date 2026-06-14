#!/usr/bin/env bash
# Deterministic verifier for the extract-assist challenge card.
# Demonstrates the full Phase-4 pipeline:
#   (1) extract_assist.py emits AI_SUGGESTED candidates with page + verbatim quote
#       (including a unit-ambiguous source_sens: "92%" vs "0.92", and a not_found
#       field) — diffed against expected/suggestions.tsv.
#   (2) AFTER a human reconciles the candidates into a confirmed DTA CSV, that CSV
#       (NOT the suggestion TSV) passes dta_extraction_qc.py.
# No network. Exit 0 = both stages match expectations.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
SCRIPTS="$HERE/.."

# --- Stage 1: suggestions are AI_SUGGESTED, with provenance, never decisions ---
actual="$(python3 "$SCRIPTS/extract_assist.py" \
  --md "$HERE/fixture/paper.md" \
  --schema "$HERE/fixture/schema.yaml" 2>/dev/null)"

if ! diff -u "$HERE/expected/suggestions.tsv" <(printf '%s\n' "$actual"); then
  echo "FAIL: extract_assist suggestions drifted from expected/suggestions.tsv" >&2
  exit 1
fi

# Every non-header row must be AI_SUGGESTED + needs_review=true (suggestions, not decisions).
bad=$(printf '%s\n' "$actual" | tail -n +2 | grep -cv $'\tAI_SUGGESTED$' || true)
if [ "$bad" -ne 0 ]; then
  echo "FAIL: $bad suggestion row(s) not labeled AI_SUGGESTED" >&2
  exit 1
fi

# --- Stage 2: human-confirmed CSV then passes the downstream QC gate ---
qc_out="$(mktemp)"
summary="$(python3 "$SCRIPTS/dta_extraction_qc.py" \
  --input "$HERE/fixture/confirmed_example.csv" \
  --out "$qc_out" 2>/dev/null | grep '^DTA QC:')"
rm -f "$qc_out"

if printf '%s' "$summary" | grep -q "OK=1 | SWAP=0 | MISMATCH=0"; then
  echo "PASS: 11 AI_SUGGESTED candidates with page+quote (1 not_found); human-confirmed CSV clears dta_extraction_qc ($summary)."
else
  echo "FAIL: confirmed CSV did not pass dta_extraction_qc cleanly: $summary" >&2
  exit 1
fi
