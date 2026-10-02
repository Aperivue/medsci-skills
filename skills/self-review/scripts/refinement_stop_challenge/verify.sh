#!/usr/bin/env bash
# Deterministic verifier for the refinement-stop terminal-state challenge card.
# Network-free, stdlib-only. Every scenario is advisory, so every run must exit 0 --
# the loop controller informs the harness; it never blocks the floor detectors.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
TOOL="$HERE/../refinement_stop.py"
cd "$HERE"

pass=1
for scenario in zero_edit overhardening minor_optional continue empty findings_major unparsed_gate \
                ceiling_only crashed_gate; do
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

# Regression: a findings-schema gate (table_percentages: {findings, kind, severity:MAJOR}) must be
# COUNTED as a floor Major, not silently skipped -- the exact bug real-manuscript verification caught.
python3 "$TOOL" --qc-dir fixture/findings_major --out "$tmp" --quiet
grep -q '"verdict": "CONTINUE"' "$tmp"          || { echo "FAIL: findings-schema Major not counted (verdict != CONTINUE)" >&2; pass=0; }
grep -q '"check_table_percentages"' "$tmp"      || { echo "FAIL: findings-schema gate absent from gates_read" >&2; pass=0; }
# Visibility guard: a detector-keyed file with an unrecognised schema must be surfaced, not dropped.
python3 "$TOOL" --qc-dir fixture/unparsed_gate --out "$tmp" --quiet
python3 -c "import json,sys; d=json.load(open('$tmp')); sys.exit(0 if 'check_novel_schema' in d.get('gates_unparsed',[]) else 1)" \
                                                || { echo "FAIL: unparsed gate not surfaced in gates_unparsed" >&2; pass=0; }
# No STOP without a floor: a clean ceiling pass alone, or a floor gate that crashed and left an
# empty / truncated qc/*.json beside clean ones, must not read as "submission-ready as-is".
for scenario in ceiling_only crashed_gate; do
  python3 "$TOOL" --qc-dir "fixture/$scenario" --out "$tmp" --quiet
  grep -q '"verdict": "INDETERMINATE"' "$tmp" || { echo "FAIL: $scenario must be INDETERMINATE" >&2; pass=0; }
  grep -q '"stop": false' "$tmp"             || { echo "FAIL: $scenario must not signal stop" >&2; pass=0; }
done
python3 -c "import json,sys; d=json.load(open('$tmp')); sys.exit(0 if d.get('artifacts_unreadable')==['reported_p.json','table_percentages.json'] else 1)" \
                                                || { echo "FAIL: unreadable artifacts not named" >&2; pass=0; }
rm -f "$tmp"

if [ "$pass" -eq 1 ]; then
  echo "PASS: refinement-stop classifies the terminal states, counts a findings-schema Major (not just the claims schema), and surfaces an unrecognised schema instead of silently dropping it; never blocks."
else
  exit 1
fi
