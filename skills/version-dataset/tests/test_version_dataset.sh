#!/usr/bin/env bash
# Regression tests for version-dataset/scripts/version_dataset.py.
# Self-contained: builds synthetic CSVs (no committed data).

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
VS="$REPO_ROOT/skills/version-dataset/scripts/version_dataset.py"
TMP="$(mktemp -d -t versionds.XXXXXX)"
trap 'rm -rf "$TMP"' EXIT

[[ -f "$VS" ]] || { echo "ENV-ERR: script missing" >&2; exit 2; }

# CSV manifest build goes through pandas (column-level value hashing); skip
# cleanly when pandas is absent. CI installs it before this gate runs.
python3 -c "import pandas" 2>/dev/null || { echo "SKIP: pandas unavailable"; exit 0; }

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

# --- tabular byte changes the column hashes did not see must not be cleared ---
# (a) duplicate header a,a re-written as a,a.1 (pandas parses both as a,a.1)
printf 'a,a\n1,2\n' > "$TMP/h.csv"
python3 "$VS" manifest "$TMP/h.csv" --out "$TMP/hm.json" >/dev/null 2>&1
check "dup header: unchanged verifies clean" 0 "$(ec python3 "$VS" verify --manifest "$TMP/hm.json" --strict)"
printf 'a,a.1\n1,2\n' > "$TMP/h.csv"
check "dup header mangling -> drift" 1 "$(ec python3 "$VS" verify --manifest "$TMP/hm.json" --strict)"
out="$(python3 "$VS" verify --manifest "$TMP/hm.json" 2>&1)"
check "dup header reports CHANGED header" 0 "$([[ "$out" == *"CHANGED header"* ]] && echo 0 || echo 1)"

# (b) record-separator collision in one column: ["a<RS>","b"] vs ["a","<RS>b"]
printf 'c\na\036\nb\n' > "$TMP/s.csv"
python3 "$VS" manifest "$TMP/s.csv" --out "$TMP/sm.json" >/dev/null 2>&1
check "separator cells: unchanged verifies clean" 0 "$(ec python3 "$VS" verify --manifest "$TMP/sm.json" --strict)"
printf 'c\na\n\036b\n' > "$TMP/s.csv"
check "separator collision -> drift" 1 "$(ec python3 "$VS" verify --manifest "$TMP/sm.json" --strict)"

# (c) CSV re-quoting changes bytes only -> still not drift (logical comparison kept)
printf 'id,g\n1,A\n2,B\n' > "$TMP/q.csv"
python3 "$VS" manifest "$TMP/q.csv" --out "$TMP/qm.json" >/dev/null 2>&1
printf '"id","g"\r\n"1","A"\r\n"2","B"\r\n' > "$TMP/q.csv"
check "csv re-quote (bytes only) stays clean" 0 "$(ec python3 "$VS" verify --manifest "$TMP/qm.json" --strict)"

# (d) Stata: variable-label change with identical values -> drift;
#     identical rewrite (fixed time stamp) -> clean
mkdta() {
    python3 - "$1" "$2" <<'PY'
import sys, datetime, pandas as pd
df = pd.DataFrame({"id": [1, 2, 3], "sbp": [120, 130, 125]})
df.to_stata(sys.argv[1], write_index=False, variable_labels={"sbp": sys.argv[2]},
            time_stamp=datetime.datetime(2020, 1, 1))
PY
}
if mkdta "$TMP/d.dta" "Systolic BP" 2>/dev/null; then
    python3 "$VS" manifest "$TMP/d.dta" --out "$TMP/dm.json" >/dev/null 2>&1
    mkdta "$TMP/d.dta" "Systolic BP"
    check "dta identical rewrite verifies clean" 0 "$(ec python3 "$VS" verify --manifest "$TMP/dm.json" --strict)"
    mkdta "$TMP/d.dta" "Diastolic BP"
    check "dta label change -> drift" 1 "$(ec python3 "$VS" verify --manifest "$TMP/dm.json" --strict)"
    out="$(python3 "$VS" verify --manifest "$TMP/dm.json" 2>&1)"
    check "dta label change reports CHANGED bytes" 0 "$([[ "$out" == *"CHANGED bytes"* ]] && echo 0 || echo 1)"
elif [[ "${CI:-}" == "true" ]]; then
    # pandas' Stata writer needs nothing beyond pandas, which CI installs: a
    # failure here is a broken environment, not a reason to skip the binary path.
    check "Stata writer available under CI" 0 1
else
    echo "  SKIP  Stata writer unavailable"
fi

# (e) a lock built by the previous script (no tabular.header key) for an
#     unchanged duplicate-header CSV must still verify clean: an absent header
#     means "not recorded", not "changed". The JSON below is verbatim output of
#     the pre-header version_dataset.py `manifest h.csv --base .` on 'a,a\n1,2\n'.
mkdir -p "$TMP/old"
printf 'a,a\n1,2\n' > "$TMP/old/h.csv"
cat > "$TMP/old/lock.json" <<'JSON'
{
  "schema_version": 1,
  "seed": null,
  "provenance": null,
  "files": {
    "h.csv": {
      "sha256": "921520be8279e81db6a46688da4ae835cadd820a6892a557e3bfe1b06746b711",
      "bytes": 8,
      "tabular": {
        "n_rows": 1,
        "n_cols": 2,
        "column_hashes": {
          "a": "6b86b273ff34fce19d6b804eff5a3f5747ada4eaa22f1d49c01e52ddb7875b4b",
          "a.1": "d4735e3a265e16eee03f59718b9b5d03019c07d8b6c51f90da3a666eec13ab35"
        }
      }
    }
  }
}
JSON
check "old lock, unchanged dup-header csv: clean" 0 "$(ec python3 "$VS" verify --manifest "$TMP/old/lock.json" --base "$TMP/old" --strict)"
out="$(python3 "$VS" verify --manifest "$TMP/old/lock.json" --base "$TMP/old" 2>&1)"
check "old lock: no CHANGED header reported" 0 "$([[ "$out" != *"CHANGED header"* ]] && echo 0 || echo 1)"
printf 'a,a\n1,9\n' > "$TMP/old/h.csv"
check "old lock: value change still drifts" 1 "$(ec python3 "$VS" verify --manifest "$TMP/old/lock.json" --base "$TMP/old" --strict)"

# (f) --ignore-cols is honoured for binary tabular files: a change confined to
#     an ignored column must not fall through to the byte-level check.
mkdtats() {
    python3 - "$1" "$2" <<'PY'
import sys, datetime, pandas as pd
df = pd.DataFrame({"id": [1, 2], "ts": [sys.argv[2], "x"]})
df.to_stata(sys.argv[1], write_index=False, time_stamp=datetime.datetime(2020, 1, 1))
PY
}
if mkdtats "$TMP/t.dta" t1 2>/dev/null; then
    python3 "$VS" manifest "$TMP/t.dta" --out "$TMP/tm.json" --ignore-cols ts >/dev/null 2>&1
    mkdtats "$TMP/t.dta" t9
    check "dta: change only in ignored col -> clean" 0 "$(ec python3 "$VS" verify --manifest "$TMP/tm.json" --ignore-cols ts --strict)"
    python3 "$VS" manifest "$TMP/t.dta" --out "$TMP/tm0.json" >/dev/null 2>&1
    mkdtats "$TMP/t.dta" t1
    check "dta: same change without --ignore-cols -> drift" 1 "$(ec python3 "$VS" verify --manifest "$TMP/tm0.json" --strict)"
elif [[ "${CI:-}" == "true" ]]; then
    check "Stata writer available under CI" 0 1
else
    echo "  SKIP  Stata writer unavailable"
fi
# .xlsx/.parquet readers (openpyxl/pyarrow) are not installed in CI, so the
# comparison is exercised through `diff` on manifests shaped as `manifest` writes
# them for those formats: same column hashes, different bytes.
for ext in xlsx parquet; do
    for ig in yes no; do
        python3 - "$TMP/o_$ext$ig.json" "$TMP/n_$ext$ig.json" "$ext" "$ig" <<'PY'
import json, sys
o, n, ext, ig = sys.argv[1:]
def m(sha):
    tab = {"n_rows": 2, "n_cols": 2, "column_hashes": {"id": "0" * 64}}
    if ig == "yes":
        tab["ignored_cols"] = ["ts"]
    return {"schema_version": 1, "files": {f"d.{ext}": {"sha256": sha, "bytes": 1, "tabular": tab}}}
json.dump(m("1" * 64), open(o, "w"))
json.dump(m("2" * 64), open(n, "w"))
PY
    done
    out="$(python3 "$VS" diff --old "$TMP/o_${ext}yes.json" --new "$TMP/n_${ext}yes.json" 2>&1)"
    check "$ext: ignored col present -> no byte drift" 0 "$([[ "$out" == "No differences"* ]] && echo 0 || echo 1)"
    out="$(python3 "$VS" diff --old "$TMP/o_${ext}no.json" --new "$TMP/n_${ext}no.json" 2>&1)"
    check "$ext: no ignored col -> CHANGED bytes" 0 "$([[ "$out" == *"CHANGED bytes"* ]] && echo 0 || echo 1)"
done

printf '\n%d/%d checks passed\n' "$((ran-fail))" "$ran"
[[ "$fail" -eq 0 ]] || exit 1
