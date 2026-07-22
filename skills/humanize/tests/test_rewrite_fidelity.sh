#!/usr/bin/env bash
# Regression test for the humanize rewrite-fidelity gate.
# (bounded)   a correct de-AI pass -> no claim, even though it changed ~62% of the words;
# (wholesale) a full rewrite        -> EDIT_FOOTPRINT_HIGH only (Minor, never blocks);
# (numdrift)  a changed number and a dropped citation -> NUMBER_DRIFT + CITATION_DROP, exit 1.
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$HERE/../scripts/check_rewrite_fidelity.py"
BEFORE="$HERE/fixtures/rewrite_before.md"
BOUNDED="$HERE/fixtures/rewrite_after_bounded.md"
WHOLESALE="$HERE/fixtures/rewrite_after_wholesale.md"
NUMDRIFT="$HERE/fixtures/rewrite_after_numdrift.md"
OUT="$(mktemp -t rwfid_XXXX).json"
trap 'rm -f "$OUT"' EXIT
fail=0
check() { local label="$1"; shift
  if "$@" >/dev/null 2>&1; then printf '  PASS  %s\n' "$label"
  else printf '  FAIL  %s\n' "$label"; fail=$((fail+1)); fi; }
[[ -f "$SCRIPT" ]] || { echo "ENV-ERR: script missing" >&2; exit 2; }

python3 "$SCRIPT" --before "$BEFORE" --after "$BOUNDED" --out "$OUT" --quiet >/dev/null 2>&1
check "no claim on a correct de-AI pass (numbers + citations preserved)" python3 -c "
import json
d=json.load(open('$OUT'))
assert not d['claims'], d['claims']
assert d['detector']=='check_rewrite_fidelity', d.get('detector')
"
check "a correct de-AI pass does not block under --strict" \
  python3 "$SCRIPT" --before "$BEFORE" --after "$BOUNDED" --strict --quiet

python3 "$SCRIPT" --before "$BEFORE" --after "$WHOLESALE" --out "$OUT" --quiet >/dev/null 2>&1
check "EDIT_FOOTPRINT_HIGH on a wholesale rewrite" python3 -c "
import json
d=json.load(open('$OUT'))
c=[x for x in d['claims'] if x['verdict']=='EDIT_FOOTPRINT_HIGH']
assert c, d['claims']
assert c[0]['severity']=='Minor', c[0]
"
check "footprint alone never blocks under --strict (advisory only)" \
  python3 "$SCRIPT" --before "$BEFORE" --after "$WHOLESALE" --strict --quiet

python3 "$SCRIPT" --before "$BOUNDED" --after "$NUMDRIFT" --out "$OUT" --quiet >/dev/null 2>&1
check "NUMBER_DRIFT when a statistic changed" python3 -c "
import json
d=json.load(open('$OUT'))
assert any(c['verdict']=='NUMBER_DRIFT' and c['severity']=='Major' for c in d['claims']), d['claims']
"
check "CITATION_DROP when a citation disappeared" python3 -c "
import json
d=json.load(open('$OUT'))
assert any(c['verdict']=='CITATION_DROP' and c['severity']=='Major' for c in d['claims']), d['claims']
"
if python3 "$SCRIPT" --before "$BOUNDED" --after "$NUMDRIFT" --strict --quiet >/dev/null 2>&1; then
  printf '  FAIL  %s\n' "--strict exits 1 on an invariant violation"; fail=$((fail+1))
else
  printf '  PASS  %s\n' "--strict exits 1 on an invariant violation"
fi

echo "fail=$fail"; [[ "$fail" -eq 0 ]] && echo "ALL PASS" || echo "FAILURES: $fail"
exit "$fail"
