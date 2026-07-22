#!/usr/bin/env bash
# Deterministic verifier for the consistency-linter challenge card.
# Runs lint_consistency.py on a synthetic manuscript with seeded defects and
# diffs against expected/report.txt. Exit 0 = match.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
LINTER="$HERE/../lint_consistency.py"

actual="$(python3 "$LINTER" "$HERE/fixture/manuscript.md")"

if diff -u "$HERE/expected/report.txt" <(printf '%s\n' "$actual"); then
  echo "PASS: linter report matches expected (11 seeded issues across 8 categories)."
else
  echo "FAIL: linter output drifted from expected/report.txt" >&2
  exit 1
fi
