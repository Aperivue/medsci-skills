#!/usr/bin/env bash
# Regression tests for meta-analysis check_ratio_ci_symmetry.py (input handling
# and verdict edges; the challenge card covers the positive/negative fixtures).
#   I1-I6 input errors exit 2 naming the problem (missing file, missing column,
#         non-numeric / NaN / blank value, bad ci_level), no traceback.
#   N1    no ratio-measure row -> NOT_ASSESSED, exit 0; --strict exit 2.
#   Z1    a printed 0.00 bound -> RATIO_CI_ASYMMETRY_NOT_ASSESSED (Minor), not
#         Major (0.004 rounds to 0.00), final line "No Major issue".
#   T1    TSV with a UTF-8 BOM and upper-case headers is read.
#   R1    impossibility allows rounding: 1.2 (1.21, 1.50) is possible.
#   I8    ci_level 0.95 (a fraction) exits 2, not a 0.95% CI.
#   O1    --out pointing at a directory exits 2, no traceback.
#   S1    a skipped non-ratio label ("aOR") is named in the summary and on the
#         line before the final OK line.
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
SCRIPT="$REPO_ROOT/skills/meta-analysis/scripts/check_ratio_ci_symmetry.py"
TMP="$(mktemp -d -t ratioci.XXXXXX)"
trap 'rm -rf "$TMP"' EXIT
[[ -f "$SCRIPT" ]] || { echo "ENV-ERR: script missing" >&2; exit 2; }

fail=0
ran=0
check() {  # check LABEL EXPECTED_EXIT ACTUAL_EXIT
    ran=$((ran + 1))
    if [[ "$2" == "$3" ]]; then
        printf '  PASS  %-60s exit=%s\n' "$1" "$3"
    else
        printf '  FAIL  %-60s expected=%s actual=%s\n' "$1" "$2" "$3"
        fail=$((fail + 1))
    fi
}
run() {  # run FILE [flags...] -> exit code in $rc, stdout in $TMP/out, stderr in $TMP/err
    python3 "$SCRIPT" --extraction "$@" --out "$TMP/out.json" > "$TMP/out" 2> "$TMP/err"
    rc=$?
}
no_tb() { if grep -q Traceback "$TMP/err"; then echo "  FAIL  $1: traceback"; fail=$((fail + 1)); fi; }
H='study,measure,estimate,lower,upper'

run "$TMP/nope.csv"; check "I1: missing file" 2 $rc; no_tb I1
printf 'study,measure,estimate,lower\nA,OR,2.00,1.35\n' > "$TMP/i2.csv"
run "$TMP/i2.csv"; check "I2: missing column upper" 2 $rc; no_tb I2
grep -q "upper" "$TMP/err" || { echo "  FAIL  I2: error must name the column"; fail=$((fail + 1)); }
printf '%s\nA,OR,2.00,1.35,about 3\n' "$H" > "$TMP/i3.csv"
run "$TMP/i3.csv"; check "I3: non-numeric upper" 2 $rc; no_tb I3
grep -q "row 2 column upper" "$TMP/err" || { echo "  FAIL  I3: error must name row and column"; fail=$((fail + 1)); }
printf '%s\nA,OR,NaN,1.35,2.96\n' "$H" > "$TMP/i4.csv"
run "$TMP/i4.csv"; check "I4: NaN estimate" 2 $rc; no_tb I4
printf '%s\nA,OR,2.00,,2.96\n' "$H" > "$TMP/i5.csv"
run "$TMP/i5.csv"; check "I5: blank lower on a ratio row" 2 $rc; no_tb I5
printf '%s,ci_level\nA,OR,2.00,1.35,2.96,120\n' "$H" > "$TMP/i6.csv"
run "$TMP/i6.csv"; check "I6: ci_level 120" 2 $rc; no_tb I6
printf '%s\nA,OR,2.00,1.35,%s\n' "$H" "$(printf '9%.0s' $(seq 1 400))" > "$TMP/i7.csv"
run "$TMP/i7.csv"; check "I7: overflowing number" 2 $rc; no_tb I7
printf '%s,ci_level\nA,OR,2.00,1.35,2.96,0.95\n' "$H" > "$TMP/i8.csv"
run "$TMP/i8.csv"; check "I8: ci_level 0.95 (fraction)" 2 $rc; no_tb I8
grep -q "ci_level" "$TMP/err" || { echo "  FAIL  I8: error must name ci_level"; fail=$((fail + 1)); }
printf '%s\nA,OR,2.00,1.35,2.96\n' "$H" > "$TMP/o1.csv"
python3 "$SCRIPT" --extraction "$TMP/o1.csv" --out "$TMP" > "$TMP/out" 2> "$TMP/err"
check "O1: --out is a directory" 2 $?; no_tb O1

printf '%s\nA,OR,2.00,1.35,2.96\nB,aOR,1.50,1.10,2.05\n' "$H" > "$TMP/s1.csv"
run "$TMP/s1.csv" --strict; check "S1: aOR row skipped, OR row OK" 0 $rc
python3 -c "import json,sys; s=json.load(open(sys.argv[1]))['summary']; assert s['skipped_measures']==['aOR'] and s['n_skipped_measure']==1, s" "$TMP/out.json" \
    || { echo "  FAIL  S1: skipped_measures"; fail=$((fail + 1)); }
grep -q '^Skipped 1 row(s) whose measure is not OR/RR/HR/IRR: aOR' "$TMP/out" \
    || { echo "  FAIL  S1: skipped line"; fail=$((fail + 1)); }
tail -n 1 "$TMP/out" | grep -q '^OK:' || { echo "  FAIL  S1: final line"; fail=$((fail + 1)); }

printf '%s\nA,MD,-3.2,-5.1,-1.3\n' "$H" > "$TMP/n1.csv"
run "$TMP/n1.csv"; check "N1: no ratio row (NOT_ASSESSED, exit 0)" 0 $rc
grep -q '^NOT ASSESSED:' "$TMP/out" || { echo "  FAIL  N1: final line"; fail=$((fail + 1)); }
python3 -c "import json,sys; assert json.load(open(sys.argv[1]))['summary']['verdict']=='NOT_ASSESSED'" "$TMP/out.json" \
    || { echo "  FAIL  N1: verdict"; fail=$((fail + 1)); }
run "$TMP/n1.csv" --strict; check "N1: --strict NOT_ASSESSED exits 2" 2 $rc

printf '%s\nA,OR,0.05,0.00,0.90\n' "$H" > "$TMP/z1.csv"
run "$TMP/z1.csv" --strict; check "Z1: printed 0.00 bound (Minor, not Major)" 0 $rc
python3 - "$TMP/out.json" <<'PY' || { echo "  FAIL  Z1: claims"; fail=$((fail + 1)); }
import json, sys
r = json.load(open(sys.argv[1]))
assert [c["verdict"] for c in r["claims"]] == ["RATIO_CI_ASYMMETRY_NOT_ASSESSED"], r["claims"]
assert r["rows"][0]["se_log"] is None and r["summary"]["verdict"] == "OK", r
PY
grep -q '^No Major issue: 1 Minor' "$TMP/out" || { echo "  FAIL  Z1: final line"; fail=$((fail + 1)); }

printf '\xef\xbb\xbfSTUDY\tMeasure\tESTIMATE\tLower\tUpper\nA\thr\t0.59\t0.42\t0.82\n' > "$TMP/t1.tsv"
run "$TMP/t1.tsv" --strict; check "T1: BOM + TSV + header case" 0 $rc
python3 - "$TMP/out.json" <<'PY' || { echo "  FAIL  T1: row read"; fail=$((fail + 1)); }
import json, sys
r = json.load(open(sys.argv[1]))
# R 4.3.3: (log(0.82)-log(0.42))/(2*qnorm(0.975)) = 0.170679062
assert r["summary"]["n_ratio_rows"] == 1 and abs(r["rows"][0]["se_log"] - 0.170679062) < 1e-9, r
PY

printf '%s\nA,OR,1.2,1.21,1.50\n' "$H" > "$TMP/r1.csv"
run "$TMP/r1.csv" --strict; check "R1: 1.2 (1.21, 1.50) possible within rounding" 0 $rc
python3 -c "import json,sys; r=json.load(open(sys.argv[1])); assert not any(c['severity']=='Major' for c in r['claims']), r" "$TMP/out.json" \
    || { echo "  FAIL  R1: Major fired"; fail=$((fail + 1)); }

echo ""
echo "ran=$ran fail=$fail"
[[ $fail -eq 0 ]]
