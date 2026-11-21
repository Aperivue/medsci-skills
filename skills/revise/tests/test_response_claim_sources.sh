#!/usr/bin/env bash
# Regression test for two ways check_response_claims.py read the wrong text.
#
# 1. A response letter that reproduces each reviewer comment under a label ("Comment 3:",
#    "Reviewer #2:") instead of a blockquote. The reviewer's own words ("the authors added the
#    sentence '...'") were scanned as if the authors had claimed an edit, and reported as major.
# 2. A claimed change that lives outside the manuscript file: a new title on the title page, a
#    paragraph in the supplement. The quote was correct and was reported absent.
#
# The negative controls matter more than the positives: skipping reviewer text must not skip
# the authors' own claims, and an extra source must not excuse a quote that is nowhere.
set -u

REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
V="$REPO_ROOT/skills/revise/scripts/check_response_claims.py"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

pass=0
fail=0
ck() {
  local label="$1" expected="$2" actual="$3"
  if [ "$expected" = "$actual" ]; then
    printf '  PASS  %-64s %s\n' "$label" "$actual"
    pass=$((pass + 1))
  else
    printf '  FAIL  %-64s expected=%s actual=%s\n' "$label" "$expected" "$actual"
    fail=$((fail + 1))
  fi
}
run() {  # run <name> <response> <manuscript> [extra args...] -> exit code; JSON at $TMP/<name>.json
  local name="$1" resp="$2" ms="$3"; shift 3
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

# --- 1. reviewer comment under a label, response under a label -------------------------------
cat > "$TMP/labelled.md" <<'MD'
Reviewer #2

Comment 3: In the revised Methods the authors added the sentence "all readers had more than
ten years of experience in thoracic imaging", but the reader table still lists two trainees.

Response: Thank you. We removed that description and now state "Readers were blinded to the
reference standard and to each other."
MD
ck "labelled reviewer comment is not an author claim: exit 0"  0 "$(run c1 labelled.md body.md)"
ck "  no major finding"                                        0 "$(field c1 "d['summary']['major']")"
ck "  one reviewer block reported as skipped"                  1 "$(field c1 "d['reviewer_comment_blocks_skipped']")"

# --- NEGATIVE: the authors' own claim after the response label is still checked ---------------
cat > "$TMP/author_claim.md" <<'MD'
Comment 1: Please describe reader blinding.

Response: We added the sentence "each reader completed a calibration set of fifty cases before
the study" to the Methods.
MD
ck "author claim after 'Response:' is still checked: exit 1"   1 "$(run c2 author_claim.md body.md)"
ck "  RESPONSE_QUOTE_UNVERIFIED"  RESPONSE_QUOTE_UNVERIFIED "$(field c2 "d['findings'][0]['verdict']")"

# --- NEGATIVE: no response labels anywhere -> only the labelled paragraph is skipped ----------
cat > "$TMP/unlabelled.md" <<'MD'
Comment 1: The authors added the sentence "the cohort was enrolled consecutively over three
calendar years", which is not what the flow diagram shows.

We agree and have added the sentence "each reader completed a calibration set of fifty cases
before the study" to the Methods.
MD
ck "letter without response labels: author paragraph checked: exit 1" 1 "$(run c3 unlabelled.md body.md)"
ck "  exactly one major finding (the authors' quote)"          1 "$(field c3 "d['summary']['major']")"
ck "  and it is the authors' quote, not the reviewer's"        True "$(field c3 "'calibration set' in d['findings'][0]['claimed_text']")"

# --- NEGATIVE: prose that names a reviewer is not a label -------------------------------------
cat > "$TMP/prose.md" <<'MD'
Reviewer 2 asked about experience, so we added the sentence "each reader completed a calibration
set of fifty cases before the study" to the Methods.
MD
ck "'Reviewer 2 asked ...' is prose, still checked: exit 1"    1 "$(run c4 prose.md body.md)"

# --- 2. text that lives outside the manuscript file -------------------------------------------
cat > "$TMP/title_page.md" <<'MD'
# Diagnostic accuracy of a synthetic index test for a synthetic target condition

Running title: Synthetic index test accuracy
MD
cat > "$TMP/supplement.md" <<'MD'
## Supplementary Methods
Calibration followed the approach of Okafor et al. [22] with a held-out set.
MD
cat > "$TMP/elsewhere.md" <<'MD'
Response: The title now reads "Diagnostic accuracy of a synthetic index test for a synthetic
target condition". We now cite Okafor et al. [22] in the Supplementary Methods.
MD
ck "title and supplement citation, manuscript only: exit 1"    1 "$(run c5 elsewhere.md body.md)"
ck "  two major findings without the extra sources"            2 "$(field c5 "d['summary']['major']")"
ck "same letter with both extra sources: exit 0" 0 \
   "$(run c6 elsewhere.md body.md --extra-source "$TMP/title_page.md" --extra-source "$TMP/supplement.md")"
ck "  both claims recorded as verified in an extra source"     2 "$(field c6 "len(d['verified_in_extra_source'])")"
ck "  the quote is attributed to the title page"               True "$(field c6 "any(v['kind']=='quote' and v['source'].endswith('title_page.md') for v in d['verified_in_extra_source'])")"

# --- NEGATIVE: an extra source does not excuse a quote that is nowhere ------------------------
ck "absent everywhere, extra source supplied: exit 1" 1 \
   "$(run c7 author_claim.md body.md --extra-source "$TMP/title_page.md")"
ck "  nothing recorded as verified in an extra source"         0 "$(field c7 "len(d['verified_in_extra_source'])")"

# --- a missing extra source is an input error, not a silent skip ------------------------------
ck "missing --extra-source file: exit 2" 2 \
   "$(run c8 elsewhere.md body.md --extra-source "$TMP/does_not_exist.md")"

echo "----"
echo "test_response_claim_sources: $pass passed, $fail failed"
[ "$fail" -eq 0 ] || { for f in c1 c2 c3 c4 c5 c6 c7 c8; do echo "--- $f"; cat "$TMP/$f.out"; done; exit 1; }
