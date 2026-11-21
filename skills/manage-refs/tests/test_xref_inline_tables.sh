#!/usr/bin/env bash
# Regression test: a table placed in the body defines its own caption.
#
# Some journals ask for each table directly after the paragraph that first cites it, written as a
# caption line followed by the table:
#
#     **Table 1.** Baseline characteristics.
#
#     | Characteristic | Value |
#     |---|---|
#
# `check_xref` read table captions only under a caption heading (`## Tables`, ...), so that layout
# was halted with MISSING_BODY for every table, while an embedded figure in the same manuscript
# passed. The negative controls pin that recognising the layout did not loosen the gate: a caption
# line with no table beside it is still not a definition, a cited table defined nowhere and a
# caption that disagrees with the DOCX still block, and the caption line is not counted as the
# table's own citation.
set -u

REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
X="$REPO_ROOT/skills/manage-refs/scripts/check_xref.py"
WORK="$(mktemp -d -t xref_inline_tables.XXXXXX)"
trap 'rm -rf "$WORK"' EXIT

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

mk_docx() {  # mk_docx <path> <caption paragraph...>
  python3 - "$@" <<'PY'
import sys, zipfile
out, caps = sys.argv[1], sys.argv[2:]
body = "".join(f"<w:p><w:r><w:t>{c}</w:t></w:r></w:p>" for c in caps)
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    z.writestr("[Content_Types].xml", '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>')
    z.writestr("_rels/.rels", '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>')
    z.writestr("word/document.xml", '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>'
        + body + '</w:body></w:document>')
PY
}

run() {  # run <md> [docx] -> exit code; JSON at $WORK/<md>.json
  local md="$1" docx="${2:-}"
  if [ -n "$docx" ]; then
    python3 "$X" --md "$WORK/$md" --docx "$WORK/$docx" --strict --out "$WORK/$md.json" > "$WORK/$md.out" 2>&1
  else
    python3 "$X" --md "$WORK/$md" --strict --out "$WORK/$md.json" > "$WORK/$md.out" 2>&1
  fi
  echo $?
}
status_of() {  # status_of <md> <label>
  python3 -c "
import json, sys
for f in json.load(open(sys.argv[1]))['findings']:
    if f['label'] == sys.argv[2]:
        print(f['status']); break
else:
    print('ABSENT')" "$WORK/$1.json" "$2"
}

TABLE='| Characteristic | Value |
|---|---|
| Age, years | 61 |'

# Caption above the table (bold and plain), and caption below it.
{
  echo "## Results"; echo
  echo "Baseline characteristics are in Table 1 and outcomes in Table 2. Readers are in Table 3."; echo
  echo "**Table 1.** Baseline characteristics of the synthetic cohort."; echo
  echo "$TABLE"; echo
  echo "Table 2: Outcomes by study arm."; echo
  echo "$TABLE"; echo
  echo "$TABLE"; echo
  echo "**Table 3.** Reader experience."
} > "$WORK/inline.md"
mk_docx "$WORK/full.docx" "Table 1. Baseline characteristics of the synthetic cohort." \
  "Table 2: Outcomes by study arm." "Table 3. Reader experience."

echo "==== a caption line beside its table is a body definition ===="
ck "inline tables, no --docx: exit 0"                  0 "$(run inline.md)"
ck "  Table 1 (caption above, bold) is OK"             OK "$(status_of inline.md Table:1)"
ck "  Table 2 (caption above, plain) is OK"            OK "$(status_of inline.md Table:2)"
ck "  Table 3 (caption below) is OK"                   OK "$(status_of inline.md Table:3)"
ck "inline tables + the DOCX they render to: exit 0"   0 "$(run inline.md full.docx)"

echo "==== NEGATIVE CONTROLS: the gate still blocks what it should ===="
{
  echo "## Results"; echo
  echo "Baseline characteristics are in Table 1."; echo
  echo "**Table 1.** Baseline characteristics of the synthetic cohort."; echo
  echo "The cohort was recruited over two years."
} > "$WORK/notable.md"
ck "caption line with no table beside it: exit 1"      1 "$(run notable.md)"
ck "  Table 1 is MISSING_BODY"                         MISSING_BODY "$(status_of notable.md Table:1)"

{
  echo "## Results"; echo
  echo "Baseline characteristics are in Table 1 and outcomes in Table 2."; echo
  echo "**Table 1.** Baseline characteristics of the synthetic cohort."; echo
  echo "$TABLE"
} > "$WORK/one.md"
ck "cited Table 2 defined nowhere: exit 1"             1 "$(run one.md)"
ck "  Table 2 is MISSING_BODY"                         MISSING_BODY "$(status_of one.md Table:2)"

mk_docx "$WORK/other.docx" "Table 1. Scanner models and reconstruction kernels by site." \
  "Table 2: Outcomes by study arm." "Table 3. Reader experience."
ck "inline caption disagrees with the DOCX: exit 1"    1 "$(run inline.md other.docx)"
ck "  Table 1 is MISMATCH"                             MISMATCH "$(status_of inline.md Table:1)"

mk_docx "$WORK/partial.docx" "Table 1. Baseline characteristics of the synthetic cohort." \
  "Table 2: Outcomes by study arm."
ck "Table 3 absent from the DOCX: exit 1"              1 "$(run inline.md partial.docx)"
ck "  Table 3 is MISSING_DOCX"                         MISSING_DOCX "$(status_of inline.md Table:3)"

# The caption line must not count as a citation of its own table.
{
  echo "## Results"; echo
  echo "The cohort was recruited over two years."; echo
  echo "**Table 1.** Baseline characteristics of the synthetic cohort."; echo
  echo "$TABLE"
} > "$WORK/uncited.md"
run uncited.md >/dev/null
ck "an inline table nobody cites is UNCITED"           UNCITED "$(status_of uncited.md Table:1)"

echo
echo "  passed=$pass failed=$fail"
[ "$fail" -eq 0 ] || { for f in inline notable one uncited; do echo "--- $f"; cat "$WORK/$f.md.out"; done; exit 1; }
echo "OK: a caption line beside its table is a body definition, and the gate still blocks real defects."
