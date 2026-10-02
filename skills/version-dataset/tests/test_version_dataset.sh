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

# (g) locks built by the pre-escaping script for UNCHANGED files whose cells hold
#     \x1b (ANSI colour codes) or \x1e must still verify clean. The JSON below is
#     verbatim output of origin/main's version_dataset.py `manifest e.csv r.csv
#     --base .` on the two files written here.
mkdir -p "$TMP/esc"
printf 'a,b\n\033[31mred\033[0m,2\nplain,3\n' > "$TMP/esc/e.csv"
printf 'c,d\nx\036y,1\nz,2\n' > "$TMP/esc/r.csv"
cat > "$TMP/esc/lock.json" <<'JSON'
{
  "schema_version": 1,
  "seed": null,
  "provenance": null,
  "files": {
    "e.csv": {
      "sha256": "8b0e512530f97e8db83f7e3652773c03620a52bc93f23744eafe091becb39ed7",
      "bytes": 27,
      "tabular": {
        "n_rows": 2,
        "n_cols": 2,
        "column_hashes": {
          "a": "03e6a9990c37bfd9f2240335dde655a87e79878c50ac7095bc74d9278310b8e4",
          "b": "6f52c50f8abbf0792f693542eb0bf3cd5086881e6e960fe1885aa46340d14380"
        }
      }
    },
    "r.csv": {
      "sha256": "0cc1fa61bf2012081b6b7cb9b6887375dc89ff79677310b75b8b9dc9acd2d92d",
      "bytes": 14,
      "tabular": {
        "n_rows": 2,
        "n_cols": 2,
        "column_hashes": {
          "c": "24e60967e73629b5ed59c021ac1ee7fca4b5ad72c93c62c6761426460af7cd18",
          "d": "d95838638b57fb04835fc9103a8a6f4d724435aad81507e74d5cdb2ff57f7d77"
        }
      }
    }
  }
}
JSON
check "old lock, unchanged \\x1b/\\x1e cells: clean" 0 "$(ec python3 "$VS" verify --manifest "$TMP/esc/lock.json" --base "$TMP/esc" --strict)"
# a new lock of the \x1b-only file hashes it exactly as the old script did
python3 "$VS" manifest "$TMP/esc/e.csv" "$TMP/esc/r.csv" --base "$TMP/esc" --out "$TMP/esc/new.json" >/dev/null 2>&1
same="$(python3 - "$TMP/esc/lock.json" "$TMP/esc/new.json" <<'PY'
import json, sys
o, n = (json.load(open(f))["files"] for f in sys.argv[1:])
ok = (o["e.csv"]["tabular"] == n["e.csv"]["tabular"]
      and n["r.csv"]["tabular"]["column_hashes"]["d"] == o["r.csv"]["tabular"]["column_hashes"]["d"]
      and n["r.csv"]["tabular"].get("escaped_cols") == ["c"])
print(0 if ok else 1)
PY
)"
check "new lock: \\x1b-only column hashes unchanged" 0 "$same"
check "new lock, unchanged \\x1e cells: clean" 0 "$(ec python3 "$VS" verify --manifest "$TMP/esc/new.json" --base "$TMP/esc" --strict)"
printf 'a,b\n\033[32mred\033[0m,2\nplain,3\n' > "$TMP/esc/e.csv"
check "old lock: changed \\x1b cell -> drift" 1 "$(ec python3 "$VS" verify --manifest "$TMP/esc/lock.json" --base "$TMP/esc" --strict)"
printf 'c,d\nx\036q,1\nz,2\n' > "$TMP/esc/r.csv"
out="$(python3 "$VS" verify --manifest "$TMP/esc/lock.json" --base "$TMP/esc" 2>&1)"
check "old lock: changed \\x1e cell -> CHANGED column" 0 "$([[ "$out" == *"CHANGED column"*"r.csv:c"* ]] && echo 0 || echo 1)"
# an escaped column in the lock whose separator cell disappears is drift
printf 'c,d\nxy,1\nz,2\n' > "$TMP/esc/r.csv"
check "new lock: \\x1e removed from cell -> drift" 1 "$(ec python3 "$VS" verify --manifest "$TMP/esc/new.json" --base "$TMP/esc" --strict)"

# (h) the CHANGED header line names the new raw header, not None
printf 'a,a\n1,2\n' > "$TMP/h2.csv"
python3 "$VS" manifest "$TMP/h2.csv" --out "$TMP/h2m.json" >/dev/null 2>&1
printf 'a,a.1\n1,2\n' > "$TMP/h2.csv"
out="$(python3 "$VS" verify --manifest "$TMP/h2m.json" 2>&1)"
check "CHANGED header shows new raw header" 0 "$([[ "$out" == *"-> ['a', 'a.1']"* ]] && echo 0 || echo 1)"

printf '\n%d/%d checks passed\n' "$((ran-fail))" "$ran"
[[ "$fail" -eq 0 ]] || exit 1
