#!/usr/bin/env bash
# Deterministic verifier for the uncertainty/OOD reporting challenge card.
# Runs check_uncertainty_reporting.py on two synthetic uncertainty manifests and diffs
# stdout against expected/. No network, no torch — every verdict is decided by rule on the
# manifest. Exit 0 = both match and exit codes correct.
#
# Fixtures (synthetic only — no real patients, no PII):
#   uncertainty_weak.json   — a deployment claim with point predictions only, an OOD claim
#                             with no held-out OOD set, and selective prediction with no
#                             target (2 Major + 1 Minor fire).
#   uncertainty_strong.json — conformal intervals with validated coverage, OOD detection on
#                             a held-out OOD cohort, selective prediction at a pre-specified
#                             target, calibration evaluated under shift (clean).
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
DET="$HERE/../check_uncertainty_reporting.py"

weak="$(python3 "$DET" --manifest "$HERE/fixture/uncertainty_weak.json")"
strong="$(python3 "$DET" --manifest "$HERE/fixture/uncertainty_strong.json")"

ok=1
if ! diff -u "$HERE/expected/weak.txt" <(printf '%s\n' "$weak"); then
  echo "FAIL: weak-fixture output drifted from expected/weak.txt" >&2; ok=0
fi
if ! diff -u "$HERE/expected/strong.txt" <(printf '%s\n' "$strong"); then
  echo "FAIL: strong-fixture output drifted from expected/strong.txt" >&2; ok=0
fi

python3 "$DET" --manifest "$HERE/fixture/uncertainty_weak.json" --strict --quiet >/dev/null 2>&1 && rc_weak=0 || rc_weak=$?
python3 "$DET" --manifest "$HERE/fixture/uncertainty_strong.json" --strict --quiet >/dev/null 2>&1 && rc_strong=0 || rc_strong=$?
[ "${rc_weak:-0}" -eq 1 ] || { echo "FAIL: weak fixture should exit 1 under --strict (got ${rc_weak:-0})" >&2; ok=0; }
[ "$rc_strong" -eq 0 ]    || { echo "FAIL: strong fixture should exit 0 under --strict (got $rc_strong)" >&2; ok=0; }

if [ "$ok" -eq 1 ]; then
  echo "PASS: uncertainty/OOD gate flags the point-prediction deployment claim and clears the calibrated one."
else
  exit 1
fi
