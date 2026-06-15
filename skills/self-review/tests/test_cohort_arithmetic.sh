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

# (4) analysis-unit: 10 records / 7 subjects + manuscript that discloses neither
#     the analysis unit nor a one-record-per-subject sensitivity -> ANALYSIS_UNIT_
#     UNDISCLOSED (auto-detected 'mockid' column), exit 1.
REPEAT="$HERE/fixtures/cohort_repeat_subjects.csv"
UNDISC="$HERE/fixtures/cohort_unit_undisclosed.md"
DISC="$HERE/fixtures/cohort_unit_disclosed.md"
python3 "$SCRIPT" --manuscript "$UNDISC" --data "$REPEAT" --out "$OUT" --strict --quiet >/dev/null 2>&1
check "exit 1 (analysis unit undisclosed, auto-detect)" test "$?" -eq 1
check "ANALYSIS_UNIT_UNDISCLOSED detected" has_verdict ANALYSIS_UNIT_UNDISCLOSED
check "reconciliation reports 7 unique subjects" python3 -c "
import json
d=json.load(open('$OUT'))
c=next(c for c in d['claims'] if c['verdict']=='ANALYSIS_UNIT_UNDISCLOSED')
assert 'unique_subjects=7' in c['detail'] and 'max_visits=3' in c['detail'], c['detail']
"

# (5) explicit --id-col also fires
python3 "$SCRIPT" --manuscript "$UNDISC" --data "$REPEAT" --id-col mockid --out "$OUT" --strict --quiet >/dev/null 2>&1
check "exit 1 (analysis unit, explicit --id-col)" test "$?" -eq 1

# (6) disclosed manuscript (states analysis unit + first-visit sensitivity) -> no fire
python3 "$SCRIPT" --manuscript "$DISC" --data "$REPEAT" --strict --quiet >/dev/null 2>&1
check "exit 0 when analysis unit disclosed" test "$?" -eq 0

echo "fail=$fail"; [[ "$fail" -eq 0 ]] && echo "ALL PASS" || echo "FAILURES: $fail"
exit "$fail"
