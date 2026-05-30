#!/usr/bin/env bash
# Regression test for pre_submission_gate.sh.
#
# Verifies the orchestration contract end-to-end:
#   - default mode (no --allow-separate-attachments): stage 4 fails on
#     MISSING_DOCX, chain exits non-zero, submission_safe=false.
#   - --allow-separate-attachments mode: stage 4 downgrades MISSING_DOCX
#     to WARN, chain exits zero, submission_safe=true.
#
# Stage 2 (verify_refs --strict) requires network. If the network call
# fails, the fixture skips with exit code 77 (autotools "SKIP" convention)
# rather than reporting a regression.

set -uo pipefail

FIXTURE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GATE="${FIXTURE_DIR}/../../../scripts/pre_submission_gate.sh"
WORK_DIR="$(mktemp -d -t pre_submission_gate_test.XXXXXX)"
trap 'rm -rf "$WORK_DIR"' EXIT

MD="$WORK_DIR/manuscript.md"
BIB="$WORK_DIR/refs.bib"
DOCX="$WORK_DIR/placeholder.docx"
QC_DEFAULT="$WORK_DIR/qc_default"
QC_RELAXED="$WORK_DIR/qc_relaxed"

cp "$FIXTURE_DIR/manuscript.md" "$MD"
cp "$FIXTURE_DIR/refs.bib"      "$BIB"

# Synthesize a minimal valid .docx (zip with the OOXML skeleton). This DOCX
# intentionally contains NO Figure 1 / Table 1 captions so that stage 4 finds
# them MISSING_DOCX. The pre-rendered placeholder skips stage 3.
python3 - "$DOCX" <<'PY'
import sys, zipfile
out = sys.argv[1]
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    z.writestr(
        "[Content_Types].xml",
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        '</Types>',
    )
    z.writestr(
        "_rels/.rels",
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
        '</Relationships>',
    )
    z.writestr(
        "word/document.xml",
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        '<w:body><w:p><w:r><w:t>Placeholder body without Figure or Table captions.</w:t></w:r></w:p></w:body>'
        '</w:document>',
    )
PY

echo "==== Test 1: default mode must FAIL on MISSING_DOCX ===="
set +e
bash "$GATE" \
    --md "$MD" --bib "$BIB" --docx "$DOCX" --qc-dir "$QC_DEFAULT" \
    > "$WORK_DIR/default.log" 2>&1
RC1=$?
set -e

# If stage 2 failed because of network, skip the entire fixture gracefully.
if grep -q '"verify_refs", "status": "FAIL"' "$QC_DEFAULT/pre_submission_gate.json" 2>/dev/null \
   || grep -qiE "network|connection|temporary failure|name resolution" "$WORK_DIR/default.log"; then
  echo "[SKIP] verify_refs stage failed (likely network-restricted environment)."
  cat "$WORK_DIR/default.log"
  exit 77
fi

if [[ "$RC1" -eq 0 ]]; then
  echo "FAIL: default mode unexpectedly passed (expected MISSING_DOCX-induced failure)." >&2
  cat "$WORK_DIR/default.log" >&2
  exit 1
fi
if ! grep -q '"submission_safe": false' "$QC_DEFAULT/pre_submission_gate.json"; then
  echo "FAIL: default mode did not write submission_safe:false." >&2
  cat "$QC_DEFAULT/pre_submission_gate.json" >&2
  exit 1
fi
echo "  OK: default mode FAIL with submission_safe:false (rc=$RC1)"

echo "==== Test 2: --allow-separate-attachments mode must PASS ===="
set +e
bash "$GATE" \
    --md "$MD" --bib "$BIB" --docx "$DOCX" \
    --allow-separate-attachments --qc-dir "$QC_RELAXED" \
    > "$WORK_DIR/relaxed.log" 2>&1
RC2=$?
set -e

if [[ "$RC2" -ne 0 ]]; then
  echo "FAIL: --allow-separate-attachments mode exited non-zero (rc=$RC2)." >&2
  cat "$WORK_DIR/relaxed.log" >&2
  exit 1
fi
if ! grep -q '"submission_safe": true' "$QC_RELAXED/pre_submission_gate.json"; then
  echo "FAIL: --allow-separate-attachments mode did not write submission_safe:true." >&2
  cat "$QC_RELAXED/pre_submission_gate.json" >&2
  exit 1
fi
if ! grep -q '"allow_separate_attachments": true' "$QC_RELAXED/xref_audit.json"; then
  echo "FAIL: xref_audit.json did not record the policy flag." >&2
  cat "$QC_RELAXED/xref_audit.json" >&2
  exit 1
fi
echo "  OK: --allow-separate-attachments PASS with submission_safe:true (rc=$RC2)"

echo "==== All regression invariants hold ===="
exit 0
