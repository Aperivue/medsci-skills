#!/usr/bin/env bash
# Regression test: --allow-separate-attachments, and the exact shape of the amnesty it grants.
#
# The situation this exists for: a submission whose supplementary tables and figures are
# separate attachment files — the norm in radiology and most medical journals — checked in
# markdown-only mode. Those floats are cited, have no caption in the manuscript body, and
# there is no rendered DOCX to look them up in, so `_classify` returns MISSING_BODY and the
# run once printed SUBMISSION BLOCKED on a correctly packaged submission.
#
# MISSING_BODY carries two different situations under one name and only one of them is the
# SSOT drift that every triage table in this repo describes:
#
#   in_docx is True  -> the float IS rendered but has no body caption. Real drift. P0.
#   in_docx is None  -> no DOCX was supplied, so there is nothing to have drifted FROM.
#
# The maintainer's decision (2026-07-29) is that --allow-separate-attachments downgrades the
# second case: with the flag set the operator has declared those floats live outside the main
# document, and a gate that is red on correct work is a gate that gets skipped.
#
# The cost of that decision is a real amnesty — in markdown-only mode a caption nobody wrote is
# indistinguishable from an attachment, and both now pass. So what this suite pins is not just
# "it passes" but that the amnesty stays VISIBLE and BOUNDED:
#   - the excused rows are named, and labelled EXCUSED WITHOUT EVIDENCE, apart from the
#     MISSING_DOCX rows that a supplied DOCX actually proved absent;
#   - the JSON separates the two counts, so a consumer cannot read one as the other;
#   - MISSING_BODY with the float present in the DOCX still BLOCKS. That is SSOT drift, and no
#     attachment policy makes it acceptable.
set -u

REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
S="$REPO_ROOT/skills/manage-refs/scripts/check_xref.py"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

pass=0
fail=0
ck() {
  local label="$1" expected="$2" actual="$3"
  if [ "$expected" = "$actual" ]; then
    printf '  PASS  %-58s %s\n' "$label" "$actual"
    pass=$((pass + 1))
  else
    printf '  FAIL  %-58s expected=%s actual=%s\n' "$label" "$expected" "$actual"
    fail=$((fail + 1))
  fi
}

EXCUSED='EXCUSED WITHOUT EVIDENCE'

# --- a correctly packaged submission: supplement lives in separate attachment files ---
cat > "$TMP/sep.md" <<'MD'
# METHODS

We measured the thing (Table 1). Details are in Supplementary Table S1 and
Supplementary Figure S1, submitted as separate attachment files.

# TABLES

**Table 1.** Baseline characteristics of the study population.
MD

# --- genuine SSOT drift: the float IS rendered, but the body defines no caption ---
cat > "$TMP/drift.md" <<'MD'
# METHODS

We measured the thing (Table 1) and Supplementary Table S1.

# TABLES

**Table 1.** Baseline characteristics of the study population.
MD

python3 - "$TMP" <<'PY'
import sys
from docx import Document
tmp = sys.argv[1]

# Renders Table 1 only — the supplement is a separate attachment.
d = Document()
for t in ["METHODS",
          "We measured the thing (Table 1). Details are in Supplementary Table S1 and "
          "Supplementary Figure S1.",
          "Table 1. Baseline characteristics of the study population."]:
    d.add_paragraph(t)
d.save(f"{tmp}/main.docx")

# Renders Supplementary Table S1 too, while drift.md defines no caption for it.
d = Document()
for t in ["METHODS",
          "We measured the thing (Table 1) and Supplementary Table S1.",
          "Table 1. Baseline characteristics of the study population.",
          "Supplementary Table S1. Sensitivity analyses by centre."]:
    d.add_paragraph(t)
d.save(f"{tmp}/drift.docx")
PY

run() { python3 "$S" --md "$1" ${2:+--docx "$2"} --out "$TMP/out.json" \
          --allow-separate-attachments --strict > "$TMP/log.txt" 2>&1; echo $?; }

# 1) The declared case: markdown-only, floats live in separate attachment files.
rc=$(run "$TMP/sep.md" "")
ck "markdown-only separate-supplement PASSES under the flag" 0 "$rc"
grep -q "$EXCUSED" "$TMP/log.txt"; ck "...and the amnesty is stated, not silent" 0 "$?"
# The labels must appear in the EXCUSED block. Grepping the whole log passes vacuously —
# every label is already printed in the findings table above.
awk "/$EXCUSED/,/Run again with --docx/" "$TMP/log.txt" | grep -q 'Table:S-S1'
ck "...and the excused rows are NAMED in that block" 0 "$?"
grep -q 'nothing here was actually checked' "$TMP/log.txt"
ck "...and it says nothing was checked, not that it verified them" 0 "$?"
python3 -c "
import json,sys
s=json.load(open('$TMP/out.json'))['summary']
sys.exit(0 if s.get('downgraded_unchecked')==2 and s.get('downgraded_proven_absent')==0 else 1)" 2>/dev/null
ck "...and the JSON counts it as unchecked, not as proven-absent" 0 "$?"

# 2) A supplied DOCX turns the same rows into an EVIDENCED downgrade, not an excuse.
rc=$(run "$TMP/sep.md" "$TMP/main.docx")
ck "with --docx the same package PASSES too" 0 "$rc"
grep -q "$EXCUSED" "$TMP/log.txt"; ck "...and nothing is excused without evidence" 1 "$?"
grep -q 'MISSING_DOCX row(s) downgraded' "$TMP/log.txt"
ck "...it is reported as a proven-absent downgrade instead" 0 "$?"
python3 -c "
import json,sys
s=json.load(open('$TMP/out.json'))['summary']
sys.exit(0 if s.get('downgraded_proven_absent')==2 and s.get('downgraded_unchecked')==0 else 1)" 2>/dev/null
ck "...and the JSON keeps the two apart" 0 "$?"

# 3) The bound on the amnesty: real SSOT drift still blocks WITH the flag set.
rc=$(run "$TMP/drift.md" "$TMP/drift.docx")
ck "rendered-but-undefined caption still BLOCKS under the flag" 1 "$rc"
grep -q "$EXCUSED" "$TMP/log.txt"; ck "...and is not excused" 1 "$?"
grep -q 'does NOT excuse' "$TMP/log.txt"; ck "...and the run says why it is different" 0 "$?"

# 4) Without the flag nothing is downgraded at all — the declaration has to be made.
rc=$(python3 "$S" --md "$TMP/sep.md" --out "$TMP/out.json" --strict > "$TMP/log.txt" 2>&1; echo $?)
ck "no flag: the same package still blocks (opt-in preserved)" 1 "$rc"

echo "----"
echo "test_xref_separate_supplement: $pass passed, $fail failed"
[ "$fail" -eq 0 ]
