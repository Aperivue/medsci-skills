#!/usr/bin/env bash
# Regression test for the reverse-coded-item / negative-alpha detector.
# Synthetic fixture: a 3-item scale where E3 is reverse-worded (stored 6-x) so the
# raw alpha is negative and E3 has a negative item-rest correlation; plus a clean
# 3-item scale (G1-G3) that should pass. Stdlib-only (python3).
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$HERE/../scripts/check_reverse_coding.py"
FIXTURE="$HERE/fixtures/scale_reverse.csv"
OUT="$(mktemp -t rc_XXXX).json"
trap 'rm -f "$OUT"' EXIT

fail=0
check() { local label="$1"; shift
    if "$@" >/dev/null 2>&1; then printf '  PASS  %s\n' "$label"
    else printf '  FAIL  %s\n' "$label"; fail=$((fail+1)); fi
}

[[ -f "$SCRIPT" ]]  || { echo "ENV-ERR: script missing"  >&2; exit 2; }
[[ -f "$FIXTURE" ]] || { echo "ENV-ERR: fixture missing" >&2; exit 2; }

# Reverse-coded scale: must flag under --strict (exit 1) and write the report.
python3 "$SCRIPT" --data "$FIXTURE" --items E1 E2 E3 --out "$OUT" --strict >/dev/null 2>&1
check "exit 1 under --strict (reverse coding present)" test "$?" -eq 1
check "JSON artifact written" test -s "$OUT"

check "verdict REVERSE_CODING_LIKELY" python3 -c "
import json; d=json.load(open('$OUT'))
assert d['verdict']=='REVERSE_CODING_LIKELY', d['verdict']"
check "alpha_raw is negative" python3 -c "
import json; d=json.load(open('$OUT'))
assert d['alpha_raw'] is not None and d['alpha_raw']<0, d['alpha_raw']"
check "E3 is the sole suspect" python3 -c "
import json; d=json.load(open('$OUT'))
assert d['suspects']==['E3'], d['suspects']"
check "E3 item-rest r is negative" python3 -c "
import json; d=json.load(open('$OUT'))
r={it['item']:it['item_rest_r'] for it in d['per_item']}
assert r['E3']<0 and r['E1']>0 and r['E2']>0, r"
check "n_complete == 8" python3 -c "
import json; d=json.load(open('$OUT'))
assert d['n_complete']==8, d['n_complete']"

# Clean scale: no reverse item -> verdict OK, exit 0 under --strict.
python3 "$SCRIPT" --data "$FIXTURE" --items G1 G2 G3 --out "$OUT" --strict >/dev/null 2>&1
check "exit 0 on a clean (aligned) scale" test "$?" -eq 0
check "verdict OK on clean scale" python3 -c "
import json; d=json.load(open('$OUT'))
assert d['verdict']=='OK' and not d['suspects'], d"

# Usage guard: a single item is not a scale.
python3 "$SCRIPT" --data "$FIXTURE" --items E1 >/dev/null 2>&1
check "exit 2 on <2 items (usage error)" test "$?" -eq 2

echo "fail=$fail"; [[ "$fail" -eq 0 ]] && echo "ALL PASS" || echo "FAILURES: $fail"
exit "$fail"
