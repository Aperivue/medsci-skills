#!/usr/bin/env bash
# Regression tests for meta-analysis check_pool_consistency.py.

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
SCRIPT="$REPO_ROOT/skills/meta-analysis/scripts/check_pool_consistency.py"
TMP="$(mktemp -d -t pool_consist.XXXXXX)"
trap 'rm -rf "$TMP"' EXIT

[[ -f "$SCRIPT" ]] || { echo "ENV-ERR: script missing" >&2; exit 2; }
python3 -c "import yaml" 2>/dev/null || { echo "SKIP: pyyaml unavailable"; exit 0; }

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
# Case 1: lock and TSV agree on 3 UIDs => PASS
# --------------------------------------------------------------------------
mkdir -p "$TMP/c1"
cat > "$TMP/c1/lock.yaml" <<'EOF'
freeze_date: "2026-01-01"
final_pool_n: 3
include_count: 3
exclude_count: 0
mixed_count: 0
include_uids: [UID_001, UID_002, UID_003]
exclude_uids: []
mixed_uids: []
EOF
cat > "$TMP/c1/r3.tsv" <<'EOF'
uid	round3_decision	notes
UID_001	INCLUDE	ok
UID_002	INCLUDE	ok
UID_003	INCLUDE	ok
UID_004	EXCLUDE	out of scope
EOF
python3 "$SCRIPT" --lock "$TMP/c1/lock.yaml" \
    --adjudication-tsv "$TMP/c1/r3.tsv" \
    --out "$TMP/c1/report.json" --quiet
assert_exit "case 1: lock and TSV agree" 0 $?

# --------------------------------------------------------------------------
# Case 2: TSV has extra UID => FAIL
# --------------------------------------------------------------------------
mkdir -p "$TMP/c2"
cat > "$TMP/c2/lock.yaml" <<'EOF'
include_uids: [UID_001, UID_002]
exclude_uids: []
mixed_uids: []
EOF
cat > "$TMP/c2/r3.tsv" <<'EOF'
uid	round3_decision
UID_001	INCLUDE
UID_002	INCLUDE
UID_009	INCLUDE
EOF
python3 "$SCRIPT" --lock "$TMP/c2/lock.yaml" \
    --adjudication-tsv "$TMP/c2/r3.tsv" \
    --out "$TMP/c2/report.json" --quiet
assert_exit "case 2: TSV extra UID (FAIL)" 1 $?
python3 - "$TMP/c2/report.json" <<'PY' || fail=$((fail + 1))
import json, sys
with open(sys.argv[1]) as fh: r = json.load(fh)
assert "UID_009" in r["in_tsv_not_lock"], r
assert not r["in_lock_not_tsv"], r
PY

# --------------------------------------------------------------------------
# Case 3: lock has extra UID => FAIL
# --------------------------------------------------------------------------
mkdir -p "$TMP/c3"
cat > "$TMP/c3/lock.yaml" <<'EOF'
include_uids: [UID_001, UID_002, UID_999]
mixed_uids: []
exclude_uids: []
EOF
cat > "$TMP/c3/r3.tsv" <<'EOF'
uid	round3_decision
UID_001	INCLUDE
UID_002	INCLUDE
EOF
python3 "$SCRIPT" --lock "$TMP/c3/lock.yaml" \
    --adjudication-tsv "$TMP/c3/r3.tsv" \
    --out "$TMP/c3/report.json" --quiet
assert_exit "case 3: lock extra UID (FAIL)" 1 $?
python3 - "$TMP/c3/report.json" <<'PY' || fail=$((fail + 1))
import json, sys
with open(sys.argv[1]) as fh: r = json.load(fh)
assert "UID_999" in r["in_lock_not_tsv"], r
PY

# --------------------------------------------------------------------------
# Case 4: missing decision column => exit 2
# --------------------------------------------------------------------------
mkdir -p "$TMP/c4"
cat > "$TMP/c4/lock.yaml" <<'EOF'
include_uids: [UID_001]
mixed_uids: []
exclude_uids: []
EOF
cat > "$TMP/c4/r3.tsv" <<'EOF'
uid	notes
UID_001	whatever
EOF
python3 "$SCRIPT" --lock "$TMP/c4/lock.yaml" \
    --adjudication-tsv "$TMP/c4/r3.tsv" \
    --out "$TMP/c4/report.json" --quiet 2>/dev/null
assert_exit "case 4: missing decision col (exit 2)" 2 $?

echo ""
echo "ran=$ran fail=$fail"
[[ $fail -eq 0 ]]
