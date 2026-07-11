#!/usr/bin/env bash
# Deterministic verifier for the table-percentage challenge card.
# Runs check_table_percentages.py on two synthetic manuscript tables and diffs
# stdout against expected/. Stdlib-only, network-free. Exit 0 = both match and
# exit codes are correct. cd into HERE so the reported source path is the stable
# relative "fixture/..." (portable across CI checkout locations).
#
# Fixtures (synthetic only — no real manuscript, no PII):
#   table_bad.md — a characteristics column under n=132 printing 79 (63) / 53 (37);
#                  true values are 59.8% / 40.2%, so BOTH cells are wrong (the real
#                  incident shape) -> 2x PERCENT_MISMATCH.
#   table_ok.md  — a correct percentage column (16 (48%) / 17 (52%) under n=33) plus
#                  a mean (SD) table (45 (12) / 24 (3)); the SD cells must NOT be
#                  read as percentages -> OK, zero findings (no false positive).
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
DET="$HERE/../check_table_percentages.py"
cd "$HERE"

bad="$(python3 "$DET" --manuscript fixture/table_bad.md)"
ok="$(python3 "$DET" --manuscript fixture/table_ok.md)"

pass=1
if ! diff -u expected/bad.txt <(printf '%s\n' "$bad"); then
  echo "FAIL: bad-fixture output drifted from expected/bad.txt" >&2; pass=0
fi
if ! diff -u expected/ok.txt <(printf '%s\n' "$ok"); then
  echo "FAIL: ok-fixture output drifted from expected/ok.txt" >&2; pass=0
fi

python3 "$DET" --manuscript fixture/table_bad.md --strict --quiet >/dev/null 2>&1 && rc_bad=0 || rc_bad=$?
python3 "$DET" --manuscript fixture/table_ok.md  --strict --quiet >/dev/null 2>&1 && rc_ok=0  || rc_ok=$?
[ "${rc_bad:-0}" -eq 1 ] || { echo "FAIL: bad fixture should exit 1 under --strict (got ${rc_bad:-0})" >&2; pass=0; }
[ "$rc_ok" -eq 0 ]       || { echo "FAIL: ok fixture should exit 0 under --strict (got $rc_ok)" >&2; pass=0; }

if [ "$pass" -eq 1 ]; then
  echo "PASS: table-percentage gate flags both mis-rounded cells and clears the correct table + mean(SD) control."
else
  exit 1
fi
