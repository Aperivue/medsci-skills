#!/usr/bin/env bash
# Regression test for the feature-selection-outside-CV leakage gate.
# (bad) log-odds feature selection on the full dataset + 5-fold CV, no nesting ->
# CV_SELECTION_LEAKAGE; (clean) selection repeated within each training fold (nested
# CV) -> no flag.
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$HERE/../scripts/check_cv_leakage.py"
BAD="$HERE/fixtures/cv_leakage_bad.md"
CLEAN="$HERE/fixtures/cv_leakage_clean.md"
OUT="$(mktemp -t cvl_XXXX).json"
trap 'rm -f "$OUT"' EXIT
fail=0
check() { local label="$1"; shift
  if "$@" >/dev/null 2>&1; then printf '  PASS  %s\n' "$label"
  else printf '  FAIL  %s\n' "$label"; fail=$((fail+1)); fi; }
[[ -f "$SCRIPT" ]] || { echo "ENV-ERR: script missing" >&2; exit 2; }

python3 "$SCRIPT" --manuscript "$BAD" --out "$OUT" --strict --quiet >/dev/null 2>&1
check "exit 1 under --strict (Major present)" test "$?" -eq 1
check "CV_SELECTION_LEAKAGE on selection+CV without nesting" python3 -c "
import json
d=json.load(open('$OUT'))
assert any(c['verdict']=='CV_SELECTION_LEAKAGE' for c in d['claims']), 'not flagged'
"
python3 "$SCRIPT" --manuscript "$CLEAN" --strict --quiet >/dev/null 2>&1
check "exit 0 when selection is nested within each fold" test "$?" -eq 0
python3 "$SCRIPT" --manuscript "$CLEAN" --out "$OUT" --quiet >/dev/null 2>&1
check "no leakage flag on nested CV" python3 -c "
import json
d=json.load(open('$OUT'))
assert not d['claims'], d['claims']
"
echo "fail=$fail"; [[ "$fail" -eq 0 ]] && echo "ALL PASS" || echo "FAILURES: $fail"
exit "$fail"
