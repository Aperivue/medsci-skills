#!/usr/bin/env bash
# Regression test: check_xref must say what would decide a MISSING_BODY it cannot decide.
#
# The situation this exists for: a submission whose supplementary tables and figures are
# separate attachment files — the norm in radiology and most medical journals — checked in
# markdown-only mode. Those floats are cited, have no caption in the manuscript body, and
# there is no rendered DOCX to look them up in. `_classify` returns MISSING_BODY, which
# `--allow-separate-attachments` does not downgrade, so the run prints
# `SUBMISSION BLOCKED` on a correctly packaged submission and offers no way forward.
#
# MISSING_BODY carries two different situations under one name and only one of them is the
# SSOT drift that every triage table in this repo describes:
#
#   in_docx is True  -> the float IS rendered but has no body caption. Real drift. P0.
#   in_docx is None  -> no DOCX was supplied, so there is nothing to have drifted FROM.
#
# This test does not change either verdict — a P0 submission gate's vocabulary is consumed by
# /self-review, /write-paper and /sync-submission triage tables, and moving it is a decision
# for a human. It pins the smaller fix: the second case must NAME the labels and say that
# supplying --docx is what decides them. A gate that is red on correct work with no stated
# way out is a gate the operator learns to skip, which costs more than the check is worth.
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

NOTE='no --docx to compare against'

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

# 1) The case the note exists for: undecidable without a DOCX.
rc=$(run "$TMP/sep.md" "")
ck "markdown-only separate-supplement still blocks (verdict unchanged)" 1 "$rc"
grep -q "$NOTE" "$TMP/log.txt"; ck "...and the run says --docx is what decides it" 0 "$?"
# The labels must appear ON the note line. Grepping the whole log passes vacuously —
# every label is already printed in the findings table above, so that assertion would
# have been green against the unfixed code too.
grep -q "$NOTE.*Table:S-S1" "$TMP/log.txt"; ck "...and the note itself NAMES them" 0 "$?"

# 2) Supplying the DOCX is genuinely the way out — the whole point of the note.
rc=$(run "$TMP/sep.md" "$TMP/main.docx")
ck "with --docx the same package PASSES under the flag" 0 "$rc"
grep -q "$NOTE" "$TMP/log.txt"; ck "...and the note is silent (nothing undecidable)" 1 "$?"
grep -q "downgraded under --allow-separate-attachments: " "$TMP/log.txt"
ck "...and the downgraded rows are named, not just counted" 0 "$?"

# 3) Real SSOT drift must be untouched: it blocks, and the note must NOT excuse it.
rc=$(run "$TMP/drift.md" "$TMP/drift.docx")
ck "rendered-but-undefined caption still BLOCKS (P0 preserved)" 1 "$rc"
grep -q "$NOTE" "$TMP/log.txt"; ck "...and the note does not fire on real drift" 1 "$?"

echo "----"
echo "test_xref_separate_supplement: $pass passed, $fail failed"
[ "$fail" -eq 0 ]
