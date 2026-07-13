#!/usr/bin/env bash
# Regression test for skills/sync-submission/scripts/check_marked_manuscript.py — the
# marked (tracked-changes) manuscript round-trip gate.
#
# The fixtures are synthetic OOXML written at run time (stdlib zipfile; no Word, no
# python-docx), so the gate is exercised on the exact revision encodings Word emits:
# w:ins / w:del for edits and w:moveFrom / w:moveTo for relocated content.
#
# The moved-paragraph case is the point of the test. It is a real discriminator: a
# verifier that knows only ins/del reconstructs the *original* as containing the moved
# paragraph twice (once from the moveFrom delText, once from the moveTo run it fails to
# recognise as an insertion) and reports a good file as corrupt. The test asserts both
# halves — the naive resolution fails, the move-aware gate passes.
set -u

REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
V="$REPO_ROOT/skills/sync-submission/scripts/check_marked_manuscript.py"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

pass=0
fail=0
ck() {
  local label="$1" expected="$2" actual="$3"
  if [ "$expected" = "$actual" ]; then
    printf '  PASS  %-54s exit=%s\n' "$label" "$actual"
    pass=$((pass + 1))
  else
    printf '  FAIL  %-54s expected=%s actual=%s\n' "$label" "$expected" "$actual"
    fail=$((fail + 1))
  fi
}

# --- fixtures -------------------------------------------------------------------
python3 - "$TMP" <<'PY'
import sys, zipfile
from pathlib import Path

TMP = Path(sys.argv[1])
NS = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
AUTHOR, OTHER = "Submitting Author", "Other Person"
D = 'w:date="2026-07-13T00:00:00Z"'
_id = iter(range(100, 999))

def run(t):        return f'<w:r><w:t xml:space="preserve">{t}</w:t></w:r>'
def drun(t):       return f'<w:r><w:delText xml:space="preserve">{t}</w:delText></w:r>'
def ins(t, a=AUTHOR):      return f'<w:ins w:id="{next(_id)}" w:author="{a}" {D}>{run(t)}</w:ins>'
def dele(t, a=AUTHOR):     return f'<w:del w:id="{next(_id)}" w:author="{a}" {D}>{drun(t)}</w:del>'
def move_from(t, a=AUTHOR): return f'<w:moveFrom w:id="{next(_id)}" w:author="{a}" {D}>{drun(t)}</w:moveFrom>'
def move_to(t, a=AUTHOR):   return f'<w:moveTo w:id="{next(_id)}" w:author="{a}" {D}>{run(t)}</w:moveTo>'
def p(*inner):     return "<w:p>" + "".join(inner) + "</w:p>"
def table(t):      return f'<w:tbl><w:tr><w:tc>{p(run(t))}</w:tc></w:tr></w:tbl>'

def docx(name, *blocks):
    body = "".join(blocks)
    doc = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
           f'<w:document {NS}><w:body>{body}'
           f'<w:sectPr><w:pgMar w:top="1440" w:bottom="1440"/></w:sectPr>'
           f'</w:body></w:document>')
    ct = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
          '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
          '<Default Extension="xml" ContentType="application/xml"/>'
          '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
          '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
          '</Types>')
    rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Target="word/document.xml" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument"/>'
            '</Relationships>')
    with zipfile.ZipFile(TMP / name, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", ct)
        z.writestr("_rels/.rels", rels)
        z.writestr("word/document.xml", doc)

A, B, C = "Alpha. ", "Bravo. ", "Charlie. "
B2 = "Bravo revised. "

# 1) baseline pair for the edit + move cases
docx("original.docx", p(run(A)), p(run(B)), p(run(C)))

# an ordinary edit: Bravo rewritten
docx("revised_edit.docx", p(run(A)), p(run(B2)), p(run(C)))
docx("marked_edit.docx", p(run(A)), p(dele(B), ins(B2)), p(run(C)))

# same edit, but half the revisions attributed to someone else
docx("marked_author.docx", p(run(A)), p(dele(B), ins(B2, OTHER)), p(run(C)))

# Compare dropped a paragraph: Charlie is simply gone from the marked file
docx("marked_dropped.docx", p(run(A)), p(dele(B), ins(B2)))

# a MOVE: Bravo relocated after Charlie. Word encodes this as moveFrom/moveTo,
# NOT as del/ins — the whole reason this gate must be move-aware.
docx("revised_move.docx", p(run(A)), p(run(C)), p(run(B)))
docx("marked_move.docx", p(run(A)), p(move_from(B)), p(run(C)), p(move_to(B)))

# a clean copy of the revised file — no tracked changes at all
docx("marked_clean.docx", p(run(A)), p(run(B2)), p(run(C)))

# 2) table-loss pair: identical text, but Compare flattened the table to a paragraph
CELL = "Cell one "
docx("original_tbl.docx", p(run(A)), table(CELL))
docx("revised_tbl.docx", p(run(B2)), table(CELL))
docx("marked_tbl.docx", p(dele(A), ins(B2)), p(run(CELL)))

# 3) a baseline that itself still carries tracked changes
docx("original_dirty.docx", p(run(A)), p(ins(B)), p(run(C)))
PY

# --- 1) a moved paragraph must PASS (move-aware) ---------------------------------
python3 "$V" --marked "$TMP/marked_move.docx" --original "$TMP/original.docx" \
  --revised "$TMP/revised_move.docx" --author "Submitting Author" --strict \
  --out "$TMP/move.json" > /dev/null 2>&1
ck "moved paragraph passes the round trip" 0 "$?"

python3 - "$TMP/move.json" <<'PY'
import json, sys
s = json.load(open(sys.argv[1]))["summary"]
m = s["revision_marks"]
assert m["moveTo"] and m["moveFrom"], f"fixture is not a move fixture: {m}"
assert not m["ins"] and not m["del"], f"move must not be encoded as ins/del: {m}"
PY
ck "fixture really encodes a move (moveFrom/moveTo, no ins/del)" 0 "$?"

# ... and the same file must FAIL a naive ins/del-only resolver — otherwise the
# fixture would not discriminate and the move-awareness could silently regress.
python3 - "$TMP/marked_move.docx" "$TMP/original.docx" <<'PY'
import re, sys, xml.etree.ElementTree as ET, zipfile
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
def dom(p): return ET.fromstring(zipfile.ZipFile(p).read("word/document.xml"))
def norm(s): return re.sub(r"\s+", " ", s).strip()

def naive_reject(root):
    """Knows only w:ins / w:del: emits every delText and every w:t outside w:ins.
    The moveTo run is not inside w:ins, so the moved paragraph comes back twice."""
    out, parents = [], {c: p for p in root.iter() for c in p}
    for el in root.iter():
        if el.tag not in (W + "t", W + "delText"):
            continue
        anc, cur = set(), el
        while cur in parents:
            cur = parents[cur]
            anc.add(cur.tag)
        if el.tag == W + "delText" or (W + "ins") not in anc:
            out.append(el.text or "")
    return norm("".join(out))

def plain(root): return norm("".join(e.text or "" for e in root.iter(W + "t")))

got, want = naive_reject(dom(sys.argv[1])), plain(dom(sys.argv[2]))
assert got != want, "naive resolver passed — fixture does not discriminate"
assert got.count("Bravo") == 2, f"expected the naive duplicate, got {got!r}"
PY
ck "naive ins/del-only resolver fails the same file (duplicate)" 0 "$?"

# --- 2) an ordinary edit passes ---------------------------------------------------
python3 "$V" --marked "$TMP/marked_edit.docx" --original "$TMP/original.docx" \
  --revised "$TMP/revised_edit.docx" --author "Submitting Author" --strict > /dev/null 2>&1
ck "ordinary ins/del edit passes the round trip" 0 "$?"

# --- 3) a dropped paragraph must FAIL ---------------------------------------------
python3 "$V" --marked "$TMP/marked_dropped.docx" --original "$TMP/original.docx" \
  --revised "$TMP/revised_edit.docx" --strict > /dev/null 2>&1
ck "dropped paragraph fails (--strict)" 1 "$?"

OUT="$(python3 "$V" --marked "$TMP/marked_dropped.docx" --original "$TMP/original.docx" \
  --revised "$TMP/revised_edit.docx" 2>&1)"
echo "$OUT" | grep -q MARKED_ACCEPT_MISMATCH
ck "dropped paragraph reports MARKED_ACCEPT_MISMATCH" 0 "$?"

ck "drift tolerated without --strict" 0 "$(
  python3 "$V" --marked "$TMP/marked_dropped.docx" --original "$TMP/original.docx" \
    --revised "$TMP/revised_edit.docx" > /dev/null 2>&1; echo $?)"

# --- 4) mixed revision authors ----------------------------------------------------
OUT="$(python3 "$V" --marked "$TMP/marked_author.docx" --original "$TMP/original.docx" \
  --revised "$TMP/revised_edit.docx" --author "Submitting Author" 2>&1)"
echo "$OUT" | grep -q MARKED_AUTHOR_MIXED
ck "revisions by a second author report MARKED_AUTHOR_MIXED" 0 "$?"

# the same file is clean when no author is asserted (the round trip still holds)
python3 "$V" --marked "$TMP/marked_author.docx" --original "$TMP/original.docx" \
  --revised "$TMP/revised_edit.docx" --strict > /dev/null 2>&1
ck "author check does not fire when --author is omitted" 0 "$?"

# --- 5) a clean copy is not a marked manuscript -------------------------------------
OUT="$(python3 "$V" --marked "$TMP/marked_clean.docx" --original "$TMP/original.docx" \
  --revised "$TMP/revised_edit.docx" 2>&1)"
echo "$OUT" | grep -q MARKED_NO_REVISIONS
ck "clean copy reports MARKED_NO_REVISIONS" 0 "$?"

# --- 6) a flattened table (identical text) ------------------------------------------
OUT="$(python3 "$V" --marked "$TMP/marked_tbl.docx" --original "$TMP/original_tbl.docx" \
  --revised "$TMP/revised_tbl.docx" 2>&1)"
echo "$OUT" | grep -q MARKED_TABLE_LOSS
ck "flattened table reports MARKED_TABLE_LOSS" 0 "$?"
echo "$OUT" | grep -q MARKED_ACCEPT_MISMATCH
ck "table loss is isolated (text round trip still holds)" 1 "$?"

# --- 7) a baseline that still carries tracked changes --------------------------------
OUT="$(python3 "$V" --marked "$TMP/marked_edit.docx" --original "$TMP/original_dirty.docx" \
  --revised "$TMP/revised_edit.docx" 2>&1)"
echo "$OUT" | grep -q MARKED_BASE_TRACKED
ck "baseline with live tracked changes reports MARKED_BASE_TRACKED" 0 "$?"

echo "----"
echo "test_marked_manuscript: $pass passed, $fail failed"
[ "$fail" -eq 0 ]
