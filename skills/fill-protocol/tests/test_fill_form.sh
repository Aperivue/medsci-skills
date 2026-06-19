#!/usr/bin/env bash
# Regression test for fill-protocol/scripts/fill_form.py.
# Builds a synthetic template .docx at runtime (python-docx) with a 2-column
# key/value table, two numbered section headers, and a title paragraph; writes a
# content YAML exercising table_kv / section_replace / paragraph_replace plus one
# deliberately-missing label; runs fill_form.py; then re-opens the output and
# asserts the values landed and the bogus label reported MISS. No committed
# binary fixture. Needs python-docx + pyyaml (already in CI deps). Network-free,
# Hangul-free (template uses English labels; eastAsia font path is exercised by
# real usage, not asserted here).
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$HERE/../scripts/fill_form.py"
TMP="$(mktemp -d -t fillform_XXXX)"
trap 'rm -rf "$TMP"' EXIT

fail=0
check() { local label="$1"; shift
    if "$@" >/dev/null 2>&1; then printf '  PASS  %s\n' "$label"
    else printf '  FAIL  %s\n' "$label"; fail=$((fail+1)); fi
}

[[ -f "$SCRIPT" ]] || { echo "ENV-ERR: fill_form.py missing" >&2; exit 2; }
python3 -c "import docx, yaml" 2>/dev/null || { echo "SKIP: python-docx/pyyaml unavailable"; exit 0; }

TEMPLATE="$TMP/template.docx"
CONTENT="$TMP/content.yaml"
OUTPUT="$TMP/filled.docx"

# --- Build synthetic template ---
python3 - "$TEMPLATE" <<'PY'
import sys
from docx import Document
doc = Document()
doc.add_paragraph("Study Title: PLACEHOLDER TITLE")
t = doc.add_table(rows=2, cols=2)
t.cell(0, 0).text = "Principal Investigator"
t.cell(0, 1).text = ""
t.cell(1, 0).text = "IRB Number"
t.cell(1, 1).text = ""
doc.add_paragraph("1. Background")
doc.add_paragraph("TODO: background placeholder")
doc.add_paragraph("2. Methods")
doc.add_paragraph("TODO: methods placeholder")
doc.save(sys.argv[1])
PY
check "synthetic template built" test -s "$TEMPLATE"

# --- Content YAML (one label intentionally absent: 'Funding Source') ---
# (no korean_font override -> fill_form.py uses its built-in default; keeps this
#  test file Hangul-free.)
cat > "$CONTENT" <<'YAML'
table_kv:
  Principal Investigator: "Alice Kim"
  IRB Number: "IRB-2026-001"
  Funding Source: "This label is absent in the template"
section_replace:
  "1. Background": "Synthetic background content for the regression test."
paragraph_replace:
  "Study Title:": "Study Title: Synthetic Protocol"
YAML

# --- Run the filler, capture stdout for MISS detection ---
LOG="$TMP/run.log"
python3 "$SCRIPT" --template "$TEMPLATE" --content "$CONTENT" --output "$OUTPUT" >"$LOG" 2>&1
check "fill_form exit 0" test "$?" -eq 0
check "output docx written" test -s "$OUTPUT"

# Absent label reported as MISS; present labels reported OK.
check "absent label reported MISS" grep -qE "\[MISS\].*Funding Source" "$LOG"
check "present label reported OK"  grep -qE "\[OK \].*Principal Investigator" "$LOG"

# --- Re-open output and assert substitutions landed ---
check "values substituted in output" python3 - "$OUTPUT" <<'PY'
import sys
from docx import Document
doc = Document(sys.argv[1])
# all text across paragraphs + table cells
texts = [p.text for p in doc.paragraphs]
for tbl in doc.tables:
    for row in tbl.rows:
        for c in row.cells:
            texts.append(c.text)
blob = "\n".join(texts)
assert "Alice Kim" in blob, "PI value missing"
assert "IRB-2026-001" in blob, "IRB value missing"
assert "Synthetic background content" in blob, "section_replace missing"
assert "Study Title: Synthetic Protocol" in blob, "paragraph_replace missing"
assert "PLACEHOLDER TITLE" not in blob, "title placeholder not replaced"
PY

echo "fail=$fail"; [[ "$fail" -eq 0 ]] && echo "ALL PASS" || echo "FAILURES: $fail"
exit "$fail"
