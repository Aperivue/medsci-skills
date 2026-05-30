#!/usr/bin/env bash
# Regression tests for verify_package_integrity.py --assert-vN-docx-changed.

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
SCRIPT="$REPO_ROOT/scripts/verify_package_integrity.py"
TMP="$(mktemp -d -t vNdocx.XXXXXX)"
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

# Case 1: identical bytes => FAIL
printf 'identical bytes\n' > "$TMP/vN.docx"
cp "$TMP/vN.docx" "$TMP/vNplus1.docx"
python3 "$SCRIPT" --assert-vN-docx-changed \
    --vN-docx "$TMP/vN.docx" --new-docx "$TMP/vNplus1.docx" >/dev/null 2>&1
assert_exit "case 1: identical bytes (FAIL)" 1 $?

# Case 2: different bytes => PASS
printf 'different bytes for v_(N+1)\n' > "$TMP/vNplus1.docx"
python3 "$SCRIPT" --assert-vN-docx-changed \
    --vN-docx "$TMP/vN.docx" --new-docx "$TMP/vNplus1.docx" >/dev/null 2>&1
assert_exit "case 2: different bytes (PASS)" 0 $?

# Case 3: missing v_N => exit 2
python3 "$SCRIPT" --assert-vN-docx-changed \
    --vN-docx "$TMP/nonexistent.docx" --new-docx "$TMP/vNplus1.docx" >/dev/null 2>&1
assert_exit "case 3: missing v_N (exit 2)" 2 $?

# Case 4: missing --new-docx arg => exit 2
python3 "$SCRIPT" --assert-vN-docx-changed \
    --vN-docx "$TMP/vN.docx" >/dev/null 2>&1
assert_exit "case 4: missing --new-docx (exit 2)" 2 $?

echo ""
echo "ran=$ran fail=$fail"
[[ $fail -eq 0 ]]
