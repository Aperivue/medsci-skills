#!/usr/bin/env bash
# Regression test for check_test_statistic_p.py (SR-2): a reported test statistic's P recomputed
# from the statistic and its df, both read at their printed precision; declared GRIM means.
# Synthetic fixtures only (fixtures/tsp_*). Every expected numeric value below was produced by a
# reference implementation, and the call is recorded next to it:
#   scipy 1.17.1  2*scipy.stats.t.sf(2.10, 48)        = 0.041009  (t(48) = 2.10, P = .041 consistent)
#                 scipy.stats.f.sf(3.40, 2, 57)        = 0.040276  (F(2, 57) = 3.40, p = 0.04)
#                 scipy.stats.chi2.sf(7.40, 2)         = 0.024724  (χ2(2) = 7.40, P = .025)
#                 2*scipy.stats.norm.sf(2.31)          = 0.020888  (z = 2.31, P = 0.021)
#                 2*scipy.stats.t.sf(1.80, 25)         = 0.083941  (t(25) = 1.80, P = 0·08)
#                 2*scipy.stats.norm.sf(4.495 / 4.505) = 6.957e-06 / 6.637e-06  (P = 6.8 × 10−6)
#                 2*scipy.stats.t.sf(2.085 / 2.095, 20) = 0.050096 / 0.049106 (t(20) = 2.09, P = .049:
#                   consistent only because the statistic is read as [2.085, 2.095])
#                 2*scipy.stats.t.sf(1.95 / 2.05, 40)  = 0.058209 / 0.046959  (t(40) = 2.0, P = .047)
#                 2*scipy.stats.t.sf(1.495 / 1.505, 28) = 0.146101 / 0.143522 (t(28) = 1.50, P = .03: Major)
#                 scipy.stats.chi2.sf(2.05 / 2.15, 1)  = 0.152206 / 0.142570  (χ2(1) = 2.10, P = .02: Major)
#                 scipy.stats.f.sf(3.95 / 4.05, 1, 40) = 0.053748 / 0.050938  (F(1, 40) = 4.0, P = .03: Major
#                   at alpha .05, Minor at alpha .01)
#                 2*scipy.stats.t.sf(1.195 / 1.205, 30) = 0.241449 / 0.237623 (t(30) = 1.20, P < .001: Major)
#                 scipy.stats.t.sf(2.745 / 2.755, 30)  = 0.005061 / 0.004940  (one-sided t(30) = 2.75, P = .005)
#   R 4.3.3       x <- (0:200)/25; any(x >= 3.465 & x <= 3.475)  -> FALSE (mean 3.47, n 25: GRIM Major)
#                 any(x >= 3.475 & x <= 3.485)                   -> TRUE  (mean 3.48, n 25: consistent)
#                 y <- (0:400)/28; any(y >= 5.185 & y <= 5.195)  -> FALSE (mean 5.19, n 28: GRIM Major)
#                 z <- (0:200)/30; any(z >= 2.495 & z <= 2.505)  -> TRUE  (mean 2.50, 10 x 3 items)
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$HERE/../scripts/check_test_statistic_p.py"
FX="$HERE/fixtures"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
OUT="$TMP/out.json"

fail=0
check() { local label="$1"; shift
    if "$@" >/dev/null 2>&1; then printf '  PASS  %s\n' "$label"
    else printf '  FAIL  %s\n' "$label"; fail=$((fail+1)); fi
}
rc() { "$@" >/dev/null 2>&1; echo $?; }
# js <python expression over d (the JSON envelope)>
js() { python3 - "$OUT" "$1" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
codes = [c["verdict"] for c in d["claims"]]
raise SystemExit(0 if eval(sys.argv[2]) else 1)
PY
}
run() { python3 "$SCRIPT" "$@" --json > "$OUT" 2>/dev/null; }

[[ -f "$SCRIPT" ]] || { echo "ENV-ERR: script missing" >&2; exit 2; }

# --- special functions vs scipy (live, when scipy is installed) ------------------------------
if python3 -c "import scipy" 2>/dev/null; then
    check "t / F / chi2 / z P match scipy.stats (relative error < 1e-8 over a random grid)" \
        python3 - "$SCRIPT" <<'PY'
import importlib.util, random, sys
spec = importlib.util.spec_from_file_location("tsp", sys.argv[1]); m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
from scipy import stats
random.seed(20261003)
worst = 0.0
def rel(a, b):
    global worst
    if b > 1e-280:
        worst = max(worst, abs(a - b) / b)
for _ in range(2000):
    df = random.choice([1, 2, 3, 5, 10, 30, 100, 1000, 1e4, 1e5]) * random.choice([1, 1.37])
    t = random.uniform(0, 40)
    rel(m.p_t(t, df), 2 * stats.t.sf(t, df))
    d1, d2 = random.choice([1, 2, 3, 7, 20]), random.choice([1, 3, 10, 50, 500, 1e5])
    f = random.uniform(0, 60)
    rel(m.p_f(f, d1, d2), stats.f.sf(f, d1, d2))
    k = random.choice([1, 2, 3, 5, 10, 50, 300, 5000]); x = random.uniform(0, 3 * k + 50)
    rel(m.p_chi2(x, k), stats.chi2.sf(x, k))
    z = random.uniform(0, 30)
    rel(m.p_z(z), 2 * stats.norm.sf(z))
assert worst < 1e-8, worst
PY
else
    echo "  SKIP  scipy not installed: special functions not compared live"
fi

# --- consistent results -------------------------------------------------------------------
run --manuscript "$FX/tsp_consistent.md"
check "consistent: 8 statistics recomputed (bare 'z = 1.2' without P not taken), verdict OK, no claims" \
    js 'd["summary"]["verdict"] == "OK" and d["summary"]["n_statistics_checked"] == 8 and not d["claims"]'
check "envelope: detector key, basis manuscript, alpha 0.05" \
    js 'd["detector"] == "check_test_statistic_p" and d["basis"] == "manuscript" and d["alpha"] == "0.05"'
check "consistent: exit 0 under --strict" test "$(rc python3 "$SCRIPT" --manuscript "$FX/tsp_consistent.md" --strict)" -eq 0
check "consistent: final line is OK:" bash -c "python3 '$SCRIPT' --manuscript '$FX/tsp_consistent.md' | tail -1 | grep -q '^OK: '"

# --- inconsistent results ----------------------------------------------------------------
run --manuscript "$FX/tsp_bad.md"
check "bad: 4 P_STAT_DECISION_ERROR (t, χ2, F, '<' bound) + 1 P_STAT_INCONSISTENT" \
    js 'codes.count("P_STAT_DECISION_ERROR") == 4 and codes.count("P_STAT_INCONSISTENT") == 1 and d["summary"]["verdict"] == "MAJOR_CANDIDATE"'
check "bad: t(48) = 2.10, P = .045 (both below alpha) is Minor only" \
    js 'any(c["verdict"] == "P_STAT_INCONSISTENT" and c["severity"] == "Minor" and "t(48) = 2.10" in c["detail"] for c in d["claims"])'
check "bad: exit 1 under --strict" test "$(rc python3 "$SCRIPT" --manuscript "$FX/tsp_bad.md" --strict)" -eq 1
check "bad: final line is MAJOR candidate:" bash -c "python3 '$SCRIPT' --manuscript '$FX/tsp_bad.md' | tail -1 | grep -q '^MAJOR candidate: '"
run --manuscript "$FX/tsp_bad.md" --alpha 0.01
check "--alpha 0.01: F(1, 40) = 4.0, P = .03 is Minor (both ranges above alpha); P < .001 stays Major" \
    js 'codes.count("P_STAT_DECISION_ERROR") == 1 and codes.count("P_STAT_INCONSISTENT") == 4 and d["alpha"] == "0.01"'

run --manuscript "$FX/tsp_frontmatter.md"
check "YAML front matter is not read; the body result keeps its file line number (L8)" \
    js 'd["summary"]["n_statistics_found"] == 1 and codes == ["P_STAT_DECISION_ERROR"] and d["claims"][0]["where"] == "L8"'

# --- sidedness and adjustment ------------------------------------------------------------
run --manuscript "$FX/tsp_sided.md"
check "one-sided t stated in the sentence: compared against the one-sided P (no finding); one-tailed F -> P_STAT_NOT_ASSESSED" \
    js 'codes == ["P_STAT_NOT_ASSESSED"] and "F(2, 57)" in d["claims"][0]["detail"] and d["summary"]["verdict"] == "OK"'
run --manuscript "$FX/tsp_unstated_side.md"
check "P matching only the one-sided P without saying so -> Minor, never Major" \
    js 'codes == ["P_STAT_INCONSISTENT"] and "one-sided" in d["claims"][0]["detail"]'
run --manuscript "$FX/tsp_doc_onesided.md"
check "one-tailed mentioned elsewhere: t decision error demoted to Minor; χ2 stays Major" \
    js 'sorted(codes) == ["P_STAT_DECISION_ERROR", "P_STAT_INCONSISTENT"] and any(c["verdict"] == "P_STAT_DECISION_ERROR" and "χ2" in c["detail"] for c in d["claims"])'
run --manuscript "$FX/tsp_adjusted.md"
check "Bonferroni-adjusted P: inconsistency is Minor, never Major" js 'codes == ["P_STAT_INCONSISTENT"]'

# --- nothing to check ---------------------------------------------------------------------
run --manuscript "$FX/tsp_none.md"
check "no statistic: verdict NOT_ASSESSED with a P_STAT_NOT_ASSESSED claim" \
    js 'd["summary"]["verdict"] == "NOT_ASSESSED" and codes == ["P_STAT_NOT_ASSESSED"]'
check "no statistic: exit 0 without --strict" test "$(rc python3 "$SCRIPT" --manuscript "$FX/tsp_none.md")" -eq 0
check "no statistic: exit 2 under --strict" test "$(rc python3 "$SCRIPT" --manuscript "$FX/tsp_none.md" --strict)" -eq 2
check "no statistic: final line is NOT ASSESSED:" bash -c "python3 '$SCRIPT' --manuscript '$FX/tsp_none.md' | tail -1 | grep -q '^NOT ASSESSED: '"
run --manuscript "$FX/tsp_unpaired.md"
check "statistic without P: listed in P_STAT_NOT_ASSESSED, verdict NOT_ASSESSED" \
    js 'd["summary"]["verdict"] == "NOT_ASSESSED" and codes == ["P_STAT_NOT_ASSESSED"] and "t(48) = 2.10" in d["claims"][0]["detail"]'

# --- declared GRIM -----------------------------------------------------------------------
run --grim "$FX/tsp_grim.json"
check "GRIM: 3.47/25 and 5.19/28 -> GRIM_INCONSISTENT (Major); 4.21/150 -> GRIM_NOT_ASSESSED; 3.48/25 and 2.50/(10x3) clean" \
    js 'sorted(codes) == ["GRIM_INCONSISTENT", "GRIM_INCONSISTENT", "GRIM_NOT_ASSESSED"] and {c["where"] for c in d["claims"] if c["verdict"] == "GRIM_INCONSISTENT"} == {"grim:Pain score, arm B", "grim:Sleep"} and d["summary"]["n_grim_checked"] == 4'
check "GRIM only: basis declared, verdict MAJOR_CANDIDATE" js 'd["basis"] == "declared" and d["summary"]["verdict"] == "MAJOR_CANDIDATE"'
check "GRIM only: exit 1 under --strict" test "$(rc python3 "$SCRIPT" --grim "$FX/tsp_grim.json" --strict)" -eq 1
printf '[{"label": "A", "mean": 3.48, "n": 25}]\n' > "$TMP/g_ok.json"
check "GRIM only, clean: final line 'OK (as declared):'" bash -c "python3 '$SCRIPT' --grim '$TMP/g_ok.json' | tail -1 | grep -q '^OK (as declared): '"
printf '[{"label": "A", "mean": 4.21, "n": 150}]\n' > "$TMP/g_np.json"
run --grim "$TMP/g_np.json"
check "GRIM without power only: verdict NOT_ASSESSED" js 'd["summary"]["verdict"] == "NOT_ASSESSED" and codes == ["GRIM_NOT_ASSESSED"]'
run --manuscript "$FX/tsp_none.md" --grim "$TMP/g_ok.json"
check "manuscript without statistic + clean GRIM: OK with the P_STAT_NOT_ASSESSED claim kept" \
    js 'd["summary"]["verdict"] == "OK" and codes == ["P_STAT_NOT_ASSESSED"] and d["basis"] == "manuscript+declared"'

# --- input errors: exit 2, message names the field ------------------------------------------
bad_input() { local label="$1" body="$2" field="$3"
    printf '%s' "$body" > "$TMP/bad.json"
    local err; err="$(python3 "$SCRIPT" --grim "$TMP/bad.json" 2>&1 >/dev/null)"; local r=$?
    if [ "$r" -eq 2 ] && printf '%s' "$err" | grep -qF -- "$field"; then printf '  PASS  %s\n' "$label"
    else printf '  FAIL  %s (exit %s: %s)\n' "$label" "$r" "$err"; fail=$((fail+1)); fi
}
bad_input "NaN mean rejected"                '[{"label":"A","mean":NaN,"n":5}]'               "NaN"
bad_input "Infinity n rejected"              '[{"label":"A","mean":1.2,"n":Infinity}]'       "Infinity"
bad_input "non-numeric mean"                 '[{"label":"A","mean":"abc","n":5}]'            "[0].mean"
bad_input "n = 0"                            '[{"label":"A","mean":1.2,"n":0}]'              "[0].n"
bad_input "fractional n"                     '[{"label":"A","mean":1.2,"n":5.5}]'            "[0].n"
bad_input "items = 0"                        '[{"label":"A","mean":1.2,"n":5,"items":0}]'    "[0].items"
bad_input "decimals fewer than printed"      '[{"label":"A","mean":1.25,"n":5,"decimals":1}]' "[0].decimals"
bad_input "unknown key"                      '[{"label":"A","mean":1.2,"n":5,"sd":1}]'       "unknown key"
bad_input "missing n"                        '[{"label":"A","mean":1.2}]'                    "[0].n"
bad_input "duplicate label"                  '[{"label":"A","mean":1.2,"n":5},{"label":"a","mean":1.4,"n":5}]' "[1].label"
bad_input "top level not a list"             '{"label":"A","mean":1.2,"n":5}'               "non-empty JSON list"
bad_input "malformed JSON"                   '[{"label":"A",'                               "cannot read GRIM file"
bad_input "deep nesting"                     "$(python3 -c 'print("["*100000 + "]"*100000)')" "cannot read GRIM file"
printf '\xef\xbb\xbf[{"label": "A", "mean": 3.48, "n": 25}]\n' > "$TMP/g_bom.json"
check "UTF-8 BOM accepted" test "$(rc python3 "$SCRIPT" --grim "$TMP/g_bom.json" --strict)" -eq 0
check "no input flag: exit 2" test "$(rc python3 "$SCRIPT")" -eq 2
check "missing manuscript: exit 2" test "$(rc python3 "$SCRIPT" --manuscript "$TMP/nope.md")" -eq 2
check "--alpha 1.5: exit 2" test "$(rc python3 "$SCRIPT" --manuscript "$FX/tsp_bad.md" --alpha 1.5)" -eq 2
check "--alpha nan: exit 2" test "$(rc python3 "$SCRIPT" --manuscript "$FX/tsp_bad.md" --alpha nan)" -eq 2

if [ "$fail" -eq 0 ]; then echo "PASS: check_test_statistic_p"; else echo "FAIL: $fail check(s)"; exit 1; fi
