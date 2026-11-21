#!/usr/bin/env bash
# Regression test for check_response_claims.py --extra-source.
#
# A claimed change does not always live in the manuscript file: a new title sits on the title
# page, a paragraph in the supplement. The quote was correct and was reported absent, as major.
# With --extra-source, text that is absent from the manuscript and present WORD FOR WORD in a
# named file is reported as minor, with the file named, for a human to confirm.
#
# The negative controls pin what an extra source must not do: excuse text that is nowhere,
# excuse a near match, excuse a citation the file does not contain, or be the letter itself.
set -u

REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
V="$REPO_ROOT/skills/revise/scripts/check_response_claims.py"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

pass=0
fail=0
names=""
ck() {
  local label="$1" expected="$2" actual="$3"
  if [ "$expected" = "$actual" ]; then
    printf '  PASS  %-66s %s\n' "$label" "$actual"
    pass=$((pass + 1))
  else
    printf '  FAIL  %-66s expected=%s actual=%s\n' "$label" "$expected" "$actual"
    fail=$((fail + 1))
  fi
}
run() {  # run <name> <response> <manuscript> [extra args...] -> exit code; JSON at $TMP/<name>.json
  local name="$1" resp="$2" ms="$3"; shift 3
  names="$names $name"
  rm -f "$TMP/$name.json"
  python3 "$V" --response "$TMP/$resp" --manuscript "$TMP/$ms" --strict \
    --out "$TMP/$name.json" "$@" > "$TMP/$name.out" 2>&1
  echo $?
}
field() {  # field <name> <python expression over d>; prints NOJSON when the run wrote none
  [ -f "$TMP/$1.json" ] || { echo NOJSON; return; }
  python3 -c "import json,sys; d=json.load(open(sys.argv[1])); print($2)" "$TMP/$1.json"
}
verdicts() { field "$1" "','.join(sorted(f['verdict'] for f in d['findings']))"; }

cat > "$TMP/body.md" <<'MD'
## Methods
Readers were blinded to the reference standard and to each other.

## Discussion
The sample was drawn from a single centre, which limits generalisability.
MD
cat > "$TMP/title_page.md" <<'MD'
# Diagnostic accuracy of a synthetic index test for a synthetic target condition

Running title: Synthetic index test accuracy
MD
cat > "$TMP/supplement.md" <<'MD'
## Supplementary Methods
Calibration followed the approach of Okafor et al. [22] with a held-out set.
Each reader independently reviewed all fifty eligible calibration cases before enrollment.
MD
cat > "$TMP/elsewhere.md" <<'MD'
The title now reads "Diagnostic accuracy of a synthetic index test for a synthetic
target condition". We now cite Okafor et al. [22] in the Supplementary Methods.
MD

echo "==== text that lives outside the manuscript file ===="
ck "title + supplement citation, manuscript only: exit 1"      1 "$(run e1 elsewhere.md body.md)"
ck "  both are major without the extra sources" \
   "RESPONSE_CITATION_UNVERIFIED,RESPONSE_QUOTE_UNVERIFIED" "$(verdicts e1)"
ck "same letter with both extra sources: exit 0" 0 \
   "$(run e2 elsewhere.md body.md --extra-source "$TMP/title_page.md" --extra-source "$TMP/supplement.md")"
ck "  both are reported as found in an extra source" \
   "RESPONSE_CITATION_IN_EXTRA_SOURCE,RESPONSE_QUOTE_IN_EXTRA_SOURCE" "$(verdicts e2)"
ck "  both are minor, none major"                              0 "$(field e2 "d['summary']['major']")"
ck "  summary counts them apart from extraction doubts"        2,0 "$(field e2 "str(d['summary']['in_extra_source'])+','+str(d['summary']['unresolved'])")"
ck "  the quote names the title page"                          True "$(field e2 "[f['source'].endswith('title_page.md') for f in d['findings'] if f['verdict']=='RESPONSE_QUOTE_IN_EXTRA_SOURCE']==[True]")"
ck "  the citation names the supplement"                       True "$(field e2 "[f['source'].endswith('supplement.md') for f in d['findings'] if f['verdict']=='RESPONSE_CITATION_IN_EXTRA_SOURCE']==[True]")"
ck "  the title page path is printed"                          1 "$(grep -c "present word for word in .*title_page.md" "$TMP/e2.out")"
ck "  the supplement path is printed"                          1 "$(grep -c "found in .*supplement.md" "$TMP/e2.out")"

echo "==== NEGATIVE CONTROLS: an extra source excuses only what it contains ===="
ck "title page only: exit 1" 1 \
   "$(run n1 elsewhere.md body.md --extra-source "$TMP/title_page.md")"
ck "  the citation stays major, the quote is found" \
   "RESPONSE_CITATION_UNVERIFIED,RESPONSE_QUOTE_IN_EXTRA_SOURCE" "$(verdicts n1)"

# A sentence that is in no file. The claim names no place, so the extra source IS searched.
printf 'We added the sentence "each reader completed a calibration set of fifty cases before the study".\n' > "$TMP/nowhere.md"
ck "absent everywhere, both extra sources supplied: exit 1" 1 \
   "$(run n2 nowhere.md body.md --extra-source "$TMP/title_page.md" --extra-source "$TMP/supplement.md")"
ck "  still RESPONSE_QUOTE_UNVERIFIED"  RESPONSE_QUOTE_UNVERIFIED "$(verdicts n2)"

# A near match in the extra source (one word differs) does not excuse the claim.
printf 'We added the sentence "Each reader independently reviewed all fifty calibration cases before enrollment".\n' > "$TMP/near.md"
ck "near match in the extra source: exit 1" 1 \
   "$(run n3 near.md body.md --extra-source "$TMP/supplement.md")"
ck "  still RESPONSE_QUOTE_UNVERIFIED"  RESPONSE_QUOTE_UNVERIFIED "$(verdicts n3)"

# A quote that IS in the manuscript is verified there; the extra source adds no finding.
printf 'We now state "Readers were blinded to the reference standard and to each other."\n' > "$TMP/inbody.md"
ck "quote present in the manuscript: exit 0" 0 \
   "$(run n4 inbody.md body.md --extra-source "$TMP/supplement.md")"
ck "  no finding at all"                                       0 "$(field n4 "len(d['findings'])")"

# The same letter against a manuscript without that sentence: the claim IS extracted and fires.
printf '## Methods\nReaders were blinded.\n' > "$TMP/body_without.md"
ck "the same quote, absent from the manuscript: exit 1"        1 "$(run n5 inbody.md body_without.md)"
ck "  RESPONSE_QUOTE_UNVERIFIED"  RESPONSE_QUOTE_UNVERIFIED "$(verdicts n5)"

# The supplement has reference [22] under another author: the claimed citation is not there.
printf '## Supplementary Methods\nCalibration followed Smith et al. [22].\n' > "$TMP/supp_other.md"
printf 'We now cite Okafor et al. [22] in the Supplementary Methods.\n' > "$TMP/cite.md"
ck "the number matches, the author does not: exit 1" 1 \
   "$(run n6 cite.md body.md --extra-source "$TMP/supp_other.md")"
ck "  RESPONSE_CITATION_UNVERIFIED"  RESPONSE_CITATION_UNVERIFIED "$(verdicts n6)"

echo "==== input errors ===="
ck "missing --extra-source file: exit 2" 2 \
   "$(run x1 elsewhere.md body.md --extra-source "$TMP/does_not_exist.md")"
ck "--extra-source is the response letter itself: exit 2" 2 \
   "$(run x2 nowhere.md body.md --extra-source "$TMP/nowhere.md")"
ck "--extra-source is the manuscript itself: exit 2" 2 \
   "$(run x3 nowhere.md body.md --extra-source "$TMP/body.md")"
ck "  and no report is written for an input error"             NOJSON "$(field x2 "1")"
# --out must not be an input: the report would overwrite the evidence it just read.
cp "$TMP/supplement.md" "$TMP/supp_copy.md"
python3 "$V" --response "$TMP/elsewhere.md" --manuscript "$TMP/body.md" \
  --extra-source "$TMP/supp_copy.md" --out "$TMP/supp_copy.md" > "$TMP/x4.out" 2>&1
ck "--out names an input file: exit 2"                         2 "$?"
ck "  and the input file is untouched"                         same "$(cmp -s "$TMP/supplement.md" "$TMP/supp_copy.md" && echo same || echo changed)"

echo "----"
echo "test_response_claim_sources: $pass passed, $fail failed"
[ "$fail" -eq 0 ] || { for f in $names; do echo "--- $f"; cat "$TMP/$f.out"; done; exit 1; }
