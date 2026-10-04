#!/usr/bin/env bash
# Regression tests for meta-analysis prisma_5way_consistency.py (DI-6).
#
# Each positive fixture isolates one false clearance the checker used to give
# (exit 0, "PASS"):
#   A. included.k = 12 "found" in methods.md because of "Follow-up was 12 months",
#      while the text actually reports nine studies. The checker does not try to
#      tell a count from a duration in prose; it must report the surface
#      NOT_ASSESSED (never PASS / OK), and exit 3 under --strict.
#   B. the SSOT's own flow arithmetic is wrong (15 assessed - 3 excluded is 12
#      reports, but included.reports = 13), and every surface faithfully
#      repeats the wrong number. Without included.reports the same gap against
#      k is NOT_ASSESSED (a report may hold several studies), never FAIL (B0).
#   C. a search CSV with a quoted multi-line abstract: 2 records, 3 data lines;
#      line counting matched an SSOT total of 3.
#   F, G, P: see each block (F0/F6/F7/F8 are negative controls; P is the
#   optional prisma2020 report-level section).
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
assert_exit "B0: assessed - excluded != k, reports undeclared (exit 0)" 0 $?
python3 - "$TMP/b/out.json" <<'PY' || fail=$((fail + 1))
import json, sys
r = json.load(open(sys.argv[1]))
rows = {c["identity"]: c for c in r["flow_identities"]}
row = rows["full_text_assessed - full_text_excluded = included.k"]
assert row["status"] == "NOT_ASSESSED" and "included.reports" in row["note"], row
assert r["mismatches"] == [], r["mismatches"]
PY
sed -i 's/included: {k: 13}/included: {k: 13, reports: 13}/' "$TMP/b/prisma.yaml"
python3 "$SCRIPT" --ssot "$TMP/b/prisma.yaml" --project-root "$TMP/b" --json > "$TMP/b/out.json"
assert_exit "B: assessed - excluded != included.reports (FAIL)" 1 $?
python3 - "$TMP/b/out.json" <<'PY' || fail=$((fail + 1))
import json, sys
r = json.load(open(sys.argv[1]))
bad = [c["identity"] for c in r["flow_identities"] if c["ok"] is False]
assert bad == ["full_text_assessed - full_text_excluded = included.reports"], r["flow_identities"]
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
screening: {title_abstract_excluded: 5, full_text_assessed: 15, full_text_excluded: 3}
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
# F: flow identities, one row each.
#   F0 (negative, reviewer counterexample): a PRISMA 2020 flow where 100
#       records were removed before screening by automation tools. The SSOT
#       has no key for them, so after_dedup -> full_text_assessed is not
#       checked at all (same as main); exit 0 with reports_not_retrieved 0 or 5.
#   F6 (negative): 25 - 13 = 12 reports for k = 10 studies; included.reports
#       undeclared -> NOT_ASSESSED, declared 12 -> OK.
#   F7-F9: PRISMA 2009 records from other sources added before dedup.
# --------------------------------------------------------------------------
mkdir -p "$TMP/f"
run_flow() {  # run_flow LABEL EXPECTED_EXIT IDENTITY_PREFIX EXPECTED_STATUS YAML
    printf '%s\n' "$5" > "$TMP/f/prisma.yaml"
    python3 "$SCRIPT" --ssot "$TMP/f/prisma.yaml" --project-root "$TMP/f" --json > "$TMP/f/out.json"
    assert_exit "$1" "$2" $?
    python3 - "$TMP/f/out.json" "$3" "$4" <<'PY2' || { echo "  FAIL  $1: identity status"; fail=$((fail + 1)); }
import json, sys
r = json.load(open(sys.argv[1]))
rows = [c for c in r["flow_identities"] if c["identity"].startswith(sys.argv[2])]
assert len(rows) == 1 and rows[0]["status"] == sys.argv[3], r["flow_identities"]
PY2
}
for nr in 0 5; do
    printf '%s\n' \
'databases: {pubmed: 600, embase: 400}' \
'deduplication: {after_dedup: 800}' \
"screening: {title_abstract_excluded: 620, reports_not_retrieved: $nr, full_text_assessed: 80, full_text_excluded: 65}" \
'included: {k: 15}' \
'exclusion_reasons: {a: 40, b: 25}' > "$TMP/f/prisma.yaml"
    python3 "$SCRIPT" --ssot "$TMP/f/prisma.yaml" --project-root "$TMP/f" --json > "$TMP/f/out.json"
    assert_exit "F0: 100 removed before screening, not_retrieved $nr (exit 0)" 0 $?
    python3 - "$TMP/f/out.json" <<'PY2' || { echo "  FAIL  F0: no after_dedup identity, no mismatch"; fail=$((fail + 1)); }
import json, sys
r = json.load(open(sys.argv[1]))
assert r["mismatches"] == [], r["mismatches"]
assert not any(c["identity"].startswith("after_dedup") for c in r["flow_identities"]), r
PY2
done
run_flow "F6a: 12 reports vs k 10, reports undeclared (NOT_ASSESSED)" 0 "full_text_assessed" NOT_ASSESSED \
'screening: {full_text_assessed: 25, full_text_excluded: 13}
included: {k: 10}'
run_flow "F6b: included.reports 12 declared (PASS)" 0 "full_text_assessed" OK \
'screening: {full_text_assessed: 25, full_text_excluded: 13}
included: {k: 10, reports: 12}'

run_flow "F7: PRISMA 2009, other records before dedup, key undeclared (NOT_ASSESSED)" 0 "sum(databases)" NOT_ASSESSED \
'databases: {pubmed: 60, embase: 40}
deduplication: {after_dedup: 104}'
run_flow "F8: other_sources_before_dedup 6 declared (PASS)" 0 "sum(databases)" OK \
'databases: {pubmed: 60, embase: 40}
deduplication: {after_dedup: 104, other_sources_before_dedup: 6}'
run_flow "F9: other_sources_before_dedup 0 declared, after_dedup too big (FAIL)" 1 "sum(databases)" FAIL \
'databases: {pubmed: 60, embase: 40}
deduplication: {after_dedup: 104, other_sources_before_dedup: 0}'

# --------------------------------------------------------------------------
# H: reports vs studies (reviewer counterexamples; main exits 0 on all).
#   H1 (negative): DTA review, 60 assessed - 40 excluded = 20 articles, k = 24
#       cohorts, included.reports undeclared -> NOT_ASSESSED naming
#       included.reports, exit 0 (round 2 failed it, 20 vs 24).
#   H2 (negative): PRISMA 2020 updated review, 30 - 20 = 10 new reports, k = 15
#       (10 new + 5 from the previous version) -> NOT_ASSESSED, exit 0.
#   H3 (negative): H1 with included.reports 20 declared -> identity OK; the
#       reports >= k row is NOT_ASSESSED (a report may hold several cohorts).
#   H4 (positive): included.reports 22 declared, 20 reports -> FAIL.
#   H5 (negative): reports 12 >= k 10, both declared -> both rows OK.
# --------------------------------------------------------------------------
run_flow "H1: DTA 20 articles / 24 cohorts, reports undeclared (NOT_ASSESSED)" 0 "full_text_assessed" NOT_ASSESSED \
'screening: {full_text_assessed: 60, full_text_excluded: 40}
included: {k: 24}'
python3 - "$TMP/f/out.json" <<'PY' || { echo "  FAIL  H1: note must name included.reports"; fail=$((fail + 1)); }
import json, sys
r = json.load(open(sys.argv[1]))
assert r["mismatches"] == [] and "included.reports" in r["flow_identities"][0]["note"], r
PY
run_flow "H2: updated review, 10 new + 5 previous studies (NOT_ASSESSED)" 0 "full_text_assessed" NOT_ASSESSED \
'screening: {full_text_assessed: 30, full_text_excluded: 20}
included: {k: 15}'
run_flow "H3: DTA, included.reports 20 declared (identity OK)" 0 "full_text_assessed" OK \
'screening: {full_text_assessed: 60, full_text_excluded: 40}
included: {k: 24, reports: 20}'
run_flow "H3: DTA, reports 20 < k 24 (NOT_ASSESSED, not FAIL)" 0 "included.reports >= included.k" NOT_ASSESSED \
'screening: {full_text_assessed: 60, full_text_excluded: 40}
included: {k: 24, reports: 20}'
run_flow "H4: included.reports 22 declared, 20 reports (FAIL)" 1 "full_text_assessed" FAIL \
'screening: {full_text_assessed: 60, full_text_excluded: 40}
included: {k: 20, reports: 22}'
run_flow "H5: reports 12 >= k 10 (OK)" 0 "included.reports >= included.k" OK \
'screening: {full_text_assessed: 25, full_text_excluded: 13}
included: {k: 10, reports: 12}'

# --------------------------------------------------------------------------
# E: sum(exclusion_reasons) vs full_text_excluded.
#   E1 (negative): several reasons recorded per excluded report, sum 14 > 10
#       excluded -> NOT_ASSESSED, exit 0 (round 2 failed it; main exits 0).
#   E2 (positive): sum 8 < 10 excluded -> two reports have no reason, FAIL.
#   E3 (negative): sum equals full_text_excluded -> OK.
# --------------------------------------------------------------------------
run_flow "E1: several reasons per report, sum > excluded (NOT_ASSESSED)" 0 "sum(exclusion_reasons)" NOT_ASSESSED \
'screening: {full_text_excluded: 10}
exclusion_reasons: {wrong_population: 8, wrong_outcome: 6}'
run_flow "E2: reasons sum < excluded (FAIL)" 1 "sum(exclusion_reasons)" FAIL \
'screening: {full_text_excluded: 10}
exclusion_reasons: {wrong_population: 5, wrong_outcome: 3}'
run_flow "E3: reasons sum = excluded (OK)" 0 "sum(exclusion_reasons)" OK \
'screening: {full_text_excluded: 10}
exclusion_reasons: {wrong_population: 6, wrong_outcome: 4}'

# --------------------------------------------------------------------------
# P: optional prisma2020 report-level section (declared counts only).
#   P1 (negative): a consistent PRISMA 2020 flow, every identity OK, exit 0.
#   P2-P4 (positive): one broken identity each -> FAIL, exit 1.
#   P5 (positive): reasons sum below reports_excluded -> FAIL; P6 (negative)
#       above it -> NOT_ASSESSED (several reasons per report).
#   P7 (negative): studies 14 > reports 12 -> NOT_ASSESSED, never FAIL.
#   P8 (negative): records_screened undeclared, 100 removed before screening ->
#       after_dedup row NOT_ASSESSED; P9 records_screened declared -> OK.
#   P10 (negative): only reports_included declared -> its identities are
#       NOT_ASSESSED, naming the undeclared terms; --strict exits 3.
#   P11: unknown prisma2020 key / non-mapping section -> exit 2.
# --------------------------------------------------------------------------
P_OK='screening: {title_abstract_excluded: 620}
prisma2020:
  records_screened: 700
  reports_sought: 80
  reports_not_retrieved: 5
  reports_assessed: 75
  reports_excluded: 60
  reports_excluded_reasons: {wrong_population: 35, wrong_outcome: 25}
  reports_included: 15
  studies_included: 12'
printf '%s\n' "$P_OK" > "$TMP/f/prisma.yaml"
python3 "$SCRIPT" --ssot "$TMP/f/prisma.yaml" --project-root "$TMP/f" --strict --json > "$TMP/f/out.json"
assert_exit "P1: consistent prisma2020 flow, --strict (PASS)" 0 $?
python3 - "$TMP/f/out.json" <<'PY' || { echo "  FAIL  P1: five OK rows"; fail=$((fail + 1)); }
import json, sys
r = json.load(open(sys.argv[1]))
rows = [c for c in r["flow_identities"] if "prisma2020" in c["identity"]]
assert len(rows) == 5 and all(c["status"] == "OK" for c in rows), rows
assert r["verdict"] == "PASS", r["verdict"]
PY
run_flow "P2: records_screened - TA excluded != reports_sought (FAIL)" 1 "prisma2020.records_screened" FAIL \
"$(printf '%s\n' "$P_OK" | sed 's/reports_sought: 80/reports_sought: 82/; s/reports_not_retrieved: 5/reports_not_retrieved: 7/')"
run_flow "P3: sought - not_retrieved != assessed (FAIL)" 1 "prisma2020.reports_sought" FAIL \
"$(printf '%s\n' "$P_OK" | sed 's/reports_not_retrieved: 5/reports_not_retrieved: 4/')"
run_flow "P4: assessed - excluded != reports_included (FAIL)" 1 "prisma2020.reports_assessed" FAIL \
"$(printf '%s\n' "$P_OK" | sed 's/reports_included: 15/reports_included: 16/')"
run_flow "P5: reasons sum 55 < reports_excluded 60 (FAIL)" 1 "sum(prisma2020.reports_excluded_reasons)" FAIL \
"$(printf '%s\n' "$P_OK" | sed 's/wrong_outcome: 25/wrong_outcome: 20/')"
run_flow "P6: reasons sum 70 > reports_excluded 60 (NOT_ASSESSED)" 0 "sum(prisma2020.reports_excluded_reasons)" NOT_ASSESSED \
"$(printf '%s\n' "$P_OK" | sed 's/wrong_outcome: 25/wrong_outcome: 35/')"
run_flow "P7: studies 14 > reports 12 (NOT_ASSESSED, not FAIL)" 0 "prisma2020.studies_included" NOT_ASSESSED \
'prisma2020: {reports_included: 12, studies_included: 14}'
run_flow "P8: after_dedup used, 100 removed pre-screening (NOT_ASSESSED)" 0 "deduplication.after_dedup" NOT_ASSESSED \
'deduplication: {after_dedup: 800}
screening: {title_abstract_excluded: 620}
prisma2020: {reports_sought: 80}'
run_flow "P9: records_screened 700 declared (OK)" 0 "prisma2020.records_screened" OK \
'deduplication: {after_dedup: 800}
screening: {title_abstract_excluded: 620}
prisma2020: {records_screened: 700, reports_sought: 80}'
run_flow "P10: only reports_included declared (NOT_ASSESSED)" 0 "prisma2020.reports_assessed" NOT_ASSESSED \
'prisma2020: {reports_included: 15}'
python3 - "$TMP/f/out.json" <<'PY' || { echo "  FAIL  P10: undeclared terms named"; fail=$((fail + 1)); }
import json, sys
r = json.load(open(sys.argv[1]))
rows = {c["identity"]: c for c in r["flow_identities"]}
assert len(rows) == 2, rows
row = rows["prisma2020.reports_assessed - prisma2020.reports_excluded = prisma2020.reports_included"]
assert row["lhs"] is None and "prisma2020.reports_assessed" in row["note"] \
    and "prisma2020.reports_excluded" in row["note"], row
assert r["mismatches"] == [] and r["verdict"] == "NOT_ASSESSED", r
PY
python3 "$SCRIPT" --ssot "$TMP/f/prisma.yaml" --project-root "$TMP/f" --strict > "$TMP/f/out.txt"
assert_exit "P10: --strict with undeclared terms (exit 3)" 3 $?
grep -q "(not computed)" "$TMP/f/out.txt" || { echo "  FAIL  P10: text row"; fail=$((fail + 1)); }
printf 'prisma2020: {reports_sougth: 80}\n' > "$TMP/f/prisma.yaml"
python3 "$SCRIPT" --ssot "$TMP/f/prisma.yaml" --project-root "$TMP/f" > /dev/null 2> "$TMP/f/err"
assert_exit "P11: unknown prisma2020 key (exit 2)" 2 $?
grep -q "reports_sougth" "$TMP/f/err" || { echo "  FAIL  P11: key named"; fail=$((fail + 1)); }
printf 'prisma2020: [1, 2]\n' > "$TMP/f/prisma.yaml"
python3 "$SCRIPT" --ssot "$TMP/f/prisma.yaml" --project-root "$TMP/f" > /dev/null 2> "$TMP/f/err"
assert_exit "P11: prisma2020 not a mapping (exit 2)" 2 $?
if grep -q Traceback "$TMP/f/err"; then echo "  FAIL  P11: traceback"; fail=$((fail + 1)); fi

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
