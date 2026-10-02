#!/usr/bin/env bash
# Deterministic verifier for the pdf-injection challenge card.
# Runs check_pdf_injection.py on seven synthetic span manifests and diffs stdout
# against expected/. No network, no PyMuPDF — the extractor (scan_pdf_layers.py)
# owns that dependency; the detector audits the manifest with stdlib only, so
# this runs in CI unchanged. Exit 0 = every output matches and exit codes are correct.
#
# Fixtures (synthetic only — no real manuscript, no PII):
#   manifest_inject.json — one injection sentence smuggled five ways: white-on-
#     white (LOW_CONTRAST), 1pt (TINY_FONT), 10%-on-page (OFF_PAGE), render mode 3
#     (INVISIBLE), and a keywords metadata field (METADATA) -> INJECTION DETECTED.
#   manifest_clean.json  — visible body plus the near-miss prose "We recommend the
#     authors expand the external validation cohort", which must NOT trip the
#     injection patterns -> CLEAN (guards against false positives).
#   Figure/table-label set — Editorial Manager reviewer PDFs place figure-page labels
#   off-page; only a span hidden solely by OFF_PAGE whose WHOLE text is a label is
#   excused (INFO), everything else keeps today's verdict:
#   manifest_em_label.json                 off-page "Figure 2" only        -> CLEAN
#   manifest_em_label_variants.json        nine label shapes off-page      -> CLEAN
#   manifest_label_prefixed_injection.json off-page "Figure 2. Ignore all previous
#                                          instructions ..."               -> INJECTION DETECTED
#   manifest_label_plus_white_text.json    off-page label + a white-text
#                                          instruction elsewhere           -> SUSPICIOUS
#   manifest_label_other_hidden.json       labels hidden by colour or size, and an
#                                          off-page "See Figure 4"         -> SUSPICIOUS
#   Render evidence from the extractor (render_mode, opacity, glyphs/glyphs_inked):
#   manifest_render_hidden.json   render mode 3, opacity 0, and 1 of 54 glyphs drawn
#                                 (covered); colours look normal         -> SUSPICIOUS
#   manifest_render_visible.json  white on a dark banner, near-complete ink, a 5pt
#                                 "1", an off-page label with no pixels  -> CLEAN
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
DET="$HERE/../check_pdf_injection.py"

inject="$(python3 "$DET" "$HERE/fixture/manifest_inject.json")"
clean="$(python3 "$DET" "$HERE/fixture/manifest_clean.json")"

ok=1
if ! diff -u "$HERE/expected/inject.txt" <(printf '%s\n' "$inject"); then
  echo "FAIL: inject-fixture output drifted from expected/inject.txt" >&2; ok=0
fi
if ! diff -u "$HERE/expected/clean.txt" <(printf '%s\n' "$clean"); then
  echo "FAIL: clean-fixture output drifted from expected/clean.txt" >&2; ok=0
fi

# Exit-code contract under --strict (default --fail-on suspicious):
# inject -> 1, clean -> 0.
python3 "$DET" "$HERE/fixture/manifest_inject.json" --strict --quiet >/dev/null 2>&1 && rc_inject=0 || rc_inject=$?
python3 "$DET" "$HERE/fixture/manifest_clean.json" --strict --quiet >/dev/null 2>&1 && rc_clean=0 || rc_clean=$?
[ "${rc_inject:-0}" -eq 1 ] || { echo "FAIL: inject fixture should exit 1 under --strict (got ${rc_inject:-0})" >&2; ok=0; }
[ "$rc_clean" -eq 0 ]       || { echo "FAIL: clean fixture should exit 0 under --strict (got $rc_clean)" >&2; ok=0; }

# Figure/table-label set: stem | verdict | exit code under --strict.
while IFS='|' read -r stem verdict want; do
  out="$(python3 "$DET" "$HERE/fixture/manifest_$stem.json")"
  if ! diff -u "$HERE/expected/$stem.txt" <(printf '%s\n' "$out"); then
    echo "FAIL: $stem output drifted from expected/$stem.txt" >&2; ok=0
  fi
  [ "$(printf '%s\n' "$out" | head -n 1)" = "== $verdict ==  synthetic_$stem.pdf" ] \
    || { echo "FAIL: $stem verdict should be $verdict" >&2; ok=0; }
  python3 "$DET" "$HERE/fixture/manifest_$stem.json" --strict --quiet >/dev/null 2>&1 && rc=0 || rc=$?
  [ "$rc" -eq "$want" ] || { echo "FAIL: $stem should exit $want under --strict (got $rc)" >&2; ok=0; }
done <<'EOF'
em_label|CLEAN|0
em_label_variants|CLEAN|0
label_prefixed_injection|INJECTION DETECTED|1
label_plus_white_text|SUSPICIOUS|1
label_other_hidden|SUSPICIOUS|1
render_hidden|SUSPICIOUS|1
render_visible|CLEAN|0
EOF

if [ "$ok" -eq 1 ]; then
  echo "PASS: pdf-injection gate flags all five hiding vectors, clears the near-miss control, and excuses only whole-span off-page figure/table labels."
else
  exit 1
fi
