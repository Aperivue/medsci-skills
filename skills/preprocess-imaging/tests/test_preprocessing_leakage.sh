#!/usr/bin/env bash
# Regression test for the preprocessing-leakage gate (preprocess-imaging).
# Synthetic, PII-free JSON manifests reproduce each verdict class. Stdlib-only (python3).
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$HERE/../scripts/check_preprocessing_leakage.py"
CH="$HERE/../scripts/check_preprocessing_leakage_challenge"
TMP="$(mktemp -d -t preproc_XXXX)"
OUT="$TMP/out.json"
trap 'rm -rf "$TMP"' EXIT

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
no_verdict() { python3 -c "
import json,sys
d=json.load(open('$OUT'))
assert not any(c['verdict']=='$1' for c in d['claims']), '$1 unexpectedly present'
"; }

[[ -f "$SCRIPT" ]] || { echo "ENV-ERR: script missing" >&2; exit 2; }

# (1) leak fixture -> 3 Major verdicts + exit 1
python3 "$SCRIPT" --manifest "$CH/fixture/manifest_leak.json" --out "$OUT" --strict --quiet >/dev/null 2>&1
check "exit 1 (leak manifest)" test "$?" -eq 1
check "PREPROCESS_BEFORE_SPLIT detected" has_verdict PREPROCESS_BEFORE_SPLIT
check "NORMALIZATION_LEAKAGE detected" has_verdict NORMALIZATION_LEAKAGE
check "PATIENT_CROSS_SPLIT detected" has_verdict PATIENT_CROSS_SPLIT
check "AUGMENTATION_ON_EVAL detected" has_verdict AUGMENTATION_ON_EVAL

# (2) clean fixture -> exit 0, no Major
python3 "$SCRIPT" --manifest "$CH/fixture/manifest_clean.json" --strict --quiet >/dev/null 2>&1
check "exit 0 (clean manifest)" test "$?" -eq 0

# (3) data-fitted transform after split with NO fit_scope -> Minor UNSPECIFIED_FIT_SCOPE, exit 0
cat > "$TMP/unspec.json" <<'EOF'
{"split_seed": 1,
 "transforms": [{"name": "scaler", "type": "minmax", "stage": "after_split"}],
 "split_assignment": [{"patient_id": "A", "split": "train"}, {"patient_id": "B", "split": "test"}]}
EOF
python3 "$SCRIPT" --manifest "$TMP/unspec.json" --out "$OUT" --quiet >/dev/null 2>&1
check "UNSPECIFIED_FIT_SCOPE detected" has_verdict UNSPECIFIED_FIT_SCOPE
python3 "$SCRIPT" --manifest "$TMP/unspec.json" --strict --quiet >/dev/null 2>&1
check "unspecified-scope is Minor (exit 0 under --strict)" test "$?" -eq 0

# (4) split present but no split_seed -> Minor MISSING_SEED
cat > "$TMP/noseed.json" <<'EOF'
{"transforms": [{"name": "z", "type": "standardize", "fit_scope": "train", "stage": "after_split"}],
 "split_assignment": [{"patient_id": "A", "split": "train"}, {"patient_id": "B", "split": "test"}]}
EOF
python3 "$SCRIPT" --manifest "$TMP/noseed.json" --out "$OUT" --quiet >/dev/null 2>&1
check "MISSING_SEED detected" has_verdict MISSING_SEED

# (5) per-image normalisation BEFORE split -> NOT a leak (sample scope is leakage-free)
cat > "$TMP/persample.json" <<'EOF'
{"split_seed": 3,
 "transforms": [{"name": "perimg", "type": "normalization", "fit_scope": "sample", "stage": "before_split"}],
 "split_assignment": [{"patient_id": "A", "split": "train"}, {"patient_id": "B", "split": "test"}]}
EOF
python3 "$SCRIPT" --manifest "$TMP/persample.json" --out "$OUT" --quiet >/dev/null 2>&1
check "per-image transform before split does NOT fire PREPROCESS_BEFORE_SPLIT" no_verdict PREPROCESS_BEFORE_SPLIT
python3 "$SCRIPT" --manifest "$TMP/persample.json" --strict --quiet >/dev/null 2>&1
check "exit 0 on per-image-safe manifest" test "$?" -eq 0

# (6) the shipped challenge card passes
check "challenge verify.sh passes" bash "$CH/verify.sh"

echo "fail=$fail"; [[ "$fail" -eq 0 ]] && echo "ALL PASS" || echo "FAILURES: $fail"
exit "$fail"
