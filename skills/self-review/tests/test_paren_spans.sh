#!/usr/bin/env bash
# Regression test for the parenthesis-span corruption gate (post em-dash reduction).
# Synthetic, PII-free fixtures: a manuscript where an em-dash→paren conversion
# wrapped an ordinal limitation ("Sixth, …") and a whole sentence inside parens
# (paren-balanced but broken), and a clean manuscript with only legitimate short
# parentheticals (CIs, citations, "Dr. Smith", "Fig. 2"). Stdlib-only (python3).
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$HERE/../scripts/check_paren_spans.py"
BAD="$HERE/fixtures/paren_corrupt.md"
CLEAN="$HERE/fixtures/paren_clean.md"
OUT="$(mktemp -t paren_XXXX).json"
trap 'rm -f "$OUT"' EXIT

fail=0
check() { local label="$1"; shift
    if "$@" >/dev/null 2>&1; then printf '  PASS  %s\n' "$label"
    else printf '  FAIL  %s\n' "$label"; fail=$((fail+1)); fi
}
has_verdict() { python3 -c "
import json,sys
d=json.load(open('$OUT'))
assert any(c['verdict']=='$1' for c in d['claims']), '$1 not found'
"; }

[[ -f "$SCRIPT" ]] || { echo "ENV-ERR: script missing" >&2; exit 2; }

# (1) corrupt manuscript -> ordinal + sentence span, exit 1
python3 "$SCRIPT" --manuscript "$BAD" --out "$OUT" --strict --quiet >/dev/null 2>&1
check "exit 1 under --strict (corruption present)" test "$?" -eq 1
check "PAREN_SPAN_ORDINAL detected"  has_verdict PAREN_SPAN_ORDINAL
check "PAREN_SPAN_SENTENCE detected" has_verdict PAREN_SPAN_SENTENCE

# (2) clean manuscript: short legitimate parentheticals only -> exit 0, no false positive
python3 "$SCRIPT" --manuscript "$CLEAN" --strict --quiet >/dev/null 2>&1
check "exit 0 on clean manuscript (no false positive on CI/citation/Dr./Fig. parens)" test "$?" -eq 0

echo "fail=$fail"; [[ "$fail" -eq 0 ]] && echo "ALL PASS" || echo "FAILURES: $fail"
exit "$fail"
