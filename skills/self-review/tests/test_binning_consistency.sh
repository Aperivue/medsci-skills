#!/usr/bin/env bash
# Regression test for the cross-script binning-consistency gate (Phase 2.5b).
# Synthetic, PII-free fixtures reproduce a derived `age_band` binned with two
# different cut signatures (breaks 45/50/60 right=FALSE vs 44/49/59 right=TRUE)
# across two analysis scripts — a real-world binning bug — and a clean pair that
# shares one identical cut signature.
# Stdlib-only (python3).
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$HERE/../scripts/check_binning_consistency.py"
DRIFT="$HERE/fixtures/binning_drift"
CLEAN="$HERE/fixtures/binning_clean"
OUT="$(mktemp -t bin_XXXX).json"
trap 'rm -f "$OUT"' EXIT

fail=0
check() { local label="$1"; shift
    if "$@" >/dev/null 2>&1; then printf '  PASS  %s\n' "$label"
    else printf '  FAIL  %s\n' "$label"; fail=$((fail+1)); fi
}
has_verdict() { python3 -c "
import json
d=json.load(open('$OUT'))
assert any(c['verdict']=='$1' for c in d['claims']), '$1 not found'
"; }

[[ -f "$SCRIPT" ]] || { echo "ENV-ERR: script missing" >&2; exit 2; }

echo "test_binning_consistency:"

# (1) drift fixtures: BINNING_DRIFT (Major) -> exit 1 under --strict
python3 "$SCRIPT" --root "$DRIFT" --out "$OUT" --strict --quiet >/dev/null 2>&1
check "exit 1 under --strict (Major present)" test "$?" -eq 1
check "JSON artifact written" test -s "$OUT"
check "BINNING_DRIFT detected (45/50/60 right=FALSE vs 44/49/59 right=TRUE)" has_verdict BINNING_DRIFT

# (2) clean fixtures: identical cut signature -> exit 0, no claim
python3 "$SCRIPT" --root "$CLEAN" --strict --quiet >/dev/null 2>&1
check "exit 0 on consistent binning" test "$?" -eq 0
python3 "$SCRIPT" --root "$CLEAN" --out "$OUT" --quiet >/dev/null 2>&1
check "no BINNING_DRIFT on clean fixtures" bash -c "
python3 -c \"import json; d=json.load(open('$OUT')); assert not d['claims']\"
"

if [[ "$fail" -eq 0 ]]; then echo "  ALL PASS"; else echo "  $fail FAILED"; fi
exit "$fail"
