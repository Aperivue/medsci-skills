#!/usr/bin/env bash
# Regression test for the float citation-ORDER gate (journal technical-check pass).
# Synthetic, PII-free fixtures: a manuscript whose main Tables (3,1,2,4) and
# supplementary Tables (S4,S9,S16,S12,S6,S2) are cited out of numerical order, and
# a clean manuscript where every series is cited in ascending order (incl. a plural
# list "Tables S4, S5", a back-matter legends block that must be excluded, and a
# non-float "S1 through S6" sensitivity label that must NOT be parsed as tables).
# Stdlib-only (python3).
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$HERE/../scripts/check_citation_order.py"
BAD="$HERE/fixtures/citation_order_bad.md"
GOOD="$HERE/fixtures/citation_order_good.md"
OUT="$(mktemp -t citorder_XXXX).json"
trap 'rm -f "$OUT"' EXIT

fail=0
check() { local label="$1"; shift
    if "$@" >/dev/null 2>&1; then printf '  PASS  %s\n' "$label"
    else printf '  FAIL  %s\n' "$label"; fail=$((fail+1)); fi
}
count_order() { python3 -c "
import json
d=json.load(open('$OUT'))
n=sum(1 for c in d['claims'] if c['verdict']=='CITATION_ORDER')
assert n==$1, f'expected $1 CITATION_ORDER, got {n}'
"; }
no_falsepos() { python3 -c "
import json
d=json.load(open('$OUT'))
assert d['summary']['n_major']==0, d['summary']
"; }

[[ -f "$SCRIPT" ]] || { echo "ENV-ERR: script missing" >&2; exit 2; }

# (1) out-of-order manuscript -> 2 CITATION_ORDER (main Table + Suppl Table), exit 1
python3 "$SCRIPT" --manuscript "$BAD" --out "$OUT" --strict --quiet >/dev/null 2>&1
check "exit 1 under --strict (out-of-order present)" test "$?" -eq 1
check "2 CITATION_ORDER series flagged (Table + Supplementary Table)" count_order 2

# (2) clean manuscript: ascending order, plural list, excluded legends, S1-S6 label
python3 "$SCRIPT" --manuscript "$GOOD" --out "$OUT" --strict --quiet >/dev/null 2>&1
check "exit 0 on clean manuscript (no false positive)" test "$?" -eq 0
check "no Major on clean manuscript" no_falsepos

# (3) DANGLING_SECTION_XREF: "Section 3.4"/"Section 3" refs with UNNUMBERED headings -> Major
SBAD="$HERE/fixtures/citation_order_section_bad.md"
python3 "$SCRIPT" --manuscript "$SBAD" --out "$OUT" --strict --quiet >/dev/null 2>&1
check "exit 1 on Section-refs with unnumbered headings" test "$?" -eq 1
check "DANGLING_SECTION_XREF flagged" python3 -c "
import json
d=json.load(open('$OUT'))
assert any(c['verdict']=='DANGLING_SECTION_XREF' for c in d['claims']), 'not flagged'
"
# (4) numbered headings resolve the refs, and 'Supplementary Section 5' is exempt -> silent
SGOOD="$HERE/fixtures/citation_order_section_good.md"
python3 "$SCRIPT" --manuscript "$SGOOD" --out "$OUT" --strict --quiet >/dev/null 2>&1
check "exit 0 when Section refs resolve to numbered headings" test "$?" -eq 0
check "no DANGLING_SECTION_XREF when headings are numbered" python3 -c "
import json
d=json.load(open('$OUT'))
assert not any(c['verdict']=='DANGLING_SECTION_XREF' for c in d['claims']), 'false positive'
"

echo "fail=$fail"; [[ "$fail" -eq 0 ]] && echo "ALL PASS" || echo "FAILURES: $fail"
exit "$fail"
