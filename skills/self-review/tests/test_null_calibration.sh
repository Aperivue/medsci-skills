#!/usr/bin/env bash
# Regression test for the null-calibration gate (self-review §C).
# Synthetic, PII-free fixtures: (a) a headline "no synergy / not associated" null
# in the Abstract + Conclusion with no MDE/power/equivalence/CI-compatibility
# statement (CONFIRM_NULL_NO_MDE), (b) the same null but accompanied by a power
# calculation + CI-compatibility sentence (suppressed).
# Stdlib-only (python3).
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$HERE/../scripts/check_null_calibration.py"
BAD="$HERE/fixtures/null_bad.md"
CLEAN="$HERE/fixtures/null_clean.md"
OUT="$(mktemp -t nullcal_XXXX).json"
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

# (1) headline null with no precision statement -> CONFIRM_NULL_NO_MDE, exit 1
python3 "$SCRIPT" --manuscript "$BAD" --out "$OUT" --strict --quiet >/dev/null 2>&1
check "exit 1 under --strict (Major present)" test "$?" -eq 1
check "JSON artifact written" test -s "$OUT"
check "CONFIRM_NULL_NO_MDE detected" has_verdict CONFIRM_NULL_NO_MDE

# (2) same null but with power + CI-compatibility -> suppressed, exit 0
python3 "$SCRIPT" --manuscript "$CLEAN" --out "$OUT" --quiet >/dev/null 2>&1
check "no CONFIRM_NULL_NO_MDE when precision present" python3 -c "
import json
d=json.load(open('$OUT'))
assert not any(c['verdict']=='CONFIRM_NULL_NO_MDE' for c in d['claims']), 'fired despite a precision statement'
"
python3 "$SCRIPT" --manuscript "$CLEAN" --strict --quiet >/dev/null 2>&1
check "exit 0 on power-aware null" test "$?" -eq 0

# (3) region-blind masking: a power/CI caveat co-located with the Abstract-Results
#     null does NOT license a bare "equivalence within the bound" in a far
#     Conclusion -> CONFIRM_NULL_NO_MDE still fires on the uncaveated claim site.
MASKED="$HERE/fixtures/null_region_masked.md"
python3 "$SCRIPT" --manuscript "$MASKED" --out "$OUT" --strict --quiet >/dev/null 2>&1
check "exit 1: masked equivalence in a far Conclusion still flagged" test "$?" -eq 1
check "CONFIRM_NULL_NO_MDE on the uncaveated claim site" has_verdict CONFIRM_NULL_NO_MDE

echo "fail=$fail"; [[ "$fail" -eq 0 ]] && echo "ALL PASS" || echo "FAILURES: $fail"
exit "$fail"
