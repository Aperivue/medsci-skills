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

echo "fail=$fail"; [[ "$fail" -eq 0 ]] && echo "ALL PASS" || echo "FAILURES: $fail"
exit "$fail"
