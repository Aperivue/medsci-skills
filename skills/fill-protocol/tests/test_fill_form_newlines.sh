#!/usr/bin/env bash
# Regression test: a newline in section content must become a line break the reader can see.
#
# `section_replace` splits its content on `\n\n` into paragraphs. Only the FIRST of those went
# through the run builder that turns `\n` into `w:br`; every later one did `t.text = chunk`, which
# leaves the newline inside `w:t` — and Word renders a newline in `w:t` as a space. An IRB form's
# inclusion criteria, written as "1) ...\n2) ...\n3) ...", therefore arrived as one flowed
# sentence. The run printed `[OK]` for every label and `validate()` returned clean, because both
# were reporting on the fill, not on the document. Only opening the rendered PDF showed it.
#
# Both defective paths are covered here: the branch that REPLACES existing body paragraphs, and
# the branch that INSERTS when a header is immediately followed by the next header. The assertions
# are made against the produced XML — the artifact — not against the filler's own report.
#
# Builds its template at runtime; no committed binary fixture. Network-free.
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$HERE/../scripts/fill_form.py"
TMP="$(mktemp -d -t fillnl_XXXX)"
trap 'rm -rf "$TMP"' EXIT

pass=0
fail=0
ck() {
  local label="$1" expected="$2" actual="$3"
  if [ "$expected" = "$actual" ]; then
    printf '  PASS  %-52s %s\n' "$label" "$actual"
    pass=$((pass + 1))
  else
    printf '  FAIL  %-52s expected=%s actual=%s\n' "$label" "$expected" "$actual"
    fail=$((fail + 1))
  fi
}

[ -f "$SCRIPT" ] || { echo "ENV-ERR: fill_form.py missing" >&2; exit 2; }
python3 -c "import docx, yaml" 2>/dev/null || { echo "SKIP: python-docx/pyyaml unavailable"; exit 0; }

TEMPLATE="$TMP/template.docx"
CONTENT="$TMP/content.yaml"
OUTPUT="$TMP/filled.docx"

python3 - "$TEMPLATE" <<'PY'
import sys
from docx import Document
doc = Document()
doc.add_paragraph("1. Background")
doc.add_paragraph("TODO: background placeholder")     # replace-path: a body paragraph exists
doc.add_paragraph("2. Eligibility")
doc.add_paragraph("3. References")                    # insert-path: header follows header
doc.add_paragraph("TODO: references placeholder")
doc.save(sys.argv[1])
PY

# Chunk 0 of Background carries one newline; chunk 1 carries two. Eligibility has no body
# paragraph after it, so it takes the insert branch, and its single chunk carries two newlines.
# The single-line section is the negative control: it must produce no break at all.
cat > "$CONTENT" <<'YAML'
section_replace:
  "1. Background": "Opening line one\nOpening line two\n\nInclusion criteria:\n1) age 19 or over\n2) index CT available\n3) written consent"
  "2. Eligibility": "Exclusion criteria:\n1) prior surgery\n2) no follow-up"
  "3. References": "A single line with no breaks at all."
YAML

LOG="$TMP/run.log"
python3 "$SCRIPT" --template "$TEMPLATE" --content "$CONTENT" --output "$OUTPUT" >"$LOG" 2>&1
rc=$?
ck "fill_form exit code" "0" "$rc"

out="$(python3 - "$OUTPUT" <<'PY'
import json, sys, zipfile, re
xml = zipfile.ZipFile(sys.argv[1]).read("word/document.xml").decode("utf-8")
from docx import Document
doc = Document(sys.argv[1])
res = {}
# w:br elements are the line breaks a reader actually sees.
res["breaks"] = str(len(re.findall(r"<w:br\s*/>", xml)))
# A newline surviving inside w:t is the defect itself, in the artifact.
res["raw_newlines_in_wt"] = str(len(re.findall(r"<w:t[^>]*>[^<]*\n[^<]*</w:t>", xml)))
# Every criterion must still be present as text — a fix that dropped content would be worse.
blob = "\n".join(p.text for p in doc.paragraphs)
for token in ("age 19 or over", "index CT available", "written consent",
              "prior surgery", "no follow-up", "Opening line two"):
    res["has_" + token.split()[0] + token.split()[-1]] = str(token in blob).lower()
res["single_line_intact"] = str("A single line with no breaks at all." in blob).lower()
print(json.dumps(res))
PY
)"
get() { python3 -c "import json,sys; print(json.loads(sys.argv[1])[sys.argv[2]])" "$out" "$1"; }

echo "==== every newline became a break the reader can see ===="
# Background: 1 (chunk 0) + 3 (chunk 1) = 4.  Eligibility, insert path: 2.  References: 0.
ck "w:br elements in the produced document"   "6"     "$(get breaks)"

echo "==== NEGATIVE CONTROLS ===="
ck "newlines left inside w:t"                 "0"     "$(get raw_newlines_in_wt)"
ck "single-line section unchanged"            "true"  "$(get single_line_intact)"

echo "==== no criterion was dropped in the process ===="
ck "chunk 0, second line"                     "true"  "$(get has_Openingtwo)"
ck "replace path, first criterion"            "true"  "$(get has_ageover)"
ck "replace path, last criterion"             "true"  "$(get has_writtenconsent)"
ck "insert path, first criterion"             "true"  "$(get has_priorsurgery)"
ck "insert path, last criterion"              "true"  "$(get has_nofollow-up)"

echo "==== validate() can see the defect if it ever returns ===="
warned="$(python3 - "$SCRIPT" "$TMP" <<'PY'
import importlib.util, sys
from pathlib import Path
from docx import Document
from docx.oxml.ns import qn

spec = importlib.util.spec_from_file_location("ff", sys.argv[1])
m = importlib.util.module_from_spec(spec)
sys.modules["ff"] = m
spec.loader.exec_module(m)

# A document poisoned the way the old code poisoned it: a newline sitting inside w:t.
p = Path(sys.argv[2]) / "poisoned.docx"
doc = Document()
para = doc.add_paragraph()
run = para.add_run()
t = run._element.find(qn("w:t"))
if t is None:
    from docx.oxml import OxmlElement
    t = OxmlElement("w:t")
    run._element.append(t)
t.text = "1) first\n2) second"
doc.save(p)

filler = m.FormFiller(str(p))
hits = [w for w in filler.validate() if "RAW-NEWLINE" in w]
print(len(hits))
PY
)"
ck "warning raised on a poisoned document"    "1"     "$warned"

echo
echo "  passed=$pass failed=$fail"
[ "$fail" -eq 0 ] || exit 1
echo "OK: line breaks reach the page, no newline hides in w:t, and validate() would say so."
