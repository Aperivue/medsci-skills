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
echo "fail=$fail"; [[ "$fail" -eq 0 ]] && echo "ALL PASS" || echo "FAILURES: $fail"
exit "$fail"
