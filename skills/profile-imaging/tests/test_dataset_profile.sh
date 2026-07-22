#!/usr/bin/env bash
# Regression test for the dataset-profile gate (profile-imaging).
# Synthetic, PII-free JSON profiles reproduce each verdict class. Stdlib-only (python3).
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$HERE/../scripts/check_dataset_profile.py"
CH="$HERE/../scripts/check_dataset_profile_challenge"
TMP="$(mktemp -d -t dsprof_XXXX)"
OUT="$TMP/out.json"
trap 'rm -rf "$TMP"' EXIT

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
no_verdict() { python3 -c "
import json
d=json.load(open('$OUT'))
assert not any(c['verdict']=='$1' for c in d['claims']), '$1 unexpectedly present'
"; }

[[ -f "$SCRIPT" ]] || { echo "ENV-ERR: script missing" >&2; exit 2; }

# (1) defect fixture -> every verdict class + exit 1
python3 "$SCRIPT" --profile "$CH/fixture/profile_defect.json" --out "$OUT" --strict --quiet >/dev/null 2>&1
check "exit 1 (defect profile)" test "$?" -eq 1
for v in LABEL_SHAPE_MISMATCH LABEL_EMPTY LABEL_VALUE_UNEXPECTED TEST_SET_UNLABELLED \
         ACCURACY_UNDER_IMBALANCE LABEL_MISSING SPACING_HETEROGENEOUS ORIENTATION_MIXED \
         INTENSITY_SCALE_INCONSISTENT EXTREME_IMBALANCE; do
  check "$v detected" has_verdict "$v"
done

# (2) clean fixture -> exit 0, nothing fires
python3 "$SCRIPT" --profile "$CH/fixture/profile_clean.json" --out "$OUT" --strict --quiet >/dev/null 2>&1
check "exit 0 (clean profile)" test "$?" -eq 0
check "no SPACING_HETEROGENEOUS when resampling declared" no_verdict SPACING_HETEROGENEOUS
check "no ORIENTATION_MIXED when reorientation declared" no_verdict ORIENTATION_MIXED
check "no EXTREME_IMBALANCE when a Dice-family loss is declared" no_verdict EXTREME_IMBALANCE
check "no ACCURACY_UNDER_IMBALANCE when accuracy is not reported" no_verdict ACCURACY_UNDER_IMBALANCE
check "no TEST_SET_UNLABELLED when the held-out split is labelled" no_verdict TEST_SET_UNLABELLED

# (3) thresholds are honoured — a permissive ratio silences the spacing flag
python3 "$SCRIPT" --profile "$CH/fixture/profile_defect.json" --spacing-ratio 99 --out "$OUT" --quiet >/dev/null 2>&1
check "spacing flag silenced by --spacing-ratio 99" no_verdict SPACING_HETEROGENEOUS

# (4) challenge card reproduces
check "challenge card verify.sh" bash "$CH/verify.sh"

echo
if [[ "$fail" -eq 0 ]]; then echo "ALL PASS (dataset-profile gate)"; else echo "$fail FAILURE(S)"; exit 1; fi
