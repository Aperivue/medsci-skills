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

echo "fail=$fail"; [[ "$fail" -eq 0 ]] && echo "ALL PASS" || echo "FAILURES: $fail"
exit "$fail"
