#!/usr/bin/env bash
# Regression test for the artifact-coverage gate (self-review Phase 2.5f).
# Synthetic, PII-free fixtures reproduce: (a) a Methods-promised multiple-
# imputation analysis that never reaches Results (FORWARD), (b) an analysis-bearing
# output CSV (a DeLong nested added-value table) present on disk but unmentioned in
# the manuscript (REVERSE). The clean manuscript reports both and mentions the disk
# outputs, so it reconciles.
# Stdlib-only (python3).
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$HERE/../scripts/check_artifact_coverage.py"
BAD="$HERE/fixtures/coverage_manuscript.md"
CLEAN="$HERE/fixtures/coverage_clean.md"
ADIR="$HERE/fixtures/coverage_analysis"
OUT="$(mktemp -t cov_XXXX).json"
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

# (1) bad manuscript + analysis dir: promised-absent + disk-unreported, Major -> exit 1
python3 "$SCRIPT" --manuscript "$BAD" --analysis-dir "$ADIR" --out "$OUT" --strict --quiet >/dev/null 2>&1
check "exit 1 under --strict (Major present)" test "$?" -eq 1
check "JSON artifact written" test -s "$OUT"
check "PROMISED_ABSENT detected (MI promised, absent from Results)" has_verdict PROMISED_ABSENT
check "DISK_UNREPORTED detected (delong nested CSV unmentioned)"    has_verdict DISK_UNREPORTED

# (2) clean manuscript: reports MI + sensitivity, mentions disk outputs -> exit 0
python3 "$SCRIPT" --manuscript "$CLEAN" --analysis-dir "$ADIR" --strict --quiet >/dev/null 2>&1
check "exit 0 on clean manuscript (all reconciled)" test "$?" -eq 0

# (3) a bound/ceiling/de-confounded AUC promised "is reported in Table S16" but
#     never given a numeric value anywhere -> PROMISED_STAT_NO_VALUE (Major), exit 1
PS="$HERE/fixtures/coverage_promised_stat.md"
python3 "$SCRIPT" --manuscript "$PS" --out "$OUT" --strict --quiet >/dev/null 2>&1
check "exit 1 (promised stat without a value)" test "$?" -eq 1
check "PROMISED_STAT_NO_VALUE detected" has_verdict PROMISED_STAT_NO_VALUE

# (4) same framing but the de-confounded AUC value (0.71) IS reported -> no fire, exit 0
PSOK="$HERE/fixtures/coverage_promised_stat_ok.md"
python3 "$SCRIPT" --manuscript "$PSOK" --out "$OUT" --quiet >/dev/null 2>&1
check "no PROMISED_STAT_NO_VALUE when the value is reported" python3 -c "
import json
d=json.load(open('$OUT'))
assert not any(c['verdict']=='PROMISED_STAT_NO_VALUE' for c in d['claims']), 'fired despite a reported value'
"
python3 "$SCRIPT" --manuscript "$PSOK" --strict --quiet >/dev/null 2>&1
check "exit 0 when the promised value is present" test "$?" -eq 0

echo "fail=$fail"; [[ "$fail" -eq 0 ]] && echo "ALL PASS" || echo "FAILURES: $fail"
exit "$fail"
