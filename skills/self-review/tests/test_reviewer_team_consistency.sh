#!/usr/bin/env bash
# Regression tests for self-review check_reviewer_team_consistency.py.

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
SCRIPT="$REPO_ROOT/skills/self-review/scripts/check_reviewer_team_consistency.py"
TMP="$(mktemp -d -t reviewer_team.XXXXXX)"
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

# --------------------------------------------------------------------------
# Case 1: clean — dual review claimed, no limits confession.
# --------------------------------------------------------------------------
cat > "$TMP/c1.md" <<'EOF'
## **METHODS**
Two reviewers independently screened titles and abstracts.

## **DISCUSSION**
The cohort overlap reduces effective sample size.
EOF
python3 "$SCRIPT" --manuscript "$TMP/c1.md" \
    --out "$TMP/c1.md.audit" --quiet
assert_exit "case 1: dual claim, no limits confession" 0 $?

# --------------------------------------------------------------------------
# Case 2: fabrication-grade — Methods dual + Limitations single confession.
# --------------------------------------------------------------------------
cat > "$TMP/c2.md" <<'EOF'
## **METHODS**
Two reviewers independently screened titles and abstracts and extracted data.

## **DISCUSSION**

### Limitations
We used a single primary reviewer for data extraction; a 20% sample by an
additional reviewer is deferred to before submission.
EOF
python3 "$SCRIPT" --manuscript "$TMP/c2.md" \
    --out "$TMP/c2.md.audit" --quiet
assert_exit "case 2: dual + single confession (FAIL)" 1 $?

# Verify the markdown report flags both claim sides.
grep -q "MAJOR red flag" "$TMP/c2.md.audit" || { echo "  FAIL c2 markdown body"; fail=$((fail + 1)); }
grep -q "single primary reviewer" "$TMP/c2.md.audit" || { echo "  FAIL c2 markdown body"; fail=$((fail + 1)); }

# --------------------------------------------------------------------------
# Case 3: PROSPERO dual + Limitations single. Also FAIL.
# --------------------------------------------------------------------------
cat > "$TMP/c3.md" <<'EOF'
## **METHODS**
Records were screened against pre-specified eligibility criteria.

## **DISCUSSION**
### Limitations
A single primary reviewer extracted data due to resource constraints.
EOF
cat > "$TMP/c3_prospero.md" <<'EOF'
# PROSPERO record
Two independent reviewers will perform full-text screening and data extraction.
EOF
python3 "$SCRIPT" --manuscript "$TMP/c3.md" --prospero "$TMP/c3_prospero.md" \
    --out "$TMP/c3.md.audit" --quiet
assert_exit "case 3: PROSPERO dual + limits single (FAIL)" 1 $?

# --------------------------------------------------------------------------
# Case 4: single confession alone (no dual claim) => PASS.
# --------------------------------------------------------------------------
cat > "$TMP/c4.md" <<'EOF'
## **METHODS**
Data extraction was performed by the first reviewer.

## **DISCUSSION**
### Limitations
A single primary reviewer extracted data; this is a limitation of our review.
EOF
python3 "$SCRIPT" --manuscript "$TMP/c4.md" \
    --out "$TMP/c4.md.audit" --quiet
assert_exit "case 4: single confession only (PASS)" 0 $?

# --------------------------------------------------------------------------
# Case 5: extraction JSON names an LLM as a reviewer => fatal FAIL.
# --------------------------------------------------------------------------
cat > "$TMP/c5.md" <<'EOF'
## **METHODS**
Records were screened against pre-specified eligibility criteria.
EOF
cat > "$TMP/c5_extract.json" <<'EOF'
{"study": "Example 2024", "reviewer_1": "Claude", "reviewer_2": "Jane Doe"}
EOF
python3 "$SCRIPT" --manuscript "$TMP/c5.md" --extraction-json "$TMP/c5_extract.json" \
    --out "$TMP/c5.md.audit" --quiet
assert_exit "case 5: LLM-as-reviewer in extraction JSON (FAIL)" 1 $?
grep -q "LLM-AS-REVIEWER" "$TMP/c5.md.audit" || { echo "  FAIL c5 markdown body"; fail=$((fail + 1)); }

# --------------------------------------------------------------------------
# Case 6: future-tense deferred mitigation => MAJOR FAIL.
# --------------------------------------------------------------------------
cat > "$TMP/c6.md" <<'EOF'
## **METHODS**
Records were screened by the primary reviewer.

## **DISCUSSION**
### Limitations
A duplicate-screening check will be completed before submission.
EOF
python3 "$SCRIPT" --manuscript "$TMP/c6.md" \
    --out "$TMP/c6.md.audit" --quiet
assert_exit "case 6: deferred mitigation (FAIL)" 1 $?
grep -q "DEFERRED-MITIGATION" "$TMP/c6.md.audit" || { echo "  FAIL c6 markdown body"; fail=$((fail + 1)); }

# --------------------------------------------------------------------------
# Case 7: clean extraction JSON (human reviewers) => PASS (backward compat).
# --------------------------------------------------------------------------
cat > "$TMP/c7_extract.json" <<'EOF'
{"study": "Example 2024", "reviewer_1": "Jane Doe", "reviewer_2": "John Roe"}
EOF
python3 "$SCRIPT" --manuscript "$TMP/c1.md" --extraction-json "$TMP/c7_extract.json" \
    --out "$TMP/c7.md.audit" --quiet
assert_exit "case 7: human reviewers in extraction JSON (PASS)" 0 $?

echo ""
echo "ran=$ran fail=$fail"
[[ $fail -eq 0 ]]
