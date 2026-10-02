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

# F4 regression: a non-numeric ("unknown") or negative sentinel (-9/-99) dose at
# the reference level is not a valid zero. It used to be skipped uncounted or
# counted as ok, giving a clean verdict and exit 0 under --strict.
SENT="$HERE/fixtures/smoking_sentinel.csv"
OUT2="$(mktemp -t sz_XXXX).json"
trap 'rm -f "$OUT" "$OUT2"' EXIT
python3 "$SCRIPT" --data "$SENT" --category-col smoking_status \
    --reference-level never --dose-col pack_years --out "$OUT2" --strict >/dev/null 2>&1
check "sentinel/unparseable dose at reference level -> exit 1 under --strict" test "$?" -eq 1
check "implied_zero_invalid == 3, ok == 1, counts sum to reference_n" python3 -c "
import json; r=json.load(open('$OUT2'))['results'][0]
assert r['implied_zero_invalid']==3 and r['implied_zero_ok']==1, r
assert r['implied_zero_missing']+r['implied_zero_nonzero']+r['implied_zero_invalid']+r['implied_zero_ok']==r['reference_n'], r"
check "verdict REVIEW_INVALID_DOSE" python3 -c "
import json; assert json.load(open('$OUT2'))['results'][0]['verdict']=='REVIEW_INVALID_DOSE'"

# Negative control: all reference-level doses are valid zeros (0 / 0.0); an
# unparseable dose at a NON-reference level is out of scope -> still clean.
python3 "$SCRIPT" --data "$HERE/fixtures/smoking_clean.csv" --category-col smoking_status \
    --reference-level never --dose-col pack_years --strict >/dev/null 2>&1
check "exit 0 when every reference-level dose is a valid zero" test "$?" -eq 0

echo "fail=$fail"; [[ "$fail" -eq 0 ]] && echo "ALL PASS" || echo "FAILURES: $fail"
exit "$fail"
