#!/usr/bin/env bash
# Regression test for check_claim_artifact.py --evalues (declared E-values, SR-02).
# Synthetic fixtures only. Each declared E-value is recomputed (VanderWeele-Ding) from its
# declared RR and CI over the printed precision of every number; a Major fires only when the
# recomputed and declared intervals cannot meet. Without --evalues the output must be
# byte-identical to the version before the flag existed (fixtures/evalue_noflag.txt).
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$HERE/../scripts/check_claim_artifact.py"
FX="$HERE/fixtures"
MAN="$FX/evalue_manuscript.md"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
OUT="$TMP/out.json"

fail=0
check() { local label="$1"; shift
    if "$@" >/dev/null 2>&1; then printf '  PASS  %s\n' "$label"
    else printf '  FAIL  %s\n' "$label"; fail=$((fail+1)); fi
}
# verdict_is <claim_id> <verdict>: that claim exists with that verdict
verdict_is() { python3 - "$OUT" "$1" "$2" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
raise SystemExit(0 if any(c["claim_id"] == sys.argv[2] and c["verdict"] == sys.argv[3]
                          for c in d["claims"]) else 1)
PY
}
count_verdict() { python3 - "$OUT" "$1" "$2" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
n = sum(1 for c in d["claims"] if c["verdict"] == sys.argv[2])
raise SystemExit(0 if n == int(sys.argv[3]) else 1)
PY
}
run() { python3 "$SCRIPT" --manuscript "$MAN" --evalues "$1" --out "$OUT" --strict >/dev/null 2>&1; echo $?; }

[[ -f "$SCRIPT" ]] || { echo "ENV-ERR: script missing" >&2; exit 2; }

# --- byte-identity without the flag ------------------------------------------
check "no --evalues: stdout identical to the pre-flag version" \
    diff <(python3 "$SCRIPT" --manuscript "$MAN") "$FX/evalue_noflag.txt"
python3 "$SCRIPT" --manuscript "$MAN" --out "$OUT" >/dev/null 2>&1
check "no --evalues: JSON has no 'evalues' key and no declared claims" python3 -c "
import json; d=json.load(open('$OUT'))
assert 'evalues' not in d and not any(c['type']=='evalue_declared' for c in d['claims'])"

# --- correct declarations pass (rounding-safe) -------------------------------
rc=$(run "$FX/evalues_good.json")
check "good: exit 0 under --strict" test "$rc" -eq 0
check "RR 1.52 -> declared E 2.42 passes (2.41 from the printed RR; 2.42 within rounding)" \
    verdict_is EVDECL-primary-point OK
check "string trailing zeros: CI E-value \"1.70\" from ci_low \"1.20\" passes" verdict_is EVDECL-primary-ci OK
check "string \"1.920\" matches text 1.92 and recomputes" verdict_is EVDECL-secondary-point OK
check "CI including 1: declared \"1.00\" passes" verdict_is EVDECL-secondary-ci OK
check "protective RR 0.70: point E 2.21 passes" verdict_is EVDECL-protective-point OK
check "protective RR 0.70: CI E from ci_high 0.89 (1.50) passes" verdict_is EVDECL-protective-ci OK
check "good: no EVALUE_DECLARED_NOT_IN_TEXT" count_verdict EVALUE_DECLARED_NOT_IN_TEXT 0
check "the prose E-value scan still runs alongside (EVAL-3)" verdict_is EVAL-3 OK
check "JSON records the evalues path" python3 -c "
import json; d=json.load(open('$OUT')); assert d['evalues'].endswith('evalues_good.json')"

# --- wrong declarations are Major --------------------------------------------
rc=$(run "$FX/evalues_bad.json")
check "bad: exit 1 under --strict" test "$rc" -eq 1
check "point E 3.10 from RR 1.52 -> EVALUE_DECLARED_MISMATCH" verdict_is EVDECL-point-wrong-point EVALUE_DECLARED_MISMATCH
check "CI E 2.42 (the point value) -> EVALUE_DECLARED_MISMATCH" verdict_is EVDECL-ci-wrong-ci EVALUE_DECLARED_MISMATCH
check "CI spanning 1 with CI E 1.50 -> EVALUE_DECLARED_MISMATCH" verdict_is EVDECL-ci-spans-null-ci EVALUE_DECLARED_MISMATCH
check "point E 2.42 in the same entry stays OK" verdict_is EVDECL-ci-wrong-point OK
check "3.10 absent from the text -> EVALUE_DECLARED_NOT_IN_TEXT" verdict_is EVDECL-point-wrong EVALUE_DECLARED_NOT_IN_TEXT
check "exactly 3 Majors" python3 -c "
import json; d=json.load(open('$OUT')); assert d['summary']['n_major']==3, d['summary']"
python3 "$SCRIPT" --manuscript "$MAN" --evalues "$FX/evalues_bad.json" >/dev/null 2>&1
check "bad without --strict: exit 0 (report only)" test "$?" -eq 0

# --- other: measure ------------------------------------------------------------
rc=$(run "$FX/evalues_other.json")
check "other: exit 0 under --strict (no Major from an unrecomputable measure)" test "$rc" -eq 0
check "other: UNLISTED_METHOD" verdict_is EVDECL-hr UNLISTED_METHOD
check "other: EVALUE_DECLARED_NOT_ASSESSED" verdict_is EVDECL-hr EVALUE_DECLARED_NOT_ASSESSED
check "other: presence check still runs (NOT_IN_TEXT)" verdict_is EVDECL-hr EVALUE_DECLARED_NOT_IN_TEXT

# --- BOM and a minimal entry ---------------------------------------------------
printf '\xef\xbb\xbf{"entries":[{"id":"a","measure":"rr","estimate":1.52,"ci_low":1.2,"ci_high":1.93,"evalue_point":2.41}]}' > "$TMP/bom.json"
rc=$(run "$TMP/bom.json")
check "UTF-8 BOM accepted; evalue_ci optional" test "$rc" -eq 0
check "...and no CI claim without evalue_ci" python3 -c "
import json; d=json.load(open('$OUT')); assert not any(c['claim_id']=='EVDECL-a-ci' for c in d['claims'])"

# --- exit 2 on every malformed class, never a traceback ------------------------
E='"id":"a","measure":"rr","estimate":1.52,"ci_low":1.2,"ci_high":1.93,"evalue_point":2.41'
bad2() { local label="$1" body="$2"
    printf '%s' "$body" > "$TMP/x.json"
    python3 "$SCRIPT" --manuscript "$MAN" --evalues "$TMP/x.json" >"$TMP/so" 2>"$TMP/se"
    local rc=$?
    if [[ $rc -eq 2 ]] && ! grep -q Traceback "$TMP/se" && grep -q "ERROR" "$TMP/se"; then
        printf '  PASS  exit 2: %s\n' "$label"
    else printf '  FAIL  exit 2: %s (rc=%s)\n' "$label" "$rc"; head -c 300 "$TMP/se"; fail=$((fail+1)); fi
}
bad2 "invalid JSON"               '{"entries": [}'
bad2 "top level not an object"     '[1, 2]'
bad2 "unknown top-level key"       "{\"entries\":[{$E}],\"extra\":1}"
bad2 "entries missing"             '{"notes":"x"}'
bad2 "entries empty"               '{"entries":[]}'
bad2 "entry not an object"         '{"entries":["a"]}'
bad2 "unknown entry key"           "{\"entries\":[{$E,\"p\":0.01}]}"
bad2 "id empty"                    '{"entries":[{"id":" ","measure":"rr","estimate":1.52,"ci_low":1.2,"ci_high":1.93,"evalue_point":2.41}]}'
bad2 "id a number"                 '{"entries":[{"id":3,"measure":"rr","estimate":1.52,"ci_low":1.2,"ci_high":1.93,"evalue_point":2.41}]}'
bad2 "measure OR (no stated conversion)" '{"entries":[{"id":"a","measure":"or","estimate":1.52,"ci_low":1.2,"ci_high":1.93,"evalue_point":2.41}]}'
bad2 "measure HR"                  '{"entries":[{"id":"a","measure":"HR","estimate":1.52,"ci_low":1.2,"ci_high":1.93,"evalue_point":2.41}]}'
bad2 "other: without description"  '{"entries":[{"id":"a","measure":"other: ","estimate":1.52,"ci_low":1.2,"ci_high":1.93,"evalue_point":2.41}]}'
bad2 "required field missing"      '{"entries":[{"id":"a","measure":"rr","estimate":1.52,"ci_low":1.2,"evalue_point":2.41}]}'
bad2 "boolean number"              "{\"entries\":[{$E,\"evalue_ci\":true}]}"
bad2 "list number"                 "{\"entries\":[{$E,\"evalue_ci\":[1.5]}]}"
bad2 "number string with letters"  "{\"entries\":[{$E,\"evalue_ci\":\"1.5x\"}]}"
bad2 "number string with exponent" "{\"entries\":[{$E,\"evalue_ci\":\"1e0\"}]}"
bad2 "zero"                        '{"entries":[{"id":"a","measure":"rr","estimate":1.52,"ci_low":0,"ci_high":1.93,"evalue_point":2.41}]}'
bad2 "negative"                    '{"entries":[{"id":"a","measure":"rr","estimate":1.52,"ci_low":-1.2,"ci_high":1.93,"evalue_point":2.41}]}'
bad2 "1e999"                       "{\"entries\":[{$E,\"evalue_ci\":1e999}]}"
bad2 "NaN"                         "{\"entries\":[{$E,\"evalue_ci\":NaN}]}"
bad2 "Infinity"                    "{\"entries\":[{$E,\"evalue_ci\":Infinity}]}"
bad2 "1e-400 (out of range)"       "{\"entries\":[{$E,\"evalue_ci\":1e-400}]}"
bad2 "ci_low above estimate"       '{"entries":[{"id":"a","measure":"rr","estimate":1.52,"ci_low":1.6,"ci_high":1.93,"evalue_point":2.41}]}'
bad2 "estimate above ci_high"      '{"entries":[{"id":"a","measure":"rr","estimate":2.5,"ci_low":1.2,"ci_high":1.93,"evalue_point":2.41}]}'
bad2 "location not a string"       "{\"entries\":[{$E,\"location\":5}]}"
bad2 "huge integer (5000 digits)"  "{\"entries\":[{$E,\"evalue_ci\":$(python3 -c 'print("9"*5000)')}]}"
bad2 "deep nesting"                "$(python3 -c 'print("["*100000 + "]"*100000)')"
python3 "$SCRIPT" --manuscript "$MAN" --evalues "$TMP/nope.json" >/dev/null 2>"$TMP/se"
check "missing evalues file: exit 2" test "$?" -eq 2

echo "fail=$fail"; [[ "$fail" -eq 0 ]] && echo "ALL PASS" || echo "FAILURES: $fail"
exit "$fail"
