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
count_uncited() { python3 -c "
import json
d=json.load(open('$OUT'))
n=sum(1 for c in d['claims'] if c['verdict']=='UNCITED_FLOAT')
assert n==$1, f'expected $1 UNCITED_FLOAT, got {n}'
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

# (5) YAML front matter narrating a display-item renumber ("old Table 1 -> Supplementary
#     Table S2", "old Table 3 -> Box 1") must NOT be scanned as body citations — a
#     `status:`/changelog block is not prose. Body cites Supplementary Tables and figures
#     in ascending order and has no main-text tables.
FM="$HERE/fixtures/citation_order_frontmatter.md"
python3 "$SCRIPT" --manuscript "$FM" --out "$OUT" --strict --quiet >/dev/null 2>&1
check "exit 0 with an out-of-order renumber in YAML front matter (body clean)" test "$?" -eq 0
check "no CITATION_ORDER from a front-matter changelog" count_order 0
check "no Major from a front-matter changelog" no_falsepos

# (6) A float DEFINED by a legend/caption but never cited in the narrative body ->
#     UNCITED_FLOAT (Minor). The fixture cites Table 1, Figure 1 and Supplementary Table
#     S1 (all defined and cited), and defines Supplementary Figure S1 with a full caption
#     that no sentence ever cites.
UNC="$HERE/fixtures/citation_order_uncited.md"
python3 "$SCRIPT" --manuscript "$UNC" --out "$OUT" --strict --quiet >/dev/null 2>&1
check "exit 0 (UNCITED_FLOAT is Minor, not Major)" test "$?" -eq 0
check "one UNCITED_FLOAT for the defined-but-uncited float" count_uncited 1
check "the uncited claim names Supplementary Figure S1" python3 -c "
import json
d=json.load(open('$OUT'))
u=[c for c in d['claims'] if c['verdict']=='UNCITED_FLOAT']
assert u and u[0]['where']=='Supplementary Figure S1', [c['where'] for c in u]
"
# (7) the clean fixture defines nothing uncited -> no UNCITED_FLOAT (no over-fire).
python3 "$SCRIPT" --manuscript "$GOOD" --out "$OUT" --strict --quiet >/dev/null 2>&1
check "no UNCITED_FLOAT on the clean manuscript (no over-fire)" count_uncited 0

echo "fail=$fail"; [[ "$fail" -eq 0 ]] && echo "ALL PASS" || echo "FAILURES: $fail"
exit "$fail"
