#!/usr/bin/env bash
# Regression test for the classical-style body lint (self-review §J).
# Synthetic, PII-free fixtures reproduce: a § symbol self-reference + an in-body
# AI-disclosure paragraph (both Major), eligibility prose, and mixed OR/HR decimals
# (Minor). The clean fixture uses a numbered eligibility list, consistent decimals,
# no § symbol, and no in-body disclosure.
# Stdlib-only (python3).
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$HERE/../scripts/check_classical_style.py"
BAD="$HERE/fixtures/style_bad.md"
CLEAN="$HERE/fixtures/style_clean.md"
OUT="$(mktemp -t style_XXXX).json"
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

# (1) bad manuscript: Major (§ + in-body disclosure) -> exit 1
python3 "$SCRIPT" --manuscript "$BAD" --out "$OUT" --strict --quiet >/dev/null 2>&1
check "exit 1 under --strict (Major present)" test "$?" -eq 1
check "JSON artifact written" test -s "$OUT"
check "SECTION_SYMBOL detected"        has_verdict SECTION_SYMBOL
check "INBODY_AI_DISCLOSURE detected"  has_verdict INBODY_AI_DISCLOSURE
check "ELIGIBILITY_PROSE detected"     has_verdict ELIGIBILITY_PROSE
check "DECIMAL_INCONSISTENCY detected" has_verdict DECIMAL_INCONSISTENCY
check "PERCENT_DECIMALS detected (35.14%, 96.12%)" has_verdict PERCENT_DECIMALS

# (2) clean manuscript: numbered eligibility, consistent decimals, no §/disclosure,
#     no >1-dp percentages -> exit 0
python3 "$SCRIPT" --manuscript "$CLEAN" --strict --quiet >/dev/null 2>&1
check "exit 0 on clean manuscript" test "$?" -eq 0
python3 "$SCRIPT" --manuscript "$CLEAN" --out "$OUT" --quiet >/dev/null 2>&1
check "no PERCENT_DECIMALS false positive on clean manuscript" python3 -c "
import json
d=json.load(open('$OUT'))
assert not any(c['verdict']=='PERCENT_DECIMALS' for c in d['claims']), 'PERCENT_DECIMALS false positive'
"

# (3) structural em-dashes (table cells, ORCID, author/affiliation, panel labels)
#     must NOT count toward the prose threshold. With --em-dash-max 0, the fixture's
#     ~9 structural dashes are excluded and its prose has 0 → no EM_DASH_OVERUSE.
STRUCT="$HERE/fixtures/style_emdash_structural.md"
python3 "$SCRIPT" --manuscript "$STRUCT" --em-dash-max 0 --out "$OUT" --quiet >/dev/null 2>&1
check "structural em-dashes excluded (no EM_DASH_OVERUSE at max 0)" python3 -c "
import json
d=json.load(open('$OUT'))
assert not any(c['verdict']=='EM_DASH_OVERUSE' for c in d['claims']), 'structural dashes were counted as prose'
"

# (4) § used as author/affiliation footnote dagger (co-senior-author line, super-
#     script markers) must NOT fire SECTION_SYMBOL — only a § section cross-ref does.
DAGGER="$HERE/fixtures/style_dagger_footnote.md"
python3 "$SCRIPT" --manuscript "$DAGGER" --out "$OUT" --quiet >/dev/null 2>&1
check "no SECTION_SYMBOL on footnote daggers" python3 -c "
import json
d=json.load(open('$OUT'))
assert not any(c['verdict']=='SECTION_SYMBOL' for c in d['claims']), 'dagger § flagged as section symbol'
"
python3 "$SCRIPT" --manuscript "$DAGGER" --strict --quiet >/dev/null 2>&1
check "exit 0 on dagger-footnote manuscript" test "$?" -eq 0

echo "fail=$fail"; [[ "$fail" -eq 0 ]] && echo "ALL PASS" || echo "FAILURES: $fail"
exit "$fail"
