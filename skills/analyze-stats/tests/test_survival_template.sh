#!/usr/bin/env bash
# Test the survival_analysis.py template hardening (A1):
#   - median survival reported WITH a 95% CI (not a bare point estimate)
#   - Cox events-per-variable (EPV) gate
#   - cluster-robust (sandwich) SE for nested observation units
# Static assertions always run (CI-safe, no heavy deps). A runtime smoke runs
# only when lifelines is importable; otherwise it SKIPs (never fails CI).
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TPL="$HERE/../references/templates/survival_analysis.py"
PASS=0
FAIL=0
ok()  { echo "  PASS: $1"; PASS=$((PASS+1)); }
bad() { echo "  FAIL: $1"; FAIL=$((FAIL+1)); }

# --- static: the template must compile + contain the hardened code paths ---
python3 -m py_compile "$TPL" 2>/dev/null && ok "template compiles" || bad "template syntax error"

grep -q "def median_with_ci" "$TPL" && ok "median_with_ci helper present" || bad "no median_with_ci helper"
grep -q "median_survival_times" "$TPL" && ok "imports median CI util" || bad "median CI util not imported"
# no bare median print left behind (the old `Median survival = {med:.1f}` form)
grep -qE 'Median survival[^\n]*median_survival_time_' "$TPL" && bad "bare median print still present" || ok "no bare median print"
grep -q "cluster_col" "$TPL" && ok "Cox cluster_col (robust SE) param" || bad "no cluster_col param"
grep -q -- "--cluster" "$TPL" && ok "--cluster CLI arg" || bad "no --cluster CLI arg"
grep -qiE "EPV =|EPV <" "$TPL" && ok "Cox EPV gate present" || bad "no Cox EPV gate"

# --- runtime smoke (optional, lifelines required) ---
if python3 -c "import lifelines" 2>/dev/null; then
  WORK="$(mktemp -d)"; trap 'rm -rf "$WORK"' EXIT
  python3 - "$WORK" <<'PY'
import csv, os, sys, random
random.seed(0)
work = sys.argv[1]
rows = [("t", "e", "g", "age", "pid")]
for i in range(120):
    rows.append((round(random.expovariate(1/12), 2), int(random.random() < 0.6),
                 "A" if i % 2 else "B", round(40 + random.gauss(0, 10), 1), i // 2))
with open(os.path.join(work, "s.csv"), "w", newline="") as f:
    csv.writer(f).writerows(rows)
PY
  OUT="$(python3 "$TPL" --input "$WORK/s.csv" --time t --event e --group g \
        --covariates age --cluster pid --output "$WORK/o" 2>&1)"
  echo "$OUT" | grep -q "95% CI" && ok "runtime: median prints 95% CI" || bad "runtime: median CI missing"
  echo "$OUT" | grep -q "EPV =" && ok "runtime: EPV line printed" || bad "runtime: EPV missing"
  echo "$OUT" | grep -q "cluster-sandwich" && ok "runtime: cluster SE applied" || bad "runtime: cluster SE missing"
else
  echo "  SKIP: lifelines not installed (static checks only)"
fi

echo ""
echo "test_survival_template: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]
