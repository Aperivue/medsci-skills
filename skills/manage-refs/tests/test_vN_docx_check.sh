#!/usr/bin/env bash
# Regression tests for check_xref.py --vN-docx-md5 / --vN-md flags.
#
# Builds minimal synthetic docx files via zipfile (no pandoc/Word required).

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
SCRIPT="$REPO_ROOT/skills/manage-refs/scripts/check_xref.py"
TMP="$(mktemp -d -t vN_docx_xref.XXXXXX)"
trap 'rm -rf "$TMP"' EXIT

[[ -f "$SCRIPT" ]] || { echo "ENV-ERR: script missing" >&2; exit 2; }

fail=0
ran=0
assert_exit() {
    local label="$1" expected="$2" actual="$3"
    ran=$((ran + 1))
    if [[ "$expected" == "$actual" ]]; then
        printf '  PASS  %-50s exit=%s\n' "$label" "$actual"
    else
        printf '  FAIL  %-50s expected=%s actual=%s\n' "$label" "$expected" "$actual"
        fail=$((fail + 1))
    fi
}

# Helper: build a minimal docx with given body text.
build_docx() {
    local body_text="$1"
    local out="$2"
    python3 - "$body_text" "$out" <<'PY'
import sys, zipfile
body_text, out = sys.argv[1], sys.argv[2]
doc_xml = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
    '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
    '<w:body><w:p><w:r><w:t xml:space="preserve">' + body_text + '</w:t></w:r></w:p>'
    '</w:body></w:document>'
)
content_types = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="xml" ContentType="application/xml"/>'
    '<Override PartName="/word/document.xml" '
    'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
    '</Types>'
)
rels = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" '
    'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
    'Target="word/document.xml"/></Relationships>'
)
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    z.writestr("[Content_Types].xml", content_types)
    z.writestr("_rels/.rels", rels)
    z.writestr("word/document.xml", doc_xml)
PY
}

# Helper: build a minimal (deflated) docx whose <w:body> is the given raw XML, so a
# case can split one word across runs the way Word does.
build_docx_xml() {
    local body_xml="$1"
    local out="$2"
    python3 - "$body_xml" "$out" <<'PY'
import sys, zipfile
body_xml, out = sys.argv[1], sys.argv[2]
doc_xml = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
    '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
    '<w:body>' + body_xml + '</w:body></w:document>'
)
content_types = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="xml" ContentType="application/xml"/>'
    '<Override PartName="/word/document.xml" '
    'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
    '</Types>'
)
rels = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" '
    'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
    'Target="word/document.xml"/></Relationships>'
)
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    z.writestr("[Content_Types].xml", content_types)
    z.writestr("_rels/.rels", rels)
    z.writestr("word/document.xml", doc_xml)
PY
}

# --------------------------------------------------------------------------
# Setup: minimal manuscript markdown + docx
# --------------------------------------------------------------------------
VN_MD="$TMP/v1.md"
cat > "$VN_MD" <<'EOF'
# Manuscript

## Methods
The cohort included 100 patients.

## Figure Legends
**Figure 1.** Pipeline overview.
EOF
NEW_MD="$TMP/v2.md"
cat > "$NEW_MD" <<'EOF'
# Manuscript

## Methods
The cohort included 100 patients enrolled across three sites in this prospective study.

## Figure Legends
**Figure 1.** Pipeline overview.
EOF

VN_DOCX="$TMP/v1.docx"
NEW_DOCX_REGEN="$TMP/v2_regen.docx"
NEW_DOCX_COPY="$TMP/v2_copy.docx"
NEW_DOCX_STALE="$TMP/v2_stale.docx"

build_docx "The cohort included 100 patients. Figure 1 Pipeline overview." "$VN_DOCX"
# Regenerated docx: contains the new diff line verbatim.
build_docx "The cohort included 100 patients enrolled across three sites in this prospective study. Figure 1 Pipeline overview." "$NEW_DOCX_REGEN"
# "Copy" docx: byte-identical to v_N.
cp "$VN_DOCX" "$NEW_DOCX_COPY"
# Stale docx: different bytes than v_N but missing the new markdown line.
build_docx "Some text that differs from v_N but lacks the markdown diff." "$NEW_DOCX_STALE"

# --------------------------------------------------------------------------
# Case 1: regenerated docx contains markdown diff. PASS.
# --------------------------------------------------------------------------
python3 "$SCRIPT" --md "$NEW_MD" --docx "$NEW_DOCX_REGEN" \
    --vN-docx-md5 "$VN_DOCX" --vN-md "$VN_MD" \
    --out "$TMP/c1.json" --quiet
assert_exit "case 1: regenerated docx, diff propagated" 0 $?

# --------------------------------------------------------------------------
# Case 2: identical bytes. FAIL.
# --------------------------------------------------------------------------
python3 "$SCRIPT" --md "$NEW_MD" --docx "$NEW_DOCX_COPY" \
    --vN-docx-md5 "$VN_DOCX" --vN-md "$VN_MD" \
    --out "$TMP/c2.json" --quiet
assert_exit "case 2: identical bytes (FAIL)" 1 $?
python3 - "$TMP/c2.json" <<'PY' || fail=$((fail + 1))
import json, sys
with open(sys.argv[1]) as fh: rep = json.load(fh)
assert rep["vN_docx_check"]["identical_bytes"] is True, rep
PY

# --------------------------------------------------------------------------
# Case 3: different bytes but missing diff line. FAIL.
# --------------------------------------------------------------------------
python3 "$SCRIPT" --md "$NEW_MD" --docx "$NEW_DOCX_STALE" \
    --vN-docx-md5 "$VN_DOCX" --vN-md "$VN_MD" \
    --out "$TMP/c3.json" --quiet
assert_exit "case 3: different bytes, missing diff (FAIL)" 1 $?
python3 - "$TMP/c3.json" <<'PY' || fail=$((fail + 1))
import json, sys
with open(sys.argv[1]) as fh: rep = json.load(fh)
assert rep["vN_docx_check"]["identical_bytes"] is False, rep
assert rep["vN_docx_check"]["diff_line_misses"], rep
PY

# --------------------------------------------------------------------------
# Case 3b: Word split a word across runs ("si" + "tes", a proofing/format run
# boundary) and a tab sits between "Figure 1" and its caption. The line IS
# verbatim in the docx. Flattening every tag to a space read "si tes" and
# reported it missing. PASS.
# --------------------------------------------------------------------------
NEW_DOCX_SPLIT="$TMP/v2_split.docx"
build_docx_xml '<w:p><w:r><w:t xml:space="preserve">The cohort included 100 patients enrolled across three si</w:t></w:r><w:proofErr w:type="spellStart"/><w:r><w:rPr><w:b/></w:rPr><w:t>tes in this prospective study.</w:t></w:r></w:p><w:p><w:r><w:t>Figure 1</w:t></w:r><w:r><w:tab/><w:t>Pipeline overview.</w:t></w:r></w:p>' "$NEW_DOCX_SPLIT"
python3 "$SCRIPT" --md "$NEW_MD" --docx "$NEW_DOCX_SPLIT" \
    --vN-docx-md5 "$VN_DOCX" --vN-md "$VN_MD" \
    --out "$TMP/c3b.json" --quiet
assert_exit "case 3b: word split across runs is still verbatim" 0 $?
python3 - "$TMP/c3b.json" <<'PY' || fail=$((fail + 1))
import json, sys
with open(sys.argv[1]) as fh: rep = json.load(fh)
assert rep["vN_docx_check"]["diff_line_misses"] == [], rep
PY

# --------------------------------------------------------------------------
# Case 3c: the same two halves in SEPARATE paragraphs are not one line. Joining
# must stop at the paragraph end, or a line broken across paragraphs would be
# certified verbatim. FAIL.
# --------------------------------------------------------------------------
NEW_DOCX_PARA="$TMP/v2_para.docx"
build_docx_xml '<w:p><w:r><w:t>The cohort included 100 patients enrolled across three si</w:t></w:r></w:p><w:p><w:r><w:t>tes in this prospective study.</w:t></w:r></w:p>' "$NEW_DOCX_PARA"
python3 "$SCRIPT" --md "$NEW_MD" --docx "$NEW_DOCX_PARA" \
    --vN-docx-md5 "$VN_DOCX" --vN-md "$VN_MD" \
    --out "$TMP/c3c.json" --quiet
assert_exit "case 3c: halves in separate paragraphs (FAIL)" 1 $?

# --------------------------------------------------------------------------
# Case 4: --vN-docx-md5 without --docx. Should error (exit 2).
# --------------------------------------------------------------------------
python3 "$SCRIPT" --md "$NEW_MD" \
    --vN-docx-md5 "$VN_DOCX" --vN-md "$VN_MD" \
    --out "$TMP/c4.json" --quiet 2>/dev/null
assert_exit "case 4: --vN-docx-md5 without --docx" 2 $?

echo ""
echo "ran=$ran fail=$fail"
[[ $fail -eq 0 ]]
