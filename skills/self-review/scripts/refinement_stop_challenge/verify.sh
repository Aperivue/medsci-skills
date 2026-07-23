#!/usr/bin/env bash
# Deterministic verifier for the refinement-stop terminal-state challenge card.
# Network-free, stdlib-only. Every scenario is advisory, so every run must exit 0 --
# the loop controller informs the harness; it never blocks the floor detectors.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
TOOL="$HERE/../refinement_stop.py"
cd "$HERE"

pass=1
for scenario in zero_edit overhardening minor_optional continue empty; do
  got="$(python3 "$TOOL" --qc-dir "fixture/$scenario")"
  if ! diff -u "expected/$scenario.txt" <(printf '%s\n' "$got"); then
    echo "FAIL: $scenario output drifted from expected/$scenario.txt" >&2
    pass=0
  fi
  python3 "$TOOL" --qc-dir "fixture/$scenario" --strict --quiet >/dev/null 2>&1 && rc=0 || rc=$?
  if [ "${rc:-0}" -ne 0 ]; then
    echo "FAIL: $scenario must exit 0 (advisory, even under --strict); got ${rc:-0}" >&2
    pass=0
  fi
done

# The verdict must be reproducible in the JSON artifact, not only on stdout.
tmp="$(mktemp)"
python3 "$TOOL" --qc-dir fixture/zero_edit --out "$tmp" --quiet
grep -q '"verdict": "STOP_ZERO_EDIT"' "$tmp" || { echo "FAIL: JSON artifact missing STOP_ZERO_EDIT verdict" >&2; pass=0; }
grep -q '"stop": true' "$tmp"               || { echo "FAIL: JSON artifact missing stop:true" >&2; pass=0; }
rm -f "$tmp"

if [ "$pass" -eq 1 ]; then
  echo "PASS: refinement-stop classifies all five terminal states (zero-edit / over-hardening / minor-optional / continue / indeterminate) from qc/*.json and never blocks."
else
  exit 1
fi
