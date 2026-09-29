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

# (direction) "18% lower than arm B" -> "18% above that of arm A": every digit survives, the
#   claim reverses. The percentage is bound to its comparator word, so the flip must fire.
DBEFORE="$HERE/fixtures/rewrite_direction_before.md"
python3 "$SCRIPT" --before "$DBEFORE" --after "$HERE/fixtures/rewrite_direction_after_flip.md" \
  --out "$OUT" --strict --quiet >/dev/null 2>&1
check "--strict exits 1 on a flipped comparison direction" test "$?" -eq 1
check "NUMBER_DRIFT names the flipped percentage (18% down -> up)" python3 -c "
import json
d=json.load(open('$OUT'))
c=[x for x in d['claims'] if x['verdict']=='NUMBER_DRIFT']
assert c and c[0]['severity']=='Major', d['claims']
toks={t['token']:(t['before'],t['after']) for t in c[0]['tokens']}
assert toks.get('18% (down)')==(1,0) and toks.get('18% (up)')==(0,1), toks
"
# (minus) a dropped leading minus (U+2212 and ASCII '-') reverses a value and must fire.
python3 "$SCRIPT" --before "$DBEFORE" --after "$HERE/fixtures/rewrite_direction_after_minus.md" \
  --out "$OUT" --strict --quiet >/dev/null 2>&1
check "--strict exits 1 when a leading minus is dropped" test "$?" -eq 1
check "NUMBER_DRIFT names both dropped minus signs (-2.4, -0.35)" python3 -c "
import json
d=json.load(open('$OUT'))
toks={t['token'] for c in d['claims'] if c['verdict']=='NUMBER_DRIFT' for t in c['tokens']}
assert {'-2.4','2.4','-0.35','0.35'} <= toks, toks
"
# Negative control: same direction in other words ("lower by 18%"), U+2212 -> ASCII '-',
# and range hyphens ("-3.1 to -1.7") -> clean.
check "same direction reworded + minus-sign normalisation stays clean" \
  python3 "$SCRIPT" --before "$DBEFORE" --after "$HERE/fixtures/rewrite_direction_after_same.md" --strict --quiet

# (context) each changed token carries one short before/after snippet, in the JSON and in the
#   printed report, so a human can tell a renumber from a changed statistic without re-reading.
python3 "$SCRIPT" --before "$BOUNDED" --after "$NUMDRIFT" --out "$OUT" --quiet >/dev/null 2>&1
check "NUMBER_DRIFT tokens carry before/after context snippets" python3 -c "
import json
d=json.load(open('$OUT'))
toks={t['token']:t for c in d['claims'] if c['verdict']=='NUMBER_DRIFT' for t in c['tokens']}
assert '78% to 91%' in (toks['91'].get('before_context') or ''), toks['91']
assert '78% to 93%' in (toks['93'].get('after_context') or ''), toks['93']
"
check "the printed report shows the context lines" bash -c "
python3 '$SCRIPT' --before '$BOUNDED' --after '$NUMDRIFT' | grep -q 'before: .*78% to 91%'
"

echo "fail=$fail"; [[ "$fail" -eq 0 ]] && echo "ALL PASS" || echo "FAILURES: $fail"
exit "$fail"
