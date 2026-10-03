#!/usr/bin/env bash
# Regression test for check_reported_p_from_counts.py --tests (declared P-value tests, SR-01).
# Synthetic fixtures only. A declared row's P is recomputed with its declared test and read
# as an interval at its printed precision; P_ALPHA_CROSSING is Major only when the whole
# reported interval and the recomputed P lie on opposite sides of alpha. Without --tests the
# output must be byte-identical to the version before the flag existed
# (fixtures/p_declared_noflag.txt).
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$HERE/../scripts/check_reported_p_from_counts.py"
FX="$HERE/fixtures"
MAN="$FX/p_declared.md"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
OUT="$TMP/out.json"

fail=0
check() { local label="$1"; shift
    if "$@" >/dev/null 2>&1; then printf '  PASS  %s\n' "$label"
    else printf '  FAIL  %s\n' "$label"; fail=$((fail+1)); fi
}
# has <kind> <row label> [detail substring]: a finding of that kind for that row
has() { python3 - "$OUT" "$@" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
kind, row = sys.argv[2], sys.argv[3]
sub = sys.argv[4] if len(sys.argv) > 4 else ""
raise SystemExit(0 if any(f["kind"] == kind and f["detail"].startswith(f"row '{row}'") and sub in f["detail"]
                          for f in d["findings"]) else 1)
PY
}
none_for() { python3 - "$OUT" "$1" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
raise SystemExit(1 if any(f["detail"].startswith(f"row '{sys.argv[2]}'") for f in d["findings"]) else 0)
PY
}

[[ -f "$SCRIPT" ]] || { echo "ENV-ERR: script missing" >&2; exit 2; }

# --- byte-identity without the flag ------------------------------------------
check "no --tests: stdout identical to the pre-flag version" \
    diff <(cd "$HERE" && python3 "$SCRIPT" --manuscript fixtures/p_declared.md) "$FX/p_declared_noflag.txt"
python3 "$SCRIPT" --manuscript "$MAN" --json > "$OUT"
check "no --tests: JSON has no declared_tests key" python3 -c "
import json; d=json.load(open('$OUT')); assert 'declared_tests' not in d and d['verdict']=='OK'"

# --- the full declaration --------------------------------------------------------
python3 "$SCRIPT" --manuscript "$MAN" --tests "$FX/p_tests_declared.json" --json > "$OUT"
python3 "$SCRIPT" --manuscript "$MAN" --tests "$FX/p_tests_declared.json" --strict --quiet
check "declared: exit 1 under --strict (alpha crossing)" test "$?" -eq 1
check "verdict P ALPHA CROSSING" python3 -c "
import json; d=json.load(open('$OUT')); assert d['verdict']=='P ALPHA CROSSING', d['verdict']
assert d['declared_tests']['rows']==18 and d['declared_tests']['alpha']=='0.05'"
check "reported 0.04, chi2 recomputes 0.053 -> P_ALPHA_CROSSING"      has P_ALPHA_CROSSING Diabetes
check "reported 0.08, Fisher recomputes 0.033 -> P_ALPHA_CROSSING (other direction; label case-folded)" \
    has P_ALPHA_CROSSING "STATIN USE"
check "correct row (0.78 vs chi2 0.777) -> no finding"                 none_for female
check "markdown-bold first cell matched; 0.021 vs chi2 0.021 -> no finding" none_for Anemia
check "reported 0.05 straddles alpha -> no crossing"                    none_for "Borderline finding"
check "<0.001 vs 0.0013 (same side of alpha) -> no crossing"            none_for "Prior stroke"
check "0.008 vs 0.011 at alpha 0.05 -> no crossing"                     none_for "Prior MI"
check "missing-data denominator (30 printed as 21.4%) -> P_NOT_ASSESSED" has P_NOT_ASSESSED Smoker "denominator"
check "continuous row -> P_NOT_ASSESSED"                                has P_NOT_ASSESSED "Age, years" "no integer counts"
check "row without a P -> P_NOT_ASSESSED"                               has P_NOT_ASSESSED Insulin "no readable P"
check "adjusted -> P_NOT_ASSESSED, never a crossing"                    has P_NOT_ASSESSED Retinopathy "adjusted"
check "...adjusted row gives no P_ALPHA_CROSSING"                       python3 -c "
import json; d=json.load(open('$OUT'))
assert not any(f['kind']=='P_ALPHA_CROSSING' and 'Retinopathy' in f['detail'] for f in d['findings'])"
check "paired -> P_NOT_ASSESSED"                                        has P_NOT_ASSESSED "Repeat visit" "paired"
check "Total column dropped; Cases vs Controls crossing found"          has P_ALPHA_CROSSING Hypertension "20/100 vs 32/100"
check "Total column dropped; correct row clears"                        none_for Dyslipidemia
check "3-group table -> P_NOT_ASSESSED"                                 has P_NOT_ASSESSED Obesity "3 groups"
check "label in two tables -> P_NOT_ASSESSED (ambiguous)"               has P_NOT_ASSESSED Male "2 table rows"
check "partial label is not a match -> P_NOT_ASSESSED (not found)"      has P_NOT_ASSESSED Statin "no table row"
check "other: -> UNLISTED_METHOD"                                       has UNLISTED_METHOD "Diabetes duration"
check "other: -> P_NOT_ASSESSED"                                        has P_NOT_ASSESSED "Diabetes duration"
check "exactly 3 crossings"                                             python3 -c "
import json; d=json.load(open('$OUT'))
assert sum(f['kind']=='P_ALPHA_CROSSING' for f in d['findings'])==3"
check "existing order-of-magnitude rule unchanged (no P_NOT_REPRODUCIBLE here)" python3 -c "
import json; d=json.load(open('$OUT'))
assert not any(f['kind']=='P_NOT_REPRODUCIBLE' for f in d['findings'])"
python3 "$SCRIPT" --manuscript "$MAN" --tests "$FX/p_tests_declared.json" --quiet
check "crossing without --strict: exit 0" test "$?" -eq 0

# --- a clean declaration ---------------------------------------------------------
python3 "$SCRIPT" --manuscript "$MAN" --tests "$FX/p_tests_clean.json" --strict --json > "$OUT"
check "clean declaration: exit 0 under --strict" test "$?" -eq 0
check "clean declaration: no findings, alpha defaults to 0.05" python3 -c "
import json; d=json.load(open('$OUT')); assert d['findings']==[] and d['declared_tests']['alpha']=='0.05'"

# --- a custom alpha --------------------------------------------------------------
python3 "$SCRIPT" --manuscript "$MAN" --tests "$FX/p_tests_alpha01.json" --strict --json > "$OUT"
check "alpha 0.01: exit 1" test "$?" -eq 1
check "alpha 0.01: 0.008 vs 0.011 -> P_ALPHA_CROSSING"                  has P_ALPHA_CROSSING "Prior MI"
check "alpha 0.01: 0.04 vs 0.053 (both above) -> no finding"            none_for Diabetes
check "alpha 0.01: 0.08 vs 0.033 (both above) -> no finding"            none_for "Statin use"

# --- the existing rule still fires alongside -------------------------------------
CH="$HERE/../scripts/check_reported_p_from_counts_challenge/fixture/p_bad.md"
printf '{"rows":[{"row":"Male","test":"chi2"}]}' > "$TMP/male.json"
python3 "$SCRIPT" --manuscript "$CH" --tests "$TMP/male.json" --json > "$OUT"
check "P_NOT_REPRODUCIBLE still reported with --tests" python3 -c "
import json; d=json.load(open('$OUT')); assert d['verdict']=='NON-REPRODUCIBLE P'
assert any(f['kind']=='P_NOT_REPRODUCIBLE' for f in d['findings'])"

# --- BOM -----------------------------------------------------------------------------
printf '\xef\xbb\xbf{"alpha":0.05,"rows":[{"row":"Female","test":"Chi2"}]}' > "$TMP/bom.json"
python3 "$SCRIPT" --manuscript "$MAN" --tests "$TMP/bom.json" --strict --quiet
check "UTF-8 BOM accepted; test name case-folded" test "$?" -eq 0

# --- exit 2 on every malformed class, never a traceback ------------------------------
R='{"row":"Female","test":"chi2"}'
bad2() { local label="$1" body="$2"
    printf '%s' "$body" > "$TMP/x.json"
    python3 "$SCRIPT" --manuscript "$MAN" --tests "$TMP/x.json" >"$TMP/so" 2>"$TMP/se"
    local rc=$?
    if [[ $rc -eq 2 ]] && ! grep -q Traceback "$TMP/se" && grep -q "error" "$TMP/se"; then
        printf '  PASS  exit 2: %s\n' "$label"
    else printf '  FAIL  exit 2: %s (rc=%s)\n' "$label" "$rc"; head -c 300 "$TMP/se"; fail=$((fail+1)); fi
}
bad2 "invalid JSON"            '{"rows": [}'
bad2 "top level not an object" '[]'
bad2 "unknown top-level key"   "{\"rows\":[$R],\"family\":\"x\"}"
bad2 "rows missing"            '{"alpha":0.05}'
bad2 "rows empty"              '{"rows":[]}'
bad2 "row not an object"       '{"rows":["Female"]}'
bad2 "unknown row key"         '{"rows":[{"row":"Female","test":"chi2","p":0.04}]}'
bad2 "row label empty"         '{"rows":[{"row":" - ","test":"chi2"}]}'
bad2 "row label a number"      '{"rows":[{"row":3,"test":"chi2"}]}'
bad2 "duplicate row label"     '{"rows":[{"row":"Female","test":"chi2"},{"row":"FEMALE","test":"fisher"}]}'
bad2 "test missing"            '{"rows":[{"row":"Female"}]}'
bad2 "test off the allow-list" '{"rows":[{"row":"Female","test":"t-test"}]}'
bad2 "other: without description" '{"rows":[{"row":"Female","test":"other:"}]}'
bad2 "alpha a string"          "{\"alpha\":\"0.05\",\"rows\":[$R]}"
bad2 "alpha a boolean"         "{\"alpha\":true,\"rows\":[$R]}"
bad2 "alpha 0"                 "{\"alpha\":0,\"rows\":[$R]}"
bad2 "alpha 1"                 "{\"alpha\":1,\"rows\":[$R]}"
bad2 "alpha 1.5"               "{\"alpha\":1.5,\"rows\":[$R]}"
bad2 "alpha 1e999"             "{\"alpha\":1e999,\"rows\":[$R]}"
bad2 "alpha NaN"               "{\"alpha\":NaN,\"rows\":[$R]}"
bad2 "alpha -Infinity"         "{\"alpha\":-Infinity,\"rows\":[$R]}"
bad2 "alpha huge integer"      "{\"alpha\":$(python3 -c 'print("9"*5000)'),\"rows\":[$R]}"
bad2 "deep nesting"            "$(python3 -c 'print("{\"rows\":" + "["*100000 + "]"*100000 + "}")')"
python3 "$SCRIPT" --manuscript "$MAN" --tests "$TMP/nope.json" >/dev/null 2>&1
check "missing tests file: exit 2" test "$?" -eq 2

echo "fail=$fail"; [[ "$fail" -eq 0 ]] && echo "ALL PASS" || echo "FAILURES: $fail"
exit "$fail"
