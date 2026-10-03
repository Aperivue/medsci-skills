#!/usr/bin/env bash
# Deterministic, network-free verifier for the acceptance-readiness challenge card.
# Runs assess_acceptance_readiness.py on synthetic manuscripts and diffs each
# report against its golden master in expected/:
#   - fixture_ceiling: seeded with design-ceiling / unfixable / importance / claim
#     signals -> must flag all four categories (9 flags) and the HIGH-impact verdict.
#   - fixture_clean: a strong multi-center externally-validated design that carries
#     management/surveillance verbs but NO ceiling trigger -> must flag nothing
#     (negative fixture: proves the gated CLAIM_MISMATCH does not false-fire).
#   - fixture_methods_vocab: routine methods wording (circular ROI, marginal
#     structural model, proxy/FIB-4 covariates, technical feasibility) -> 0 flags.
#   - fixture_references: design words only inside the reference list -> 0 flags.
#   - fixture_refs_then_appendix: a section after References is scanned again.
#   - fixture_narrowed_positive: the narrowed patterns still fire on real signals.
#   - fixture_paraphrase: signals the lexical scan cannot match -> 0 flags, and the
#     empty verdict must say it is NOT a design clearance.
# Then checks that non-text input (zip/.docx, PDF, non-UTF-8 bytes) exits 2 with
# no report on stdout instead of returning the empty-scan verdict.
# Exit 0 = every check passes.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
TOOL="$HERE/../assess_acceptance_readiness.py"

status=0
for case in ceiling clean methods_vocab references refs_then_appendix narrowed_positive paraphrase; do
  actual="$(python3 "$TOOL" "$HERE/fixture_${case}/manuscript.md")"
  if diff -u "$HERE/expected/report_${case}.txt" <(printf '%s\n' "$actual"); then
    echo "PASS: ${case} report matches expected."
  else
    echo "FAIL: ${case} report drifted from expected/report_${case}.txt" >&2
    status=1
  fi
done

if grep -q "NOT A DESIGN CLEARANCE" "$HERE/expected/report_paraphrase.txt"; then
  echo "PASS: empty-scan verdict states it is not a design clearance."
else
  echo "FAIL: empty-scan verdict reads as a clearance" >&2
  status=1
fi

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
python3 - "$TMP" <<'PY'
import sys, zipfile
from pathlib import Path
d = Path(sys.argv[1])
body = "This single-center cross-sectional pilot study had no external validation.\n"
with zipfile.ZipFile(d / "manuscript.docx", "w", zipfile.ZIP_DEFLATED) as z:
    z.writestr("word/document.xml", "<w:document><w:body><w:p><w:r><w:t>" + body * 20
               + "</w:t></w:r></w:p></w:body></w:document>")
(d / "manuscript.pdf").write_bytes(b"%PDF-1.4\n" + body.encode() * 5)
(d / "latin1.md").write_bytes("Café single-center study.\n".encode("latin-1"))
(d / "nul.md").write_bytes(b"single-center\x00\x00\x00 study\n")
PY
for bad in manuscript.docx manuscript.pdf latin1.md nul.md; do
  set +e
  out="$(python3 "$TOOL" "$TMP/$bad" 2>"$TMP/err")"
  rc=$?
  set -e
  if [ "$rc" -eq 2 ] && [ -z "$out" ] && grep -q "No scan was run" "$TMP/err"; then
    echo "PASS: non-text input ${bad} rejected with exit 2."
  else
    echo "FAIL: non-text input ${bad} gave exit ${rc} (want 2, empty stdout)" >&2
    status=1
  fi
done

# A UTF-8 file with a BOM is still text and must scan normally.
printf '\xef\xbb\xbfThis single-center study.\n' > "$TMP/bom.md"
if python3 "$TOOL" "$TMP/bom.md" | grep -q "single-center ::"; then
  echo "PASS: UTF-8 BOM input scanned."
else
  echo "FAIL: UTF-8 BOM input not scanned" >&2
  status=1
fi

if [ "$status" -eq 0 ]; then
  echo "PASS: acceptance-readiness pre-flight matches all golden masters and rejects non-text input."
fi
exit "$status"
