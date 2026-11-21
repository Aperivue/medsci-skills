#!/usr/bin/env bash
# Regression test for two ways check_response_claims.py read the wrong text.
#
# 1. A response letter that reproduces each reviewer comment under a label ("Comment 3:",
#    "Reviewer #2:") instead of a blockquote. The reviewer's own words ("the authors added the
#    sentence '...'") were scanned as if the authors had claimed an edit, and reported as major.
# 2. A claimed change that lives outside the manuscript file: a new title on the title page, a
#    paragraph in the supplement. The quote was correct and was reported absent.
#
# Most cases here are negative controls. Skipping reviewer text must never skip the authors'
# own claims, so a labelled comment is skipped only up to an explicit response label; and an
# extra source must not excuse a quote that is nowhere, or that the letter placed in the main text.
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
  python3 "$V" --response "$TMP/$resp" --manuscript "$TMP/$ms" --strict --quiet \
    --out "$TMP/$name.json" "$@" > "$TMP/$name.out" 2>&1
  echo $?
}
field() {  # field <name> <python expression over d>
  python3 -c "import json,sys; d=json.load(open(sys.argv[1])); print($2)" "$TMP/$1.json"
}

cat > "$TMP/body.md" <<'MD'
## Methods
Readers were blinded to the reference standard and to each other.

## Discussion
The sample was drawn from a single centre, which limits generalisability.
MD

# The authors' absent claim used throughout: this sentence is in no file.
ABSENT='each reader completed a calibration set of fifty cases before the study'
# A reviewer's quotation of text that is not in the revised manuscript either.
RQUOTE='all readers had more than ten years of experience in thoracic imaging'

echo "==== 1. a labelled reviewer comment is not an author claim ===="
cat > "$TMP/labelled.md" <<MD
Reviewer #2:

Comment 3: In the revised Methods the authors added the sentence "$RQUOTE", but the reader
table still lists two trainees.

Response: Thank you. We removed that description and now state "Readers were blinded to the
reference standard and to each other."
MD
ck "labelled comment, then 'Response:': exit 0"                0 "$(run c1 labelled.md body.md)"
ck "  no major finding"                                        0 "$(field c1 "d['summary']['major']")"
ck "  one reviewer block reported as skipped"                  1 "$(field c1 "d['reviewer_comment_blocks_skipped']")"

# A reviewer block of several paragraphs under two labels, then the authors' absent claim.
cat > "$TMP/multi.md" <<MD
Reviewer #2:
The study is clearly presented.

The authors added the sentence "$RQUOTE", which the reader table contradicts.

Comment 2: Response to calibration was measured. The authors added the sentence "the cohort was
enrolled consecutively over three calendar years", which the flow diagram contradicts.

Response: We added the sentence "$ABSENT" to the Methods.
MD
ck "multi-paragraph reviewer block + absent author claim: exit 1" 1 "$(run c2 multi.md body.md)"
ck "  exactly one major finding"                               1 "$(field c2 "d['summary']['major']")"
ck "  and it is the authors' quote"                            True "$(field c2 "'calibration set' in d['findings'][0]['claimed_text']")"

echo "==== NEGATIVE CONTROLS: author claims are never skipped ===="
printf 'Comment 1: Please describe reader blinding.\n\nResponse: We added the sentence "%s" to the Methods.\n' "$ABSENT" > "$TMP/n1.md"
ck "claim after 'Response:': exit 1"                           1 "$(run n1 n1.md body.md)"
ck "  RESPONSE_QUOTE_UNVERIFIED"  RESPONSE_QUOTE_UNVERIFIED "$(field n1 "d['findings'][0]['verdict']")"

printf 'Comment 1: We added the sentence "%s" to the Methods.\n' "$ABSENT" > "$TMP/n2.md"
ck "authors use 'Comment 1:' as their own heading: exit 1"     1 "$(run n2 n2.md body.md)"

printf 'Comment 2.1 prompted this change. We added the sentence "%s" to the Methods.\n' "$ABSENT" > "$TMP/n3.md"
ck "'Comment 2.1 prompted ...' is prose: exit 1"               1 "$(run n3 n3.md body.md)"

printf 'Comment 1: Please clarify.\n1. Response: We added the sentence "%s" to the Methods.\n' "$ABSENT" > "$TMP/n4.md"
ck "numbered '1. Response:' on the next line: exit 1"          1 "$(run n4 n4.md body.md)"

printf 'Comment 1: Please clarify. Response: We added the sentence "%s" to the Methods.\n' "$ABSENT" > "$TMP/n5.md"
ck "'Response:' on the same line as the comment: exit 1"       1 "$(run n5 n5.md body.md)"

printf 'Reviewer 2 asked about experience, so we added the sentence "%s" to the Methods.\n' "$ABSENT" > "$TMP/n6.md"
ck "'Reviewer 2 asked ...' is prose: exit 1"                   1 "$(run n6 n6.md body.md)"

# No response label anywhere: nothing can be attributed to the reviewer, so nothing is skipped.
cat > "$TMP/n7.md" <<MD
Comment 1: The authors added the sentence "$RQUOTE", which the reader table contradicts.

We agree and have added the sentence "$ABSENT" to the Methods.
MD
ck "no response label in the letter: exit 1"                   1 "$(run n7 n7.md body.md)"
ck "  nothing skipped"                                         0 "$(field n7 "d['reviewer_comment_blocks_skipped']")"
ck "  the authors' quote is among the findings"                True "$(field n7 "any('calibration set' in f['claimed_text'] for f in d['findings'])")"

echo "==== 2. text that lives outside the manuscript file ===="
cat > "$TMP/title_page.md" <<'MD'
# Diagnostic accuracy of a synthetic index test for a synthetic target condition

Running title: Synthetic index test accuracy
MD
cat > "$TMP/supplement.md" <<MD
## Supplementary Methods
Calibration followed the approach of Okafor et al. [22] with a held-out set.
In a sensitivity analysis, $ABSENT.
MD
cat > "$TMP/elsewhere.md" <<'MD'
Response: The title now reads "Diagnostic accuracy of a synthetic index test for a synthetic
target condition". We now cite Okafor et al. [22] in the Supplementary Methods.
MD
ck "title + supplement citation, manuscript only: exit 1"      1 "$(run e1 elsewhere.md body.md)"
ck "  two major findings without the extra sources"            2 "$(field e1 "d['summary']['major']")"
ck "same letter with both extra sources: exit 0" 0 \
   "$(run e2 elsewhere.md body.md --extra-source "$TMP/title_page.md" --extra-source "$TMP/supplement.md")"
ck "  the quote is attributed to the title page"               True "$(field e2 "any(v['kind']=='quote' and v['source'].endswith('title_page.md') for v in d['verified_in_extra_source'])")"
ck "  the citation is attributed to the supplement"            True "$(field e2 "any(v['kind']=='citation' and v['source'].endswith('supplement.md') for v in d['verified_in_extra_source'])")"
ck "  exactly two claims verified in extra sources"            2 "$(field e2 "len(d['verified_in_extra_source'])")"

echo "==== NEGATIVE CONTROLS: an extra source excuses only what it contains ===="
ck "title page only: the citation is still unverified: exit 1" 1 \
   "$(run e3 elsewhere.md body.md --extra-source "$TMP/title_page.md")"
ck "  the remaining finding is the citation" RESPONSE_CITATION_UNVERIFIED "$(field e3 "d['findings'][0]['verdict']")"
ck "  one major finding"                                       1 "$(field e3 "d['summary']['major']")"

ck "absent everywhere, extra source supplied: exit 1" 1 \
   "$(run e4 n1.md body.md --extra-source "$TMP/title_page.md")"
ck "  nothing recorded as verified in an extra source"         0 "$(field e4 "len(d['verified_in_extra_source'])")"

# The letter places the sentence in the Methods; it is only in the supplement. Not excused.
ck "claimed for the Methods, present only in the supplement: exit 1" 1 \
   "$(run e5 n1.md body.md --extra-source "$TMP/supplement.md")"
ck "  nothing recorded as verified in an extra source"         0 "$(field e5 "len(d['verified_in_extra_source'])")"

# The same sentence claimed for the supplement is found there.
printf 'Response: We added the sentence "%s" to the Supplementary Methods.\n' "$ABSENT" > "$TMP/supp_claim.md"
ck "claimed for the supplement, present in the supplement: exit 0" 0 \
   "$(run e6 supp_claim.md body.md --extra-source "$TMP/supplement.md")"

echo "==== input errors ===="
ck "missing --extra-source file: exit 2" 2 \
   "$(run x1 elsewhere.md body.md --extra-source "$TMP/does_not_exist.md")"
ck "--extra-source is the response letter itself: exit 2" 2 \
   "$(run x2 n1.md body.md --extra-source "$TMP/n1.md")"
ck "--extra-source is the manuscript itself: exit 2" 2 \
   "$(run x3 n1.md body.md --extra-source "$TMP/body.md")"

echo "----"
echo "test_response_claim_sources: $pass passed, $fail failed"
[ "$fail" -eq 0 ] || { for f in $names; do echo "--- $f"; cat "$TMP/$f.out"; done; exit 1; }
