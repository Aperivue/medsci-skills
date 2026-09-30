#!/usr/bin/env bash
# Regression test for the PHI scanner (deidentify.py scan) and for the
# review/apply safety contract (explicit decisions, no raw values in reports).
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

# --- Fixture 3: edge cases -> REVIEW_NEEDED=2, SAFE=4 (no crash, fixed contract) ---
# Column 5 holds one street address among seven values. It used to be SAFE
# (and so passed through) because fewer than 30% of its values matched; the
# old expectation SAFE == 5 encoded that leak.
python3 "$SCRIPT" scan "$HERE/test_edge_cases.csv" --locale kr -o "$OUTDIR" >/dev/null 2>&1
check "edge fixture: exit 0 (no crash)" test "$?" -eq 0
EDGE_REPORT="$OUTDIR/scan_report.json"
check "edge fixture: REVIEW_NEEDED == 2" test "$(count "$EDGE_REPORT" REVIEW_NEEDED)" -eq 2
check "edge fixture: SAFE == 4"          test "$(count "$EDGE_REPORT" SAFE)"          -eq 4
check "edge fixture: one address in col 5 is REVIEW_NEEDED/address" python3 -c "
import json
c=json.load(open('$EDGE_REPORT'))['classifications'][5]
assert (c['classification'], c['phi_type'])==('REVIEW_NEEDED','address'), c"

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

# ====================================================================
# Review/apply safety contract. Fixtures are built at run time from
# invented values; the RRN-shaped values have an invalid check digit.
# ====================================================================
review_with() {  # usage: review_with <report.json> <answer>...  (one answer per prompt)
    local report="$1"; shift
    printf '%s\n' "$@" | python3 "$SCRIPT" review "$report" >/dev/null 2>&1
}
no_deid_output() { ! ls "$1"/*_deidentified* >/dev/null 2>&1; }

# --- Columns the scanner cannot vouch for are never SAFE ---
# A PHI word inside a longer column name, prose that can carry a name, nine
# chart numbers, and compact YYYYMMDD dates were all SAFE, and SAFE columns
# are kept without being shown when --auto-accept-safe is used.
U="$OUTDIR/unrec"; mkdir -p "$U"
python3 - "$U/unrec.csv" <<'PY'
import csv, sys
names = ["John Carter", "Mary Olsen", "Peter Quill", "Anna Berg", "Tom Hale",
         "Lena Fisk", "Omar Reyes", "Ines Vogt", "Carl Moss"]
with open(sys.argv[1], "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["legal_patient_name", "clinical_note", "ref_code", "visit", "tag",
                "group", "score"])
    for i, n in enumerate(names):
        w.writerow([n, f"Seen with {n} in clinic today, stable, continue current plan.",
                    str(40000000 + i * 7919), f"202601{10 + i}", f"visit=202602{10 + i}",
                    "control" if i % 2 else "treatment", str(60 + i)])
PY
python3 "$SCRIPT" scan "$U/unrec.csv" --locale us -o "$U" >/dev/null 2>&1
for col in legal_patient_name clinical_note ref_code visit tag; do
    check "unrecognised: $col is not SAFE" test "$(classify "$U/scan_report.json" "$col")" != SAFE
done
check "unrecognised: categorical group stays SAFE (control)" \
    test "$(classify "$U/scan_report.json" group)" = SAFE
check "unrecognised: numeric score stays SAFE (control)" \
    test "$(classify "$U/scan_report.json" score)" = SAFE

# --- Reports the agent may read hold no cell values ---
# The scan report used to store five raw values of any chart-number column.
NOVALUES='
import csv, sys
report = open(sys.argv[1], encoding="utf-8").read()
with open(sys.argv[2], newline="") as f:
    cells = [v for row in list(csv.reader(f))[1:] for v in row if len(v) >= 6]
assert cells, "vacuous: no cell values to look for"
leaked = [v for v in cells if v in report]
assert not leaked, leaked'
I="$OUTDIR/ids10"; mkdir -p "$I"
python3 -c "
import sys
rows = ['ref_code,score'] + [f'{40000000 + i * 7919},{60 + i}' for i in range(10)]
open(sys.argv[1], 'w').write('\\n'.join(rows) + '\\n')" "$I/ids.csv"
python3 "$SCRIPT" scan "$I/ids.csv" --locale us -o "$I" >/dev/null 2>&1
check "no raw values: scan report" python3 -c "$NOVALUES" "$I/scan_report.json" "$I/ids.csv"
review_with "$I/scan_report.json" a "" ""
check "no raw values: reviewed report" python3 -c "$NOVALUES" "$I/reviewed_report.json" "$I/ids.csv"
check "no raw values: unrecognised-columns scan report" \
    python3 -c "$NOVALUES" "$U/scan_report.json" "$U/unrec.csv"

# --- Applying needs an explicit, complete review ---
python3 "$SCRIPT" apply "$U/scan_report.json" >/dev/null 2>&1
check "unreviewed report: apply refuses" test "$?" -ne 0
check "unreviewed report: nothing written" no_deid_output "$U"
# Enter and 'f' (flag) used to keep a REVIEW_NEEDED column. Now they are
# asked again, and only the explicit 'a' that follows settles it.
E="$OUTDIR/enter"; mkdir -p "$E"
python3 -c "
import sys
rows = ['note,score'] + ['Routine visit and stable.,1'] * 9 + ['Call back at 555-201-3344 re results.,1']
open(sys.argv[1], 'w').write('\\n'.join(rows) + '\\n')" "$E/e.csv"
python3 "$SCRIPT" scan "$E/e.csv" --locale us -o "$E" >/dev/null 2>&1
check "sparse phone note is REVIEW_NEEDED" test "$(classify "$E/scan_report.json" note)" = REVIEW_NEEDED
review_with "$E/scan_report.json" "" f a "" ""
check "Enter or 'f' does not settle a REVIEW_NEEDED column; 'a' does" python3 -c "
import json, sys
c = json.load(open(sys.argv[1]))['classifications'][0]
assert c['approved_action'] == 'anonymize', c" "$E/reviewed_report.json"
# 3 REVIEW_NEEDED (anonymize), 2 PHI and 2 SAFE (Enter), confirm, key = row
review_with "$U/scan_report.json" a a a "" "" "" "" "" row
check "review: reviewed report written" test -s "$U/reviewed_report.json"
check "no raw values: unrecognised-columns reviewed report" \
    python3 -c "$NOVALUES" "$U/reviewed_report.json" "$U/unrec.csv"
python3 "$SCRIPT" apply "$U/reviewed_report.json" >/dev/null 2>&1
check "free text: anonymize runs (exit 0)" test "$?" -eq 0
check "free text: no name survives in the output" python3 -c "
import sys
out = open(sys.argv[1], encoding='utf-8').read()
leaked = [n for n in ('John Carter', 'Mary Olsen', 'Carl Moss') if n in out]
assert not leaked, leaked" "$U/unrec_deidentified.csv"
check "patient key 'row': one offset per row" python3 -c "
import json, sys
assert len(json.load(open(sys.argv[1]))['date_offsets']) == 9" "$U/mapping.json"
mkdir -p "$U/flag" && python3 - "$U/reviewed_report.json" "$U/flag/reviewed_report.json" <<'PY'
import json, sys
r = json.load(open(sys.argv[1]))
next(c for c in r["classifications"] if c["column"] == "clinical_note")["approved_action"] = "flag"
json.dump(r, open(sys.argv[2], "w"))
PY
python3 "$SCRIPT" apply "$U/flag/reviewed_report.json" >/dev/null 2>&1
check "unresolved 'flag' decision: apply refuses" test "$?" -ne 0
check "unresolved 'flag' decision: nothing written" no_deid_output "$U/flag"

# --- A column added after the review is not passed through ---
C="$OUTDIR/changed"; mkdir -p "$C"
printf 'patient_name,score\nJohn Carter,61\nMary Olsen,62\n' > "$C/c.csv"
python3 "$SCRIPT" scan "$C/c.csv" --locale us -o "$C" >/dev/null 2>&1
review_with "$C/scan_report.json" "" "" ""
printf 'patient_name,score,contact\nJohn Carter,61,555-201-3344\nMary Olsen,62,555-201-3345\n' > "$C/c.csv"
python3 "$SCRIPT" apply "$C/reviewed_report.json" >/dev/null 2>&1
check "column added after review: apply refuses" test "$?" -ne 0
check "column added after review: nothing written" no_deid_output "$C"

# --- Dates shift per chosen patient key; audit hashes are keyed ---
V="$OUTDIR/visits"; mkdir -p "$V"
printf '%s\n' 'mrn,patient_name,admit_date,discharge_date' \
    '10000001,John Carter,2024-01-10,2024-01-15' '10000001,John Carter,2024-03-01,2024-03-04' \
    '10000002,Mary Olsen,2024-02-01,2024-02-03' > "$V/v.csv"
python3 "$SCRIPT" scan "$V/v.csv" --locale us -o "$V" >/dev/null 2>&1
review_with "$V/scan_report.json" "" "" "" "" "" 1
python3 "$SCRIPT" apply "$V/reviewed_report.json" >/dev/null 2>&1
check "patient key: apply runs (exit 0)" test "$?" -eq 0
check "patient key: one offset per patient, intervals kept across rows" python3 -c "
import csv, json, sys
from datetime import date
rows = list(csv.DictReader(open(sys.argv[1])))
d = lambda s: date.fromisoformat(s)
assert len(json.load(open(sys.argv[2]))['date_offsets']) == 2
assert (d(rows[1]['admit_date']) - d(rows[0]['admit_date'])).days == 51, rows
assert [(d(r['discharge_date']) - d(r['admit_date'])).days for r in rows] == [5, 3, 2], rows
" "$V/v_deidentified.csv" "$V/mapping.json"
check "audit: plain SHA-256 of an original date is not in the log" python3 -c "
import csv, hashlib, sys
audit = open(sys.argv[1]).read()
for v in ('2024-01-10', '2024-03-04', 'John Carter', '10000001'):
    assert hashlib.sha256(v.encode()).hexdigest() not in audit, v" "$V/audit_log.csv"
check "audit: keyed hash verifies with the key in mapping.json (control)" python3 -c "
import csv, hashlib, hmac, json, sys
key = bytes.fromhex(json.load(open(sys.argv[2]))['_meta']['audit_hash_key'])
row = next(r for r in csv.DictReader(open(sys.argv[1])) if r['column'] == 'admit_date')
want = hmac.new(key, b'2024-01-10', hashlib.sha256).hexdigest()
assert row['row'] == '0' and row['before_hash'] == want, row" "$V/audit_log.csv" "$V/mapping.json"
mkdir -p "$V/nokey" && python3 - "$V/reviewed_report.json" "$V/nokey/reviewed_report.json" <<'PY'
import json, sys
r = json.load(open(sys.argv[1])); r.pop("patient_key", None); json.dump(r, open(sys.argv[2], "w"))
PY
python3 "$SCRIPT" apply "$V/nokey/reviewed_report.json" >/dev/null 2>&1
check "dates without a patient key: apply refuses" test "$?" -ne 0
check "dates without a patient key: nothing written" no_deid_output "$V/nokey"
mkdir -p "$V/blank" && cp "$V/reviewed_report.json" "$V/blank/"
sed -i.bak 's/^10000002,/,/' "$V/v.csv"
python3 "$SCRIPT" apply "$V/blank/reviewed_report.json" >/dev/null 2>&1
check "blank patient key on a dated row: apply refuses" test "$?" -ne 0
check "blank patient key on a dated row: nothing written" no_deid_output "$V/blank"

# --- An address matching the detector is never SAFE, however rare ---
python3 - "$OUTDIR/addr_kr.csv" "$OUTDIR/addr_us.csv" <<'PY'
import csv, sys
kr = "".join(map(chr, [0xC11C, 0xC6B8, 0xD2B9, 0xBCC4, 0xC2DC, 32, 0xAC15, 0xB0A8,
                        0xAD6C, 32, 0xD14C, 0xD5E4, 0xB780, 0xB85C])) + " 12"  # a Seoul street address
for path, addr in ((sys.argv[1], kr), (sys.argv[2], "Lives at 12 Oak Street")):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["memo", "flag"])
        for i in range(10):
            w.writerow([addr if i == 3 else f"check {i}", "yes"])
PY
for loc in kr us; do
    python3 "$SCRIPT" scan "$OUTDIR/addr_$loc.csv" --locale $loc -o "$OUTDIR/addr_$loc" >/dev/null 2>&1
    check "sparse address ($loc): one in ten is REVIEW_NEEDED" \
        test "$(classify "$OUTDIR/addr_$loc/scan_report.json" memo)" = REVIEW_NEEDED
    check "sparse address ($loc): other column stays SAFE (control)" \
        test "$(classify "$OUTDIR/addr_$loc/scan_report.json" flag)" = SAFE
done

# --- Separators and international prefixes do not hide an identifier ---
K="$OUTDIR/kr_variants"; mkdir -p "$K"
printf '%s\n' 'ref_a,ref_b,ref_c,note' \
    '8503151234567,+82 10 1234 5678,010 1234 5678,stable' \
    '9001012345671,+82-10-9876-5432,010.9876.5432,no change' > "$K/k.csv"
python3 "$SCRIPT" scan "$K/k.csv" --locale kr -o "$K" >/dev/null 2>&1
check "kr: national ID without hyphen is PHI/rrn" python3 -c "
import json, sys
c = next(x for x in json.load(open(sys.argv[1]))['classifications'] if x['column'] == 'ref_a')
assert (c['classification'], c['phi_type']) == ('PHI', 'rrn'), c" "$K/scan_report.json"
check "kr: +82 phone is PHI"               test "$(classify "$K/scan_report.json" ref_b)" = PHI
check "kr: spaced/dotted phone is PHI"     test "$(classify "$K/scan_report.json" ref_c)" = PHI
check "kr: short note stays SAFE (control)" test "$(classify "$K/scan_report.json" note)" = SAFE
for spec in "de|+49 30 12345678" "jp|090 1234 5678" "cn|+86 138 1234 5678" \
            "in|+91 98765 43210" "fr|+33 6 12 34 56 78"; do
    loc="${spec%%|*}"; num="${spec#*|}"
    printf 'contact,note\n"call %s",stable\n' "$num" > "$OUTDIR/intl_$loc.csv"
    python3 "$SCRIPT" scan "$OUTDIR/intl_$loc.csv" --locale "$loc" -o "$OUTDIR/intl_$loc" >/dev/null 2>&1
    check "$loc: '$num' is not SAFE" \
        test "$(classify "$OUTDIR/intl_$loc/scan_report.json" contact)" != SAFE
done

# --- Native Excel dates are shifted, not replaced by [DATE_SHIFTED] ---
check "excel dates: datetime cells shift and keep their interval" python3 -c "
import sys; sys.path.insert(0, sys.argv[1])
from datetime import datetime
import deidentify as d
a, b, t = (d._cell_text(x) for x in (datetime(2020, 1, 2), datetime(2020, 1, 9),
                                     datetime(2021, 5, 3, 14, 30)))
s = d.DateShifter(seed=7)
sa, sb, st = s.shift(a, 'p'), s.shift(b, 'p'), s.shift(t, 'p')
assert '[DATE_SHIFTED]' not in (sa, sb, st), (sa, sb, st)
assert (datetime.fromisoformat(sb) - datetime.fromisoformat(sa)).days == 7
assert st.endswith(' 14:30:00'), st" "$SKILL"
if python3 -c "import openpyxl" 2>/dev/null; then
    X="$OUTDIR/xlsx"; mkdir -p "$X"
    python3 -c "
import sys, openpyxl
from datetime import datetime
wb = openpyxl.Workbook(); ws = wb.active
ws.append(['mrn', 'admission_date', 'discharge_date'])
ws.append(['10000001', datetime(2020, 1, 2), datetime(2020, 1, 9)])
wb.save(sys.argv[1])" "$X/x.xlsx"
    python3 "$SCRIPT" scan "$X/x.xlsx" --locale us -o "$X" >/dev/null 2>&1
    review_with "$X/scan_report.json" "" "" "" "" 1
    python3 "$SCRIPT" apply "$X/reviewed_report.json" >/dev/null 2>&1
    check "excel dates: end to end through an .xlsx file" python3 -c "
import sys, openpyxl
from datetime import datetime
r = list(openpyxl.load_workbook(sys.argv[1]).active.iter_rows(values_only=True))[1]
a, b = (datetime.fromisoformat(v) for v in r[1:])
assert (b - a).days == 7, r" "$X/x_deidentified.xlsx"
else
    echo "  SKIP  excel dates end to end (openpyxl not installed; unit check above ran)"
fi

# --- Importable on Python 3.9 (stock macOS python3) ---
# 'X | None' in a signature is evaluated at import on 3.9 unless annotations
# are postponed. Checked statically so it holds on any CI interpreter.
check "py3.9: PEP 604 annotations are postponed" python3 -c "
import ast, sys
tree = ast.parse(open(sys.argv[1], encoding='utf-8').read())
postponed = any(isinstance(n, ast.ImportFrom) and n.module == '__future__'
                and any(a.name == 'annotations' for a in n.names) for n in tree.body)
def union(a):
    return a is not None and any(isinstance(x, ast.BinOp) and isinstance(x.op, ast.BitOr)
                                 for x in ast.walk(a))
uses = [f.name for f in ast.walk(tree) if isinstance(f, (ast.FunctionDef, ast.AsyncFunctionDef))
        and (union(f.returns) or any(union(a.annotation) for a in f.args.args + f.args.kwonlyargs))]
assert postponed or not uses, uses" "$SCRIPT"
for py in python3.9 /usr/bin/python3; do
    if command -v "$py" >/dev/null 2>&1 && "$py" -c 'import sys; sys.exit(sys.version_info[:2] != (3, 9))'; then
        check "py3.9: --help runs under $py" "$py" "$SCRIPT" --help
        break
    fi
done

# --- A row with more fields than the header is refused, not passed through ---
# csv.DictReader files the extra field under the key None. No column holds
# it, so the review never showed it, and "keep" wrote it to the output.
G="$OUTDIR/ragged"; mkdir -p "$G"
printf 'score\n1,SYNTHETIC_SECRET_NAME\n' > "$G/r.csv"
python3 "$SCRIPT" scan "$G/r.csv" --locale us -o "$G" > "$G/scan.out" 2>&1
check "ragged row: scan refuses" test "$?" -ne 0
check "ragged row: scan writes no report" test ! -e "$G/scan_report.json"
check "ragged row: message gives the line, not the value" python3 -c "
import sys
out = open(sys.argv[1]).read()
assert 'line 2' in out and 'SYNTHETIC_SECRET_NAME' not in out, out" "$G/scan.out"
mkdir -p "$G/apply" && printf 'score\n1\n' > "$G/apply/r.csv"
python3 "$SCRIPT" scan "$G/apply/r.csv" --locale us -o "$G/apply" >/dev/null 2>&1
review_with "$G/apply/scan_report.json" "" ""
printf 'score\n1,SYNTHETIC_SECRET_NAME\n' > "$G/apply/r.csv"
python3 "$SCRIPT" apply "$G/apply/reviewed_report.json" > "$G/apply.out" 2>&1
check "ragged row: apply refuses" test "$?" -ne 0
check "ragged row: apply writes nothing" no_deid_output "$G/apply"
check "ragged row: apply message has no value" \
    python3 -c "import sys; assert 'SYNTHETIC_SECRET_NAME' not in open(sys.argv[1]).read()" "$G/apply.out"
# A short row is only missing values; it is kept (and must not crash review).
mkdir -p "$G/short" && printf 'mrn,dob\n10000001,2001-02-03\n10000002\n' > "$G/short/s.csv"
python3 "$SCRIPT" scan "$G/short/s.csv" --locale us -o "$G/short" >/dev/null 2>&1
review_with "$G/short/scan_report.json" "" "" "" 1
python3 "$SCRIPT" apply "$G/short/reviewed_report.json" >/dev/null 2>&1
check "short row: review and apply run (exit 0)" test "$?" -eq 0
check "short row: both rows written" \
    python3 -c "import csv, sys; assert len(list(csv.reader(open(sys.argv[1])))) == 3" "$G/short/s_deidentified.csv"

# --- A shifted date is never the original date ---
# Offsets were drawn from [-365, 365], so about one patient in 731 got 0:
# with seed 827 the first patient's date of birth came out unchanged, and
# the audit log's after_value showed it next to the keyed before_hash.
check "date shift: no offset is zero (seeds 0-2999)" python3 -c "
import sys; sys.path.insert(0, sys.argv[1])
import deidentify as d
same = [s for s in range(3000) if d.DateShifter(seed=s).shift('2001-02-03', 'p') == '2001-02-03']
assert not same, same[:5]" "$SKILL"
check "date shift: output and audit never repeat an input date (seeds 0-999)" python3 -c "
import sys; sys.path.insert(0, sys.argv[1])
import deidentify as d
data = [{'mrn': '10000001', 'dob': '2001-02-03'}, {'mrn': '10000002', 'dob': '1999-12-31'}]
rep = {'reviewed': True, 'patient_key': {'type': 'column', 'column': 'mrn'},
       'classifications': [{'column': 'mrn', 'phi_type': 'id', 'approved_action': 'keep'},
                           {'column': 'dob', 'phi_type': 'date', 'approved_action': 'anonymize'}]}
for seed in range(1000):
    out, _, audit = d.apply_anonymization(data, rep, date_shift_seed=seed)
    for row, orig in zip(out, data):
        assert row['dob'] != orig['dob'], (seed, row)
    for a in audit:
        assert a['after_value'] not in ('2001-02-03', '1999-12-31'), (seed, a)" "$SKILL"

echo "fail=$fail"; [[ "$fail" -eq 0 ]] && echo "ALL PASS" || echo "FAILURES: $fail"
exit "$fail"
