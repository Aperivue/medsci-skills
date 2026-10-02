#!/usr/bin/env bash
# Regression tests for meta-analysis prisma_5way_consistency.py (DI-6).
#
# Each positive fixture isolates one false clearance the checker used to give
# (exit 0, "PASS"):
#   A. included.k = 12 "found" in methods.md because of "Follow-up was 12 months",
#      while the text actually reports nine studies.
#   B. the SSOT's own flow arithmetic is impossible (15 assessed - 3 excluded is
#      12, but k = 13), and every surface faithfully repeats the wrong k.
#   C. a search CSV with a quoted multi-line abstract: 2 records, 3 data lines;
#      line counting matched an SSOT total of 3.
# The negative control is a consistent PRISMA flow whose prose also carries
# decoy numbers (follow-up months, a table number, a citation, "1,500") and a
# multi-line CSV record; it must stay clean.

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
assert_exit "A: k matched only by '12 months' (FAIL)" 1 $?
python3 - "$TMP/a/out.json" <<'PY' || fail=$((fail + 1))
import json, sys
r = json.load(open(sys.argv[1]))
assert r["surfaces"]["methods_md"]["missing_numbers"] == ["included.k"], r
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
assert_exit "negative: consistent flow with decoy numbers (PASS)" 0 $?

echo ""
echo "ran=$ran fail=$fail"
[[ $fail -eq 0 ]]
