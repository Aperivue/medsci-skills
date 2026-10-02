#!/usr/bin/env bash
# Regression test for references/profiling_template.py: missing values written
# as "." or "missing" must be counted as missing, not profiled as 0% missing.
# Fixture: 12 rows; age has one ".", sbp has one "." and one "missing";
# id/hr/sex are complete (negative controls). Needs pandas (installed in CI).
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE_DIR="$HERE/../references"
FIXTURE="$HERE/fixtures/profile_na_tokens.csv"

fail=0
check() { local label="$1"; shift
    if "$@" >/dev/null 2>&1; then printf '  PASS  %s\n' "$label"
    else printf '  FAIL  %s\n' "$label"; fail=$((fail+1)); fi
}

[[ -f "$TEMPLATE_DIR/profiling_template.py" ]] || { echo "ENV-ERR: template missing" >&2; exit 2; }
[[ -f "$FIXTURE" ]] || { echo "ENV-ERR: fixture missing" >&2; exit 2; }
python3 -c "import pandas" 2>/dev/null || { echo "ENV-ERR: pandas not installed" >&2; exit 2; }

# run "<python assertions over s (summary indexed by variable) and pt>"
run() {
    python3 - "$TEMPLATE_DIR" "$FIXTURE" "$1" <<'PY'
import sys
sys.path.insert(0, sys.argv[1])
import profiling_template as pt
df = pt.load_data(sys.argv[2])
s = pt.build_variable_summary(df).set_index("variable")
exec(sys.argv[3])
PY
}

check "age: '.' counted missing (1 of 12), still typed numeric" run "
r = s.loc['age']; assert r['n_missing'] == 1 and r['pct_missing'] == round(100 / 12, 2), r
assert r['inferred_type'] == 'numeric', r"
check "sbp: '.' and 'missing' counted missing (2 of 12)" run "
r = s.loc['sbp']; assert r['n_missing'] == 2 and r['pct_missing'] == round(200 / 12, 2), r"
check "flag_missing fires for age and sbp" run "
f = set(pt.flag_missing(s.reset_index())['variable']); assert f == {'age', 'sbp'}, f"
check "sbp mean is over the 10 observed values only" run "
obs = [120, 135, 128, 142, 118, 125, 131, 138, 122, 127]
assert abs(s.loc['sbp', 'mean'] - round(sum(obs) / len(obs), 4)) < 1e-9, s.loc['sbp', 'mean']"
check "n_non_numeric == 0 once NA tokens are read as missing" run "
assert s.loc['age', 'n_non_numeric'] == 0 and s.loc['sbp', 'n_non_numeric'] == 0, s"
check "negative control: complete columns stay at 0% missing" run "
for c in ('id', 'hr', 'sex'):
    assert s.loc[c, 'n_missing'] == 0 and s.loc[c, 'pct_missing'] == 0.0, (c, s.loc[c])"

echo "fail=$fail"; [[ "$fail" -eq 0 ]] && echo "ALL PASS" || echo "FAILURES: $fail"
exit "$fail"
