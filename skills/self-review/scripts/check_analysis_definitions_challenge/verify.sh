#!/usr/bin/env bash
# Deterministic verifier for the analysis-definitions challenge card.
# Fixtures (synthetic only — no real manuscript, no PII):
#   undefined.md — a Cox model and a Fine–Gray model with no outcome named, and
#                  discrimination/calibration with no reference standard.
#   defined.md   — THE SAME ANALYSES (models=2, auxiliary=2), each carrying its
#                  outcome, time variable, censoring rule, and reference standard.
# The two differ only in whether the analyses are DEFINED. That is the point: the
# count is identical, so a load-counting detector could not tell them apart.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"; DET="$HERE/../check_analysis_definitions.py"; cd "$HERE"
und="$(python3 "$DET" --manuscript fixture/undefined.md)"
def="$(python3 "$DET" --manuscript fixture/defined.md)"
pass=1
diff -u expected/undefined.txt <(printf '%s\n' "$und") || { echo "FAIL: undefined drift" >&2; pass=0; }
diff -u expected/defined.txt  <(printf '%s\n' "$def") || { echo "FAIL: defined drift" >&2; pass=0; }
python3 "$DET" --manuscript fixture/undefined.md --strict --quiet >/dev/null 2>&1 && ru=0 || ru=$?
python3 "$DET" --manuscript fixture/defined.md   --strict --quiet >/dev/null 2>&1 && rd=0 || rd=$?
[ "${ru:-0}" -eq 1 ] || { echo "FAIL: undefined should exit 1 (got ${ru:-0})" >&2; pass=0; }
[ "$rd" -eq 0 ]      || { echo "FAIL: defined should exit 0 (got $rd)" >&2; pass=0; }
[ "$pass" -eq 1 ] && echo "PASS: same analysis count, opposite verdict — definition is what the gate reads." || exit 1
