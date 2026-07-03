#!/usr/bin/env bash
# Regression test for the radiomics/classical-ML pipeline-rigor gate (radiomics-ml).
# Synthetic, PII-free JSON manifests reproduce each verdict class + the suppressions.
# Stdlib-only (python3).
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$HERE/../scripts/check_radiomics_ml.py"
CH="$HERE/../scripts/check_radiomics_ml_challenge"
TMP="$(mktemp -d -t radml_XXXX)"
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

# (1) weak fixture -> 3 Major + exit 1
python3 "$SCRIPT" --manifest "$CH/fixture/pipeline_weak.json" --out "$OUT" --strict --quiet >/dev/null 2>&1
check "exit 1 (weak pipeline)" test "$?" -eq 1
check "NO_NESTED_CV detected" has_verdict NO_NESTED_CV
check "HIGH_DIM_LOW_EVENTS detected" has_verdict HIGH_DIM_LOW_EVENTS
check "SELECTION_OUTSIDE_CV detected" has_verdict SELECTION_OUTSIDE_CV
check "NO_FEATURE_STABILITY detected" has_verdict NO_FEATURE_STABILITY
check "NO_CALIBRATION detected" has_verdict NO_CALIBRATION
check "NO_EXTERNAL_VALIDATION detected" has_verdict NO_EXTERNAL_VALIDATION

# (2) strong fixture -> exit 0, no claims
python3 "$SCRIPT" --manifest "$CH/fixture/pipeline_strong.json" --strict --quiet >/dev/null 2>&1
check "exit 0 (strong pipeline)" test "$?" -eq 0

# (3) dimensionality_reduction=true suppresses HIGH_DIM_LOW_EVENTS even when p >= events
cat > "$TMP/dimred.json" <<'EOF'
{"n_features": 1000, "n_events": 30, "cv_scheme": "nested", "feature_selection_stage": "inside_cv",
 "dimensionality_reduction": true, "feature_stability": "icc", "calibration_reported": true,
 "external_validation": "external", "model": "lasso_logistic"}
EOF
python3 "$SCRIPT" --manifest "$TMP/dimred.json" --out "$OUT" --quiet >/dev/null 2>&1
check "dim-reduction suppresses HIGH_DIM_LOW_EVENTS" no_verdict HIGH_DIM_LOW_EVENTS

# (4) single_split is an acceptable validation scheme (no NO_NESTED_CV)
cat > "$TMP/single.json" <<'EOF'
{"n_features": 50, "n_events": 120, "cv_scheme": "single_split", "feature_selection_stage": "inside_cv",
 "dimensionality_reduction": true, "feature_stability": "icc", "calibration_reported": true,
 "external_validation": "temporal", "model": "random_forest"}
EOF
python3 "$SCRIPT" --manifest "$TMP/single.json" --out "$OUT" --quiet >/dev/null 2>&1
check "single_split does NOT fire NO_NESTED_CV" no_verdict NO_NESTED_CV
python3 "$SCRIPT" --manifest "$TMP/single.json" --strict --quiet >/dev/null 2>&1
check "exit 0 on rigorous single-split pipeline" test "$?" -eq 0

# (5) cv_scheme none -> NO_NESTED_CV (no validation at all)
cat > "$TMP/nocv.json" <<'EOF'
{"n_features": 20, "n_events": 200, "cv_scheme": "none", "feature_selection_stage": "inside_cv",
 "dimensionality_reduction": true, "feature_stability": "icc", "calibration_reported": true,
 "external_validation": "external", "model": "xgboost"}
EOF
python3 "$SCRIPT" --manifest "$TMP/nocv.json" --out "$OUT" --quiet >/dev/null 2>&1
check "cv_scheme=none fires NO_NESTED_CV" has_verdict NO_NESTED_CV

# (6) n_events absent -> falls back to n_samples for the dimensionality check
cat > "$TMP/samplesonly.json" <<'EOF'
{"n_features": 500, "n_samples": 60, "cv_scheme": "nested", "feature_selection_stage": "inside_cv",
 "dimensionality_reduction": false, "feature_stability": "icc", "calibration_reported": true,
 "external_validation": "external", "model": "random_forest"}
EOF
python3 "$SCRIPT" --manifest "$TMP/samplesonly.json" --out "$OUT" --quiet >/dev/null 2>&1
check "HIGH_DIM_LOW_EVENTS uses n_samples fallback when n_events missing" has_verdict HIGH_DIM_LOW_EVENTS

# (7) the shipped challenge card passes
check "challenge verify.sh passes" bash "$CH/verify.sh"

echo "fail=$fail"; [[ "$fail" -eq 0 ]] && echo "ALL PASS" || echo "FAILURES: $fail"
exit "$fail"
