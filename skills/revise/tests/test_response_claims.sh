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

echo "----"
echo "test_response_claims: $pass passed, $fail failed"
[ "$fail" -eq 0 ]
