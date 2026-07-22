#!/usr/bin/env bash
# Regression test for check_review_length.py and check_review_boxes.py.
#
# Both gates read the same artifact, a review draft with two boxes, so they share fixtures
# here rather than inventing two synthetic ones. The fixtures carry the real shapes:
#   bad.md      the editor block opens with a clause pasted out of the author block, a
#               recommendation grade sits in the authors' box, and one Major runs long
#   good.md     two blocks written at different altitudes, grade confined to the editor's
#   nearmiss.md the false-positive guard: prose that merely contains "accept" and "reject"
#               in ordinary sentences ("the authors accept that", "we reject the null") and
#               must stay clean, because a gate that fires on those gets switched off
#   noheads.md  no author heading at all; the length gate must refuse to measure the whole
#               file and call it a pass, and the box gate must report the block missing
set -u

REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
LEN="$REPO_ROOT/skills/peer-review/scripts/check_review_length.py"
BOX="$REPO_ROOT/skills/peer-review/scripts/check_review_boxes.py"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

pass=0
fail=0
ck() {
  local label="$1" expected="$2" actual="$3"
  if [ "$expected" = "$actual" ]; then
    printf '  PASS  %-58s %s\n' "$label" "$actual"
    pass=$((pass + 1))
  else
    printf '  FAIL  %-58s expected=%s actual=%s\n' "$label" "$expected" "$actual"
    fail=$((fail + 1))
  fi
}
verdicts() { python3 "$1" --review "$2" --quiet --out "$TMP/o.json" >/dev/null 2>&1
             python3 -c "import json,sys;print(','.join(sorted(f['verdict'] for f in json.load(open('$TMP/o.json'))['findings'])) or 'CLEAN')"; }

# --- fixtures ---------------------------------------------------------------------------
# The duplicated sentence below is the real failure mode: an editor note assembled by pasting
# the author-facing summary instead of being written for the editor.
DUP="The re-extraction has been done properly and the comparator definition now sits in the Methods, with the paired pools contracted accordingly and the sign counts reproducing from the published tables alone."

cat > "$TMP/bad.md" <<MD
## CONFIDENTIAL COMMENTS TO THE EDITOR

$DUP I would put this at major revision.

## COMMENTS TO THE AUTHORS

**Research summary and general comments**

$DUP My comments follow.

**Major Comments**

1) **The pooled estimate is not stable.**
$DUP The leave-one-out table moves the estimate across a range wide enough to change how a
reader would describe it, and three separate places in the manuscript describe that range as
confirmed rather than as the span it is. The single-arm pools behave differently from the paired
comparison, so the claim needs splitting rather than softening, and the observed range belongs in
the Results where a reader meets the number rather than in a supplement they may not open. I
would also note that the methods promise an analysis whose table I could not locate anywhere in
the supplementary material, which is the kind of thing a production editor will catch later at
greater cost. My recommendation is major revision before this can proceed further.

**Closing remark**

This can become a strong contribution.
MD

cat > "$TMP/good.md" <<'MD'
## CONFIDENTIAL COMMENTS TO THE EDITOR

They did the work. What is left needs correcting, not re-reviewing: one statistical column is
wrong and the Results quote it. I would put this at minor revision.

## COMMENTS TO THE AUTHORS

**Research summary and general comments**

This revision pools 50 studies comparing two training paradigms. The re-extraction is verifiable
and I want to say so plainly.

**Major Comments**

1) **The adjusted column needs recomputing.**
All four rows carry one value although the raw inputs differ, and those inputs cannot produce
that column. No conclusion changes, but the Results quote the figure.

**Closing remark**

A considerably stronger paper than the one I read first.
MD

cat > "$TMP/nearmiss.md" <<'MD'
## CONFIDENTIAL COMMENTS TO THE EDITOR

A careful study whose framing needs one adjustment.

## COMMENTS TO THE AUTHORS

**Research summary and general comments**

The authors accept that the cohort is single-centre, and say so plainly. Where the model and the
readers disagree the paper does not reject the null on the strength of a single subgroup, which
is the right instinct.

**Major Comments**

1) **State the analysis unit.**
Please say whether the split was made per patient or per image.

**Closing remark**

Thank you for a clear paper.
MD

cat > "$TMP/noheads.md" <<'MD'
# Review notes

Some scratch prose with no box headings at all, which a measurement run over the whole file
would happily count and report as a comfortable word total.
MD

# A long review is long because it carries many comments, not because one paragraph swelled.
# Build the over-tier fixtures that way rather than padding a single item, so the per-item
# table has something real to say about where the words are.
mk_long() {  # $1 = number of Major comments, $2 = output path
  {
    printf '## CONFIDENTIAL COMMENTS TO THE EDITOR\n\nA careful study with several separable concerns.\n\n'
    printf '## COMMENTS TO THE AUTHORS\n\n**Research summary and general comments**\n\nThis study compares two approaches across a pooled cohort.\n\n**Major Comments**\n\n'
    for i in $(seq 1 "$1"); do
      printf '%s) **Concern %s needs its own treatment.**\n' "$i" "$i"
      printf 'The reported estimate rests on a step that the manuscript states but does not show, and a\n'
      printf 'reader cannot tell from the current text whether the choice was made before or after the\n'
      printf 'results were known. Please give the pre-specified version, the observed range, and the\n'
      printf 'sensitivity result in the Results rather than in a supplement, so that a reader meets the\n'
      printf 'number where the claim is made. If the decision was taken at manuscript stage, saying so\n'
      printf 'costs very little and settles the question for anyone reading it later. The same applies\n'
      printf 'to the subgroup that carries this comparison: its denominator is stated once, in a table\n'
      printf 'note, and never again where the estimate is discussed, so a reader who begins at the\n'
      printf 'Results has no way to size it. I would also welcome a sentence on how the missing values\n'
      printf 'were handled here, since the count changes between the flow diagram and the model, and\n'
      printf 'the difference is large enough that it deserves a line rather than an inference.\n\n'
    done
    printf '**Closing remark**\n\nThank you for a careful paper.\n'
  } > "$2"
}
mk_long 4 "$TMP/long.md"     # over tier 1, under 2x baseline and under the hard cap
mk_long 8 "$TMP/huge.md"     # over the 1400-word hard cap

# --- length gate ------------------------------------------------------------------------
echo "check_review_length.py"
ck "bad: one Major over the per-Major budget" "MAJOR_OVERLONG" "$(verdicts "$LEN" "$TMP/bad.md")"
ck "long: over a declared tier-1 ceiling" "MAJOR_OVERLONG,TIER_EXCEEDED" \
   "$(python3 "$LEN" --review "$TMP/long.md" --tier 1 --quiet --out "$TMP/o.json" >/dev/null 2>&1; python3 -c "import json;print(','.join(sorted(f['verdict'] for f in json.load(open('$TMP/o.json'))['findings'])))")"
python3 "$LEN" --review "$TMP/long.md" --tier 1 --strict --quiet >/dev/null 2>&1 && rc=0 || rc=$?
ck "long: --strict exits 1 against tier 1" "1" "$rc"
# Same file, no tier declared: the ceiling verdict must disappear, because there is no
# declared ceiling to exceed. Everything else about the draft is unchanged.
ck "long: no declared tier, so no TIER_EXCEEDED" "MAJOR_OVERLONG" "$(verdicts "$LEN" "$TMP/long.md")"
ck "huge: hard cap fires with no tier declared" "HARD_CAP,RATIO_HIGH" "$(verdicts "$LEN" "$TMP/huge.md")"
ck "good: clean" "CLEAN" "$(verdicts "$LEN" "$TMP/good.md")"
python3 "$LEN" --review "$TMP/good.md" --tier 1 --strict --quiet >/dev/null 2>&1 && rc=0 || rc=$?
ck "good: --strict exits 0" "0" "$rc"
ck "no headings: refuses to measure" "AUTHOR_BLOCK_NOT_FOUND" "$(verdicts "$LEN" "$TMP/noheads.md")"

# The count must ignore markup. good.md has bold labels, a numbered item and a bold headline;
# none of those tokens are words, and a naive `wc -w` counts every one of them.
naive=$(sed -n '/COMMENTS TO THE AUTHORS/,$p' "$TMP/good.md" | wc -w | tr -d ' ')
measured=$(python3 "$LEN" --review "$TMP/good.md" --quiet --out "$TMP/o.json" >/dev/null 2>&1; python3 -c "import json;print(json.load(open('$TMP/o.json'))['words'])")
if [ "$measured" -lt "$naive" ]; then
  printf '  PASS  %-58s %s < %s (naive wc -w)\n' "markup excluded from the count" "$measured" "$naive"; pass=$((pass + 1))
else
  printf '  FAIL  %-58s measured=%s naive=%s\n' "markup excluded from the count" "$measured" "$naive"; fail=$((fail + 1))
fi

# --- box gate ---------------------------------------------------------------------------
echo "check_review_boxes.py"
ck "bad: duplicated block + grade in the authors' box" \
   "BOX_DUPLICATION,RECOMMENDATION_IN_AUTHOR_BOX" "$(verdicts "$BOX" "$TMP/bad.md")"
python3 "$BOX" --review "$TMP/bad.md" --strict --quiet >/dev/null 2>&1 && rc=0 || rc=$?
ck "bad: --strict exits 1" "1" "$rc"
ck "good: clean" "CLEAN" "$(verdicts "$BOX" "$TMP/good.md")"
ck "near miss: 'accept that' / 'reject the null' stay clean" "CLEAN" "$(verdicts "$BOX" "$TMP/nearmiss.md")"
ck "no headings: both blocks missing" "BOX_MISSING" "$(verdicts "$BOX" "$TMP/noheads.md")"

# The duplicated clause must be reported, not merely counted, or the writer cannot act on it.
run=$(python3 "$BOX" --review "$TMP/bad.md" --quiet --out "$TMP/o.json" >/dev/null 2>&1; python3 -c "import json;print(json.load(open('$TMP/o.json'))['longest_shared_run'])")
if [ "$run" -ge 12 ]; then
  printf '  PASS  %-58s %s tokens\n' "longest shared run located" "$run"; pass=$((pass + 1))
else
  printf '  FAIL  %-58s run=%s (expected >=12)\n' "longest shared run located" "$run"; fail=$((fail + 1))
fi

echo
echo "passed=$pass failed=$fail"
[ "$fail" -eq 0 ] || exit 1
echo "PASS: review-draft length and two-box gates fire on the real shapes and clear the near miss."
