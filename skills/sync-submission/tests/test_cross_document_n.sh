#!/usr/bin/env bash
# Regression tests for sync-submission cross_document_n_check.py.
#
# Synthetic fixtures only (no project paths, no manuscript IDs).
# Skip with NETWORK=0 — this script does not use the network.
#
# Usage:
#   skills/sync-submission/tests/test_cross_document_n.sh
# Exit codes:
#   0 — all tests passed
#   1 — at least one test regressed
#   2 — environment problem

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
SCRIPT="$REPO_ROOT/skills/sync-submission/scripts/cross_document_n_check.py"
TMP="$(mktemp -d -t cross_doc_n.XXXXXX)"
trap 'rm -rf "$TMP"' EXIT

if [[ ! -f "$SCRIPT" ]]; then
    echo "ENV-ERR: script not found at $SCRIPT" >&2
    exit 2
fi
command -v python3 >/dev/null 2>&1 || { echo "ENV-ERR: python3 missing" >&2; exit 2; }

fail=0
ran=0

assert_exit() {
    local label="$1" expected="$2" actual="$3"
    ran=$((ran + 1))
    if [[ "$expected" == "$actual" ]]; then
        printf '  PASS  %-50s exit=%s\n' "$label" "$actual"
    else
        printf '  FAIL  %-50s expected=%s actual=%s\n' "$label" "$expected" "$actual"
        fail=$((fail + 1))
    fi
}

# --------------------------------------------------------------------------
# Case 1: two documents agreeing on N. Should PASS (exit 0).
# --------------------------------------------------------------------------
PROJ1="$TMP/case1_consistent"
mkdir -p "$PROJ1"
cat > "$PROJ1/abstract.md" <<'EOF'
We included 42 studies after screening.
EOF
cat > "$PROJ1/manuscript.md" <<'EOF'
Results section. Across 42 included studies, the pooled estimate was...
EOF
python3 "$SCRIPT" --root "$PROJ1" --out "$PROJ1/qc/n.json" --quiet
assert_exit "case 1: consistent N (42 = 42)" 0 $?

# --------------------------------------------------------------------------
# Case 2: drift. Should FAIL (exit 1).
# --------------------------------------------------------------------------
PROJ2="$TMP/case2_drift"
mkdir -p "$PROJ2"
cat > "$PROJ2/abstract.md" <<'EOF'
We included 63 studies after dual-reviewer screening.
EOF
cat > "$PROJ2/manuscript.md" <<'EOF'
A total of 64 included studies were extracted for synthesis.
EOF
python3 "$SCRIPT" --root "$PROJ2" --out "$PROJ2/qc/n.json" --quiet
assert_exit "case 2: drift (63 vs 64)" 1 $?
# Verify the JSON content is well-formed and flags the right category.
python3 - "$PROJ2/qc/n.json" <<'PY' || fail=$((fail + 1))
import json, sys
with open(sys.argv[1]) as fh:
    rep = json.load(fh)
assert rep["submission_safe"] is False, rep
assert rep["drift_count"] == 1, rep
assert rep["drifts"][0]["category"] == "included", rep
vs = set(rep["drifts"][0]["values"])
assert vs == {63, 64}, rep
PY

# --------------------------------------------------------------------------
# Case 3: pool-lock mismatch.
# --------------------------------------------------------------------------
if python3 -c "import yaml" 2>/dev/null; then
    PROJ3="$TMP/case3_lock"
    mkdir -p "$PROJ3"
    cat > "$PROJ3/abstract.md" <<'EOF'
We included 50 studies after screening.
EOF
    cat > "$PROJ3/manuscript.md" <<'EOF'
Across 50 included studies, the pooled estimate was ...
EOF
    cat > "$PROJ3/lock.yaml" <<'EOF'
freeze_date: 2026-01-01
final_pool_n: 48
include_count: 48
exclude_count: 100
EOF
    python3 "$SCRIPT" --root "$PROJ3" --pool-lock "$PROJ3/lock.yaml" \
        --out "$PROJ3/qc/n.json" --quiet
    assert_exit "case 3: pool-lock mismatch (50 vs locked 48)" 1 $?
    python3 - "$PROJ3/qc/n.json" <<'PY' || fail=$((fail + 1))
import json, sys
with open(sys.argv[1]) as fh:
    rep = json.load(fh)
assert rep["lock_violations"], rep
v = rep["lock_violations"][0]
assert v["violation"] == "pool-lock-mismatch", v
assert v["expected"] == 48, v
assert v["actual"] == 50, v
PY
else
    printf '  SKIP  %-50s reason=pyyaml unavailable\n' "case 3: pool-lock"
fi

# --------------------------------------------------------------------------
# Case 4: explicit --files. Should also work.
# --------------------------------------------------------------------------
PROJ4="$TMP/case4_files"
mkdir -p "$PROJ4/sub"
cat > "$PROJ4/sub/a.md" <<'EOF'
We included 30 patients in the analysis.
EOF
cat > "$PROJ4/sub/b.md" <<'EOF'
30 patients were enrolled.
EOF
python3 "$SCRIPT" --files "$PROJ4/sub/a.md" "$PROJ4/sub/b.md" \
    --out "$PROJ4/qc/n.json" --quiet
assert_exit "case 4: explicit --files PASS (30 = 30)" 0 $?

# --------------------------------------------------------------------------
# Case 5 (F4): the per-journal cover letter (submission/<journal>/cover_letter.md,
# the path preflight_gate.py uses) and supplement/ were outside the glob set,
# so drift there was a PASS.
# --------------------------------------------------------------------------
PROJ5="$TMP/case5_submission_cover"
mkdir -p "$PROJ5/submission/chest"
echo "We enrolled 120 patients in the cohort." > "$PROJ5/manuscript.md"
echo "Dear Editor, our study of 118 patients is enclosed." > "$PROJ5/submission/chest/cover_letter.md"
python3 "$SCRIPT" --root "$PROJ5" --out "$PROJ5/qc/n.json" --quiet
assert_exit "case 5: submission/<j>/cover_letter.md drift (120 vs 118)" 1 $?

PROJ6="$TMP/case6_supplement"
mkdir -p "$PROJ6/supplement"
echo "We enrolled 120 patients in the cohort." > "$PROJ6/manuscript.md"
echo "Table S1 describes the 118 patients analysed." > "$PROJ6/supplement/S1.md"
python3 "$SCRIPT" --root "$PROJ6" --out "$PROJ6/qc/n.json" --quiet
assert_exit "case 6: supplement/ drift (120 vs 118)" 1 $?

# NEGATIVE control: the same layout with agreeing N stays clean.
PROJ7="$TMP/case7_submission_cover_ok"
mkdir -p "$PROJ7/submission/chest" "$PROJ7/supplement"
echo "We enrolled 120 patients in the cohort." > "$PROJ7/manuscript.md"
echo "Dear Editor, our study of 120 patients is enclosed." > "$PROJ7/submission/chest/cover_letter.md"
echo "Table S1 describes the 120 patients analysed." > "$PROJ7/supplement/S1.md"
python3 "$SCRIPT" --root "$PROJ7" --out "$PROJ7/qc/n.json" --quiet
assert_exit "case 7: negative control, agreeing N in new paths" 0 $?

# --------------------------------------------------------------------------
# Case 8 (F4): a non-UTF-8 file was silently dropped yet listed in files_scanned
# (PASS). It is now an input error (exit 2) naming the file, and is reported as
# unreadable, not scanned.
# --------------------------------------------------------------------------
PROJ8="$TMP/case8_unreadable"
mkdir -p "$PROJ8"
echo "We enrolled 120 patients in the cohort." > "$PROJ8/manuscript.md"
printf 'Dear Editor, our caf\xe9 study of 118 patients.\n' > "$PROJ8/cover_letter.md"
python3 "$SCRIPT" --root "$PROJ8" --out "$PROJ8/qc/n.json" --quiet 2>/dev/null
assert_exit "case 8: non-UTF-8 cover letter -> exit 2 (not PASS)" 2 $?
python3 - "$PROJ8/qc/n.json" <<'PY' || fail=$((fail + 1))
import json, sys
rep = json.load(open(sys.argv[1]))
assert rep["unreadable_files"] and rep["unreadable_files"][0].endswith("cover_letter.md"), rep
assert not any(f.endswith("cover_letter.md") for f in rep["files_scanned"]), rep
assert rep["coverage"] == "incomplete" and rep["submission_safe"] is False, rep
PY

echo ""
echo "ran=$ran fail=$fail"
[[ $fail -eq 0 ]]
