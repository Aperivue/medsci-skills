#!/usr/bin/env bash
# Regression test for the PHI scanner (deidentify.py scan).
# Asserts the exact classification contract on three committed CSV fixtures so a
# silent break in PHI detection -- which would leak patient data -- fails CI.
# CSV scan path is stdlib-only (openpyxl is a lazy import for .xlsx only),
# so this test needs no third-party deps and makes no network calls.
#
# This shell file contains NO Hangul (keeps clear of the locale-inventory gate).
# Column-specific assertions read the fixture header at runtime and address
# columns positionally; the Korean data itself lives only in the fixture CSVs.
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL="$HERE/.."
SCRIPT="$SKILL/deidentify.py"
OUTDIR="$(mktemp -d -t deid_XXXX)"
trap 'rm -rf "$OUTDIR"' EXIT

fail=0
check() { local label="$1"; shift
    if "$@" >/dev/null 2>&1; then printf '  PASS  %s\n' "$label"
    else printf '  FAIL  %s\n' "$label"; fail=$((fail+1)); fi
}

[[ -f "$SCRIPT" ]] || { echo "ENV-ERR: deidentify.py missing" >&2; exit 2; }
for fx in test_phi_korean test_clean test_edge_cases; do
    [[ -f "$HERE/$fx.csv" ]] || { echo "ENV-ERR: fixture $fx.csv missing" >&2; exit 2; }
done

# Counts a classification class in a scan_report.json.
# usage: count <report.json> <PHI|REVIEW_NEEDED|SAFE>
COUNTER='
import json,sys
d=json.load(open(sys.argv[1]))
from collections import Counter
c=Counter(x["classification"] for x in d["classifications"])
print(c.get(sys.argv[2],0))'
count() { python3 -c "$COUNTER" "$1" "$2"; }

# --- Fixture 1: Korean PHI (10 columns) -> PHI=7, REVIEW_NEEDED=0, SAFE=3 ---
python3 "$SCRIPT" scan "$HERE/test_phi_korean.csv" --locale kr -o "$OUTDIR" >/dev/null 2>&1
PHI_REPORT="$OUTDIR/scan_report.json"
check "phi fixture: report written"      test -s "$PHI_REPORT"
check "phi fixture: PHI == 7"             test "$(count "$PHI_REPORT" PHI)"           -eq 7
check "phi fixture: REVIEW_NEEDED == 0"   test "$(count "$PHI_REPORT" REVIEW_NEEDED)" -eq 0
check "phi fixture: SAFE == 3"            test "$(count "$PHI_REPORT" SAFE)"          -eq 3

# Exactly one column has phi_type 'rrn' (resident-registration-number) -> PHI.
check "phi fixture: rrn column is PHI/rrn" python3 -c "
import json
d=json.load(open('$PHI_REPORT'))
rrn=[x for x in d['classifications'] if x.get('phi_type')=='rrn']
assert len(rrn)==1, rrn
assert rrn[0]['classification']=='PHI', rrn[0]"

# Header positions 7 (diagnosis) and 8 (measurement) must be SAFE.
# Read the header from the fixture so this file stays Hangul-free.
check "phi fixture: diagnosis + measurement (cols 7,8) are SAFE" python3 -c "
import json,csv
d=json.load(open('$PHI_REPORT'))
with open('$HERE/test_phi_korean.csv', encoding='utf-8') as f:
    hdr=next(csv.reader(f))
cl={x['column']: x['classification'] for x in d['classifications']}
for i in (7, 8):
    assert cl.get(hdr[i])=='SAFE', (i, hdr[i], cl.get(hdr[i]))"

# --- Fixture 2: clean (no PHI) -> PHI == 0 (false-positive guard) ---
python3 "$SCRIPT" scan "$HERE/test_clean.csv" --locale kr -o "$OUTDIR" >/dev/null 2>&1
CLEAN_REPORT="$OUTDIR/scan_report.json"
check "clean fixture: PHI == 0" test "$(count "$CLEAN_REPORT" PHI)" -eq 0

# --- Fixture 3: edge cases -> REVIEW_NEEDED=1, SAFE=5 (no crash, fixed contract) ---
python3 "$SCRIPT" scan "$HERE/test_edge_cases.csv" --locale kr -o "$OUTDIR" >/dev/null 2>&1
check "edge fixture: exit 0 (no crash)" test "$?" -eq 0
EDGE_REPORT="$OUTDIR/scan_report.json"
check "edge fixture: REVIEW_NEEDED == 1" test "$(count "$EDGE_REPORT" REVIEW_NEEDED)" -eq 1
check "edge fixture: SAFE == 5"          test "$(count "$EDGE_REPORT" SAFE)"          -eq 5

# --- Case-insensitive ID and postcode detection (runtime-built fixtures) ---
# Letter-bearing national IDs and postcodes are often exported in lower case.
# A missed match classifies the column SAFE, so it is passed through
# un-stripped. Column names are deliberately NOT in any locale's name map,
# so only the value patterns can decide. Each case carries a positive control
# (upper case), the regression (the same values in lower case), and a
# false-positive control (ordinary lower-case text that must stay SAFE).
# Values are published format examples or constructed strings, not people's IDs.
classify() {  # usage: classify <report.json> <column>
    python3 -c "
import json,sys
d=json.load(open(sys.argv[1]))
print(next(x['classification'] for x in d['classifications'] if x['column']==sys.argv[2]))" "$1" "$2"
}
case_check() {  # usage: case_check <locale> <label> <v1> <v2> <v3>
    local loc="$1" label="$2" csv="$OUTDIR/case_$1_$2.csv" out="$OUTDIR/case_$1_$2"
    local lo1 lo2 lo3
    lo1="$(printf '%s' "$3" | tr 'A-Z' 'a-z')"; lo2="$(printf '%s' "$4" | tr 'A-Z' 'a-z')"
    lo3="$(printf '%s' "$5" | tr 'A-Z' 'a-z')"
    printf 'ref_upper,ref_lower,note\n%s,%s,stable on review\n%s,%s,no acute findings\n%s,%s,follow up as planned\n' \
        "$3" "$lo1" "$4" "$lo2" "$5" "$lo3" > "$csv"
    python3 "$SCRIPT" scan "$csv" --locale "$loc" -o "$out" >/dev/null 2>&1
    check "case $loc $label: upper case is PHI (positive control)" \
        test "$(classify "$out/scan_report.json" ref_upper)" = PHI
    check "case $loc $label: lower case is PHI" \
        test "$(classify "$out/scan_report.json" ref_lower)" = PHI
    check "case $loc $label: ordinary lower-case text stays SAFE" \
        test "$(classify "$out/scan_report.json" note)" = SAFE
}
case_check in pan      ABCDE1234F PQRST5678Z LMNOP9012K
case_check uk nino     AB123456C  CE654321A  JK112233D
case_check uk postcode "SW1A 1AA" "M1 1AE"   "B33 8TH"
case_check ca postcode "K1A 0B1"  "M5V 3L9"  "H2X 1Y4"

# --- Sparse PHI in a long column: every value is checked, deterministically ---
# The scan used to check a random sample of at most 500 values. A column
# where one value in 5,000 carries a phone number came out SAFE about nine
# runs in ten, and SAFE columns are passed through un-stripped. The verdict
# must not depend on luck, and must not change between runs.
SPARSE_CSV="$OUTDIR/sparse.csv"
python3 - "$SPARSE_CSV" <<'PY'
import csv, sys
with open(sys.argv[1], "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["clinical_note", "value"])
    for i in range(5000):
        note = f"Routine follow up visit, stable, plan unchanged, entry {i}."
        if i == 4321:
            note = "Asked to call back at 555-201-3344 about scheduling."
        w.writerow([note, 1])
PY
python3 "$SCRIPT" scan "$SPARSE_CSV" --locale us -o "$OUTDIR/sparse1" >/dev/null 2>&1
python3 "$SCRIPT" scan "$SPARSE_CSV" --locale us -o "$OUTDIR/sparse2" >/dev/null 2>&1
check "sparse: one phone in 5,000 notes is not SAFE" \
    test "$(classify "$OUTDIR/sparse1/scan_report.json" clinical_note)" != SAFE
check "sparse: all 5,000 values were checked" python3 -c "
import json,sys
d=json.load(open(sys.argv[1]))
x=next(c for c in d['classifications'] if c['column']=='clinical_note')
assert x.get('sample_size')==5000, x" "$OUTDIR/sparse1/scan_report.json"
check "sparse: two runs give identical classifications" python3 -c "
import json,sys
a,b=(json.load(open(p))['classifications'] for p in sys.argv[1:3])
assert a==b" "$OUTDIR/sparse1/scan_report.json" "$OUTDIR/sparse2/scan_report.json"

echo "fail=$fail"; [[ "$fail" -eq 0 ]] && echo "ALL PASS" || echo "FAILURES: $fail"
exit "$fail"
