#!/usr/bin/env bash
# Deterministic verifier for the refinement-regression challenge card.
# Network-free, stdlib-only. The gate is advisory, so every run must exit 0 -- it reports
# the regression axis (what the revision broke), it never blocks.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
DET="$HERE/../refinement_regression.py"
cd "$HERE"

pass=1
for s in progressing regression churning converged firstrun; do
  got="$(python3 "$DET" --qc-dir "fixture/$s/qc" --ledger "fixture/$s/ledger.jsonl")"
  if ! diff -u "expected/$s.txt" <(printf '%s\n' "$got"); then
    echo "FAIL: $s output drifted from expected/$s.txt" >&2; pass=0
  fi
  python3 "$DET" --qc-dir "fixture/$s/qc" --ledger "fixture/$s/ledger.jsonl" --strict --quiet >/dev/null 2>&1 && rc=0 || rc=$?
  if [ "${rc:-0}" -ne 0 ]; then
    echo "FAIL: $s must exit 0 (advisory, even under --strict); got ${rc:-0}" >&2; pass=0
  fi
done

# Regression and churning must carry the offending key in the JSON artifact.
tmp="$(mktemp)"
python3 "$DET" --qc-dir fixture/regression/qc --ledger fixture/regression/ledger.jsonl --out "$tmp" --quiet
grep -q '"verdict": "REGRESSION"' "$tmp" || { echo "FAIL: regression JSON verdict" >&2; pass=0; }
grep -q "RATE_BACKCALC@Methods" "$tmp"   || { echo "FAIL: regression JSON missing the new finding key" >&2; pass=0; }
python3 "$DET" --qc-dir fixture/churning/qc --ledger fixture/churning/ledger.jsonl --out "$tmp" --quiet
grep -q '"verdict": "CHURNING"' "$tmp"    || { echo "FAIL: churning JSON verdict" >&2; pass=0; }
rm -f "$tmp"

# --append must record the current run as a new ledger line, on a COPY so fixtures stay immutable.
tled="$(mktemp)"; cp fixture/regression/ledger.jsonl "$tled"
before=$(wc -l < "$tled")
python3 "$DET" --qc-dir fixture/regression/qc --ledger "$tled" --append --quiet
after=$(wc -l < "$tled")
[ "$after" -eq "$((before + 1))" ] || { echo "FAIL: --append did not add exactly one ledger entry ($before -> $after)" >&2; pass=0; }
grep -q '"run": 2' "$tled" || { echo "FAIL: appended entry missing run ordinal" >&2; pass=0; }
rm -f "$tled"

# The committed fixture ledger must be untouched by the read-only runs above.
[ "$(wc -l < fixture/regression/ledger.jsonl)" -eq 1 ] || { echo "FAIL: fixture ledger was mutated by a classify-only run" >&2; pass=0; }

if [ "$pass" -eq 1 ]; then
  echo "PASS: refinement-regression separates fixed/still-open from broke/resurfaced across the ledger (PROGRESSING / REGRESSION / CHURNING / CONVERGED / INDETERMINATE), appends only with --append, and never blocks."
else
  exit 1
fi
