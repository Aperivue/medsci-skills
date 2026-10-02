#!/usr/bin/env bash
# Regression test for skills/revise/scripts/check_response_claims.py — the
# response-letter <-> revised-manuscript verification gate. Confirms an anchored
# claim absent from the body fails under --strict, a present one passes, and the
# false-positive guards (vague claims, reviewer blockquotes) do not fire.
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
    printf '  PASS  %-52s exit=%s\n' "$label" "$actual"
    pass=$((pass + 1))
  else
    printf '  FAIL  %-52s expected=%s actual=%s\n' "$label" "$expected" "$actual"
    fail=$((fail + 1))
  fi
}

# --- manuscript that DOES contain the added sentence + citation ---
cat > "$TMP/body_good.md" <<'MD'
## Methods
Diabetes was defined by a fasting glucose of at least 126 mg/dL or medication use.

## Discussion
Dosing errors are a recognized hazard in this setting, as Tariq et al. [15] reported.
MD

# --- manuscript that is MISSING both ---
cat > "$TMP/body_bad.md" <<'MD'
## Methods
Baseline characteristics were summarized descriptively.

## Discussion
The findings are consistent with prior work.
MD

# --- response letter with an anchored quote claim + a citation claim ---
cat > "$TMP/response.md" <<'MD'
**Comment 1.**
> The Methods do not define diabetes.

**Response 1.** Thank you. We added the sentence "Diabetes was defined by a fasting glucose of at least 126 mg/dL or medication use." to the Methods.

**Comment 2.**
> Please acknowledge dosing-error risk.

**Response 2.** We now cite Tariq et al. [15] in the Discussion.
MD

# --- response with only a VAGUE claim (no quote, no citation) ---
cat > "$TMP/response_vague.md" <<'MD'
**Response.** We clarified the Methods and revised the Introduction for readability.
MD

# --- response whose ONLY unverifiable quote is inside a reviewer blockquote ---
cat > "$TMP/response_reviewerquote.md" <<'MD'
**Comment 1.**
> The authors claim "a mortality reduction of ninety percent" without support.

**Response 1.** We have tempered this statement and now report the observed range only.
MD

# 1) anchored claims absent from body -> exit 1 (--strict)
python3 "$V" --response "$TMP/response.md" --manuscript "$TMP/body_bad.md" --strict > /dev/null 2>&1
ck "missing added quote + citation fails (--strict)" 1 "$?"

# 2) same claims present in body -> exit 0
python3 "$V" --response "$TMP/response.md" --manuscript "$TMP/body_good.md" --strict > /dev/null 2>&1
ck "verified quote + citation passes (--strict)" 0 "$?"

# 3) vague claim (no anchor) -> not flagged, exit 0
python3 "$V" --response "$TMP/response_vague.md" --manuscript "$TMP/body_bad.md" --strict > /dev/null 2>&1
ck "vague unanchored claim not flagged" 0 "$?"

# 4) reviewer-blockquote quote (not an author addition) -> not flagged, exit 0
python3 "$V" --response "$TMP/response_reviewerquote.md" --manuscript "$TMP/body_bad.md" --strict > /dev/null 2>&1
ck "reviewer blockquote quote not flagged" 0 "$?"

# 5) drift reported but tolerated without --strict -> exit 0
python3 "$V" --response "$TMP/response.md" --manuscript "$TMP/body_bad.md" > /dev/null 2>&1
ck "drift tolerated without --strict" 0 "$?"

# 6) the flagged verdicts are the expected two
OUT="$(python3 "$V" --response "$TMP/response.md" --manuscript "$TMP/body_bad.md" 2>&1)"
echo "$OUT" | grep -q RESPONSE_QUOTE_UNVERIFIED && echo "$OUT" | grep -q RESPONSE_CITATION_UNVERIFIED
ck "both expected verdicts present" 0 "$?"

# --- extraction tolerance: a CORRECT quote must survive a dirty extraction ---------------
# Each manuscript below really does contain the claimed sentence; the variants are what an
# extractor emits, not what the author wrote. A contiguous substring test calls every one of
# them "absent" — the false-positive class that once nearly had accurate quotes deleted.
cat > "$TMP/resp_quote.md" <<'MD'
**Response 1.** We added the sentence "learners form independent assessments before seeing AI output" to the Discussion.
MD

# (a) two-column PDF: a reference line bled into the middle of the sentence
cat > "$TMP/body_bleed.md" <<'MD'
## Discussion
We note that learners form independent civile. Rev Med Suisse 2019;15:1122. assessments before seeing AI output.
MD
# (b) line-numbered supplement PDF: line numbers sit inside the sentence
cat > "$TMP/body_linenum.md" <<'MD'
## Discussion
86 We note that learners form 87 independent assessments 88 before seeing AI output.
MD
# (c) a superscript / footnote marker landed mid-clause
cat > "$TMP/body_supersc.md" <<'MD'
## Discussion
learners form independent 3 assessments before seeing AI output
MD
# (d) hyphenation across a line break split one word in two
cat > "$TMP/body_hyphen.md" <<'MD'
## Discussion
learners form independent assess-
ments before seeing AI output
MD

for variant in bleed linenum supersc hyphen; do
  python3 "$V" --response "$TMP/resp_quote.md" --manuscript "$TMP/body_$variant.md" --strict > /dev/null 2>&1
  ck "dirty extraction ($variant) is not drift (--strict)" 0 "$?"
done

# the interleaved variants must SAY so (unresolved), not pass silently
for variant in bleed linenum supersc; do
  python3 "$V" --response "$TMP/resp_quote.md" --manuscript "$TMP/body_$variant.md" 2>&1 \
    | grep -q RESPONSE_QUOTE_UNRESOLVED
  ck "dirty extraction ($variant) reports UNRESOLVED" 0 "$?"
done

# the hyphen split is repaired outright -> no finding at all
python3 "$V" --response "$TMP/resp_quote.md" --manuscript "$TMP/body_hyphen.md" 2>&1 \
  | grep -q RESPONSE_QUOTE
ck "line-break hyphenation repaired (no finding)" 1 "$?"

# PRECISION GUARD: tolerance must not excuse a genuine miss. The words below appear in
# order but scattered a paragraph apart — that is not the claimed sentence.
{
  echo "## Discussion"
  echo "Some learners were enrolled."
  for _ in $(seq 1 12); do echo "The study reported outcomes across sites and years."; done
  echo "We form working groups."
  for _ in $(seq 1 12); do echo "The study reported outcomes across sites and years."; done
  echo "An independent committee met."
  for _ in $(seq 1 12); do echo "The study reported outcomes across sites and years."; done
  echo "Their assessments were filed before seeing AI output."
} > "$TMP/body_scattered.md"
python3 "$V" --response "$TMP/resp_quote.md" --manuscript "$TMP/body_scattered.md" --strict > /dev/null 2>&1
ck "scattered words are still MAJOR drift (--strict)" 1 "$?"

# --- a long quote is checked whole, not dropped at the window edge ----------------------
# The quote below opens right after its claim verb but closes ~440 chars later. Reading a
# fixed 320-char window lost the closing mark, so the quote was never checked at all and a
# stale response passed --strict. Synthetic text only.
LONG_Q="Participants were enrolled consecutively at three synthetic sites between two fixed calendar dates, and every enrolled participant contributed exactly one baseline examination, one follow-up examination at a prespecified interval, and one adjudicated outcome record, so that no participant could contribute more than one observation to any analysis and the unit of analysis was the participant throughout the study rather than the examination"
printf '**Response 3.** We added the sentence "%s." to the Methods.\n' "$LONG_Q" > "$TMP/resp_long.md"
printf '## Methods\nBaseline characteristics were summarized descriptively.\n' > "$TMP/body_long_absent.md"
printf '## Methods\n%s.\n' "$LONG_Q" > "$TMP/body_long_present.md"
python3 "$V" --response "$TMP/resp_long.md" --manuscript "$TMP/body_long_absent.md" --strict > /dev/null 2>&1
ck "long quote absent from body fails (--strict)" 1 "$?"
python3 "$V" --response "$TMP/resp_long.md" --manuscript "$TMP/body_long_present.md" --strict > /dev/null 2>&1
ck "long quote present in body passes (--strict)" 0 "$?"

# --- "Changes to text:" labels anchor their quote --------------------------------------
# Many letters give the new text under a label instead of an edit verb. Without the label
# as an anchor, no claim verb was seen and the quoted text was never checked.
cat > "$TMP/resp_changes.md" <<'MD'
**Response 4.** We agree with the reviewer.

Changes to text: "The index test was interpreted without knowledge of the reference standard." (Methods, page 5)

**Response 5.** Thank you for this suggestion.

Changes to Text (page 7, lines 3-4): "Readers were blinded to all clinical information other than the examination date."
MD
printf '## Methods\nBaseline characteristics were summarized descriptively.\n' > "$TMP/body_changes_absent.md"
printf '## Methods\nThe index test was interpreted without knowledge of the reference standard. Readers were blinded to all clinical information other than the examination date.\n' > "$TMP/body_changes_present.md"
python3 "$V" --response "$TMP/resp_changes.md" --manuscript "$TMP/body_changes_absent.md" --strict > /dev/null 2>&1
ck "'Changes to text:' quote absent fails (--strict)" 1 "$?"
N_UNVER="$(python3 "$V" --response "$TMP/resp_changes.md" --manuscript "$TMP/body_changes_absent.md" 2>&1 | grep -c RESPONSE_QUOTE_UNVERIFIED)"
ck "both labelled quotes (text: / Text (page..):) checked" 2 "$N_UNVER"
python3 "$V" --response "$TMP/resp_changes.md" --manuscript "$TMP/body_changes_present.md" --strict > /dev/null 2>&1
ck "'Changes to text:' quote present passes (--strict)" 0 "$?"

# an apostrophe inside a quote does not end it: the checked text is the whole sentence
cat > "$TMP/resp_apos.md" <<'MD'
**Response 6.** The sentence now reads "the model's threshold was fixed before the test set was opened".
MD
printf '## Methods\nThe model'"'"'s threshold was fixed before the test set was opened.\n' > "$TMP/body_apos.md"
python3 "$V" --response "$TMP/resp_apos.md" --manuscript "$TMP/body_apos.md" --strict > /dev/null 2>&1
ck "apostrophe inside a double-quoted quote is not its end" 0 "$?"
# ...and the words BEFORE the apostrophe are checked too. Cutting the quote at the
# apostrophe checked only "s threshold was fixed ...", which a different sentence
# ("Each reader's threshold ...") also contains, so the claim looked verified.
printf '## Methods\nEach reader'"'"'s threshold was fixed before the test set was opened.\n' > "$TMP/body_apos_other.md"
python3 "$V" --response "$TMP/resp_apos.md" --manuscript "$TMP/body_apos_other.md" 2>&1 | grep -q RESPONSE_QUOTE
ck "a different subject before the apostrophe is not verified" 0 "$?"

# --- a changed number or negation is a different claim, not extraction damage ------------
# The tolerant matcher let a quote through as minor UNRESOLVED when the body differed by one
# number ("0.92" vs "0.87") or by a "not" — a changed result or a flipped finding passed
# --strict. Those are now major. Synthetic text only.
printf '**Response 7.** The sentence now reads "the sensitivity of the model was 0.92 in the external test set".\n' > "$TMP/resp_num.md"
printf '## Results\nThe sensitivity of the model was 0.87 in the external test set.\n' > "$TMP/body_num_changed.md"
python3 "$V" --response "$TMP/resp_num.md" --manuscript "$TMP/body_num_changed.md" --strict > /dev/null 2>&1
ck "quoted number changed in body fails (--strict)" 1 "$?"
python3 "$V" --response "$TMP/resp_num.md" --manuscript "$TMP/body_num_changed.md" 2>&1 | grep -q RESPONSE_QUOTE_UNVERIFIED
ck "quoted number changed reports UNVERIFIED" 0 "$?"
# control: same number, proof line numbers wedged in -> still extraction damage, not drift
printf '## Results\n41 The sensitivity of the model 42 was 0.92 in the external test set.\n' > "$TMP/body_num_linenum.md"
python3 "$V" --response "$TMP/resp_num.md" --manuscript "$TMP/body_num_linenum.md" --strict > /dev/null 2>&1
ck "same number + line numbers is not drift (--strict)" 0 "$?"

printf '**Response 8.** We added the sentence "age was associated with mortality in the adjusted model".\n' > "$TMP/resp_neg_add.md"
printf '## Results\nAge was not associated with mortality in the adjusted model.\n' > "$TMP/body_neg_add.md"
python3 "$V" --response "$TMP/resp_neg_add.md" --manuscript "$TMP/body_neg_add.md" --strict > /dev/null 2>&1
ck "negation added in body fails (--strict)" 1 "$?"
printf '**Response 9.** We added the sentence "age was not associated with mortality in the adjusted model".\n' > "$TMP/resp_neg_drop.md"
printf '## Results\nAge was associated with mortality in the adjusted model.\n' > "$TMP/body_neg_drop.md"
python3 "$V" --response "$TMP/resp_neg_drop.md" --manuscript "$TMP/body_neg_drop.md" --strict > /dev/null 2>&1
ck "negation dropped from body fails (--strict)" 1 "$?"
# control: the negated sentence is present as quoted -> passes
python3 "$V" --response "$TMP/resp_neg_drop.md" --manuscript "$TMP/body_neg_add.md" --strict > /dev/null 2>&1
ck "negated quote present as quoted passes (--strict)" 0 "$?"
# control: a bled reference line that happens to contain "not" is still extraction debris
printf '## Results\nAge was associated with civile. Why age is not enough. Rev Med Suisse 2019;15:1122. mortality in the adjusted model.\n' > "$TMP/body_neg_bleed.md"
python3 "$V" --response "$TMP/resp_neg_add.md" --manuscript "$TMP/body_neg_bleed.md" --strict > /dev/null 2>&1
ck "bled reference line containing 'not' is not drift" 0 "$?"

# control: an EARLIER contrast sentence holding a negator is not part of the quote. The
# matcher's first full run borrows 'not' from the training-set sentence; the run the quote
# came from is the one with the fewest insertions, and it holds only a proof line number.
printf '**Response 14.** We added the sentence "accuracy was high in the test set of the external cohort".\n' > "$TMP/resp_contrast.md"
printf '## Results\nAccuracy was not high in the training set. Accuracy was 112 high in the test set of the external cohort.\n' > "$TMP/body_contrast.md"
python3 "$V" --response "$TMP/resp_contrast.md" --manuscript "$TMP/body_contrast.md" --strict > /dev/null 2>&1
ck "negator in an earlier contrast sentence is not drift" 0 "$?"
python3 "$V" --response "$TMP/resp_contrast.md" --manuscript "$TMP/body_contrast.md" 2>&1 | grep -q RESPONSE_QUOTE_UNVERIFIED
ck "earlier contrast sentence reports no UNVERIFIED" 1 "$?"
# ...while the same quote against a body whose only matching sentence is negated still fails
printf '## Results\nAccuracy was not high in the test set of the external cohort.\n' > "$TMP/body_contrast_neg.md"
python3 "$V" --response "$TMP/resp_contrast.md" --manuscript "$TMP/body_contrast_neg.md" --strict > /dev/null 2>&1
ck "negated test-set sentence still fails (--strict)" 1 "$?"

# controls: a number written differently, or with a superscript reference glued on in
# extraction, is the same number.
printf '**Response 15.** The sentence now reads "the difference between the two arms was significant with P < 0.001 in the adjusted model".\n' > "$TMP/resp_p.md"
printf '## Results\nThe difference between the two arms was significant with P < .001 in the adjusted 57 model.\n' > "$TMP/body_p.md"
python3 "$V" --response "$TMP/resp_p.md" --manuscript "$TMP/body_p.md" --strict > /dev/null 2>&1
ck "'P < 0.001' vs 'P < .001' is not drift (--strict)" 0 "$?"
printf '**Response 16.** We added "a total of 1234 patients were enrolled at the three participating centres".\n' > "$TMP/resp_thou.md"
printf '## Methods\nA total of 1,234 patients were enrolled at the three 88 participating centres.\n' > "$TMP/body_thou.md"
python3 "$V" --response "$TMP/resp_thou.md" --manuscript "$TMP/body_thou.md" --strict > /dev/null 2>&1
ck "'1234' vs '1,234' is not drift (--strict)" 0 "$?"
printf '**Response 17.** We added "the guideline was last updated in 2019 by the international working group".\n' > "$TMP/resp_sup.md"
printf '## Discussion\nThe guideline was last updated in 2019\xc2\xb2\xc2\xb3 by the international 64 working group.\n' > "$TMP/body_sup.md"
python3 "$V" --response "$TMP/resp_sup.md" --manuscript "$TMP/body_sup.md" --strict > /dev/null 2>&1
ck "superscript reference glued to '2019' is not drift" 0 "$?"
# ...but a different year in the same place is
printf '## Discussion\nThe guideline was last updated in 2021 by the international 64 working group.\n' > "$TMP/body_year.md"
python3 "$V" --response "$TMP/resp_sup.md" --manuscript "$TMP/body_year.md" --strict > /dev/null 2>&1
ck "quoted year changed in body fails (--strict)" 1 "$?"

# controls: a negation on BOTH sides, spelled differently, cancels.
printf '**Response 18.** We added "the model cannot be applied to paediatric patients in this setting".\n' > "$TMP/resp_cannot.md"
printf '## Discussion\nThe model can not be applied to paediatric patients in this setting.\n' > "$TMP/body_cannot.md"
python3 "$V" --response "$TMP/resp_cannot.md" --manuscript "$TMP/body_cannot.md" 2>&1 | grep -q RESPONSE_QUOTE_UNVERIFIED
ck "'cannot' vs 'can not' is not a one-sided negation" 1 "$?"
printf '**Response 19.** We added "the association isn'"'"'t explained by age or sex in the cohort".\n' > "$TMP/resp_isnt.md"
printf '## Discussion\nThe association is not explained by age or sex in the cohort.\n' > "$TMP/body_isnt.md"
python3 "$V" --response "$TMP/resp_isnt.md" --manuscript "$TMP/body_isnt.md" 2>&1 | grep -q RESPONSE_QUOTE_UNVERIFIED
ck "\"isn't\" vs 'is not' is not a one-sided negation" 1 "$?"

# --- citation intent read past a leading 'We (have) added' --------------------------------
# The leftmost verb alternative 'we (have) added' swallowed the match, so 'added the citation'
# / 'added a reference' were never seen and the claim was never checked.
printf '**Response 10.** We added the citation [15] to the Discussion.\n' > "$TMP/resp_cit_added.md"
printf '**Response 11.** We have added a reference to Tariq et al. [15] in the Discussion.\n' > "$TMP/resp_ref_added.md"
python3 "$V" --response "$TMP/resp_cit_added.md" --manuscript "$TMP/body_bad.md" --strict > /dev/null 2>&1
ck "'We added the citation [15]' absent fails (--strict)" 1 "$?"
python3 "$V" --response "$TMP/resp_ref_added.md" --manuscript "$TMP/body_bad.md" --strict > /dev/null 2>&1
ck "'We have added a reference to X [15]' absent fails" 1 "$?"
python3 "$V" --response "$TMP/resp_ref_added.md" --manuscript "$TMP/body_good.md" --strict > /dev/null 2>&1
ck "'We have added a reference to X [15]' present passes" 0 "$?"
# control: an added SENTENCE that merely mentions a cited study is not a citation claim
printf '**Response 12.** We added a limitation paragraph to the Discussion, as Tariq et al. [15] suggested.\n' > "$TMP/resp_not_cit.md"
python3 "$V" --response "$TMP/resp_not_cit.md" --manuscript "$TMP/body_bad.md" --strict > /dev/null 2>&1
ck "added text mentioning a study is not a citation claim" 0 "$?"

# --- numeric citations match whole bracket elements --------------------------------------
printf '**Response 13.** We now cite [5] in the Discussion.\n' > "$TMP/resp_cit5.md"
printf '## Discussion\nPrior work agrees [15].\n' > "$TMP/body_cit15.md"
python3 "$V" --response "$TMP/resp_cit5.md" --manuscript "$TMP/body_cit15.md" --strict > /dev/null 2>&1
ck "claimed [5] is not satisfied by [15] (--strict)" 1 "$?"
printf '## Discussion\nPrior work agrees [25, 31].\n' > "$TMP/body_cit25.md"
python3 "$V" --response "$TMP/resp_cit5.md" --manuscript "$TMP/body_cit25.md" --strict > /dev/null 2>&1
ck "claimed [5] is not satisfied by [25, 31] (--strict)" 1 "$?"
# controls: the number as a later list element, and inside a range, are real citations
printf '## Discussion\nPrior work agrees [2, 3, 5].\n' > "$TMP/body_cit_list.md"
python3 "$V" --response "$TMP/resp_cit5.md" --manuscript "$TMP/body_cit_list.md" --strict > /dev/null 2>&1
ck "claimed [5] found as third list element passes" 0 "$?"
printf '## Discussion\nPrior work agrees [3–7].\n' > "$TMP/body_cit_range.md"
python3 "$V" --response "$TMP/resp_cit5.md" --manuscript "$TMP/body_cit_range.md" --strict > /dev/null 2>&1
ck "claimed [5] found inside range [3-7] passes" 0 "$?"

echo "----"
echo "test_response_claims: $pass passed, $fail failed"
[ "$fail" -eq 0 ]
