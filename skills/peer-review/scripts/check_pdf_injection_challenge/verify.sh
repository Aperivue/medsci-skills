#!/usr/bin/env bash
# Deterministic verifier for the pdf-injection challenge card.
# Runs check_pdf_injection.py on two synthetic span manifests and diffs stdout
# against expected/. No network, no PyMuPDF — the extractor (scan_pdf_layers.py)
# owns that dependency; the detector audits the manifest with stdlib only, so
# this runs in CI unchanged. Exit 0 = both match and exit codes are correct.
#
# Fixtures (synthetic only — no real manuscript, no PII):
#   manifest_inject.json — one injection sentence smuggled five ways: white-on-
#     white (LOW_CONTRAST), 1pt (TINY_FONT), 10%-on-page (OFF_PAGE), render mode 3
#     (INVISIBLE), and a keywords metadata field (METADATA) -> INJECTION DETECTED.
#   manifest_clean.json  — visible body plus the near-miss prose "We recommend the
#     authors expand the external validation cohort", which must NOT trip the
#     injection patterns -> CLEAN (guards against false positives).
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

if [ "$ok" -eq 1 ]; then
  echo "PASS: pdf-injection gate flags all five hiding vectors and clears the near-miss control."
else
  exit 1
fi
