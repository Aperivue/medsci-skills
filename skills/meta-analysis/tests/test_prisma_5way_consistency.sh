#!/usr/bin/env bash
# Regression tests for meta-analysis prisma_5way_consistency.py (DI-6).
#
# Each positive fixture isolates one false clearance the checker used to give
# (exit 0, "PASS"):
#   A. included.k = 12 "found" in methods.md because of "Follow-up was 12 months",
#      while the text actually reports nine studies. The checker does not try to
#      tell a count from a duration in prose; it must report the surface
#      NOT_ASSESSED (never PASS / OK), and exit 3 under --strict.
#   B. the SSOT's own flow arithmetic is impossible (15 assessed - 3 excluded is
#      12, but k = 13), and every surface faithfully repeats the wrong k.
#   C. a search CSV with a quoted multi-line abstract: 2 records, 3 data lines;
#      line counting matched an SSOT total of 3.
#   F, G: see each block (F1/F2/F4/F6 are negative controls for two-column flows).
# Negative controls: a consistent PRISMA flow whose prose carries "1,500" and a
# multi-line CSV record (exit 0, no mismatch), and a structured-only SSOT with
# no prose surface (verdict PASS, exit 0 even under --strict).

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
SCRIPT="$REPO_ROOT/skills/meta-analysis/scripts/prisma_5way_consistency.py"
TMP="$(mktemp -d -t prisma5.XXXXXX)"
trap 'rm -rf "$TMP"' EXIT

[[ -f "$SCRIPT" ]] || { echo "ENV-ERR: script missing" >&2; exit 2; }
python3 -c "import yaml" 2>/dev/null || { echo "SKIP: pyyaml unavailable"; exit 0; }

fail=0
ran=0
assert_exit() {
    local label="$1" expected="$2" actual="$3"
    ran=$((ran + 1))
    if [[ "$expected" == "$actual" ]]; then
        printf '  PASS  %-55s exit=%s\n' "$label" "$actual"
    else
        printf '  FAIL  %-55s expected=%s actual=%s\n' "$label" "$expected" "$actual"
        fail=$((fail + 1))
    fi
}

# write_csv DIR N : N single-line records under DIR/1_Search/db.csv
write_csv() {
    mkdir -p "$1/1_Search"
    python3 - "$1/1_Search/db.csv" "$2" <<'PY'
import sys
with open(sys.argv[1], "w") as fh:
    fh.write("id,title\n")
    for i in range(int(sys.argv[2])):
        fh.write(f"{i + 1},Record {i + 1}\n")
PY
}

# --------------------------------------------------------------------------
# A: k appears only as a follow-up duration
# --------------------------------------------------------------------------
mkdir -p "$TMP/a/7_Manuscript"
write_csv "$TMP/a" 20
cat > "$TMP/a/prisma.yaml" <<'EOF'
databases: {pubmed: 20}
deduplication: {after_dedup: 20}
screening: {title_abstract_excluded: 5, full_text_assessed: 15, full_text_excluded: 3}
included: {k: 12}
exclusion_reasons: {wrong_population: 3}
surfaces:
  search_csv_glob: "1_Search/*.csv"
  methods_md: {path: "7_Manuscript/methods.md", require: ["included.k"]}
EOF
echo "Nine (9) studies were included. Follow-up was 12 months." > "$TMP/a/7_Manuscript/methods.md"
python3 "$SCRIPT" --ssot "$TMP/a/prisma.yaml" --project-root "$TMP/a" --json > "$TMP/a/out.json"
assert_exit "A: k present only as '12 months' (no mismatch, exit 0)" 0 $?
python3 - "$TMP/a/out.json" <<'PY' || { echo "  FAIL  A: surface must be NOT_ASSESSED"; fail=$((fail + 1)); }
import json, sys
r = json.load(open(sys.argv[1]))
s = r["surfaces"]["methods_md"]
assert s["status"] == "NOT_ASSESSED", s
assert s["present_not_verified_as_count"] == ["included.k"], s
assert r["verdict"] == "NOT_ASSESSED", r["verdict"]
assert any(m.startswith("methods_md:") for m in r["not_assessed"]), r["not_assessed"]
PY
python3 "$SCRIPT" --ssot "$TMP/a/prisma.yaml" --project-root "$TMP/a" > "$TMP/a/out.txt"
assert_exit "A: text mode exit 0" 0 $?
if grep -q "PASS" "$TMP/a/out.txt" || ! grep -q "NOT_ASSESSED" "$TMP/a/out.txt"; then
    echo "  FAIL  A: text output must say NOT_ASSESSED, never PASS"; fail=$((fail + 1))
fi
python3 "$SCRIPT" --ssot "$TMP/a/prisma.yaml" --project-root "$TMP/a" --strict > /dev/null
assert_exit "A: --strict, prose surface NOT_ASSESSED (exit 3)" 3 $?

# A2: k absent from the surface altogether -> FAIL (unchanged from main).
echo "Nine (9) studies were included. Follow-up was 6 months." > "$TMP/a/7_Manuscript/methods.md"
python3 "$SCRIPT" --ssot "$TMP/a/prisma.yaml" --project-root "$TMP/a" --json > "$TMP/a/out2.json"
assert_exit "A2: k absent from methods.md (FAIL)" 1 $?
python3 - "$TMP/a/out2.json" <<'PY' || fail=$((fail + 1))
import json, sys
r = json.load(open(sys.argv[1]))
assert r["surfaces"]["methods_md"]["missing_numbers"] == ["included.k"], r
assert r["verdict"] == "FAIL", r["verdict"]
PY

# --------------------------------------------------------------------------
# B: impossible flow arithmetic, repeated consistently on every surface
# --------------------------------------------------------------------------
mkdir -p "$TMP/b/7_Manuscript"
write_csv "$TMP/b" 20
cat > "$TMP/b/prisma.yaml" <<'EOF'
databases: {pubmed: 20}
deduplication: {after_dedup: 20}
screening: {title_abstract_excluded: 5, full_text_assessed: 15, full_text_excluded: 3}
included: {k: 13}
exclusion_reasons: {wrong_population: 3}
surfaces:
  search_csv_glob: "1_Search/*.csv"
  methods_md: {path: "7_Manuscript/methods.md", require: ["included.k"]}
EOF
echo "Thirteen (13) studies were included." > "$TMP/b/7_Manuscript/methods.md"
python3 "$SCRIPT" --ssot "$TMP/b/prisma.yaml" --project-root "$TMP/b" --json > "$TMP/b/out.json"
assert_exit "B: assessed - excluded != k (FAIL)" 1 $?
python3 - "$TMP/b/out.json" <<'PY' || fail=$((fail + 1))
import json, sys
r = json.load(open(sys.argv[1]))
bad = [c["identity"] for c in r["flow_identities"] if not c["ok"]]
assert bad == ["full_text_assessed - full_text_excluded = included.k"], r["flow_identities"]
PY

# --------------------------------------------------------------------------
# C: multi-line CSV record counted as two
# --------------------------------------------------------------------------
mkdir -p "$TMP/c/1_Search"
printf 'id,title,abstract\n1,"A","line one\nline two"\n2,"B","x"\n' > "$TMP/c/1_Search/db.csv"
cat > "$TMP/c/prisma.yaml" <<'EOF'
databases: {pubmed: 3}
surfaces:
  search_csv_glob: "1_Search/*.csv"
EOF
python3 "$SCRIPT" --ssot "$TMP/c/prisma.yaml" --project-root "$TMP/c" --json > "$TMP/c/out.json"
assert_exit "C: 2 CSV records vs SSOT 3 (FAIL)" 1 $?
python3 - "$TMP/c/out.json" <<'PY' || fail=$((fail + 1))
import json, sys
r = json.load(open(sys.argv[1]))
assert r["surfaces"]["search_csv"]["found"] == 2, r
PY

# --------------------------------------------------------------------------
# Negative control: consistent flow, decoy numbers, multi-line record
# --------------------------------------------------------------------------
mkdir -p "$TMP/n/7_Manuscript"
write_csv "$TMP/n" 1499
printf '1500,"Last","an abstract\nthat wraps"\n' >> "$TMP/n/1_Search/db.csv"
cat > "$TMP/n/prisma.yaml" <<'EOF'
databases: {pubmed: 1200, embase: 300}
deduplication: {after_dedup: 1500}
screening: {title_abstract_excluded: 1400, full_text_assessed: 100, full_text_excluded: 85}
included: {k: 15}
exclusion_reasons: {wrong_population: 30, wrong_intervention: 25, wrong_outcome: 20, wrong_study_design: 10}
surfaces:
  search_csv_glob: "1_Search/*.csv"
  results_md: "7_Manuscript/results.md"
EOF
cat > "$TMP/n/7_Manuscript/results.md" <<'EOF'
Searches returned 1,200 PubMed and 300 Embase records; 1,500 remained after
deduplication. After 1400 were excluded at title/abstract screening, 100 full
texts were assessed and 85 excluded (wrong population 30, wrong intervention 25,
wrong outcome 20, wrong study design 10). Fifteen (15) studies were included
(Table 2) [12], with median follow-up of 24 months.
EOF
python3 "$SCRIPT" --ssot "$TMP/n/prisma.yaml" --project-root "$TMP/n" --json > "$TMP/n/out.json"
assert_exit "negative: consistent flow, '1,500' form (no mismatch)" 0 $?
python3 - "$TMP/n/out.json" <<'PY' || { echo "  FAIL  negative: report"; fail=$((fail + 1)); }
import json, sys
r = json.load(open(sys.argv[1]))
assert r["mismatches"] == [], r["mismatches"]
assert all(c["status"] == "OK" for c in r["flow_identities"]), r["flow_identities"]
assert r["surfaces"]["search_csv"]["ok"] is True, r["surfaces"]["search_csv"]
assert r["surfaces"]["results_md"]["status"] == "NOT_ASSESSED", r["surfaces"]["results_md"]
PY

# Negative control for --strict: structured surfaces only (flow + CSV), all OK.
mkdir -p "$TMP/p"
write_csv "$TMP/p" 20
cat > "$TMP/p/prisma.yaml" <<'EOF'
databases: {pubmed: 20}
deduplication: {after_dedup: 20}
screening: {title_abstract_excluded: 5, full_text_assessed: 15, full_text_excluded: 3, reports_not_retrieved: 0, other_methods_assessed: 0}
included: {k: 12}
exclusion_reasons: {wrong_population: 3}
surfaces:
  search_csv_glob: "1_Search/*.csv"
EOF
python3 "$SCRIPT" --ssot "$TMP/p/prisma.yaml" --project-root "$TMP/p" --strict --json > "$TMP/p/out.json"
assert_exit "negative: structured-only SSOT, --strict (PASS)" 0 $?
python3 - "$TMP/p/out.json" <<'PY' || { echo "  FAIL  negative: verdict PASS"; fail=$((fail + 1)); }
import json, sys
r = json.load(open(sys.argv[1]))
assert r["verdict"] == "PASS" and r["not_assessed"] == [], r
PY

# --------------------------------------------------------------------------
# F: PRISMA 2020 two-column flow. 90 after dedup - 70 TA-excluded = 20 database
# reports, plus 5 from citation searching = 25 assessed.
#   F1 (negative): other_methods_assessed undeclared -> the identity cannot be
#       decided; NOT_ASSESSED, exit 0 (round 1 failed it, 20 vs 25).
#   F2 (negative): declared 5 -> OK.
#   F3 (positive): declared 2 -> FAIL (22 vs 25).
#   F4 (negative): 2 reports not retrieved, key undeclared -> NOT_ASSESSED.
#   F5 (positive): reports_not_retrieved declared 0 but the gap is 2 -> FAIL.
#   F6 (negative): 25 - 13 = 12 reports for k = 10 studies; included.reports
#       undeclared -> NOT_ASSESSED, declared 12 -> OK.
# --------------------------------------------------------------------------
mkdir -p "$TMP/f"
run_flow() {  # run_flow LABEL EXPECTED_EXIT IDENTITY_PREFIX EXPECTED_STATUS YAML
    printf '%s\n' "$5" > "$TMP/f/prisma.yaml"
    python3 "$SCRIPT" --ssot "$TMP/f/prisma.yaml" --project-root "$TMP/f" --json > "$TMP/f/out.json"
    assert_exit "$1" "$2" $?
    python3 - "$TMP/f/out.json" "$3" "$4" <<'PY' || { echo "  FAIL  $1: identity status"; fail=$((fail + 1)); }
import json, sys
r = json.load(open(sys.argv[1]))
rows = [c for c in r["flow_identities"] if c["identity"].startswith(sys.argv[2])]
assert len(rows) == 1 and rows[0]["status"] == sys.argv[3], r["flow_identities"]
PY
}
run_flow "F1: other-methods reports, key undeclared (NOT_ASSESSED)" 0 "after_dedup" NOT_ASSESSED \
'deduplication: {after_dedup: 90}
screening: {title_abstract_excluded: 70, full_text_assessed: 25, full_text_excluded: 15}
included: {k: 10}'
python3 "$SCRIPT" --ssot "$TMP/f/prisma.yaml" --project-root "$TMP/f" --strict > /dev/null
assert_exit "F1: --strict, identity NOT_ASSESSED (exit 3)" 3 $?
run_flow "F2: other_methods_assessed 5 declared (PASS)" 0 "after_dedup" OK \
'deduplication: {after_dedup: 90}
screening: {title_abstract_excluded: 70, full_text_assessed: 25, full_text_excluded: 15, other_methods_assessed: 5}
included: {k: 10}'
run_flow "F3: other_methods_assessed 2 declared, gap 5 (FAIL)" 1 "after_dedup" FAIL \
'deduplication: {after_dedup: 90}
screening: {title_abstract_excluded: 70, full_text_assessed: 25, full_text_excluded: 15, other_methods_assessed: 2}
included: {k: 10}'
run_flow "F4: reports not retrieved, key undeclared (NOT_ASSESSED)" 0 "after_dedup" NOT_ASSESSED \
'deduplication: {after_dedup: 90}
screening: {title_abstract_excluded: 70, full_text_assessed: 18, full_text_excluded: 8}
included: {k: 10}'
run_flow "F5: reports_not_retrieved 0 declared, gap 2 (FAIL)" 1 "after_dedup" FAIL \
'deduplication: {after_dedup: 90}
screening: {title_abstract_excluded: 70, full_text_assessed: 18, full_text_excluded: 8, reports_not_retrieved: 0}
included: {k: 10}'
run_flow "F6a: 12 reports vs k 10, reports undeclared (NOT_ASSESSED)" 0 "full_text_assessed" NOT_ASSESSED \
'screening: {full_text_assessed: 25, full_text_excluded: 13}
included: {k: 10}'
run_flow "F6b: included.reports 12 declared (PASS)" 0 "full_text_assessed" OK \
'screening: {full_text_assessed: 25, full_text_excluded: 13}
included: {k: 10, reports: 12}'

# --------------------------------------------------------------------------
# G: a non-numeric SSOT count is a clean exit 2, not a traceback.
# --------------------------------------------------------------------------
mkdir -p "$TMP/g"
printf 'screening: {full_text_assessed: "about 25", full_text_excluded: 13}\nincluded: {k: 10}\n' > "$TMP/g/prisma.yaml"
python3 "$SCRIPT" --ssot "$TMP/g/prisma.yaml" --project-root "$TMP/g" > /dev/null 2> "$TMP/g/err"
assert_exit "G: non-numeric SSOT count (exit 2)" 2 $?
if grep -q Traceback "$TMP/g/err"; then echo "  FAIL  G: traceback"; fail=$((fail + 1)); fi

echo ""
echo "ran=$ran fail=$fail"
[[ $fail -eq 0 ]]
