#!/usr/bin/env bash
# Deterministic verifier for the explainability-report challenge card.
# Runs check_explainability_report.py on two synthetic report manifests and diffs
# stdout against expected/. No network, no torch — every verdict is decided by rule
# on the manifest. Exit 0 = both match and exit codes correct.
#
# Fixtures (synthetic only — no real patients, no PII):
#   report_weak.json   — a Grad-CAM localisation claim with no sanity check
#                        (NO_SANITY_CHECK), no localisation metric (NO_LOCALIZATION_METRIC),
#                        and only 4 illustrative cases (CHERRY_PICKED_EXAMPLES).
#   report_strong.json — Grad-CAM++ over 200 cases, cohort-level IoU against ground truth,
#                        both Adebayo randomisation sanity checks.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
DET="$HERE/../check_explainability_report.py"

weak="$(python3 "$DET" --manifest "$HERE/fixture/report_weak.json")"
strong="$(python3 "$DET" --manifest "$HERE/fixture/report_strong.json")"

ok=1
if ! diff -u "$HERE/expected/weak.txt" <(printf '%s\n' "$weak"); then
  echo "FAIL: weak-fixture output drifted from expected/weak.txt" >&2; ok=0
fi
if ! diff -u "$HERE/expected/strong.txt" <(printf '%s\n' "$strong"); then
  echo "FAIL: strong-fixture output drifted from expected/strong.txt" >&2; ok=0
fi

python3 "$DET" --manifest "$HERE/fixture/report_weak.json" --strict --quiet >/dev/null 2>&1 && rc_weak=0 || rc_weak=$?
python3 "$DET" --manifest "$HERE/fixture/report_strong.json" --strict --quiet >/dev/null 2>&1 && rc_strong=0 || rc_strong=$?
[ "${rc_weak:-0}" -eq 1 ] || { echo "FAIL: weak fixture should exit 1 under --strict (got ${rc_weak:-0})" >&2; ok=0; }
[ "$rc_strong" -eq 0 ]    || { echo "FAIL: strong fixture should exit 0 under --strict (got $rc_strong)" >&2; ok=0; }

if [ "$ok" -eq 1 ]; then
  echo "PASS: explainability-report gate flags the unsanitised, unmeasured, cherry-picked analysis and clears the rigorous one."
else
  exit 1
fi
