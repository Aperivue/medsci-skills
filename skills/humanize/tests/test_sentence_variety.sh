#!/usr/bin/env bash
# Regression test for the sentence-length variety gate (humanize SKILL.md Fix rule 7).
# (uniform) every sentence in the middle band, no long ones -> SENTENCE_UNIFORM;
# (mixed)   both short (<=12) and long (>=25) bands populated -> no claim;
# (short)   a text below --min-sentences is skipped rather than judged.
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$HERE/../scripts/check_sentence_variety.py"
UNIFORM="$HERE/fixtures/variety_uniform.md"
MIXED="$HERE/fixtures/variety_mixed.md"
OUT="$(mktemp -t svar_XXXX).json"
SHORT="$(mktemp -t svarshort_XXXX).md"
trap 'rm -f "$OUT" "$SHORT"' EXIT
fail=0
check() { local label="$1"; shift
  if "$@" >/dev/null 2>&1; then printf '  PASS  %s\n' "$label"
  else printf '  FAIL  %s\n' "$label"; fail=$((fail+1)); fi; }
[[ -f "$SCRIPT" ]] || { echo "ENV-ERR: script missing" >&2; exit 2; }

python3 "$SCRIPT" --manuscript "$UNIFORM" --out "$OUT" --quiet >/dev/null 2>&1
check "SENTENCE_UNIFORM when no long sentences exist" python3 -c "
import json
d=json.load(open('$OUT'))
c=[x for x in d['claims'] if x['verdict']=='SENTENCE_UNIFORM']
assert c, d['claims']
assert c[0]['missing_band']=='long', c[0]
assert d['detector']=='check_sentence_variety', d.get('detector')
"
python3 "$SCRIPT" --manuscript "$MIXED" --out "$OUT" --quiet >/dev/null 2>&1
check "no claim when both bands are populated" python3 -c "
import json
d=json.load(open('$OUT'))
assert not d['claims'], d['claims']
assert d['stats']['short_count'] > 0 and d['stats']['long_count'] > 0, d['stats']
"
check "decimals and abbreviations do not split a sentence" python3 -c "
import json
d=json.load(open('$OUT'))
# 'R 4.3.1' and 'et al.' appear in the mixed fixture; a naive splitter inflates the count.
assert d['stats']['sentences'] < 25, d['stats']
"
printf 'One short line. Another one here. A third.\n' > "$SHORT"
python3 "$SCRIPT" --manuscript "$SHORT" --out "$OUT" --quiet >/dev/null 2>&1
check "a text below --min-sentences is skipped, not judged" python3 -c "
import json
d=json.load(open('$OUT'))
assert not d['claims'], d['claims']
assert 'skipped' in d['stats'], d['stats']
"
# Rule 7 names a RANGE and this gate only ever checked its lower edge: a single 97-word
# sentence populates the ">= 25 words" band, so the check passed while printing max_words: 97
# in its own stats. Two external reviewers read such prose as machine-written on two different
# manuscripts while the detector returned nothing.
OL="$HERE/fixtures/variety_overlong.md"
python3 "$SCRIPT" --manuscript "$OL" --out "$OUT" --quiet >/dev/null 2>&1
check "a 97-word sentence fires SENTENCE_OVERLONG" python3 -c "
import json
d=json.load(open('$OUT'))
c=[x for x in d['claims'] if x['verdict']=='SENTENCE_OVERLONG']
assert c, d['claims']
assert c[0]['word_counts']==[97], c[0]
"
check "...and the band check still says the prose is varied" python3 -c "
import json
d=json.load(open('$OUT'))
assert not [x for x in d['claims'] if x['verdict']=='SENTENCE_UNIFORM'], d['claims']
"
check "...and it stays Minor: --strict does not fail the build" test "$(python3 "$SCRIPT" --manuscript "$OL" --strict >/dev/null 2>&1; echo $?)" -eq 0

# The bound has to be a bound, not a synonym for "long". Same text, longest sentence at 64
# words -- over rule 7's band of 25-35, under the 70 ceiling -- must stay silent, or the
# verdict would just be re-reporting the long band it already checks.
WB="$HERE/fixtures/variety_long_within_bound.md"
python3 "$SCRIPT" --manuscript "$WB" --out "$OUT" --quiet >/dev/null 2>&1
check "a 64-word sentence does NOT fire (over rule 7's band, under the ceiling)" python3 -c "
import json
d=json.load(open('$OUT'))
assert not [x for x in d['claims'] if x['verdict']=='SENTENCE_OVERLONG'], d['claims']
"
check "...and the count over rule 7's band is reported, not judged" python3 -c "
import json
d=json.load(open('$OUT'))
assert d['stats']['over_rule7_band_count'] >= 1, d['stats']
assert not d['claims'], d['claims']
"
# The threshold is configurable, and lowering it must actually change the answer -- otherwise
# the default could be doing nothing and every assertion above would still pass.
python3 "$SCRIPT" --manuscript "$WB" --out "$OUT" --long-max 50 --quiet >/dev/null 2>&1
check "--long-max 50 makes the same 64-word sentence fire" python3 -c "
import json
d=json.load(open('$OUT'))
assert [x for x in d['claims'] if x['verdict']=='SENTENCE_OVERLONG'], d['claims']
"

echo "fail=$fail"; [[ "$fail" -eq 0 ]] && echo "ALL PASS" || echo "FAILURES: $fail"
exit "$fail"
