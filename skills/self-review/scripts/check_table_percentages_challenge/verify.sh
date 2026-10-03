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
#   table_precision.md    — one-decimal cells under n=150: 23 (15.0%) and 40 (27.1%) are
#                  15.3% / 26.7%; within 0.5 pp but not at the printed precision
#                  -> 2x PERCENT_MISMATCH (the SKILL.md 23/150 example).
#   table_precision_ok.md — the same counts printed correctly at one decimal and as
#                  integers, exact half-unit ties (1/8 = 12.5%) and two-decimal cells
#                  (1/3 = 33.33%) -> OK.
#   table_precision_footnote.md — 23 (15.4%) / 18 (15.1%) on a footnoted row whose footnote
#                  gives 149 / 119 known: off only at the printed precision on a footnoted
#                  row -> OK with two MINOR PERCENT_PRECISION_NOTE (main cleared it).
#   table_precision_footnote_bad.md — the same row printed 23 (16.4%) (1.1 pp off): a
#                  footnote does not excuse a miss beyond 0.5 pp -> PERCENT_MISMATCH.
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

for c in precision precision_ok precision_footnote precision_footnote_bad; do
  out="$(python3 "$DET" --manuscript "fixture/table_$c.md")"
  diff -u "expected/$c.txt" <(printf '%s\n' "$out") || { echo "FAIL: $c drifted from expected/$c.txt" >&2; pass=0; }
done
python3 "$DET" --manuscript fixture/table_precision.md --strict --quiet >/dev/null 2>&1 && rc_pr=0 || rc_pr=$?
python3 "$DET" --manuscript fixture/table_precision_ok.md --strict --quiet >/dev/null 2>&1 && rc_pro=0 || rc_pro=$?
[ "${rc_pr:-0}" -eq 1 ] || { echo "FAIL: precision fixture should exit 1 under --strict (got ${rc_pr:-0})" >&2; pass=0; }
[ "$rc_pro" -eq 0 ]      || { echo "FAIL: precision_ok fixture should exit 0 under --strict (got $rc_pro)" >&2; pass=0; }
python3 "$DET" --manuscript fixture/table_precision_footnote.md --strict --quiet >/dev/null 2>&1 && rc_pf=0 || rc_pf=$?
python3 "$DET" --manuscript fixture/table_precision_footnote_bad.md --strict --quiet >/dev/null 2>&1 && rc_pfb=0 || rc_pfb=$?
[ "$rc_pf" -eq 0 ]         || { echo "FAIL: precision_footnote should exit 0 under --strict (got $rc_pf)" >&2; pass=0; }
[ "${rc_pfb:-0}" -eq 1 ]   || { echo "FAIL: precision_footnote_bad should exit 1 under --strict (got ${rc_pfb:-0})" >&2; pass=0; }

python3 "$DET" --manuscript fixture/table_bad.md --strict --quiet >/dev/null 2>&1 && rc_bad=0 || rc_bad=$?
python3 "$DET" --manuscript fixture/table_ok.md  --strict --quiet >/dev/null 2>&1 && rc_ok=0  || rc_ok=$?
[ "${rc_bad:-0}" -eq 1 ] || { echo "FAIL: bad fixture should exit 1 under --strict (got ${rc_bad:-0})" >&2; pass=0; }
[ "$rc_ok" -eq 0 ]       || { echo "FAIL: ok fixture should exit 0 under --strict (got $rc_ok)" >&2; pass=0; }

if [ "$pass" -eq 1 ]; then
  echo "PASS: table-percentage gate flags both mis-rounded cells and clears the correct table + mean(SD) control."
else
  exit 1
fi
