#!/usr/bin/env bash
# Deterministic verifier for the dataset-profile challenge card.
# Runs check_dataset_profile.py on two synthetic profiles and diffs stdout against
# expected/. No network, no nibabel, no images — every finding is decided by rule and
# set arithmetic over the profile JSON. Exit 0 = both match and exit codes correct.
#
# Fixtures (synthetic only — no real patients, no PII):
#   profile_defect.json — 5 Major (label grid mismatch, empty label, stray label index,
#                         an unlabelled `test` split, accuracy planned at 0.4% foreground)
#                         + 5 Minor (missing label file, 5.3x z-spacing with no resampling
#                         declared, mixed orientation, one case off the HU scale, extreme
#                         imbalance with no Dice-family loss).
#   profile_clean.json  — the same *kind* of dataset with every decision declared:
#                         spacing is still heterogeneous and orientation still mixed, but
#                         resampling and reorientation are declared, the loss is Dice-family,
#                         accuracy is not reported, and the held-out split is labelled.
#                         Nothing fires — heterogeneity that has been dealt with is not a defect.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
DET="$HERE/../check_dataset_profile.py"

defect="$(python3 "$DET" --profile "$HERE/fixture/profile_defect.json")"
clean="$(python3 "$DET" --profile "$HERE/fixture/profile_clean.json")"

ok=1
if ! diff -u "$HERE/expected/defect.txt" <(printf '%s\n' "$defect"); then
  echo "FAIL: defect-fixture output drifted from expected/defect.txt" >&2; ok=0
fi
if ! diff -u "$HERE/expected/clean.txt" <(printf '%s\n' "$clean"); then
  echo "FAIL: clean-fixture output drifted from expected/clean.txt" >&2; ok=0
fi

python3 "$DET" --profile "$HERE/fixture/profile_defect.json" --strict --quiet >/dev/null 2>&1 && rc_d=0 || rc_d=$?
python3 "$DET" --profile "$HERE/fixture/profile_clean.json" --strict --quiet >/dev/null 2>&1 && rc_c=0 || rc_c=$?
[ "${rc_d:-0}" -eq 1 ] || { echo "FAIL: defect fixture should exit 1 under --strict (got ${rc_d:-0})" >&2; ok=0; }
[ "$rc_c" -eq 0 ]      || { echo "FAIL: clean fixture should exit 0 under --strict (got $rc_c)" >&2; ok=0; }

if [ "$ok" -eq 1 ]; then
  echo "PASS: dataset-profile gate flags the 5 Major defects + 5 Minor decisions and clears the declared profile."
fi
[ "$ok" -eq 1 ] || exit 1
