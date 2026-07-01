#!/usr/bin/env bash
# Regression test for the rounded-component vs stated-difference gate (Phase 2.5a).
# Synthetic fixtures: (bad) components 0.70/0.73 with a stated difference 0.02 (shown
# gap is 0.03) -> ROUNDED_DELTA_MISMATCH; (clean) a correct 0.03 delta, a legit
# higher-precision unrounded 0.02 delta, and an unrelated decimal pair -> no flag.
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$HERE/../scripts/check_rounded_delta.py"
BAD="$HERE/fixtures/rounded_delta_bad.md"
CLEAN="$HERE/fixtures/rounded_delta_clean.md"
OUT="$(mktemp -t rdelta_XXXX).json"
trap 'rm -f "$OUT"' EXIT
fail=0
check() { local label="$1"; shift
  if "$@" >/dev/null 2>&1; then printf '  PASS  %s\n' "$label"
  else printf '  FAIL  %s\n' "$label"; fail=$((fail+1)); fi; }
has_verdict() { python3 -c "
import json
d=json.load(open('$OUT'))
assert any(c['verdict']=='$1' for c in d['claims']), '$1 not found'
"; }
[[ -f "$SCRIPT" ]] || { echo "ENV-ERR: script missing" >&2; exit 2; }

python3 "$SCRIPT" --manuscript "$BAD" --out "$OUT" --quiet >/dev/null 2>&1
check "ROUNDED_DELTA_MISMATCH on 0.70/0.73 vs stated 0.02" has_verdict ROUNDED_DELTA_MISMATCH
check "JSON artifact written" test -s "$OUT"

python3 "$SCRIPT" --manuscript "$CLEAN" --out "$OUT" --quiet >/dev/null 2>&1
check "no mismatch on correct/unrounded/unrelated decimals" python3 -c "
import json
d=json.load(open('$OUT'))
assert not d['claims'], d['claims']
"
echo "fail=$fail"; [[ "$fail" -eq 0 ]] && echo "ALL PASS" || echo "FAILURES: $fail"
exit "$fail"
