#!/usr/bin/env bash
# Regression/challenge test for check_summary_box.py — deterministic, network-free,
# synthetic fixtures built at runtime. Covers each journal format + each hard rule.
set -u

HERE="$(cd "$(dirname "$0")" && pwd)"
SCRIPT="$HERE/../scripts/check_summary_box.py"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

pass=0
fail=0
ck() {
  local label="$1" expected="$2" actual="$3"
  if [ "$expected" = "$actual" ]; then
    printf '  PASS  %-50s exit=%s\n' "$label" "$actual"
    pass=$((pass + 1))
  else
    printf '  FAIL  %-50s expected=%s actual=%s\n' "$label" "$expected" "$actual"
    fail=$((fail + 1))
  fi
}
run() { python3 "$SCRIPT" --out "$TMP/r.json" "$@" > /dev/null 2>&1; echo $?; }

# 1) conformant Key Points (3 one-claim bullets) -> exit 0
cat > "$TMP/kp_ok.md" <<'EOF'
## Key Points
- The model improved detection sensitivity in an internal test set.
- Specificity was preserved at the chosen operating threshold.
- External validation is still required before deployment.
EOF
ck "key_points conformant" 0 "$(run --manuscript "$TMP/kp_ok.md" --journal radiology --strict)"

# 2) wrong bullet count (2) -> NONCONFORMANT under --strict
cat > "$TMP/kp_bad.md" <<'EOF'
## Key Points
- The model improved detection sensitivity.
- Specificity was preserved.
EOF
ck "key_points wrong bullet count fails" 1 "$(run --manuscript "$TMP/kp_bad.md" --journal radiology --strict)"

# 3) Research in context missing a sub-block -> NONCONFORMANT
cat > "$TMP/ric_bad.md" <<'EOF'
## Research in context
**Evidence before this study** We searched PubMed for prior work.
**Added value of this study** This study adds an external cohort.
EOF
ck "research_in_context missing subblock fails" 1 "$(run --manuscript "$TMP/ric_bad.md" --journal lancet-digital-health --strict)"

# 4) Research in context complete -> CONFORMANT
cat > "$TMP/ric_ok.md" <<'EOF'
## Research in context
**Evidence before this study** We searched PubMed for prior work.
**Added value of this study** This study adds an external cohort.
**Implications of all the available evidence** Findings support a prospective trial.
EOF
ck "research_in_context complete conformant" 0 "$(run --manuscript "$TMP/ric_ok.md" --journal lancet-digital-health --strict)"

# 5) Plain-language summary over the band -> NONCONFORMANT
{ echo "## Plain-language summary"; for i in $(seq 1 260); do printf 'word '; done; echo; } > "$TMP/pls_bad.md"
ck "plain_language over-length fails" 1 "$(run --manuscript "$TMP/pls_bad.md" --format plain_language_summary --strict)"

# 6) absent box -> NONCONFORMANT
echo "## Abstract" > "$TMP/none.md"
ck "absent box fails" 1 "$(run --manuscript "$TMP/none.md" --format key_points --strict)"

# 7) without --strict, a nonconformant box is reported but tolerated (exit 0)
ck "nonconformant tolerated without --strict" 0 "$(run --manuscript "$TMP/kp_bad.md" --journal radiology)"

echo "----"
echo "test_summary_box: $pass passed, $fail failed"
[ "$fail" -eq 0 ]
