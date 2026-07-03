#!/usr/bin/env bash
# Deterministic verifier for the radiomics/classical-ML challenge card.
# Runs check_radiomics_ml.py on two synthetic pipeline manifests and diffs stdout
# against expected/. No network, no sklearn — every verdict is decided by rule on the
# manifest. Exit 0 = both match and exit codes correct.
#
# Fixtures (synthetic only — no real patients, no PII):
#   pipeline_weak.json   — 1200 features / 40 events, flat CV, selection on the whole
#                          dataset, no dim-reduction / stability / calibration / external
#                          validation (all six verdicts fire).
#   pipeline_strong.json — nested CV, selection inside the fold, dim-reduction on, ICC
#                          stability filter, calibration + temporal external validation.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
DET="$HERE/../check_radiomics_ml.py"

weak="$(python3 "$DET" --manifest "$HERE/fixture/pipeline_weak.json")"
strong="$(python3 "$DET" --manifest "$HERE/fixture/pipeline_strong.json")"

ok=1
if ! diff -u "$HERE/expected/weak.txt" <(printf '%s\n' "$weak"); then
  echo "FAIL: weak-fixture output drifted from expected/weak.txt" >&2; ok=0
fi
if ! diff -u "$HERE/expected/strong.txt" <(printf '%s\n' "$strong"); then
  echo "FAIL: strong-fixture output drifted from expected/strong.txt" >&2; ok=0
fi

python3 "$DET" --manifest "$HERE/fixture/pipeline_weak.json" --strict --quiet >/dev/null 2>&1 && rc_weak=0 || rc_weak=$?
python3 "$DET" --manifest "$HERE/fixture/pipeline_strong.json" --strict --quiet >/dev/null 2>&1 && rc_strong=0 || rc_strong=$?
[ "${rc_weak:-0}" -eq 1 ] || { echo "FAIL: weak fixture should exit 1 under --strict (got ${rc_weak:-0})" >&2; ok=0; }
[ "$rc_strong" -eq 0 ]    || { echo "FAIL: strong fixture should exit 0 under --strict (got $rc_strong)" >&2; ok=0; }

if [ "$ok" -eq 1 ]; then
  echo "PASS: radiomics/ML gate flags the overfit, leaky, uncalibrated pipeline and clears the rigorous one."
else
  exit 1
fi
