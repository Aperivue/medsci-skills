#!/usr/bin/env bash
# Deterministic verifier for the deck-budget challenge card.
#
# The claim being tested is the whole reason this check takes an --archetype: THE SAME DECK IS RIGHT
# FOR ONE ROOM AND WRONG FOR ANOTHER. A single global "words per slide" number would have to be
# wrong for most of the table.
#
# So one deck is built and judged twice:
#
#   as a 10-minute CONFERENCE ORAL  -> fits. 40 words on a slide is an ordinary academic slide.
#   as a 20-minute KEYNOTE          -> too dense. That same slide is a wall of text to a room that
#                                      came to be moved and is not taking notes.
#
# And a deck that is over budget in ANY room (60 slides for a 10-minute oral) must fail as one.
#
# No network. python-pptx builds the fixtures; the detector is stdlib-only.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
DET="$HERE/../check_deck_budget.py"

FIX="$(mktemp -d)"
trap 'rm -rf "$FIX"' EXIT
python3 "$HERE/make_fixtures.py" "$FIX" >/dev/null

fail=0
pass() { echo "PASS  $1"; }
bad()  { echo "FAIL  $1"; fail=1; }

verdicts() { python3 "$DET" "$1" --archetype "$2" --minutes "$3" | grep -oE '^\s+\[[A-Z_]+\]' | tr -d ' []' | sort -u; }

# --- the same deck, two rooms -------------------------------------------------------------------
if python3 "$DET" "$FIX/academic.pptx" --archetype conference_oral --minutes 10 | grep -q '^OK:'; then
  pass "an academic deck fits a 10-minute conference oral"
else
  bad "the academic deck was rejected by its own archetype"
  python3 "$DET" "$FIX/academic.pptx" --archetype conference_oral --minutes 10
fi

if verdicts "$FIX/academic.pptx" keynote 20 | grep -q SLIDE_TOO_DENSE; then
  pass "...and the SAME deck is too dense for a keynote (the archetype is doing the work)"
else
  bad "the same deck passed as a keynote — then --archetype is decoration"
fi

# --- a keynote deck is not judged by academic density --------------------------------------------
if python3 "$DET" "$FIX/keynote.pptx" --archetype keynote --minutes 20 | grep -q '^OK:'; then
  pass "a keynote deck fits a keynote"
else
  bad "the keynote deck was rejected by its own archetype"
  python3 "$DET" "$FIX/keynote.pptx" --archetype keynote --minutes 20
fi

# --- the clock ------------------------------------------------------------------------------------
if verdicts "$FIX/bloated.pptx" conference_oral 10 | grep -q DECK_OVER_BUDGET; then
  pass "60 slides for a 10-minute oral is caught"
else
  bad "a 60-slide deck passed a 10-minute oral"
fi

# --- the back row ---------------------------------------------------------------------------------
if verdicts "$FIX/tiny_type.pptx" conference_oral 10 | grep -q TYPE_TOO_SMALL; then
  pass "12-pt body text is caught (the back row exists)"
else
  bad "12-pt text passed the type floor"
fi

# --- text nothing can measure ---------------------------------------------------------------------
# The regression is the PAIR, not the fire. Same words, same 11.5 pt, two geometries:
#   broken -> the shape is dropped before any check sees it, so the deck reads as clean
#   fixed  -> the density and the type floor were always breached and now say so
# Assert the fixed deck's findings explicitly: if this pair ever stops differing, ZERO_AREA_TEXT has
# stopped meaning anything and is just another verdict that fires.
if verdicts "$FIX/zero_area.pptx" conference_oral 10 | grep -q ZERO_AREA_TEXT; then
  pass "a half-written placeholder xfrm is caught (text in a shape with no area)"
else
  bad "text in a zero-area shape passed — the deck that cannot be read reads as clean"
  python3 "$DET" "$FIX/zero_area.pptx" --archetype conference_oral --minutes 10
fi

if verdicts "$FIX/zero_area_fixed.pptx" conference_oral 10 | grep -q ZERO_AREA_TEXT; then
  bad "ZERO_AREA_TEXT fired on a deck whose four coordinates are all written (false positive)"
else
  pass "...and does NOT fire once left/top/width/height are all set"
fi

fixed_verdicts="$(verdicts "$FIX/zero_area_fixed.pptx" conference_oral 10)"
if grep -q SLIDE_TOO_DENSE <<<"$fixed_verdicts" && grep -q TYPE_TOO_SMALL <<<"$fixed_verdicts"; then
  pass "the SAME text, once measurable, breaches both the density ceiling and the type floor"
else
  bad "the fixed deck reported no density/type finding — then the pair proves nothing"
  echo "$fixed_verdicts"
fi

if verdicts "$FIX/zero_area.pptx" conference_oral 10 | grep -qE 'SLIDE_TOO_DENSE|TYPE_TOO_SMALL'; then
  pass "(those two are now visible on the broken deck as well)"
else
  pass "the broken deck hides both of them — which is what the green was made of"
fi

# --- one clean deck, to be sure the new verdict is not simply always on -----------------------------
if verdicts "$FIX/academic.pptx" conference_oral 10 | grep -q ZERO_AREA_TEXT; then
  bad "ZERO_AREA_TEXT fired on the clean academic deck"
else
  pass "ZERO_AREA_TEXT is silent on a well-formed deck"
fi

# --- --strict, and the artifact contract ----------------------------------------------------------
if python3 "$DET" "$FIX/bloated.pptx" --archetype conference_oral --minutes 10 --strict >/dev/null 2>&1; then
  bad "--strict returned 0 on an over-budget deck"
else
  pass "--strict exits non-zero on an over-budget deck"
fi

python3 "$DET" "$FIX/bloated.pptx" --archetype conference_oral --minutes 10 --json "$FIX/o.json" >/dev/null
python3 - "$FIX/o.json" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
assert d["detector"] == "check_deck_budget", d.get("detector")
assert d["archetype"] == "conference_oral" and d["findings"]
assert all(f["detector"] == "check_deck_budget" for f in d["findings"])
PY
pass "qc JSON self-identifies and records the archetype it judged against"

[ "$fail" -eq 0 ] || exit 1
echo "----"
echo "deck-budget challenge: all checks passed"
