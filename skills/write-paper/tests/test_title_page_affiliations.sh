#!/usr/bin/env bash
# Challenge/regression test for build_title_page_affiliations.py — deterministic,
# network-free, runtime fixtures. Build uses a .json authors file (no PyYAML dep);
# check is stdlib-only.
set -u

HERE="$(cd "$(dirname "$0")" && pwd)"
S="$HERE/../scripts/build_title_page_affiliations.py"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

pass=0
fail=0
ck() {
  local label="$1" cond="$2"
  if [ "$cond" = "1" ]; then printf '  PASS  %s\n' "$label"; pass=$((pass + 1))
  else printf '  FAIL  %s\n' "$label"; fail=$((fail + 1)); fi
}
 rc() { "$@" > /dev/null 2>&1; echo $?; }

# --- BUILD: first-appearance numbering, affiliation reuse, ascending block ---
cat > "$TMP/authors.json" <<'JSON'
{"authors":[
  {"name":"Jane Doe","affiliations":["uh","mmc"]},
  {"name":"Alan Poe","affiliations":["cgh"]},
  {"name":"John Roe","affiliations":["uh"],"corresponding":true},
  {"name":"Mary Sue","affiliations":["mmc","mmc_rad"],"corresponding":true}],
 "affiliations":{
  "uh":"Department of Radiology, University Hospital, City, Country",
  "mmc":"Department of Convergence Medicine, Metro Medical Center, City, Country",
  "cgh":"Department of Radiology, Coastal General Hospital, Town, Country",
  "mmc_rad":"Department of Radiology, Metro Medical Center, City, Country"}}
JSON
python3 "$S" --authors "$TMP/authors.json" --out "$TMP/built.md" > /dev/null 2>&1
ck "build emits first-appearance numbering (Doe^1,2^)" "$(grep -cF 'Jane Doe^1,2^' "$TMP/built.md")"
ck "build reuses affiliation 1 for a later author (John Roe^1)" "$(grep -cF 'John Roe^1,\*^' "$TMP/built.md")"
ck "build reuses 2 + adds 4 (Mary Sue^2,4)" "$(grep -cF 'Mary Sue^2,4,\*^' "$TMP/built.md")"
ck "block lists ^4^ last" "$(grep -cE '^\^4\^ ' "$TMP/built.md")"

# --- CHECK: the built title page round-trips clean ---
ck "built title page passes --check --strict" "$([ "$(rc python3 "$S" --check "$TMP/built.md" --strict)" = "0" ] && echo 1 || echo 0)"

# --- CHECK: out-of-order (affiliation 1 is not the first author's) -> exit 1 ---
cat > "$TMP/bad_order.md" <<'MD'
Alice Lee^3^; Bob Park^1^; Carol Kim^2,1^

^1^ Department of X, Hospital A, Seoul, Republic of Korea
^2^ Department of Y, Hospital B, Busan, Republic of Korea
^3^ Department of Z, Hospital C, Daegu, Republic of Korea
MD
ck "out-of-order numbering fails (--strict)" "$([ "$(rc python3 "$S" --check "$TMP/bad_order.md" --strict)" = "1" ] && echo 1 || echo 0)"
ck "out-of-order tolerated without --strict" "$([ "$(rc python3 "$S" --check "$TMP/bad_order.md")" = "0" ] && echo 1 || echo 0)"

# --- CHECK: author cites an undefined affiliation -> exit 1 ---
cat > "$TMP/undef.md" <<'MD'
Alice Lee^1^; Bob Park^2^

^1^ Department of X, Hospital A, Seoul, Republic of Korea
MD
ck "undefined affiliation reference fails (--strict)" "$([ "$(rc python3 "$S" --check "$TMP/undef.md" --strict)" = "1" ] && echo 1 || echo 0)"

# --- CHECK: missing city/country is a SOFT finding (exit 0 without --strict) ---
cat > "$TMP/nocity.md" <<'MD'
Alice Lee^1^; Bob Park^2^

^1^ Department of X, Hospital A
^2^ Department of Y, Hospital B, Seoul, Republic of Korea
MD
ck "missing city/country is soft (exit 0)" "$([ "$(rc python3 "$S" --check "$TMP/nocity.md")" = "0" ] && echo 1 || echo 0)"

echo "----"
echo "test_title_page_affiliations: $pass passed, $fail failed"
[ "$fail" -eq 0 ]
