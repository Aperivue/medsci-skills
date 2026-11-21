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

# A line that merely starts with "|" is not a table: here it is an absolute-value expression.
{
  echo "## Results"; echo
  echo "The error metric is defined in Table 1."; echo
  echo "**Table 1.** Error metric."; echo
  echo "|x - y| denotes the absolute error between readers."
} > "$WORK/pipeprose.md"
ck "a '|' that is not a table: exit 1"                 1 "$(run pipeprose.md)"
ck "  Table 1 is MISSING_BODY"                         MISSING_BODY "$(status_of pipeprose.md Table:1)"

# One table cannot define the caption above it and a different caption below it.
{
  echo "## Results"; echo
  echo "Baseline characteristics are in Table 1 and outcomes in Table 2."; echo
  echo "**Table 1.** Baseline characteristics of the synthetic cohort."; echo
  echo "$TABLE"; echo
  echo "**Table 2.** Outcomes by study arm."
} > "$WORK/onetable.md"
ck "one table, two captions: exit 1"                   1 "$(run onetable.md)"
ck "  Table 1 (above) is OK"                           OK "$(status_of onetable.md Table:1)"
ck "  Table 2 (no table of its own) is MISSING_BODY"   MISSING_BODY "$(status_of onetable.md Table:2)"

# A caption and table shown inside a fenced code block are an example, not a float.
{
  echo "## Results"; echo
  echo "Baseline characteristics are in Table 1."; echo
  echo '```'
  echo "**Table 1.** Baseline characteristics of the synthetic cohort."; echo
  echo "$TABLE"
  echo '```'
} > "$WORK/fenced.md"
ck "caption and table inside a code fence: exit 1"     1 "$(run fenced.md)"
ck "  Table 1 is MISSING_BODY"                         MISSING_BODY "$(status_of fenced.md Table:1)"

# Table forms other than a fully piped table: no outer pipes, and HTML with the caption below.
{
  echo "## Results"; echo
  echo "Ages are in Table 1 and sites in Table 2."; echo
  echo "**Table 1.** Age by group."; echo
  echo "Group | N"; echo "--- | ---"; echo "A | 4"; echo
  echo "<table>"; echo "<tr><td>Site</td><td>N</td></tr>"; echo "</table>"; echo
  echo "**Table 2.** Participants by site."
} > "$WORK/forms.md"
ck "pipe table without outer pipes, HTML table: exit 0" 0 "$(run forms.md)"
ck "  Table 1 is OK"                                   OK "$(status_of forms.md Table:1)"
ck "  Table 2 is OK"                                   OK "$(status_of forms.md Table:2)"

# Things that look like a table and are not one. Each follows a caption for a cited Table 1.
nat=0
not_a_table() {  # not_a_table <label> <lines after the caption...>; each call has its own files
  local label="$1"; shift
  nat=$((nat + 1))
  {
    echo "## Results"; echo
    echo "The values are in Table 1."; echo
    echo "**Table 1.** Results."; echo
    for line in "$@"; do echo "$line"; done
  } > "$WORK/nat$nat.md"
  ck "not a table: $label (exit 1)" 1 "$(run "nat$nat.md")"
  ck "  Table 1 is MISSING_BODY" MISSING_BODY "$(status_of "nat$nat.md" Table:1)"
}
not_a_table "header and delimiter rows with different cell counts" "A | B" "--- | --- | ---"
not_a_table "a '+---+' line over a '+' list item"                  "+---+" "+ List item"
not_a_table "'<table>' inside an attribute value"                  '<div data-example="<table></table>"></div>'
not_a_table "a code fence between the caption and a table"         '```' 'x = 1' '```' "" "| A | B |" "|---|---|" "| 1 | 2 |"
not_a_table "'<table>' in an attribute value after a space"        '<div title="see <table></table>"></div>'
not_a_table "an unclosed grid cell row"                            "+---+" "| unfinished" "+------+"

# A heading ends a pipe table; a caption below the heading does not belong to that table.
{
  echo "## Results"; echo
  echo "The values are in Table 1."; echo
  echo "| A | B |"; echo "|-|-|"; echo "| 1 | 2 |"; echo "## Error | bias"; echo
  echo "**Table 1.** Results."
} > "$WORK/heading.md"
ck "a heading ends the table above it: exit 1"         1 "$(run heading.md)"
ck "  Table 1 is MISSING_BODY"                         MISSING_BODY "$(status_of heading.md Table:1)"

# An HTML table whose opening tag runs over two lines is a table.
{
  echo "## Results"; echo
  echo "The values are in Table 1."; echo
  echo "**Table 1.** Results."; echo
  echo "<table"; echo ' class="results">'; echo "<tr><td>1</td></tr>"; echo "</table>"
} > "$WORK/htmlwrap.md"
run htmlwrap.md >/dev/null
ck "an HTML table with a wrapped opening tag"          OK "$(status_of htmlwrap.md Table:1)"

# A table GFM renders with one-hyphen delimiter cells is a table.
{
  echo "## Results"; echo
  echo "The values are in Table 1."; echo
  echo "**Table 1.** Results."; echo
  echo "| A | B |"; echo "|-|-|"; echo "|1|2|"
} > "$WORK/short.md"
run short.md >/dev/null
ck "one-hyphen delimiter cells are a table"            OK "$(status_of short.md Table:1)"

# A grid table with cell rows and a closing border is a table.
{
  echo "## Results"; echo
  echo "The values are in Table 1."; echo
  echo "**Table 1.** Results."; echo
  echo "+-----+-----+"; echo "| A   | B   |"; echo "+=====+=====+"; echo "| 1   | 2   |"; echo "+-----+-----+"
} > "$WORK/grid.md"
run grid.md >/dev/null
ck "a grid table with cell rows and a closing border"  OK "$(status_of grid.md Table:1)"

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
[ "$fail" -eq 0 ] || { for f in inline notable one uncited pipeprose onetable fenced forms short grid heading htmlwrap; do echo "--- $f"; cat "$WORK/$f.md.out"; done; exit 1; }
echo "OK: a caption line beside its table is a body definition, and the gate still blocks real defects."
