#!/usr/bin/env bash
# Regression test for the confounding-completeness gate (self-review Phase 2.5e).
# Synthetic, PII-free fixture mirroring the canonical failure pattern: five
# measured covariates imbalanced by exposure (uric acid, pack-years, HDL, total
# cholesterol, HbA1c) that are absent from an age/sex/BMI/HTN/DM adjustment set.
# Stdlib-only (python3); no pandas/statsmodels.
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$HERE/../scripts/check_confounding_completeness.py"
FIXTURE="$HERE/fixtures/table1_by_exposure.csv"
OUT="$(mktemp -t cc_XXXX).json"
trap 'rm -f "$OUT"' EXIT

fail=0
check() {  # check "label" expr...
    local label="$1"; shift
    if "$@" >/dev/null 2>&1; then printf '  PASS  %s\n' "$label"
    else printf '  FAIL  %s\n' "$label"; fail=$((fail+1)); fi
}

[[ -f "$SCRIPT" ]]  || { echo "ENV-ERR: script missing"  >&2; exit 2; }
[[ -f "$FIXTURE" ]] || { echo "ENV-ERR: fixture missing" >&2; exit 2; }

# 1. Runs and writes JSON.
python3 "$SCRIPT" --table1 "$FIXTURE" \
    --adjusted-list "age, sex, BMI, hypertension, diabetes" \
    --out "$OUT" --strict >/dev/null 2>&1
rc=$?
check "exit 1 under --strict (unadjusted-imbalanced present)" test "$rc" -eq 1
check "JSON artifact written" test -s "$OUT"

# 2. Exactly five unadjusted-imbalanced covariates.
n=$(python3 -c "import json,sys; print(json.load(open('$OUT'))['n_unadjusted_imbalanced'])" 2>/dev/null)
check "n_unadjusted_imbalanced == 5" test "$n" = "5"

# 3. Each expected offender flagged; adjusted/balanced ones not.
for cov in "Uric acid" "Smoking, pack-years" "HDL" "Total cholesterol" "HbA1c"; do
    check "flagged: $cov" python3 -c "
import json
d=json.load(open('$OUT'))
assert any('$cov'.lower() in f['covariate'].lower() and f['verdict']=='UNADJUSTED_IMBALANCED' for f in d['findings'])
"
done
for cov in "Age" "BMI"; do
    check "not flagged: $cov" python3 -c "
import json
d=json.load(open('$OUT'))
assert not any('$cov'.lower() in f['covariate'].lower() and f['verdict']=='UNADJUSTED_IMBALANCED' for f in d['findings'])
"
done

# 4. '<0.001' p-value cell parsed as imbalanced (HDL row uses '<0.001').
check "verdict MAJOR_CANDIDATE" python3 -c "
import json; assert json.load(open('$OUT'))['verdict']=='MAJOR_CANDIDATE'
"

# 5. Clean case: adjusting for everything yields exit 0.
python3 "$SCRIPT" --table1 "$FIXTURE" \
    --adjusted-list "age, sex, BMI, hypertension, diabetes, uric acid, smoking, HDL, total cholesterol, HbA1c" \
    --strict >/dev/null 2>&1
check "exit 0 when all imbalanced covariates adjusted" test "$?" -eq 0

# 6. DB-code Table 1 + prose adjustment list: the alias map must resolve he_sbp ~
#    "systolic blood pressure" etc., so adjusted DB-code covariates are NOT
#    false-flagged; only the genuinely unadjusted ones (alcohol/waist/hemoglobin/
#    fasting glucose) remain ✗.
DBFIX="$HERE/fixtures/table1_by_exposure_dbcodes.csv"
[[ -f "$DBFIX" ]] || { echo "ENV-ERR: db-code fixture missing" >&2; exit 2; }
DBOUT="$(mktemp -t cc_db_XXXX).json"
trap 'rm -f "$OUT" "$DBOUT"' EXIT
python3 "$SCRIPT" --table1 "$DBFIX" \
    --adjusted-list "age, sex, body mass index, systolic blood pressure, diastolic blood pressure, total cholesterol, HDL cholesterol, triglycerides, uric acid, HbA1c" \
    --out "$DBOUT" --strict >/dev/null 2>&1
check "exit 1 (db-code: genuine unadjusted present)" test "$?" -eq 1
ndb=$(python3 -c "import json; print(json.load(open('$DBOUT'))['n_unadjusted_imbalanced'])" 2>/dev/null)
check "db-code: n_unadjusted_imbalanced == 4" test "$ndb" = "4"
for cov in he_sbp he_dbp b_chol_t b_chol_hdl b_tg b_uric b_hba1c he_bmi; do
    check "db-code adjusted (alias resolved): $cov" python3 -c "
import json
d=json.load(open('$DBOUT'))
assert any(f['covariate']=='$cov' and f['in_adjustment_set'] for f in d['findings']), '$cov not resolved'
"
done
for cov in alc he_wc he_hb he_glu; do
    check "db-code unadjusted: $cov" python3 -c "
import json
d=json.load(open('$DBOUT'))
assert any(f['covariate']=='$cov' and f['verdict']=='UNADJUSTED_IMBALANCED' for f in d['findings']), '$cov should flag'
"
done

echo "ran=$(( ${fail} + 0 )) fail=$fail"
[[ "$fail" -eq 0 ]] && echo "ALL PASS" || echo "FAILURES: $fail"
exit "$fail"
