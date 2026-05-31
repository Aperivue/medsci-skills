#!/usr/bin/env bash
# Regression tests for version-dataset/scripts/version_dataset.py.
# Self-contained: builds synthetic CSVs (no committed data).

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
VS="$REPO_ROOT/skills/version-dataset/scripts/version_dataset.py"
TMP="$(mktemp -d -t versionds.XXXXXX)"
trap 'rm -rf "$TMP"' EXIT

[[ -f "$VS" ]] || { echo "ENV-ERR: script missing" >&2; exit 2; }

fail=0; ran=0
check() {
    local label="$1" expected="$2" actual="$3"
    ran=$((ran+1))
    if [[ "$expected" == "$actual" ]]; then printf '  PASS  %-48s %s\n' "$label" "$actual"
    else printf '  FAIL  %-48s expected=%s actual=%s\n' "$label" "$expected" "$actual"; fail=$((fail+1)); fi
}
ec() { "$@" >/dev/null 2>&1; echo $?; }

printf 'id,age,grp\n1,50,A\n2,61,B\n3,47,A\n' > "$TMP/d.csv"

# manifest builds (exit 0)
check "manifest build" 0 "$(ec python3 "$VS" manifest "$TMP/d.csv" --out "$TMP/m.json" --seed 42 --provenance test)"
check "manifest file written" 0 "$([[ -f "$TMP/m.json" ]] && echo 0 || echo 1)"

# verify clean (exit 0)
check "verify clean --strict" 0 "$(ec python3 "$VS" verify --manifest "$TMP/m.json" --strict)"

# mutate a value -> drift (exit 1) + CHANGED column reported
printf 'id,age,grp\n1,50,A\n2,99,B\n3,47,A\n' > "$TMP/d.csv"
check "verify value-change --strict" 1 "$(ec python3 "$VS" verify --manifest "$TMP/m.json" --strict)"
out="$(python3 "$VS" verify --manifest "$TMP/m.json" 2>&1)"
check "drift reports CHANGED column age" 0 "$([[ "$out" == *"CHANGED column"*":age"* ]] && echo 0 || echo 1)"
check "non-strict drift exits 0" 0 "$(ec python3 "$VS" verify --manifest "$TMP/m.json")"

# add a row -> new manifest + diff reports ROW COUNT
printf 'id,age,grp\n1,50,A\n2,99,B\n3,47,A\n4,55,C\n' > "$TMP/d.csv"
python3 "$VS" manifest "$TMP/d.csv" --out "$TMP/m2.json" >/dev/null 2>&1
dout="$(python3 "$VS" diff --old "$TMP/m.json" --new "$TMP/m2.json" 2>&1)"
check "diff reports ROW COUNT 3 -> 4" 0 "$([[ "$dout" == *"ROW COUNT"*"3 -> 4"* ]] && echo 0 || echo 1)"

# --ignore-cols excludes a volatile column from hashing
printf 'id,age,ts\n1,50,t1\n2,61,t2\n' > "$TMP/v.csv"
python3 "$VS" manifest "$TMP/v.csv" --out "$TMP/vm.json" --ignore-cols ts >/dev/null 2>&1
printf 'id,age,ts\n1,50,t9\n2,61,t8\n' > "$TMP/v.csv"   # only ts changes
check "verify ignores volatile col" 0 "$(ec python3 "$VS" verify --manifest "$TMP/vm.json" --ignore-cols ts --strict)"

printf '\n%d/%d checks passed\n' "$((ran-fail))" "$ran"
[[ "$fail" -eq 0 ]] || exit 1
