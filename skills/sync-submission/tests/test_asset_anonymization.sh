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
def make_docx(path, creator, body='<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"/>'):
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
    body='<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
         'xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:pic><pic:nvPicPr>'
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

# 9. Person-bearing places beyond core.xml dc:creator and the body parts, read by XML
#    namespace + local name. Every positive case plants a fictional value in one place
#    and states the finding it must produce: type, severity, the FULL value and the
#    part/attribute. Negative cases carry tool defaults, placeholders, structural
#    bookmarks and look-alike text, and must produce no finding even under --strict.
sec9="$(python3 - "$WORK" "$SCRIPT" <<'PY'
import json, os, subprocess, sys, warnings, zipfile
warnings.filterwarnings("ignore", message="Duplicate name")  # duplicate_entry is deliberate
work, script = sys.argv[1], sys.argv[2]
W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W15 = "http://schemas.microsoft.com/office/word/2012/wordml"
CP = "http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
DC = "http://purl.org/dc/elements/1.1/"
EP = "http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"
def core(inner):
    return f'<cp:coreProperties xmlns:cp="{CP}" xmlns:dc="{DC}">{inner}</cp:coreProperties>'
def app(inner):
    return f'<Properties xmlns="{EP}">{inner}</Properties>'
def doc(inner):
    return f'<w:document xmlns:w="{W}"><w:body><w:p>{inner}</w:p></w:body></w:document>'
def ins(author):
    return f'<w:ins w:id="1" w:author="{author}"><w:r><w:t>a</w:t></w:r></w:ins>'
ZITEM = "ADDIN ZOTERO_ITEM CSL_CITATION "
def field(*pieces, tag="instrText"):
    """A complex field as Word writes it: begin, instruction runs, separate, result, end."""
    return ('<w:r><w:fldChar w:fldCharType="begin"/></w:r>'
            + "".join(f'<w:r><w:{tag} xml:space="preserve">{p}</w:{tag}></w:r>' for p in pieces)
            + '<w:r><w:fldChar w:fldCharType="separate"/></w:r><w:r><w:t>(1)</w:t></w:r>'
            + '<w:r><w:fldChar w:fldCharType="end"/></w:r>')
def custom(inner):
    return ('<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/custom-properties" '
            f'xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">\n  {inner}</Properties>')
def prop(pid, name, value):
    value = value.replace("&", "&amp;").replace("<", "&lt;")
    return (f'<property fmtid="{{D5CDD505-2E9C-101B-9397-08002B2CF9AE}}" pid="{pid}" name="{name}">\n'
            f'    <vt:lpwstr>{value}</vt:lpwstr>\n  </property>\n  ')
def people(provider, userid, author="Author"):
    return (f'<w15:people xmlns:w15="{W15}"><w15:person w15:author="{author}"><w15:presenceInfo '
            f'w15:providerId="{provider}" w15:userId="{userid}"/></w15:person></w15:people>')
BASE = [("docProps/core.xml", core("<dc:creator>Pandoc</dc:creator>")),
        ("word/document.xml", doc(ins("Author")))]

def make(case, parts, replace_base=True):
    d = os.path.join(work, "places", case)
    os.makedirs(d, exist_ok=True)
    names = {n for n, _ in parts}
    entries = ([e for e in BASE if e[0] not in names] if replace_base else list(BASE)) + list(parts)
    with zipfile.ZipFile(os.path.join(d, "marked.docx"), "w") as z:
        for n, v in entries:
            z.writestr(n, v if isinstance(v, bytes) else v.encode("utf-8"))
    return d

def scan(d, strict):
    # A fresh report path per run, removed first: a run that dies cannot hand back the
    # previous run's report.
    out = os.path.join(d, "report_strict.json" if strict else "report_default.json")
    if os.path.exists(out):
        os.remove(out)
    args = [sys.executable, script, "--dir", d, "--out", out, "--quiet"] + (["--strict"] if strict else [])
    proc = subprocess.run(args, capture_output=True, text=True)
    if not os.path.exists(out):
        print(f"      no report written; stderr: {proc.stderr.strip()[:300]}")
        return proc.returncode, {"findings": []}
    return proc.returncode, json.load(open(out))

def matches(f, ftype, sev, value, where):
    return (f["type"] == ftype and f["severity"] == sev
            and (not value or f"'{value}'" in f["detail"])
            and all(w in f["detail"] for w in where))

def exact(rep, expect):
    """Each expected finding appears exactly once and nothing else is reported."""
    if len(rep["findings"]) != len(expect):
        return False
    return all(sum(matches(f, *e) for f in rep["findings"]) == 1 for e in expect)

T = "Test Author"
POSITIVE = [
    # (case, parts, [(type, severity, full value, [places])], expected default exit)
    ("core_lastmod", [("docProps/core.xml", core(f"<dc:creator>Pandoc</dc:creator><cp:lastModifiedBy>{T}</cp:lastModifiedBy>"))],
     [("docx_metadata_author", "leak", T, ["docProps/core.xml cp:lastModifiedBy"])], 1),
    ("core_cdata", [("docProps/core.xml", core(f"<dc:creator><![CDATA[{T}]]></dc:creator>"))],
     [("docx_metadata_author", "leak", T, ["docProps/core.xml dc:creator"])], 1),
    ("added_token_is_exact", [("docProps/core.xml", core(f"<cp:lastModifiedBy>medsci-skills / {T}</cp:lastModifiedBy>"))],
     [("docx_metadata_author", "leak", f"medsci-skills / {T}", ["docProps/core.xml cp:lastModifiedBy"])], 1),
    ("app_manager", [("docProps/app.xml", app(f'<Manager xml:space="preserve">{T}</Manager>'))],
     [("docx_metadata_author", "leak", T, ["docProps/app.xml Manager"])], 1),
    ("styles_single_quoted", [("word/styles.xml",
        f"<w:styles xmlns:w='{W}'><w:style w:styleId='N'><w:rPr><w:b/>"
        f"<w:rPrChange w:id='9' w:author = '{T}'><w:rPr/></w:rPrChange></w:rPr></w:style></w:styles>")],
     [("docx_revision_author", "leak", T, ["word/styles.xml w:author"])], 1),
    ("numbering_other_prefix", [("word/numbering.xml",
        f'<x:numbering xmlns:x="{W}"><x:abstractNum x:abstractNumId="0"><x:lvl x:ilvl="0"><x:pPr>'
        f'<x:pPrChange x:id="3" x:author="{T}"><x:pPr/></x:pPrChange></x:pPr></x:lvl></x:abstractNum></x:numbering>')],
     [("docx_revision_author", "leak", T, ["word/numbering.xml w:author"])], 1),
    ("glossary", [("word/glossary/document.xml",
        f'<w:glossaryDocument xmlns:w="{W}"><w:docParts><w:docPart><w:docPartBody><w:p>{ins(T)}'
        f'</w:p></w:docPartBody></w:docPart></w:docParts></w:glossaryDocument>')],
     [("docx_revision_author", "leak", T, ["word/glossary/document.xml w:author"])], 1),
    ("utf16_part", [("word/comments.xml",
        (f'<?xml version="1.0" encoding="UTF-16"?><w:comments xmlns:w="{W}">'
         f'<w:comment w:id="0" w:author="{T}"><w:p/></w:comment></w:comments>').encode("utf-16"))],
     [("docx_revision_author", "leak", T, ["word/comments.xml w:author"])], 1),
    ("uppercase_extension", [("word/revisions.XML", doc(ins(T)))],
     [("docx_revision_author", "leak", T, ["word/revisions.XML w:author"])], 1),
    ("entity_in_name", [("word/document.xml", doc(ins("Test &amp; Author")))],
     [("docx_revision_author", "leak", "Test & Author", ["word/document.xml w:author"])], 1),
    ("two_parts_one_name", [("word/document.xml", doc(ins(T))),
        ("word/footnotes.xml", f'<w:footnotes xmlns:w="{W}"><w:footnote w:id="1"><w:p>{ins(T)}</w:p></w:footnote></w:footnotes>')],
     [("docx_revision_author", "leak", T, ["word/document.xml w:author", "word/footnotes.xml w:author"])], 1),
    ("people_userid_ad", [("word/people.xml", people("AD", "S::test.author@example.org::00000000-0000-0000-0000-000000000000"))],
     [("docx_revision_author", "leak", "S::test.author@example.org::00000000-0000-0000-0000-000000000000",
       ["word/people.xml w15:userId", "providerId=AD"])], 1),
    ("people_neutral_userid_under_ad", [("word/people.xml", people("AD", "Author"))],
     [("docx_revision_author", "leak", "Author", ["word/people.xml w15:userId", "providerId=AD"])], 1),
    ("people_person_author", [("word/people.xml", people("None", "Author", author=T))],
     [("docx_revision_author", "leak", T, ["word/people.xml w15:author"])], 1),
    # Placeholder matching is exact on the whole value: a value that merely starts with
    # "Author" or a tool name is a person.
    ("manager_placeholder_prefix", [("docProps/app.xml", app(f"<Manager>Author ({T})</Manager>"))],
     [("docx_metadata_author", "leak", f"Author ({T})", ["docProps/app.xml Manager"])], 1),
    ("creator_tool_prefix", [("docProps/core.xml", core(f"<dc:creator>Pandoc {T}</dc:creator>"))],
     [("docx_metadata_author", "leak", f"Pandoc {T}", ["docProps/core.xml dc:creator"])], 1),
    ("people_none_placeholder_prefix", [("word/people.xml", people("None", "author.smith@example.org"))],
     [("docx_revision_author", "leak", "author.smith@example.org", ["word/people.xml w15:userId", "providerId=None"])], 1),
    # Under providerId "None" a real display name is still reported.
    ("people_none_real_name", [("word/people.xml", people("None", T))],
     [("docx_revision_author", "leak", T, ["word/people.xml w15:userId", "providerId=None"])], 1),
    # providerId is compared exactly, as Word writes it: "NONE" is not "None".
    ("people_provider_case", [("word/people.xml", people("NONE", "Author"))],
     [("docx_revision_author", "leak", "Author", ["word/people.xml w15:userId", "providerId=NONE"])], 1),
    # ISO/IEC 29500 Strict namespaces.
    ("strict_namespaces", [("docProps/app.xml", f'<Properties xmlns="http://purl.oclc.org/ooxml/officeDocument/extendedProperties"><Manager>{T}</Manager></Properties>'),
        ("word/document.xml", f'<w:document xmlns:w="http://purl.oclc.org/ooxml/wordprocessingml/main"><w:body><w:p>{ins(T)}</w:p></w:body></w:document>')],
     [("docx_metadata_author", "leak", T, ["docProps/app.xml Manager"]),
      ("docx_revision_author", "leak", T, ["word/document.xml w:author"])], 1),
    # A property value split across child elements is read whole.
    ("manager_child_element", [("docProps/app.xml", app(f'<Manager><x:v xmlns:x="urn:x">{T}</x:v></Manager>'))],
     [("docx_metadata_author", "leak", T, ["docProps/app.xml Manager"])], 1),
    # The finding names the entry as it is stored in the ZIP.
    ("uppercase_property_part", [("DOCPROPS/APP.XML", app(f"<Manager>{T}</Manager>"))],
     [("docx_metadata_author", "leak", T, ["DOCPROPS/APP.XML Manager"])], 1),
    # A word/ part with another extension that [Content_Types].xml declares as XML.
    ("content_type_declared_part", [("[Content_Types].xml",
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Override PartName="/word/comments.wml" '
        'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.comments+xml"/></Types>'),
        ("word/comments.wml", f'<w:comments xmlns:w="{W}"><w:comment w:id="0" w:author="{T}"><w:p/></w:comment></w:comments>')],
     [("docx_revision_author", "leak", T, ["word/comments.wml w:author"])], 1),
    # Two ZIP entries with one name: both are read, and the duplication is reported.
    ("duplicate_entry", [("word/styles.xml", f'<w:styles xmlns:w="{W}"><w:style><w:rPr><w:rPrChange w:author="{T}"/></w:rPr></w:style></w:styles>'),
        ("word/styles.xml", f'<w:styles xmlns:w="{W}"><w:style><w:rPr><w:rPrChange w:author="Author"/></w:rPr></w:style></w:styles>')],
     [("docx_revision_author", "leak", T, ["word/styles.xml w:author"]),
      ("docx_part_unreadable", "review", "", ["word/styles.xml", "duplicate ZIP entry"])], 1),
    # A part truncated after a complete start tag still yields that tag's author.
    ("truncated_after_start_tag", [("word/comments.xml", f'<w:comments xmlns:w="{W}"><w:comment w:id="0" w:author="{T}">')],
     [("docx_revision_author", "leak", T, ["word/comments.xml w:author"]),
      ("docx_part_unreadable", "review", "", ["word/comments.xml"])], 1),
    # An unreadable part alone is review: default exit 0, --strict exit 1.
    ("unreadable_only", [("word/comments.xml", f'<w:comments xmlns:w="{W}"><w:comment w:id="0">')],
     [("docx_part_unreadable", "review", "", ["word/comments.xml"])], 0),
    # A part that cannot be read is reported, and names found in other parts survive it,
    # whichever side of the broken part they are on.
    ("corrupt_next_to_name", [("docProps/app.xml", app("<Manager>unclosed")),
        ("docProps/core.xml", core(f"<dc:creator>{T}</dc:creator>")),
        ("word/charts/chart1.xml", "<c:chart xmlns:c='urn:c'><c:x></c:chart>"),
        ("word/document.xml", doc(ins(T)))],
     [("docx_metadata_author", "leak", T, ["docProps/core.xml dc:creator"]),
      ("docx_revision_author", "leak", T, ["word/document.xml w:author"]),
      ("docx_part_unreadable", "review", "", ["docProps/app.xml"]),
      ("docx_part_unreadable", "review", "", ["word/charts/chart1.xml"])], 1),
    # Zotero citation data carries the numeric id of the synced library: review. Word splits a
    # field instruction over runs, so the pieces of one field are joined; a tracked-deleted
    # field counts; the same id in two parts is one finding naming both.
    ("zotero_user_id_split_runs", [("word/document.xml", doc(ins("Author")
        + field(ZITEM + '{"citationItems":[{"id":7,"uris":["http://zotero.org/us', 'ers/1234567/items/ABCD2345"]}]}'))),
        ("word/footnotes.xml", f'<w:footnotes xmlns:w="{W}"><w:footnote w:id="1"><w:p><w:del w:id="5" w:author="Author">'
            + field(ZITEM + '{"citationItems":[{"uris":["http:\\/\\/zotero.org\\/users\\/1234567\\/items\\/EFGH2345"]}]}', tag="delInstrText")
            + '</w:del></w:p></w:footnote></w:footnotes>')],
     [("docx_reference_manager_id", "review", "user 1234567", ["word/document.xml field code", "word/footnotes.xml field code"])], 0),
    # A group library, an older "uri" key, a simple field and a /-escaped slash.
    ("zotero_group_id_simple_field", [("word/document.xml", doc(ins("Author")
        + '<w:fldSimple w:instr="' + (ZITEM + '{"citationItems":[{"uri":["http:\\u002f\\u002fzotero.org\\u002fgroups\\u002f7654321\\u002fitems\\u002fABCD2345"]}]}').replace('"', "&quot;")
        + '"><w:r><w:t>(1)</w:t></w:r></w:fldSimple>'))],
     [("docx_reference_manager_id", "review", "group 7654321", ["word/document.xml field code"])], 0),
    # Only the uris of the citation name the library of the document: a Zotero link in the
    # URL field of the cited item (another library) is not reported, the uris id is.
    ("zotero_uris_not_item_url", [("word/document.xml", doc(ins("Author")
        + field(ZITEM + '{"citationItems":[{"uris":["http://zotero.org/users/1234567/items/ABCD2345"],'
                        '"itemData":{"URL":"https://www.zotero.org/users/2222222/items/ZZZZ2345"}}]}')))],
     [("docx_reference_manager_id", "review", "user 1234567", ["word/document.xml field code"])], 0),
    # Bookmark mode: the data of one citation in numbered ZOTERO_BREF chunks, joined by number
    # whatever their order and layout in the file; other properties are not citation data.
    ("zotero_bookmark_mode", [("docProps/custom.xml", custom(
        prop(3, "ZOTERO_BREF_aBcD_2", '34567/items/ABCD2345"]}]}')
        + prop(4, "ProjectURL", '{"uris":["http://zotero.org/users/3333333/items/ABCD2345"]}')
        + prop(5, "ZOTERO_BREF_eFgH_1", 'ZOTERO_ITEM CSL_CITATION {"citationItems":[{"uri":"https://www.zotero.org/groups/76')
        + prop(2, "ZOTERO_BREF_aBcD_1", 'ZOTERO_ITEM CSL_CITATION {"citationItems":[{"uris":["http://zotero.org/users/12')
        + prop(6, "ZOTERO_BREF_eFgH_2", '54321/items/ABCD2345"}]}')
        # a citation with chunk 2 missing cannot be rebuilt, so no id is made up from 1 + 3
        + prop(7, "ZOTERO_BREF_iJkL_1", 'ZOTERO_ITEM CSL_CITATION {"citationItems":[{"uris":["http://zotero.org/users/31')
        + prop(8, "ZOTERO_BREF_iJkL_3", '31313/items/ABCD2345"]}]}')))],
     [("docx_reference_manager_id", "review", "user 1234567", ["docProps/custom.xml custom property"]),
      ("docx_reference_manager_id", "review", "group 7654321", ["docProps/custom.xml custom property"])], 0),
    # A citation field nested in the result of another field keeps its own code; an edit
    # tracked inside a code is read as the current text and the deleted text, not as both.
    ("zotero_nested_and_edited", [("word/document.xml", doc(ins("Author")
        + '<w:r><w:fldChar w:fldCharType="begin"/></w:r><w:r><w:instrText>IF 1 = 1 </w:instrText></w:r>'
        + field(ZITEM + '{"citationItems":[{"uris":["http://zotero.org/users/1234567/items/ABCD2345"]}]}')
        + '<w:r><w:fldChar w:fldCharType="end"/></w:r>'
        + '<w:r><w:fldChar w:fldCharType="begin"/></w:r>'
        + '<w:r><w:instrText>' + ZITEM + '{"citationItems":[{"uris":["http://zotero.org/users/20</w:instrText></w:r>'
        + '<w:r><w:delInstrText>99</w:delInstrText></w:r>'
        + '<w:r><w:instrText>20202/items/ABCD2345"]}]}</w:instrText></w:r>'
        + '<w:r><w:fldChar w:fldCharType="end"/></w:r>'))],
     [("docx_reference_manager_id", "review", "user 1234567", ["word/document.xml field code"]),
      ("docx_reference_manager_id", "review", "user 2020202", ["word/document.xml field code"])], 0),
    # A custom.xml that cannot be parsed is reported, by name, as not checked.
    ("custom_xml_unreadable", [("docProps/custom.xml", '<Properties xmlns="urn:x"><property name="ZOTERO_BREF_a_1">')],
     [("docx_part_unreadable", "review", "", ["docProps/custom.xml"])], 0),
    # Company is an organisation, not a person: review, so default exit 0 and --strict exit 1.
    ("company", [("docProps/app.xml", app("<Company>Example General Hospital</Company>"))],
     [("docx_metadata_company", "review", "Example General Hospital", ["docProps/app.xml Company"])], 0),
    ("company_not_person_tool", [("docProps/app.xml", app("<Company>Google</Company>"))],
     [("docx_metadata_company", "review", "Google", ["docProps/app.xml Company"])], 0),
]
NEGATIVE = [
    ("neutral", [
        ("docProps/core.xml", core("<dc:creator>python-docx</dc:creator><cp:lastModifiedBy>Anonymous</cp:lastModifiedBy>")),
        ("docProps/app.xml", app('<Manager></Manager><Company>&#77;icrosoft</Company>'
                                 '<v:Company xmlns:v="urn:other">Series 1</v:Company>')),
        ("word/document.xml", doc(
            "".join(f'<w:bookmarkStart w:id="{i}" w:name="{n}"/><w:bookmarkEnd w:id="{i}"/>'
                    for i, n in enumerate(("_GoBack", "_Toc123456", "_Ref98765", "_Hlk4242", "ref-smith2020")))
            + ins("Author")
            + '<w:r><w:t>w:author="Figure 2" and w15:userId="Figure 3"</w:t></w:r>'
            + '<!-- w:author="Figure 4" -->'
            + '<o:note xmlns:o="urn:other" o:author="Figure 5" o:userId="Figure 6"/>')),
        ("word/styles.xml", f'<w:styles xmlns:w="{W}"><w:style w:styleId="N"><w:rPr>'
                            f'<w:rPrChange w:id="8" w:author="Author"><w:rPr/></w:rPrChange></w:rPr></w:style></w:styles>'),
        ("word/people.xml", people("None", "Author")),
        # w15 person/presenceInfo attributes count only in word/people.xml.
        ("word/commentsExtended.xml", f'<w15:commentsEx xmlns:w15="{W15}"><w15:commentEx w15:userId="chart-42"/>'
            f'<w15:person w15:author="Figure 7"><w15:presenceInfo w15:providerId="AD" w15:userId="chart-43"/>'
            f'</w15:person></w15:commentsEx>'),
    ]),
    ("other_tool_values", [("docProps/core.xml",
        core("<dc:creator>python-pptx</dc:creator><cp:lastModifiedBy>LibreOffice/7.6</cp:lastModifiedBy>"))]),
    # Not the id of a synced library: a local (never synced) library; a full Zotero item URI in
    # the field of another reference manager, in a hyperlink field or in body text; pieces of
    # two separate fields that would only form an id if joined; a look-alike host; a
    # library URL that is not an item; a Zotero field with no uris.
    ("zotero_local_and_lookalikes", [("word/document.xml", doc(ins("Author")
        + field(ZITEM + '{"citationItems":[{"uris":["http://zotero.org/users/local/AbCd1234/items/ABCD2345"]}]}')
        + field('ADDIN EN.CITE {"uris":["http://zotero.org/users/4444444/items/ABCD2345"]}')
        + field('HYPERLINK "http://zotero.org/users/5555555/items/ABCD2345"')
        + field(ZITEM + '{"citationItems":[{"uris":["http://zotero.org/users/66')
        + field('66666/items/ABCD2345"]}]}')
        + field(ZITEM + '{"citationItems":[{"uris":["http://notzotero.org/users/7777777/items/ABCD2345",'
                        '"http://zotero.org/users/8888888/settings"]}]}')
        + field('ADDIN ZOTERO_BIBL {"uncited":[],"custom":[]} CSL_BIBLIOGRAPHY')
        + field('ADDIN EN.CITE {"title":"ZOTERO_ITEM","citationItems":[{"uris":["http://zotero.org/users/1010101/items/ABCD2345"]}]}')
        + field(ZITEM + '{"citationItems":[{"itemData":{"uris":["http://zotero.org/users/1212121/items/ABCD2345"]},'
                        '"uris":["https://example.org/zotero.org/users/1313131/items/ABCD2345","http://zotero.org/users/1414141/items/"]}]}')
        + '<w:r><w:t>{"uris":["http://zotero.org/users/9999999/items/ABCD2345"]}</w:t></w:r>'))]),
    ("company_neutral_values", [("docProps/app.xml", app("<Company>Anonymous</Company><Company> python-docx </Company>"))]),
    ("templatedefault", [("docProps/core.xml",
        core("<dc:creator>medsci-skills</dc:creator><cp:lastModifiedBy>medsci-skills</cp:lastModifiedBy>"))]),
]

for case, parts, expect, rc_default in POSITIVE:
    d = make(case, parts)
    for strict, want_rc in ((False, rc_default), (True, 1)):
        mode = "--strict" if strict else "default"
        rc, rep = scan(d, strict=strict)
        print(("OK" if rc == want_rc else "BAD") + f": {case}: {mode} exit {rc} (want {want_rc})")
        good = exact(rep, expect)
        print(("OK" if good else "BAD") + f": {case}: {mode} report holds exactly "
              + "; ".join(f"{sev} {ftype} '{value}' at {', '.join(where)}" for ftype, sev, value, where in expect))
        if not good:
            for f in rep["findings"]:
                print("      got:", f)
for case, parts in NEGATIVE:
    d = make(case, parts)
    rc, rep = scan(d, strict=True)
    good = rc == 0 and not rep["findings"]
    print(("OK" if good else "BAD") + f": {case}: tool/placeholder/look-alike values give no finding under --strict")
    if not good:
        for f in rep["findings"]:
            print("      got:", f)
PY
)"
sec9_rc=$?
while IFS= read -r line; do
  case "$line" in
    OK:*)  ok "${line#OK: }" ;;
    BAD:*) bad "${line#BAD: }" ;;
    *)     [ -n "$line" ] && echo "$line" ;;
  esac
done <<< "$sec9"
[ "$sec9_rc" -eq 0 ] && ok "section 9 harness ran to the end" || bad "section 9 harness crashed (exit $sec9_rc)"

echo ""
echo "test_asset_anonymization: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]
