#!/usr/bin/env bash
# Regression test: a plural float mention is a citation.
#
# `check_xref` recognised only the singular "Figure 1". The plural "s" breaks its `\s+`, so
# "Figures 1 and 2" — the way people actually write it — matched NOTHING. The consequence was not a
# missed note, it was a disabled gate: a float cited only that way scored UNCITED instead of
# MISSING_DOCX, and UNCITED is not in `blocking_statuses`. Two manuscripts identical in meaning got
# opposite verdicts:
#
#     "Figures 1 and 2"        -> exit 0, submission_safe: true   <- Figure 2 absent from the DOCX
#     "Figure 1 and Figure 2"  -> exit 1, SUBMISSION BLOCKED
#
# So ordinary English turned the submission blocker off, while the repetitive form this tool's own
# examples happen to use kept it on. The invariant this test pins is that equivalence: the same
# package must get the same verdict however the citation is phrased.
set -u

REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
X="$REPO_ROOT/skills/manage-refs/scripts/check_xref.py"
WORK="$(mktemp -d -t xref_plural_test.XXXXXX)"
trap 'rm -rf "$WORK"' EXIT

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

# A DOCX containing ONLY Figure 1's caption, so Figure 2 is genuinely absent from the rendered file.
mk_docx() {  # mk_docx <path> <caption text...>
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

mk_md() {  # mk_md <path> <citation sentence> [extra legend lines...]
  local path="$1" cite="$2"; shift 2
  {
    echo "## Results"; echo
    echo "$cite"; echo
    echo "## Figure Legends"; echo
    echo "**Figure 1.** Study flow diagram."; echo
    echo "**Figure 2.** Kaplan-Meier survival curves."
    for extra in "$@"; do echo; echo "$extra"; done
  } > "$path"
}

run() {  # run <md> <docx> -> exit code; JSON at $WORK/<md>.json
  python3 "$X" --md "$WORK/$1" --docx "$WORK/$2" --strict --out "$WORK/$1.json" \
    > "$WORK/$1.out" 2>&1
  echo $?
}
safe() { python3 -c "import json;print(json.load(open('$WORK/$1.json'))['submission_safe'])"; }
status_of() {  # status_of <md> <label>   e.g. status_of plural.md Figure:2
  python3 -c "
import json, sys
d = json.load(open(sys.argv[1]))
for f in d['findings']:
    if f['label'] == sys.argv[2]:
        print(f['status']); break
else:
    print('ABSENT')" "$WORK/$1.json" "$2"
}

mk_docx "$WORK/partial.docx" "Figure 1. Study flow diagram."
mk_docx "$WORK/full.docx" "Figure 1. Study flow diagram." "Figure 2. Kaplan-Meier survival curves."

mk_md "$WORK/plural.md"     "As shown in Figures 1 and 2, the effect held."
mk_md "$WORK/repeated.md"   "As shown in Figure 1 and Figure 2, the effect held."
mk_md "$WORK/range.md"      "As shown in Figures 1-2, the effect held."
mk_md "$WORK/wordrange.md"  "As shown in Figures 1 to 2, the effect held."
mk_md "$WORK/uncited.md"    "The analysis is described in the Methods."

echo "==== the equivalence: phrasing must not change the verdict ===="
rc_plural="$(run plural.md partial.docx)"
rc_repeat="$(run repeated.md partial.docx)"
ck "plural 'Figures 1 and 2' blocks"        1 "$rc_plural"
ck "repetitive form blocks (unchanged)"     1 "$rc_repeat"
ck "same verdict either way"                "$rc_repeat" "$rc_plural"
ck "plural: submission_safe false"          False "$(safe plural.md)"
ck "plural: Figure 2 is MISSING_DOCX"       MISSING_DOCX "$(status_of plural.md Figure:2)"

echo "==== ranges expand; an endpoint-only read would drop the interior ===="
ck "'Figures 1-2' blocks"                   1 "$(run range.md partial.docx)"
ck "'Figures 1 to 2' blocks"                1 "$(run wordrange.md partial.docx)"

echo "==== NEGATIVE CONTROLS ===="
ck "a genuinely uncited figure stays UNCITED" UNCITED "$(run uncited.md full.docx >/dev/null; status_of uncited.md Figure:2)"
rc_ok="$(run plural.md full.docx)"
ck "complete package: exit 0"               0 "$rc_ok"
ck "complete package: submission_safe true" True "$(safe plural.md)"
ck "no double count (singular is a prefix of plural)" 2 \
   "$(run repeated.md full.docx >/dev/null; grep -o 'in-text citations: [0-9]*' "$WORK/repeated.md.out" | grep -o '[0-9]*')"

echo
echo "  passed=$pass failed=$fail"
[ "$fail" -eq 0 ] || { for f in plural repeated uncited; do echo "--- $f"; cat "$WORK/$f.md.out"; done; exit 1; }
echo "OK: 'Figures 1 and 2' and 'Figure 1 and Figure 2' are the same claim, and both block."
