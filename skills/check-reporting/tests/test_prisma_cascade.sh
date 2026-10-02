#!/usr/bin/env bash
# Regression tests for check-reporting prisma_cascade_check.py.

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
SCRIPT="$REPO_ROOT/skills/check-reporting/scripts/prisma_cascade_check.py"
TMP="$(mktemp -d -t prisma_cas.XXXXXX)"
trap 'rm -rf "$TMP"' EXIT

[[ -f "$SCRIPT" ]] || { echo "ENV-ERR: script missing" >&2; exit 2; }

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

build_tsv() {
    local out="$1" col="$2"
    shift 2
    {
        printf 'uid\t%s\n' "$col"
        local i=1
        for label in "$@"; do
            printf 'UID_%03d\t%s\n' "$i" "$label"
            i=$((i + 1))
        done
    } > "$out"
}

# --------------------------------------------------------------------------
# Case 1: matching counts (no manuscript) => PASS.
# round 1: 5 INCLUDE, 5 EXCLUDE
# round 2: 3 INCLUDE, 2 EXCLUDE
# round 3: 2 INCLUDE, 1 EXCLUDE
# --------------------------------------------------------------------------
build_tsv "$TMP/c1_r1.tsv" decision INCLUDE INCLUDE INCLUDE INCLUDE INCLUDE EXCLUDE EXCLUDE EXCLUDE EXCLUDE EXCLUDE
build_tsv "$TMP/c1_r2.tsv" decision INCLUDE INCLUDE INCLUDE EXCLUDE EXCLUDE
build_tsv "$TMP/c1_r3.tsv" round3_decision INCLUDE INCLUDE EXCLUDE
python3 "$SCRIPT" --round1 "$TMP/c1_r1.tsv" --round2 "$TMP/c1_r2.tsv" \
    --round3 "$TMP/c1_r3.tsv" --out "$TMP/c1.json" --quiet
assert_exit "case 1: TSV only, no manuscript (PASS)" 0 $?
python3 - "$TMP/c1.json" <<'PY' || fail=$((fail + 1))
import json, sys
r = json.load(open(sys.argv[1]))
sc = r["stage_counts"]
assert sc["round1_total"] == 10, sc
assert sc["round1_include"] == 5, sc
assert sc["round3_include"] == 2, sc
PY

# --------------------------------------------------------------------------
# Case 2: manuscript claims correct count => PASS.
# --------------------------------------------------------------------------
cat > "$TMP/c2_manuscript.md" <<'EOF'
## **METHODS**
After title and abstract screening, 3 records were retrieved for full-text review.
Finally included 2 studies in the meta-analysis.
EOF
python3 "$SCRIPT" --round1 "$TMP/c1_r1.tsv" --round2 "$TMP/c1_r2.tsv" \
    --round3 "$TMP/c1_r3.tsv" \
    --manuscript "$TMP/c2_manuscript.md" \
    --out "$TMP/c2.json" --quiet
assert_exit "case 2: manuscript matches (PASS)" 0 $?

# --------------------------------------------------------------------------
# Case 3: manuscript prose off-by-one => FAIL.
# Computed round3_include = 2; manuscript says "3 studies"
# --------------------------------------------------------------------------
cat > "$TMP/c3_manuscript.md" <<'EOF'
## **RESULTS**
Finally included 3 studies in the meta-analysis.
EOF
python3 "$SCRIPT" --round1 "$TMP/c1_r1.tsv" --round2 "$TMP/c1_r2.tsv" \
    --round3 "$TMP/c1_r3.tsv" \
    --manuscript "$TMP/c3_manuscript.md" \
    --out "$TMP/c3.json" --quiet
assert_exit "case 3: off-by-one prose drift (FAIL)" 1 $?
python3 - "$TMP/c3.json" <<'PY' || fail=$((fail + 1))
import json, sys
r = json.load(open(sys.argv[1]))
drifts = r["manuscript_drift"]
assert any(d["stage"] == "round3_include" and d["manuscript"] == 3 for d in drifts), drifts
PY

# --------------------------------------------------------------------------
# Case 4: bad column => exit 2.
# --------------------------------------------------------------------------
build_tsv "$TMP/c4.tsv" notes INCLUDE EXCLUDE
python3 "$SCRIPT" --round1 "$TMP/c4.tsv" --round2 "$TMP/c1_r2.tsv" \
    --round3 "$TMP/c1_r3.tsv" --out "$TMP/c4.json" --quiet 2>/dev/null
assert_exit "case 4: bad column (exit 2)" 2 $?

# --------------------------------------------------------------------------
# Case 5: --manuscript path that does not exist => exit 2 (was a silent PASS).
# --------------------------------------------------------------------------
python3 "$SCRIPT" --round1 "$TMP/c1_r1.tsv" --round2 "$TMP/c1_r2.tsv" \
    --round3 "$TMP/c1_r3.tsv" --manuscript "$TMP/no_such_manuscript.md" \
    --out "$TMP/c5.json" --quiet 2>/dev/null
assert_exit "case 5: missing --manuscript (exit 2)" 2 $?

# --------------------------------------------------------------------------
# Case 6: manuscript states a count in phrasing no stage pattern matches.
# Computed round3_include = 2; prose says 99. The drift check cannot run, so
# the result must say UNVERIFIED and submission_safe false (was PASS / true).
# --------------------------------------------------------------------------
cat > "$TMP/c6_manuscript.md" <<'EOF'
## **RESULTS**
Overall, 99 eligible studies were analysed.
EOF
err="$(python3 "$SCRIPT" --round1 "$TMP/c1_r1.tsv" --round2 "$TMP/c1_r2.tsv" \
    --round3 "$TMP/c1_r3.tsv" --manuscript "$TMP/c6_manuscript.md" \
    --out "$TMP/c6.json" --quiet 2>&1 >/dev/null)"
assert_exit "case 6: unmatched prose, default (exit 0)" 0 $?
ran=$((ran + 1))
if [[ "$err" == *"UNVERIFIED"* ]] && python3 - "$TMP/c6.json" <<'PY'
import json, sys
r = json.load(open(sys.argv[1]))
assert r["submission_safe"] is False, r
assert r["manuscript_check"] == "unverifiable", r
assert r["stages_compared"] == [], r
PY
then
    printf '  PASS  %-50s\n' "case 6: UNVERIFIED + submission_safe false"
else
    printf '  FAIL  %-50s\n' "case 6: UNVERIFIED + submission_safe false"
    fail=$((fail + 1))
fi
python3 "$SCRIPT" --round1 "$TMP/c1_r1.tsv" --round2 "$TMP/c1_r2.tsv" \
    --round3 "$TMP/c1_r3.tsv" --manuscript "$TMP/c6_manuscript.md" \
    --out "$TMP/c6s.json" --quiet --strict 2>/dev/null
assert_exit "case 6s: unmatched prose, --strict (exit 1)" 1 $?

# --------------------------------------------------------------------------
# Case 7: negative control - matching manuscript under --strict stays PASS,
# with the matched stages recorded.
# --------------------------------------------------------------------------
python3 "$SCRIPT" --round1 "$TMP/c1_r1.tsv" --round2 "$TMP/c1_r2.tsv" \
    --round3 "$TMP/c1_r3.tsv" --manuscript "$TMP/c2_manuscript.md" \
    --out "$TMP/c7.json" --quiet --strict
assert_exit "case 7: matching manuscript, --strict (PASS)" 0 $?
python3 - "$TMP/c7.json" <<'PY' || fail=$((fail + 1))
import json, sys
r = json.load(open(sys.argv[1]))
assert r["submission_safe"] is True, r
assert r["manuscript_check"] == "compared", r
assert "round3_include" in r["stages_compared"], r
PY

echo ""
echo "ran=$ran fail=$fail"
[[ $fail -eq 0 ]]
