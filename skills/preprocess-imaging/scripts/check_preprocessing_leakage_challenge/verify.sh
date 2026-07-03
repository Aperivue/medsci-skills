#!/usr/bin/env bash
# Deterministic verifier for the preprocessing-leakage challenge card.
# Runs check_preprocessing_leakage.py on two synthetic preprocessing manifests and
# diffs stdout against expected/. No network, no torch — every leak is decided by
# rule + set arithmetic on the manifest. Exit 0 = both match and exit codes correct.
#
# Fixtures (synthetic only — no real patients, no PII):
#   manifest_leak.json  — 4 leaks: a histogram_match fit on 'all' (NORMALIZATION_LEAKAGE),
#                         a dataset standardize before the split (PREPROCESS_BEFORE_SPLIT),
#                         augmentation applied to test (AUGMENTATION_ON_EVAL), and patient
#                         P03 in train+test (PATIENT_CROSS_SPLIT).
#   manifest_clean.json — train-only z-score after split, per-image norm (leakage-free even
#                         before split), augmentation on train only, fixed HU window, and a
#                         disjoint patient split.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
DET="$HERE/../check_preprocessing_leakage.py"

leak="$(python3 "$DET" --manifest "$HERE/fixture/manifest_leak.json")"
clean="$(python3 "$DET" --manifest "$HERE/fixture/manifest_clean.json")"

ok=1
if ! diff -u "$HERE/expected/leak.txt" <(printf '%s\n' "$leak"); then
  echo "FAIL: leak-fixture output drifted from expected/leak.txt" >&2; ok=0
fi
if ! diff -u "$HERE/expected/clean.txt" <(printf '%s\n' "$clean"); then
  echo "FAIL: clean-fixture output drifted from expected/clean.txt" >&2; ok=0
fi

python3 "$DET" --manifest "$HERE/fixture/manifest_leak.json" --strict --quiet >/dev/null 2>&1 && rc_leak=0 || rc_leak=$?
python3 "$DET" --manifest "$HERE/fixture/manifest_clean.json" --strict --quiet >/dev/null 2>&1 && rc_clean=0 || rc_clean=$?
[ "${rc_leak:-0}" -eq 1 ] || { echo "FAIL: leak fixture should exit 1 under --strict (got ${rc_leak:-0})" >&2; ok=0; }
[ "$rc_clean" -eq 0 ]      || { echo "FAIL: clean fixture should exit 0 under --strict (got $rc_clean)" >&2; ok=0; }

if [ "$ok" -eq 1 ]; then
  echo "PASS: preprocessing-leakage gate flags the 3 Major leaks + 1 augmentation-on-eval flag and clears the safe manifest."
else
  exit 1
fi
