#!/usr/bin/env bash
# Test scripts/check_asset_anonymization.py — the A2 asset-anonymization gate.
# Synthetic, PII-free fixtures: a figure script with a generic institution token,
# a docx with a (synthetic) author metadata, a --names-file name hit, and clean
# counterparts. Stdlib-only; does not require poppler (PDF paths are exercised
# only opportunistically).
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$HERE/../scripts/check_asset_anonymization.py"
PASS=0
FAIL=0
ok()  { echo "  PASS: $1"; PASS=$((PASS+1)); }
bad() { echo "  FAIL: $1"; FAIL=$((FAIL+1)); }

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

# --- fixtures ---
mkdir -p "$WORK/leaky/figures" "$WORK/clean/figures" "$WORK/pathleak"
mkdir -p "$WORK/custompath" "$WORK/relationshippath"

# figure script with an institution token (review-severity)
cat > "$WORK/leaky/figures/flow.R" <<'EOF'
# CONSORT flow diagram
label <- "Recruited at General Hospital, 2020-2024"
plot(1:10)
EOF
# clean figure script
cat > "$WORK/clean/figures/plot.py" <<'EOF'
import matplotlib.pyplot as plt
plt.plot([1, 2, 3]); plt.savefig("fig1.png")
EOF
# figure script with a name that only --names-file knows (leak-severity)
cat > "$WORK/leaky/figures/panel.py" <<'EOF'
caption = "Data from Mercy Riverside Clinic cohort"
EOF
cat > "$WORK/names.txt" <<'EOF'
Mercy Riverside Clinic
EOF

# build a docx with synthetic author metadata (leak) and a clean one (tool author)
python3 - "$WORK" <<'PY'
import sys, zipfile, os
work = sys.argv[1]
def make_docx(path, creator, body="<w:document/>"):
    core = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
        'xmlns:dc="http://purl.org/dc/elements/1.1/">'
        f'<dc:creator>{creator}</dc:creator>'
        f'<cp:lastModifiedBy>{creator}</cp:lastModifiedBy>'
        '</cp:coreProperties>'
    )
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("docProps/core.xml", core)
        z.writestr("word/document.xml", body)
make_docx(os.path.join(work, "leaky", "manuscript.docx"), "Alex P. Investigator")
make_docx(os.path.join(work, "clean", "manuscript.docx"), "Microsoft Office User")
# clean metadata but an absolute home path leaked into a pic descr (pandoc pattern)
make_docx(
    os.path.join(work, "pathleak", "supplement.docx"),
    "Microsoft Office User",
    body='<w:document><pic:pic><pic:nvPicPr>'
         '<pic:cNvPr id="1" name="Picture" '
         'descr="/Users/testuser/proj/figures/funnel.png"/>'
         '</pic:nvPicPr></pic:pic></w:document>',
)
# Build-input properties and external relationships live outside word/*.xml.
make_docx(os.path.join(work, "custompath", "manuscript.docx"), "Pandoc")
with zipfile.ZipFile(os.path.join(work, "custompath", "manuscript.docx"), "a") as z:
    z.writestr("docProps/custom.xml", '<Properties><property name="csl">'
               '<value>/Users/testuser/styles/journal.csl</value></property></Properties>')
make_docx(os.path.join(work, "relationshippath", "manuscript.docx"), "Pandoc")
with zipfile.ZipFile(os.path.join(work, "relationshippath", "manuscript.docx"), "a") as z:
    z.writestr("word/_rels/document.xml.rels", '<Relationships><Relationship '
               'Target="C:\\Users\\testuser\\figures\\plot.png"/></Relationships>')
PY

run() { python3 "$SCRIPT" "$@" 2>/dev/null; }

# 1. leaky dir (no names file): docx author leak -> exit 1
run --dir "$WORK/leaky" --quiet
[ $? -eq 1 ] && ok "leaky dir fails (docx author leak)" || bad "leaky dir should fail"

# 2. JSON reports the docx author + institution token finding types
out="$(run --dir "$WORK/leaky" --names-file "$WORK/names.txt" --out "$WORK/r.json"; cat "$WORK/r.json")"
echo "$out" | python3 -c "
import json,sys
d=json.load(open('$WORK/r.json'))
types={f['type'] for f in d['findings']}
need={'docx_metadata_author','figure_script_institution','figure_script_name'}
sys.exit(0 if need <= types and d['submission_safe'] is False else 1)
" && ok "JSON: docx author + institution + name-file findings" || bad "JSON findings incomplete"

# 3. name-file hit is a 'leak'
run --dir "$WORK/leaky" --names-file "$WORK/names.txt" --out "$WORK/r2.json" --quiet
python3 -c "
import json,sys
d=json.load(open('$WORK/r2.json'))
sys.exit(0 if d['summary']['leak'] >= 2 else 1)  # docx author + name hit
" && ok "name-file hit counts as leak" || bad "name-file hit should be leak"

# 4. clean dir -> exit 0
run --dir "$WORK/clean" --quiet
[ $? -eq 0 ] && ok "clean dir passes (tool author, no tokens)" || bad "clean dir should pass"

# 5. review-only dir under --strict fails; default passes
mkdir -p "$WORK/reviewonly/figures"
cp "$WORK/leaky/figures/flow.R" "$WORK/reviewonly/figures/flow.R"
run --dir "$WORK/reviewonly" --quiet
[ $? -eq 0 ] && ok "review-only passes by default" || bad "review-only should pass by default"
run --dir "$WORK/reviewonly" --strict --quiet
[ $? -eq 1 ] && ok "review-only fails under --strict" || bad "review-only should fail under --strict"

# 6. docx with an absolute home path in pic descr -> leak (even with tool author)
run --dir "$WORK/pathleak" --quiet
[ $? -eq 1 ] && ok "docx embedded abs-path fails (pic descr leak)" || bad "abs-path docx should fail"
run --dir "$WORK/pathleak" --out "$WORK/r3.json" --quiet
python3 -c "
import json,sys
d=json.load(open('$WORK/r3.json'))
types={f['type'] for f in d['findings']}
sys.exit(0 if 'docx_embedded_abs_path' in types and d['submission_safe'] is False else 1)
" && ok "JSON: docx_embedded_abs_path finding present" || bad "abs-path finding missing"

for case in custompath relationshippath; do
  run --dir "$WORK/$case" --out "$WORK/$case.json" --quiet
  [ $? -eq 1 ] && ok "$case fails with clean author metadata" || bad "$case leak was missed"
  python3 - "$WORK/$case.json" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
assert not d["submission_safe"]
assert any(f["type"] == "docx_embedded_abs_path" for f in d["findings"])
PY
  [ $? -eq 0 ] && ok "$case reports the path leak" || bad "$case finding missing"
done

# 8. tracked-change / comment authors: a real-looking name fails even when core.xml is
#    clean; a neutral "Author" does not. Core metadata alone never showed these.
python3 - "$WORK" <<'PY'
import os, sys, zipfile
work = sys.argv[1]
W = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
def marked(path, author):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    core = ('<cp:coreProperties xmlns:cp="c" xmlns:dc="d"><dc:creator>Pandoc</dc:creator>'
            '</cp:coreProperties>')
    doc = (f'<w:document {W}><w:body><w:p><w:ins w:id="1" w:author="{author}" '
           f'w:date="2026-01-01T00:00:00Z"><w:r><w:t>added</w:t></w:r></w:ins></w:p></w:body></w:document>')
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("docProps/core.xml", core)
        z.writestr("word/document.xml", doc)
marked(os.path.join(work, "revleak", "marked.docx"), "Casey Q. Reviewer")
marked(os.path.join(work, "revneutral", "marked.docx"), "Author")
PY
run --dir "$WORK/revleak" --out "$WORK/revleak.json" --quiet
[ $? -eq 1 ] && ok "tracked-change author name fails (core.xml clean)" || bad "revision author leak was missed"
python3 -c "
import json,sys; d=json.load(open('$WORK/revleak.json'))
sys.exit(0 if any(f['type']=='docx_revision_author' for f in d['findings']) else 1)
" && ok "JSON: docx_revision_author finding present" || bad "revision author finding missing"
run --dir "$WORK/revneutral" --quiet
[ $? -eq 0 ] && ok "neutral tracked-change author passes" || bad "neutral author should pass"

echo ""
echo "test_asset_anonymization: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]
