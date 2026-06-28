#!/usr/bin/env bash
# Deterministic verifier for the split-leakage challenge card.
# Runs check_split_leakage.py on two synthetic split-assignment CSVs and diffs the
# stdout against expected/. No network, no torch — the leak is decided by set
# arithmetic on the patient IDs. Exit 0 = both match and exit codes are correct.
#
# Fixtures (synthetic only — no real patients, no PII):
#   splits_leak.csv  — patient P03 in train+test and P07 in train+val (2 leaks).
#   splits_clean.csv — each patient in exactly one partition; the synonyms
#                      training/validation/holdout collapse, so they do NOT
#                      register as extra partitions (no false overlap).
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
DET="$HERE/../check_split_leakage.py"

leak="$(python3 "$DET" --splits "$HERE/fixture/splits_leak.csv")"
clean="$(python3 "$DET" --splits "$HERE/fixture/splits_clean.csv")"

ok=1
if ! diff -u "$HERE/expected/leak.txt" <(printf '%s\n' "$leak"); then
  echo "FAIL: leak-fixture output drifted from expected/leak.txt" >&2; ok=0
fi
if ! diff -u "$HERE/expected/clean.txt" <(printf '%s\n' "$clean"); then
  echo "FAIL: clean-fixture output drifted from expected/clean.txt" >&2; ok=0
fi

# Exit-code contract under --strict: leak -> 1 (Major), clean -> 0.
python3 "$DET" --splits "$HERE/fixture/splits_leak.csv" --strict --quiet >/dev/null 2>&1 && rc_leak=0 || rc_leak=$?
python3 "$DET" --splits "$HERE/fixture/splits_clean.csv" --strict --quiet >/dev/null 2>&1 && rc_clean=0 || rc_clean=$?
[ "${rc_leak:-0}" -eq 1 ] || { echo "FAIL: leak fixture should exit 1 under --strict (got ${rc_leak:-0})" >&2; ok=0; }
[ "$rc_clean" -eq 0 ]      || { echo "FAIL: clean fixture should exit 0 under --strict (got $rc_clean)" >&2; ok=0; }

if [ "$ok" -eq 1 ]; then
  echo "PASS: split-leakage gate flags the 2 patient-overlap leaks (P03, P07) and clears the disjoint split."
else
  exit 1
fi
