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
# verdict + severity/rule of each finding from the last run's JSON report
verdict() { python3 -c 'import json,sys; r=json.load(open(sys.argv[1])); print(" ".join([r["verdict"]]+[f["severity"]+" "+f["rule"] for f in r["findings"]]))' "$TMP/r.json"; }

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

# --- Block anchoring / bullet scope / sub-block content (regression) ---------
# 8) bold-labelled box with 2 bullets followed by a bold-labelled list: the
#    following list must not be counted into the box -> NONCONFORMANT
cat > "$TMP/kp_bold_two.md" <<'EOF'
**Key Points**
- Model A reached a higher AUC.
- Model B reached a lower AUC.

**Abbreviations**
- CT = computed tomography
EOF
ck "bold box ends at next bold label (2 bullets fails)" 1 "$(run --manuscript "$TMP/kp_bold_two.md" --journal radiology --strict)"

# 9) negative control: same shape with 3 bullets -> CONFORMANT
cat > "$TMP/kp_bold_three.md" <<'EOF'
**Key Points**
- Model A reached a higher AUC.
- Model B reached a lower AUC.
- External validation is still required.

**Abbreviations**
- CT = computed tomography
EOF
ck "bold box with 3 bullets + abbreviations list ok" 0 "$(run --manuscript "$TMP/kp_bold_three.md" --journal radiology --strict)"

# 10) a body sentence starting with the label words is not the box
cat > "$TMP/kp_body_line.md" <<'EOF'
# Introduction
Key points of prior work are summarized below.
- one
- two
- three
# Key Points
- only one bullet
EOF
ck "body line starting with label is not the box" 1 "$(run --manuscript "$TMP/kp_body_line.md" --journal radiology --strict)"

# 11) sub-bullets are not counted: 2 top-level + 1 nested -> NONCONFORMANT
cat > "$TMP/kp_nested_two.md" <<'EOF'
## Key Points
- Claim one
  - supporting detail
- Claim two
EOF
ck "sub-bullet not counted (2 top-level fails)" 1 "$(run --manuscript "$TMP/kp_nested_two.md" --journal radiology --strict)"

# 12) negative control: 3 top-level bullets with sub-bullets -> CONFORMANT
cat > "$TMP/kp_nested_three.md" <<'EOF'
## Key Points
- Claim one
  - supporting detail
- Claim two
  - supporting detail
- Claim three
EOF
ck "3 top-level bullets with sub-bullets ok" 0 "$(run --manuscript "$TMP/kp_nested_three.md" --journal radiology --strict)"

# 13) Research in context: labels present but every sub-block empty
cat > "$TMP/ric_empty.md" <<'EOF'
## Research in context
Evidence before this study
Added value of this study
Implications of all the available evidence
## Introduction
EOF
ck "research_in_context empty sub-blocks fail" 1 "$(run --manuscript "$TMP/ric_empty.md" --journal lancet-digital-health --strict)"

# 14) Research in context: sub-blocks only named inside one prose sentence
cat > "$TMP/ric_prose.md" <<'EOF'
## Research in context
We omit the evidence before this study, the added value of this study and the implications of all the available evidence.
## Methods
EOF
ck "research_in_context labels in prose fail" 1 "$(run --manuscript "$TMP/ric_prose.md" --journal lancet --strict)"

# 15) negative control: bold-only sub-labels with the text on the next line
cat > "$TMP/ric_block_labels.md" <<'EOF'
## Research in context
**Evidence before this study**
We searched PubMed for prior work.

**Added value of this study**
This study adds an external cohort.

**Implications of all the available evidence**
Findings support a prospective trial.
EOF
ck "research_in_context bold-only sub-labels ok" 0 "$(run --manuscript "$TMP/ric_block_labels.md" --journal lancet-digital-health --strict)"

# --- Radiology box label (templates label it "Key Results") -----------------
cat > "$TMP/kr_ok.md" <<'EOF'
## Key Results
- The model improved detection sensitivity in an internal test set.
- Specificity was preserved at the chosen operating threshold.
- External validation is still required before deployment.
EOF
# 16) Radiology accepts the template's "Key Results" label
ck "radiology Key Results box accepted" 0 "$(run --manuscript "$TMP/kr_ok.md" --journal radiology --strict)"
# 17) the template id rsna-radiology selects the format
ck "template id rsna-radiology accepted" 0 "$(run --manuscript "$TMP/kr_ok.md" --journal rsna-radiology --strict)"
# 18) negative control: RYAI keeps "Key Points" only
ck "ryai Key Results label still rejected" 1 "$(run --manuscript "$TMP/kr_ok.md" --journal ryai --strict)"
# 19) negative control: Radiology still accepts "Key Points"
ck "radiology Key Points box still accepted" 0 "$(run --manuscript "$TMP/kp_ok.md" --journal radiology --strict)"
# 20) a Key Results box with 2 bullets still fails for Radiology
printf '## Key Results\n- a.\n- b.\n' > "$TMP/kr_bad.md"
ck "radiology Key Results wrong bullet count fails" 1 "$(run --manuscript "$TMP/kr_bad.md" --journal radiology --strict)"

# --- Research-in-context box boundaries (reviewer counter-examples) ----------
# 21) bold-only sub-labels ending in a period, each followed by text -> CONFORMANT
cat > "$TMP/ric_period_labels.md" <<'EOF'
## Research in context
**Evidence before this study.**
We searched PubMed for prior work.

**Added value of this study.**
This study adds an external cohort.

**Implications of all the available evidence.**
Findings support a prospective trial.
EOF
ck "research_in_context period sub-labels ok" 0 "$(run --manuscript "$TMP/ric_period_labels.md" --journal lancet-digital-health --strict)"

# 22) a bold-only line inside a sub-block does not end the box -> CONFORMANT
cat > "$TMP/ric_inner_bold.md" <<'EOF'
## Research in context
**Evidence before this study**
We searched PubMed for prior work.

**Search strategy**
Terms were combined with Boolean operators.

**Added value of this study**
This study adds an external cohort.

**Implications of all the available evidence**
Findings support a prospective trial.
EOF
ck "research_in_context inner bold line kept" 0 "$(run --manuscript "$TMP/ric_inner_bold.md" --journal lancet-digital-health --strict)"

# 23) after the last sub-block a bold-only line still ends the box. The input
#     cannot tell "**Funding**" (next section) from a sub-heading inside
#     Implications (case 29), so the empty Implications is a soft ADVISORY,
#     not a hard failure (main cleared both shapes).
cat > "$TMP/ric_trailing_bold.md" <<'EOF'
## Research in context
**Evidence before this study**
We searched PubMed for prior work.
**Added value of this study**
This study adds an external cohort.
**Implications of all the available evidence**

**Funding**
Synthetic grant text.
EOF
ck "research_in_context empty last sub-block before bold label: exit" 0 "$(run --manuscript "$TMP/ric_trailing_bold.md" --journal lancet-digital-health --strict)"
ck "research_in_context empty last sub-block before bold label: verdict" "ADVISORY soft subblock_content" "$(verdict)"

# --- Indentation, bare-label punctuation, last sub-block sub-heading ---------
# (reviewer counter-examples: origin/main cleared each correct box below)
# 24) uniformly space-indented 3 bullets: the first bullet keeps its indent -> ok
printf '**Key Points**\n\n  - The model improved sensitivity.\n  - Specificity was preserved.\n  - External validation is needed.\n\n## Introduction\n' > "$TMP/kp_indent.md"
ck "uniformly indented 3 bullets ok" 0 "$(run --manuscript "$TMP/kp_indent.md" --journal radiology --strict)"
# 25) tab-indented 3 bullets -> ok
printf '**Key Points**\n\n\t- The model improved sensitivity.\n\t- Specificity was preserved.\n\t- External validation is needed.\n\n## Introduction\n' > "$TMP/kp_tab.md"
ck "tab-indented 3 bullets ok" 0 "$(run --manuscript "$TMP/kp_tab.md" --journal radiology --strict)"
# 26) indented box with an indented sub-bullet: 2 top-level bullets still fail
printf '**Key Points**\n\n  - Claim one.\n    - supporting detail\n  - Claim two.\n\n## Introduction\n' > "$TMP/kp_indent_nested.md"
ck "indented 2 top-level + sub-bullet fails" 1 "$(run --manuscript "$TMP/kp_indent_nested.md" --journal radiology --strict)"
# 27) bare label line ending in a period starts the box
printf 'Key Points.\n- The model improved sensitivity.\n- Specificity was preserved.\n- External validation is needed.\n' > "$TMP/kp_bare_period.md"
ck "bare label 'Key Points.' ok" 0 "$(run --manuscript "$TMP/kp_bare_period.md" --journal radiology --strict)"
# 28) bare 'Research in context.' label with complete sub-blocks -> ok
cat > "$TMP/ric_bare_period.md" <<'EOF'
Research in context.
Evidence before this study: We searched PubMed for prior work.
Added value of this study: This study adds an external cohort.
Implications of all the available evidence: Findings support a prospective trial.
EOF
ck "bare label 'Research in context.' ok" 0 "$(run --manuscript "$TMP/ric_bare_period.md" --journal lancet-digital-health --strict)"
# 29) bold sub-heading inside the last sub-block (Implications) -> not a hard fail
cat > "$TMP/ric_last_inner_bold.md" <<'EOF'
## Research in context
**Evidence before this study**
We searched PubMed for prior work.

**Added value of this study**
This study adds an external cohort.

**Implications of all the available evidence**

**For clinicians**
Findings support a prospective trial.
EOF
ck "research_in_context sub-heading in last sub-block: exit" 0 "$(run --manuscript "$TMP/ric_last_inner_bold.md" --journal lancet-digital-health --strict)"
ck "research_in_context sub-heading in last sub-block: verdict" "ADVISORY soft subblock_content" "$(verdict)"
# 30) negative control: an empty last sub-block ending at a heading stays hard
printf '## Research in context\n**Evidence before this study** a.\n**Added value of this study** b.\n**Implications of all the available evidence**\n\n## Introduction\nText.\n' > "$TMP/ric_last_empty_heading.md"
ck "research_in_context empty last sub-block before heading fails" 1 "$(run --manuscript "$TMP/ric_last_empty_heading.md" --journal lancet-digital-health --strict)"

echo "----"
echo "test_summary_box: $pass passed, $fail failed"
[ "$fail" -eq 0 ]
