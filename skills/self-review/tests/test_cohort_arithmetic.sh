#!/usr/bin/env bash
# Regression test for the cohort-arithmetic gate (self-review Phase 2.5 / 2.5b).
# Synthetic, PII-free fixtures reproduce: (a) an incidence rate that does not
# recompute from its events/person-years, (b) a complete-case footnote that does
# not balance (total - missing != complete), (c) an ordinal tier partition whose
# stratum denominators and events sum above the stated total.
# Stdlib-only (python3).
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$HERE/../scripts/check_cohort_arithmetic.py"
BAD="$HERE/fixtures/cohort_bad.md"
CLEAN="$HERE/fixtures/cohort_clean.md"
PART="$HERE/fixtures/cohort_partition.csv"
OUT="$(mktemp -t coh_XXXX).json"
trap 'rm -f "$OUT"' EXIT

fail=0
check() { local label="$1"; shift
    if "$@" >/dev/null 2>&1; then printf '  PASS  %s\n' "$label"
    else printf '  FAIL  %s\n' "$label"; fail=$((fail+1)); fi
}
has_verdict() { python3 -c "
import json,sys
d=json.load(open('$OUT'))
assert any(c['verdict']=='$1' for c in d['claims']), '$1 not found'
"; }

[[ -f "$SCRIPT" ]] || { echo "ENV-ERR: script missing" >&2; exit 2; }

# (1) bad manuscript: all three discrepancies, Major present -> exit 1 under --strict
python3 "$SCRIPT" --manuscript "$BAD" --out "$OUT" --strict --quiet >/dev/null 2>&1
check "exit 1 under --strict (Major present)" test "$?" -eq 1
check "JSON artifact written" test -s "$OUT"
check "RATE_BACKCALC detected (5.0 vs 120/50000*1000=2.4)" has_verdict RATE_BACKCALC
check "CASCADE_SUM detected (4252-583=3669 != 3667)"       has_verdict CASCADE_SUM
check "PARTITION_OVERLAP detected (sum 12498 != 12019)"     has_verdict PARTITION_OVERLAP

# (2) clean manuscript: everything balances -> exit 0
python3 "$SCRIPT" --manuscript "$CLEAN" --strict --quiet >/dev/null 2>&1
check "exit 0 on clean manuscript (all arithmetic balances)" test "$?" -eq 0

# (3) --data CSV partition: stratum n sum above total -> PARTITION_OVERLAP, exit 1
python3 "$SCRIPT" --manuscript "$CLEAN" --data "$PART" --out "$OUT" --strict --quiet >/dev/null 2>&1
check "exit 1 with overlapping --data partition CSV" test "$?" -eq 1
check "PARTITION_OVERLAP from --data CSV" has_verdict PARTITION_OVERLAP

echo "fail=$fail"; [[ "$fail" -eq 0 ]] && echo "ALL PASS" || echo "FAILURES: $fail"
exit "$fail"
