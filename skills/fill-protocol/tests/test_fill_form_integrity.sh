#!/usr/bin/env bash
# Regression test: the filler must not change, drop or leave behind form content under an [OK].
#
# Three silent failures, each asserted against the produced document, not the filler's report:
#   F1  section_replace on the LAST numbered header had no end boundary and deleted every paragraph
#       to the end of the document (a signature/date block), printing [OK] with no WARN.
#   F2  yaml.safe_load + str() rewrote values: 012345 -> 5349, 12:30 -> 750, 1.10 -> 1.1,
#       No -> False, an empty value -> "None", a list -> its Python repr.
#   F3  paragraph replacement removed only direct w:r children, so a placeholder inside a
#       w:hyperlink or a w:ins stayed in the paragraph next to the new text.
# Each has a negative control that must stay as before (same text, no new WARN).
#
# Builds its templates at runtime; no committed binary fixture. Network-free.
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="${FILL_FORM:-$HERE/../scripts/fill_form.py}"
TMP="$(mktemp -d -t fillint_XXXX)"
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

[ -f "$SCRIPT" ] || { echo "ENV-ERR: fill_form.py missing" >&2; exit 2; }
python3 -c "import docx, yaml" 2>/dev/null || { echo "SKIP: python-docx/pyyaml unavailable"; exit 0; }

python3 - "$TMP" <<'PY'
import sys
from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
tmp = sys.argv[1]

def run(text):
    r = OxmlElement("w:r"); t = OxmlElement("w:t"); t.text = text
    t.set(qn("xml:space"), "preserve"); r.append(t); return r

# F1 positive: last section followed by a signature/date block.
d = Document()
for s in ["1. Background", "placeholder", "2. References", "placeholder refs",
          "Investigator signature: ________", "Date: ________"]:
    d.add_paragraph(s)
d.save(f"{tmp}/sig.docx")

# F1 negative: last section is the end of the document; a bounded middle section.
d = Document()
for s in ["1. Background", "placeholder", "2. References", "placeholder refs"]:
    d.add_paragraph(s)
d.save(f"{tmp}/plain.docx")

# F2: key/value table.
d = Document()
labels = ["IRB Number", "Visit time", "Dose (mg)", "Vulnerable subjects", "Quoted", "Date"]
t = d.add_table(rows=len(labels), cols=2)
for i, l in enumerate(labels):
    t.cell(i, 0).text = l
d.add_paragraph("1. Background")
d.add_paragraph("placeholder")
d.add_paragraph("2. Methods")
d.save(f"{tmp}/kv.docx")

# F3: placeholder inside w:hyperlink; direct text + tracked insertion; bookmark control.
d = Document()
p = d.add_paragraph()
h = OxmlElement("w:hyperlink"); h.append(run("[ENTER TITLE HERE]")); p._p.append(h)
p = d.add_paragraph()
p._p.append(run("Sponsor: "))
ins = OxmlElement("w:ins"); ins.set(qn("w:id"), "1"); ins.set(qn("w:author"), "t")
ins.append(run("[TRACKED PLACEHOLDER]")); p._p.append(ins)
p = d.add_paragraph()
bs = OxmlElement("w:bookmarkStart"); bs.set(qn("w:id"), "7"); bs.set(qn("w:name"), "anchor")
be = OxmlElement("w:bookmarkEnd"); be.set(qn("w:id"), "7")
p._p.append(bs); p._p.append(run("Version: draft")); p._p.append(be)
d.save(f"{tmp}/links.docx")
PY

fill() {  # fill <template> <yaml> <out> -> sets rc, log
  python3 "$SCRIPT" --template "$TMP/$1" --content "$TMP/$2" --output "$TMP/$3" >"$TMP/$3.log" 2>&1
  rc=$?
}
paras() { python3 -c 'import sys; from docx import Document; print("|".join(p.text for p in Document(sys.argv[1]).paragraphs if p.text.strip()))' "$TMP/$1"; }
cells() { python3 -c 'import sys; from docx import Document; print("|".join(r.cells[1].text for r in Document(sys.argv[1]).tables[0].rows))' "$TMP/$1"; }
nwarn() { grep -c "$1" "$TMP/$2.log"; }

echo "--- F1: last section must not delete what follows it ---"
cat > "$TMP/sec.yaml" <<'YAML'
section_replace:
  "2. References": "Ref A"
YAML
fill sig.docx sec.yaml sig_out.docx
ck "F1+ exit code" "0" "$rc"
ck "F1+ signature and date kept" \
   "1. Background|placeholder|2. References|Ref A|Investigator signature: ________|Date: ________" \
   "$(paras sig_out.docx)"
ck "F1+ SECTION-UNBOUNDED warned" "1" "$(nwarn 'WARN: \[SECTION-UNBOUNDED\]' sig_out.docx)"

cat > "$TMP/sec2.yaml" <<'YAML'
section_replace:
  "1. Background": "New background"
  "2. References": "Ref A"
YAML
fill plain.docx sec2.yaml plain_out.docx
ck "F1- exit code" "0" "$rc"
ck "F1- both sections replaced" "1. Background|New background|2. References|Ref A" "$(paras plain_out.docx)"
ck "F1- no WARN at all" "0" "$(nwarn 'WARN:' plain_out.docx)"

echo "--- F2: form values are written as typed ---"
cat > "$TMP/kv.yaml" <<'YAML'
protections:
  blank_around_section_header: false
table_kv:
  IRB Number: 012345
  Visit time: 12:30
  Dose (mg): 1.10
  Vulnerable subjects: No
  Quoted: "IRB-2026-001"
  Date: 2026-01-15
section_replace:
  "1. Background": "Text"
YAML
fill kv.docx kv.yaml kv_out.docx
ck "F2+ exit code" "0" "$rc"
ck "F2+ values verbatim" "012345|12:30|1.10|No|IRB-2026-001|2026-01-15" "$(cells kv_out.docx)"
ck "F2- protections boolean still honoured (no blank)" "3" \
   "$(python3 -c 'import sys; from docx import Document; print(len(Document(sys.argv[1]).paragraphs))' "$TMP/kv_out.docx")"
ck "F2- no WARN" "0" "$(nwarn 'WARN:' kv_out.docx)"

printf 'table_kv:\n  IRB Number:\n' > "$TMP/empty.yaml"
fill kv.docx empty.yaml empty_out.docx
ck "F2+ empty value -> exit 2" "2" "$rc"
ck "F2+ empty value names the label" "1" "$(grep -c "IRB Number" "$TMP/empty_out.docx.log")"
ck "F2+ empty value -> no output written" "no" "$([ -e "$TMP/empty_out.docx" ] && echo yes || echo no)"

printf 'table_kv:\n  IRB Number: [A, B]\n' > "$TMP/list.yaml"
fill kv.docx list.yaml list_out.docx
ck "F2+ list value -> exit 2" "2" "$rc"
ck "F2+ list value names the label" "1" "$(grep -c "IRB Number" "$TMP/list_out.docx.log")"

printf "table_kv:\n  IRB Number: ''\n" > "$TMP/blank.yaml"
fill kv.docx blank.yaml blank_out.docx
ck "F2- explicit '' accepted" "0" "$rc"

echo "--- F3: placeholder in a run container must not survive ---"
cat > "$TMP/links.yaml" <<'YAML'
paragraph_replace:
  "[ENTER TITLE HERE]": "Title: Real Study"
  "Sponsor:": "Sponsor: Real Sponsor"
  "Version:": "Version: 1.0"
YAML
fill links.docx links.yaml links_out.docx
ck "F3+ exit code" "0" "$rc"
ck "F3+ paragraph texts" "Title: Real Study|Sponsor: Real Sponsor|Version: 1.0" "$(paras links_out.docx)"
ck "F3+ no placeholder left in document.xml" "0" \
   "$(python3 -c 'import sys,zipfile; x=zipfile.ZipFile(sys.argv[1]).read("word/document.xml").decode(); print(x.count("ENTER TITLE HERE")+x.count("TRACKED PLACEHOLDER"))' "$TMP/links_out.docx")"
ck "F3- bookmark kept" "1" \
   "$(python3 -c 'import sys,zipfile; x=zipfile.ZipFile(sys.argv[1]).read("word/document.xml").decode(); print(x.count("w:name=\"anchor\""))' "$TMP/links_out.docx")"

echo "passed=$pass failed=$fail"
[ "$fail" -eq 0 ]
