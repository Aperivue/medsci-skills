#!/usr/bin/env bash
# Deterministic verifier for the citation-snowballing challenge card.
# No network: reads recorded Semantic Scholar responses from fixture/.
# Exit 0 = output matches expected/snowball.bib ; non-zero = regression.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
SNOWBALL="$HERE/../snowball.py"

actual="$(python3 "$SNOWBALL" \
  --seed DOI:10.0/seed1 \
  --direction all \
  --offline-fixture "$HERE/fixture" \
  --pool "$HERE/fixture/library.bib" \
  --as-of 2026-06-14 \
  --stdout 2>/dev/null)"

if diff -u "$HERE/expected/snowball.bib" <(printf '%s\n' "$actual"); then
  echo "PASS: snowball output matches expected (4 new candidates; 1 backward dup removed)."
else
  echo "FAIL: snowball output drifted from expected/snowball.bib" >&2
  exit 1
fi
