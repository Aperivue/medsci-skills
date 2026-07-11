#!/usr/bin/env bash
# Deterministic verifier for the DTA-denominator challenge card. cd HERE for a
# stable relative source path.
# Fixtures (synthetic only — no real manuscript, no PII):
#   dta_bad.md — reference-standard table gives pN0=14 (neg) / pN1+pN2=19 (pos), but
#                Results report specificity 14/15 and sensitivity 13/18; grand totals
#                still agree (33) -> 2x DTA_DENOMINATOR_MISMATCH + GRAND_TOTAL_AGREES.
#   dta_ok.md  — Results 14/14 and 13/19 match the table -> OK.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"; DET="$HERE/../check_dta_denominators.py"; cd "$HERE"
bad="$(python3 "$DET" --manuscript fixture/dta_bad.md)"; ok="$(python3 "$DET" --manuscript fixture/dta_ok.md)"
pass=1
diff -u expected/bad.txt <(printf '%s\n' "$bad") || { echo "FAIL: bad drift" >&2; pass=0; }
diff -u expected/ok.txt  <(printf '%s\n' "$ok")  || { echo "FAIL: ok drift" >&2; pass=0; }
python3 "$DET" --manuscript fixture/dta_bad.md --strict --quiet >/dev/null 2>&1 && rb=0 || rb=$?
python3 "$DET" --manuscript fixture/dta_ok.md  --strict --quiet >/dev/null 2>&1 && ro=0 || ro=$?
[ "${rb:-0}" -eq 1 ] || { echo "FAIL: bad should exit 1 (got ${rb:-0})" >&2; pass=0; }
[ "$ro" -eq 0 ]      || { echo "FAIL: ok should exit 0 (got $ro)" >&2; pass=0; }
[ "$pass" -eq 1 ] && echo "PASS: DTA-denominator gate flags the split mismatch behind a matching grand total." || exit 1
