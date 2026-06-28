#!/usr/bin/env bash
# Deterministic, network-free verifier for the acceptance-readiness challenge card.
# Runs assess_acceptance_readiness.py on two synthetic manuscripts:
#   - fixture_ceiling: seeded with design-ceiling / unfixable / importance / claim
#     signals -> must flag all four categories (9 flags) and the HIGH-impact verdict.
#   - fixture_clean: a strong multi-center externally-validated design that carries
#     management/surveillance verbs but NO ceiling trigger -> must flag nothing
#     (negative fixture: proves the gated CLAIM_MISMATCH does not false-fire).
# Exit 0 = both reports match their golden masters.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
TOOL="$HERE/../assess_acceptance_readiness.py"

status=0
for case in ceiling clean; do
  actual="$(python3 "$TOOL" "$HERE/fixture_${case}/manuscript.md")"
  if diff -u "$HERE/expected/report_${case}.txt" <(printf '%s\n' "$actual"); then
    echo "PASS: ${case} report matches expected."
  else
    echo "FAIL: ${case} report drifted from expected/report_${case}.txt" >&2
    status=1
  fi
done

if [ "$status" -eq 0 ]; then
  echo "PASS: acceptance-readiness pre-flight matches both golden masters (positive + negative)."
fi
exit "$status"
