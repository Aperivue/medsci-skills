#!/usr/bin/env bash
# Regression test for the radiomics/classical-ML pipeline-rigor gate (radiomics-ml).
# Synthetic, PII-free JSON manifests reproduce each verdict class + the suppressions.
# Stdlib-only (python3), except check (8), which executes the guide's scikit-learn skeleton.
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

# Helpers for the cases below. gate deletes $OUT first, so a crash cannot leave a previous case's
# JSON to be asserted; callers check its exit code.
gate() { local f="$1"; shift; rm -f "$OUT"
    python3 "$SCRIPT" --manifest "$f" --out "$OUT" --quiet "$@" >/dev/null 2>&1; }
# mk NAME 'python dict': the SKILL.md Phase 3 example (clean) with the given keys changed
# (a value of None removes the key).
mk() { python3 -c "
import json
m = {'task': 'classification', 'n_features': 40, 'n_samples': 300, 'n_events': 110,
     'cv_scheme': 'nested', 'feature_selection_stage': 'inside_cv',
     'dimensionality_reduction': True, 'feature_stability': 'icc', 'calibration_reported': True,
     'external_validation': 'temporal', 'model': 'xgboost'}
for k, v in ($2).items():
    if v is None: m.pop(k, None)
    else: m[k] = v
json.dump(m, open('$TMP/$1.json', 'w'))
"; }
only_verdict() { python3 -c "
import json
d = json.load(open('$OUT'))
v = [c['verdict'] for c in d['claims']]
assert v == ['$1'], v
"; }
no_claims() { python3 -c "
import json
d = json.load(open('$OUT'))
assert d['claims'] == [], d['claims']
"; }

# (3) dimensionality_reduction=true does NOT clear HIGH_DIM_LOW_EVENTS: n_features counts the
#     candidates left after outcome-blind reduction, and LASSO does not rescue 1000 features on
#     30 events (SKILL.md failure mode 2).
cat > "$TMP/dimred.json" <<'EOF'
{"n_features": 1000, "n_events": 30, "cv_scheme": "nested", "feature_selection_stage": "inside_cv",
 "dimensionality_reduction": true, "feature_stability": "icc", "calibration_reported": true,
 "external_validation": "external", "model": "lasso_logistic"}
EOF
gate "$TMP/dimred.json" --strict
check "dim-reduction flag does not clear 1000 features / 30 events (exit 1)" test "$?" -eq 1
check "dim-reduction flag: HIGH_DIM_LOW_EVENTS still fires" has_verdict HIGH_DIM_LOW_EVENTS
detail_no_rescue() { python3 -c "
import json
d = json.load(open('$OUT'))
m = [c['detail'] for c in d['claims'] if c['verdict'] == 'HIGH_DIM_LOW_EVENTS'][0]
assert 'does not clear' in m and 'with no dimensionality reduction' not in m, m
"; }
check "dim-reduction flag: detail says the flag does not clear it" detail_no_rescue
mk dimred_neg "{}"
gate "$TMP/dimred_neg.json" --strict
check "control: 40 candidates / 110 events (dim-reduction on) exits 0" test "$?" -eq 0
check "control: 40 candidates / 110 events -> no claims" no_claims

# (3b) feature_selection_stage must be shown to be in-fold: missing, separator variants of
#      outside_cv, and unrecognised values all fire SELECTION_OUTSIDE_CV (Major).
i=0
for v in None "'outside-cv'" "'whole-dataset'" "'before cv'" "'all data'" "'sometime'"; do
  i=$((i+1)); mk "sel_pos_$i" "{'feature_selection_stage': $v}"
  gate "$TMP/sel_pos_$i.json" --strict
  check "feature_selection_stage=$v exits 1" test "$?" -eq 1
  check "feature_selection_stage=$v -> SELECTION_OUTSIDE_CV only" only_verdict SELECTION_OUTSIDE_CV
done
i=0
for v in "'inside-cv'" "'Inside CV'" "'none'"; do
  i=$((i+1)); mk "sel_neg_$i" "{'feature_selection_stage': $v}"
  gate "$TMP/sel_neg_$i.json" --strict
  check "control: feature_selection_stage=$v exits 0" test "$?" -eq 0
  check "control: feature_selection_stage=$v -> no claims" no_claims
done

# (3c) stability / external validation use positive allow-lists: a value that is not ICC /
#      test-retest, or not external / temporal / geographic, is flagged.
i=0
for v in "'not_assessed'" "'planned'"; do
  i=$((i+1)); mk "stab_pos_$i" "{'feature_stability': $v}"
  gate "$TMP/stab_pos_$i.json"
  check "feature_stability=$v exits 0 (Minor)" test "$?" -eq 0
  check "feature_stability=$v -> NO_FEATURE_STABILITY only" only_verdict NO_FEATURE_STABILITY
done
i=0
for v in "'internal'" "'bootstrap'" "'random_split'"; do
  i=$((i+1)); mk "ext_pos_$i" "{'external_validation': $v}"
  gate "$TMP/ext_pos_$i.json"
  check "external_validation=$v exits 0 (Minor)" test "$?" -eq 0
  check "external_validation=$v -> NO_EXTERNAL_VALIDATION only" only_verdict NO_EXTERNAL_VALIDATION
done
i=0
for kv in "'feature_stability': 'test-retest'" "'feature_stability': 'ICC'" \
          "'external_validation': 'External'" "'external_validation': 'geographic'"; do
  i=$((i+1)); mk "se_neg_$i" "{$kv}"
  gate "$TMP/se_neg_$i.json" --strict
  check "control: {$kv} exits 0" test "$?" -eq 0
  check "control: {$kv} -> no claims" no_claims
done

# (3d) count fields: non-integer / bool / negative counts and n_events > n_samples are input
#      errors (exit 2), never a silent skip; 0 events and a majority-class n_events still fire.
i=0
for d in "{'n_features': '1200', 'n_events': 40}" "{'n_events': '40', 'n_samples': 2000}" \
         "{'n_events': True}" "{'n_features': -5}" "{'n_features': 0}" "{'n_samples': 50}"; do
  i=$((i+1)); mk "cnt_err_$i" "$d"
  gate "$TMP/cnt_err_$i.json"
  check "count input error $d exits 2" test "$?" -eq 2
done
mk cnt_zero "{'n_features': 1200, 'n_events': 0}"
gate "$TMP/cnt_zero.json" --strict
check "n_events=0 with 1200 features exits 1" test "$?" -eq 1
check "n_events=0 -> HIGH_DIM_LOW_EVENTS only" only_verdict HIGH_DIM_LOW_EVENTS
mk cnt_major "{'n_features': 200, 'n_events': 250, 'n_samples': 300}"
gate "$TMP/cnt_major.json" --strict
check "250/300 events uses minority count 50 vs 200 features (exit 1)" test "$?" -eq 1
check "250/300 events -> HIGH_DIM_LOW_EVENTS only" only_verdict HIGH_DIM_LOW_EVENTS
mk cnt_neg "{'n_events': 190}"
gate "$TMP/cnt_neg.json" --strict
check "control: 190/300 events (minority 110) vs 40 features exits 0" test "$?" -eq 0
check "control: 190/300 events -> no claims" no_claims
mk cnt_float "{'n_features': 40.0}"
gate "$TMP/cnt_float.json" --strict
check "control: integral float n_features=40.0 accepted (exit 0)" test "$?" -eq 0

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
# the p >= events rule is a floor: its message must send the user to a sample-size calculation
# and must not present LASSO/PCA as the cure for a small sample (Riley et al. 2020, 2021)
detail_sizes_study() { python3 -c "
import json
d = json.load(open('$OUT'))
m = [c['detail'] for c in d['claims'] if c['verdict'] == 'HIGH_DIM_LOW_EVENTS'][0]
assert 'pmsampsize' in m and 'not a sample-size criterion' in m, m
assert 'apply LASSO' not in m, m
"; }
check "HIGH_DIM_LOW_EVENTS detail points to pmsampsize, not LASSO as a cure" detail_sizes_study

# (7) the shipped challenge card passes
check "challenge verify.sh passes" bash "$CH/verify.sh"

# (8) the guide's nested-CV skeleton, executed on synthetic lesion-level null data, keeps each
#     patient in one outer fold and does not report patient identity as signal. Needs sklearn:
#     SKIP locally without it, hard error when CI is set.
if ! python3 "$HERE/nested_cv_skeleton_check.py" 2>"$TMP/skeleton.err"; then
  printf '  FAIL  nested-CV skeleton check\n'; tail -5 "$TMP/skeleton.err" | sed 's/^/        /'
  fail=$((fail+1))
fi

echo "fail=$fail"; [[ "$fail" -eq 0 ]] && echo "ALL PASS" || echo "FAILURES: $fail"
exit "$fail"
