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

# --------------------------------------------------------------------------
# Case 8: the Methods heading uses an ampersand or a compound form. Before this
# case the heading was not recognised, the Methods text was empty, the dual
# claim was never seen and the conflict below PASSED.
# --------------------------------------------------------------------------
for heading in "Materials & Methods" 'Materials \& Methods' "Material and Methods" \
               "Patients and Methods" "Methods and Materials"; do
    {
        printf '## %s\n' "$heading"
        printf 'Two reviewers independently screened titles and abstracts and extracted data.\n\n'
        printf '## Discussion\n\n### Limitations\n'
        printf 'We used a single primary reviewer for data extraction.\n'
    } > "$TMP/c8.md"
    python3 "$SCRIPT" --manuscript "$TMP/c8.md" --out "$TMP/c8.md.audit" --quiet
    assert_exit "case 8: '$heading' is the Methods section (FAIL)" 1 $?
done

# --------------------------------------------------------------------------
# Case 9: no Methods heading at all. The dual-review claim cannot be checked,
# so the run must say so instead of reporting a bare PASS.
# --------------------------------------------------------------------------
{
    printf '## Study procedures\nTwo reviewers independently screened titles and abstracts.\n\n'
    printf '## Discussion\n\n### Limitations\n'
    printf 'We used a single primary reviewer for data extraction.\n'
} > "$TMP/c9.md"
python3 "$SCRIPT" --manuscript "$TMP/c9.md" --out "$TMP/c9.md.audit" --quiet \
    > "$TMP/c9.stdout" 2> "$TMP/c9.stderr"
assert_exit "case 9: missing Methods heading keeps exit 0" 0 $?
ran=$((ran + 1))
if grep "Methods section not found" "$TMP/c9.stderr" >/dev/null \
   && ! grep "Methods section not found" "$TMP/c9.stdout" >/dev/null \
   && grep "Methods section not found" "$TMP/c9.md.audit" >/dev/null \
   && grep '"methods_section_found": false' "$TMP/c9.md.audit.json" >/dev/null; then
    echo "  PASS  case 9: missing Methods heading is reported"
else
    echo "  FAIL  case 9: missing Methods heading is not reported"; fail=$((fail + 1))
fi
ran=$((ran + 1))
if grep '"methods_section_found": true' "$TMP/c1.md.audit.json" >/dev/null \
   && ! grep "Methods section not found" "$TMP/c1.md.audit" >/dev/null; then
    echo "  PASS  case 9b: a recognised Methods heading carries no warning"
else
    echo "  FAIL  case 9b: warning or flag wrong on a recognised heading"; fail=$((fail + 1))
fi

# --------------------------------------------------------------------------
# Case 10: a heading that only starts like a compound Methods heading is not one.
# "## Patients" followed by a body line "and Methods ..." has no Methods section.
# --------------------------------------------------------------------------
{
    printf '## Patients\nand Methods\n'
    printf 'Two reviewers independently screened titles and abstracts.\n\n'
    printf '## Discussion\n\n### Limitations\n'
    printf 'We used a single primary reviewer for data extraction.\n'
} > "$TMP/c10.md"
python3 "$SCRIPT" --manuscript "$TMP/c10.md" --out "$TMP/c10.md.audit" --quiet 2> "$TMP/c10.stderr"
ran=$((ran + 1))
if grep "Methods section not found" "$TMP/c10.stderr" >/dev/null; then
    echo "  PASS  case 10: a heading split across lines is not a Methods heading"
else
    echo "  FAIL  case 10: '## Patients' + 'and Methods' was read as a Methods heading"; fail=$((fail + 1))
fi

# --------------------------------------------------------------------------
# Case 11: a Methods heading inside a fenced code block is an example, not a section;
# and a heading followed by a no-break space is still a heading.
# --------------------------------------------------------------------------
# The fenced example holds a Methods heading AND a dual-review claim; neither is the paper's.
# Three layouts: a plain fence, a four-tilde fence holding a three-tilde line, an HTML comment.
c11() {  # c11 <name> <opening line> <inner extra line or ''> <closing line>
    {
        printf '## Study procedures\nRecords were screened.\n\n'
        printf '%s\n' "$2"
        [ -n "$3" ] && printf '%s\n' "$3"
        printf '## Materials & Methods\nTwo reviewers independently screened titles and abstracts.\n'
        printf '%s\n\n' "$4"
        printf '## Discussion\n\n### Limitations\nWe used a single primary reviewer for data extraction.\n'
    } > "$TMP/$1.md"
    python3 "$SCRIPT" --manuscript "$TMP/$1.md" --out "$TMP/$1.md.audit" --quiet 2> "$TMP/$1.stderr"
    assert_exit "case 11 ($1): an example in a fence or comment is no conflict" 0 $?
    ran=$((ran + 1))
    if grep "Methods section not found" "$TMP/$1.stderr" >/dev/null \
       && grep '"methods_section_found": false' "$TMP/$1.md.audit.json" >/dev/null \
       && python3 -c "import json,sys; sys.exit(0 if json.load(open(sys.argv[1]))['dual_hits']==[] else 1)" "$TMP/$1.md.audit.json"; then
        echo "  PASS  case 11 ($1): not found, and no dual claim read from the example"
    else
        echo "  FAIL  case 11 ($1): the example was read as manuscript text"; fail=$((fail + 1))
    fi
}
c11 fence '```' '' '```'
c11 tilde4 '~~~~' '~~~' '~~~~'
c11 comment '<!--' '' '-->'
{
    printf '## Methods\302\240\nTwo reviewers independently screened titles and abstracts and extracted data.\n\n'
    printf '## Discussion\n\n### Limitations\nWe used a single primary reviewer for data extraction.\n'
} > "$TMP/c11b.md"
python3 "$SCRIPT" --manuscript "$TMP/c11b.md" --out "$TMP/c11b.md.audit" --quiet
assert_exit "case 11b: '## Methods' + no-break space is the Methods section (FAIL)" 1 $?

echo ""
echo "ran=$ran fail=$fail"
[[ $fail -eq 0 ]]
