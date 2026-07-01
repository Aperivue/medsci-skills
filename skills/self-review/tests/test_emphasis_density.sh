#!/usr/bin/env bash
# Regression test for the inline-emphasis over-use gate (§J / humanize P25).
# (overuse) a paragraph with single-word + whole-clause italics -> EMPHASIS_OVERUSE;
# (clean) only allowlisted italics (P value, in vitro/in vivo, BRCA1, t) -> no flag.
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$HERE/../scripts/check_emphasis_density.py"
BAD="$HERE/fixtures/emphasis_overuse.md"
CLEAN="$HERE/fixtures/emphasis_clean.md"
OUT="$(mktemp -t emph_XXXX).json"
trap 'rm -f "$OUT"' EXIT
fail=0
check() { local label="$1"; shift
  if "$@" >/dev/null 2>&1; then printf '  PASS  %s\n' "$label"
  else printf '  FAIL  %s\n' "$label"; fail=$((fail+1)); fi; }
[[ -f "$SCRIPT" ]] || { echo "ENV-ERR: script missing" >&2; exit 2; }

python3 "$SCRIPT" --manuscript "$BAD" --out "$OUT" --quiet >/dev/null 2>&1
check "EMPHASIS_OVERUSE on over-italicised prose" python3 -c "
import json
d=json.load(open('$OUT'))
assert any(c['verdict']=='EMPHASIS_OVERUSE' for c in d['claims']), 'not flagged'
"
python3 "$SCRIPT" --manuscript "$CLEAN" --out "$OUT" --quiet >/dev/null 2>&1
check "no flag when only allowlisted italics (P/in vitro/BRCA1/t)" python3 -c "
import json
d=json.load(open('$OUT'))
assert not d['claims'], d['claims']
"
echo "fail=$fail"; [[ "$fail" -eq 0 ]] && echo "ALL PASS" || echo "FAILURES: $fail"
exit "$fail"
