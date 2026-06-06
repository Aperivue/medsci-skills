#!/usr/bin/env bash
# Regression test for the categorical-implied-zero (structural-zero) detector.
# Synthetic fixture: never-smokers with NULL pack-years (the bug), one with an
# explicit 0 (ok), one mislabeled with a positive dose. Stdlib-only (python3).
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$HERE/../scripts/check_structural_zero.py"
FIXTURE="$HERE/fixtures/smoking.csv"
OUT="$(mktemp -t sz_XXXX).json"
trap 'rm -f "$OUT"' EXIT

fail=0
check() { local label="$1"; shift
    if "$@" >/dev/null 2>&1; then printf '  PASS  %s\n' "$label"
    else printf '  FAIL  %s\n' "$label"; fail=$((fail+1)); fi
}

[[ -f "$SCRIPT" ]]  || { echo "ENV-ERR: script missing"  >&2; exit 2; }
[[ -f "$FIXTURE" ]] || { echo "ENV-ERR: fixture missing" >&2; exit 2; }

python3 "$SCRIPT" --data "$FIXTURE" --category-col smoking_status \
    --reference-level never --dose-col pack_years --out "$OUT" --strict >/dev/null 2>&1
check "exit 1 under --strict (implied-zero missing present)" test "$?" -eq 1
check "JSON artifact written" test -s "$OUT"

check "implied_zero_missing == 2" python3 -c "
import json; d=json.load(open('$OUT'))
assert d['total_implied_zero_missing']==2, d['total_implied_zero_missing']"
check "implied_zero_nonzero (mislabel) == 1" python3 -c "
import json; d=json.load(open('$OUT'))
assert d['results'][0]['implied_zero_nonzero']==1"
check "implied_zero_ok == 1" python3 -c "
import json; d=json.load(open('$OUT'))
assert d['results'][0]['implied_zero_ok']==1"
check "reference_n == 4 (never-smokers)" python3 -c "
import json; d=json.load(open('$OUT'))
assert d['results'][0]['reference_n']==4"
check "verdict FIX_STRUCTURAL_ZERO" python3 -c "
import json; d=json.load(open('$OUT'))
assert d['results'][0]['verdict']=='FIX_STRUCTURAL_ZERO'"

# Clean case: a reference level with no missing dose -> exit 0 under --strict.
python3 "$SCRIPT" --data "$FIXTURE" --category-col smoking_status \
    --reference-level former --dose-col pack_years --strict >/dev/null 2>&1
check "exit 0 when reference level has no missing dose" test "$?" -eq 0

echo "fail=$fail"; [[ "$fail" -eq 0 ]] && echo "ALL PASS" || echo "FAILURES: $fail"
exit "$fail"
