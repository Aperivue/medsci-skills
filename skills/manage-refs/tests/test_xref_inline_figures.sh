#!/usr/bin/env bash
# Regression test: an embedded figure defines its own caption.
#
# /write-paper Phase 2 embeds every figure in Results as `![Figure N. Caption](path)`. pandoc
# renders that alt text as the figure's caption paragraph in the DOCX. `check_xref` read caption
# definitions only under legend headings (`## Figure Legends`, `## Figures`, ...), so a manuscript
# that followed write-paper's instructions literally was halted at the Phase 7.6a submission gate:
#
#     no --docx       -> MISSING_BODY for every figure, SUBMISSION BLOCKED
#     with the DOCX   -> MISSING_BODY with the float IN the DOCX, a blocker under every policy
#
# although the markdown defined exactly the caption the DOCX carried. The negative controls pin
# that recognising the embed did not loosen the gate: a figure missing from the DOCX, a caption
# that disagrees with the DOCX, and a cited figure defined nowhere all still block.
set -u

REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
X="$REPO_ROOT/skills/manage-refs/scripts/check_xref.py"
WORK="$(mktemp -d -t xref_inline_test.XXXXXX)"
trap 'rm -rf "$WORK"' EXIT

pass=0
fail=0
ck() {
  local label="$1" expected="$2" actual="$3"
  if [ "$expected" = "$actual" ]; then
    printf '  PASS  %-56s %s\n' "$label" "$actual"
    pass=$((pass + 1))
  else
    printf '  FAIL  %-56s expected=%s actual=%s\n' "$label" "$expected" "$actual"
    fail=$((fail + 1))
  fi
}

mk_docx() {  # mk_docx <path> <caption paragraph...>  (the text pandoc writes for each embed)
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

mk_md() {  # mk_md <path> <embed line...> : Results cite Figures 1 and 2, then the given embeds
  local path="$1"; shift
  {
    echo "## Results"; echo
    echo "Enrolment is shown in Figure 1 and discrimination in Figure 2."
    for line in "$@"; do echo; echo "$line"; done
  } > "$path"
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

# Exactly the form write-paper Phase 2 step 5 writes (both separators the checker accepts elsewhere).
FIG1='![Figure 1. Study flow diagram.](analysis/figures/flow.png){width=80%}'
FIG2='![Figure 2: ROC curve for the synthetic model.](analysis/figures/roc.png){width=80%}'
mk_md "$WORK/inline.md" "$FIG1" "$FIG2"
mk_docx "$WORK/full.docx" "Figure 1. Study flow diagram." "Figure 2: ROC curve for the synthetic model."

echo "==== write-paper's own embed form passes ===="
ck "inline embeds, no --docx: exit 0"                  0 "$(run inline.md)"
ck "  Figure 1 is OK"                                  OK "$(status_of inline.md Figure:1)"
ck "inline embeds + the DOCX they render to: exit 0"   0 "$(run inline.md full.docx)"
ck "  Figure 2 is OK"                                  OK "$(status_of inline.md Figure:2)"

if command -v pandoc >/dev/null 2>&1; then
  pandoc "$WORK/inline.md" -o "$WORK/pandoc.docx" 2>/dev/null
  ck "inline embeds + a real pandoc render: exit 0"    0 "$(run inline.md pandoc.docx)"
else
  echo "  NOTE  pandoc not installed; the real-render case ran on the synthetic DOCX only"
fi

echo "==== NEGATIVE CONTROLS: the gate still blocks what it should ===="
mk_docx "$WORK/partial.docx" "Figure 1. Study flow diagram."
ck "Figure 2 absent from the DOCX: exit 1"             1 "$(run inline.md partial.docx)"
ck "  Figure 2 is MISSING_DOCX"                        MISSING_DOCX "$(status_of inline.md Figure:2)"

mk_docx "$WORK/other.docx" "Figure 1. Study flow diagram." "Figure 2. Kaplan-Meier survival by treatment arm."
ck "embed caption disagrees with the DOCX: exit 1"     1 "$(run inline.md other.docx)"
ck "  Figure 2 is MISMATCH"                            MISMATCH "$(status_of inline.md Figure:2)"

mk_md "$WORK/one.md" "$FIG1" '![Graphical abstract](analysis/figures/abstract.png)'
ck "cited Figure 2 defined nowhere: exit 1"            1 "$(run one.md)"
ck "  Figure 2 is MISSING_BODY"                        MISSING_BODY "$(status_of one.md Figure:2)"

mk_md "$WORK/legend.md" "$FIG1" "$FIG2" "## Figure Legends" "**Figure 2.** Kaplan-Meier survival by treatment arm."
ck "a legend section still defines the caption: exit 1" 1 "$(run legend.md full.docx)"
ck "  the legend (not the embed) is compared: MISMATCH"  MISMATCH "$(status_of legend.md Figure:2)"

echo
echo "  passed=$pass failed=$fail"
[ "$fail" -eq 0 ] || { for f in inline one legend; do echo "--- $f"; cat "$WORK/$f.md.out"; done; exit 1; }
echo "OK: an embedded figure's caption is a body definition, and the gate still blocks real defects."
