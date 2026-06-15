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

# 7. A3 — wide Table 1 with mean±SD group columns and NO p/SMD column: the gate
#    computes SMD itself and still runs. With only 'age' adjusted, the imbalanced
#    metabolic labs flag.
MSFIX="$HERE/fixtures/table1_meansd_wide.csv"
[[ -f "$MSFIX" ]] || { echo "ENV-ERR: mean±SD fixture missing" >&2; exit 2; }
MSOUT="$(mktemp -t cc_ms_XXXX).json"
trap 'rm -f "$OUT" "$DBOUT" "$MSOUT"' EXIT
python3 "$SCRIPT" --table1 "$MSFIX" --adjusted-list "age" --out "$MSOUT" --strict >/dev/null 2>&1
check "exit 1 (mean±SD: SMD computed, imbalanced present)" test "$?" -eq 1
check "smd_source == computed_from_mean_sd" python3 -c "
import json; assert json.load(open('$MSOUT'))['smd_source']=='computed_from_mean_sd'"
check "mean±SD: n_unadjusted_imbalanced == 5" python3 -c "
import json; assert json.load(open('$MSOUT'))['n_unadjusted_imbalanced']==5"
check "age (SMD<0.1) not flagged" python3 -c "
import json
d=json.load(open('$MSOUT'))
assert not any(f['covariate']=='age' for f in d['findings'])"

# 8. A4 — exposure-defining covariates (the exposure's diagnostic criteria) are
#    exempt from the residual-confounding flag; only the non-defining prognostic
#    covariate (fib-4) remains a Major.
python3 "$SCRIPT" --table1 "$MSFIX" --adjusted-list "age" \
    --exposure-defining-list "body mass index, systolic blood pressure, HbA1c, HDL cholesterol" \
    --out "$MSOUT" --strict >/dev/null 2>&1
check "exit 1 (A4: non-defining fib-4 still flags)" test "$?" -eq 1
check "A4: 4 exposure-defining exempt" python3 -c "
import json; assert json.load(open('$MSOUT'))['n_exposure_defining_exempt']==4"
check "A4: only 1 unadjusted-imbalanced (fib-4)" python3 -c "
import json
d=json.load(open('$MSOUT'))
assert d['n_unadjusted_imbalanced']==1
assert any(f['covariate']=='fib-4' and f['verdict']=='UNADJUSTED_IMBALANCED' for f in d['findings'])"
check "A4: defining covariate not a Major" python3 -c "
import json
d=json.load(open('$MSOUT'))
assert all(f['verdict']=='EXPOSURE_DEFINING_EXEMPT' for f in d['findings'] if 'body mass' in f['covariate'])"

# 9. A4 + adjust the non-defining prognostic covariate -> clean (exit 0)
python3 "$SCRIPT" --table1 "$MSFIX" --adjusted-list "age, FIB-4" \
    --exposure-defining-list "body mass index, systolic blood pressure, HbA1c, HDL cholesterol" \
    --strict >/dev/null 2>&1
check "exit 0 when defining exempt + non-defining adjusted" test "$?" -eq 0

echo "ran=$(( ${fail} + 0 )) fail=$fail"
[[ "$fail" -eq 0 ]] && echo "ALL PASS" || echo "FAILURES: $fail"
exit "$fail"
