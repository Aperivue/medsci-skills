#!/usr/bin/env bash
# Deterministic verifier for the slide-tells challenge card.
#
# Builds two decks with the same content and runs the detector on both:
#
#   tells.pptx  — every mark planted on purpose. All six verdicts must fire.
#   clean.pptx  — the same talk, made by someone trying to be understood. ZERO findings.
#
# The clean deck is the half that matters, and it is not decoration. The first version of this
# detector flagged it twice: the "empty band" check counted the footer as an object, so an ordinary
# title-above-body slide looked like a hole. A checker that fires on good work gets switched off,
# and it takes the honest checks down with it. That false positive is why the dead-space rule now
# demands a wide band AND a nearly empty slide, and why this file asserts CLEAN and not merely
# "fewer findings".
#
# No network. python-pptx builds the fixtures (CI installs it); the DETECTOR itself is stdlib-only,
# so it runs on any .pptx from anyone with nothing installed.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
DET="$HERE/../check_slide_tells.py"

# Built into a temp dir, never into the repo: a .pptx is a binary, and a binary that lands in the
# tree gets inventoried into the release manifest while being (rightly) gitignored — after which the
# classroom ZIP fails its own hash check. Found exactly that way.
FIX="$(mktemp -d)"
trap 'rm -rf "$FIX"' EXIT
python3 "$HERE/make_fixtures.py" "$FIX" >/dev/null

fail=0

# --- the AI-made deck: every mark must be found -------------------------------------------------
got="$(python3 "$DET" "$FIX/tells.pptx" | grep -oE '^\s+\[[A-Z_]+\]' | tr -d ' []' | sort -u)"
want="ARROW_NO_SEMANTICS
CHROME_ON_EVERY_SLIDE
DEAD_SPACE_BAND
SCAFFOLD_PHRASE
SHAPE_MONOTONY
TOPIC_TITLE"

if [ "$got" = "$want" ]; then
  echo "PASS  tells.pptx -> all six marks found"
else
  echo "FAIL  tells.pptx -> verdicts differ"
  diff <(echo "$want") <(echo "$got") || true
  fail=1
fi

# --- the human-made deck: nothing may fire ------------------------------------------------------
if python3 "$DET" "$FIX/clean.pptx" | grep -q '^OK:'; then
  echo "PASS  clean.pptx -> no false positives"
else
  echo "FAIL  clean.pptx -> the detector fired on a well-made deck (this is how a checker dies)"
  python3 "$DET" "$FIX/clean.pptx"
  fail=1
fi

# --- --strict is what a build gate would use ----------------------------------------------------
if python3 "$DET" "$FIX/tells.pptx" --strict >/dev/null 2>&1; then
  echo "FAIL  --strict returned 0 on a deck full of marks"
  fail=1
else
  echo "PASS  --strict exits non-zero on the AI-made deck"
fi

if python3 "$DET" "$FIX/clean.pptx" --strict >/dev/null 2>&1; then
  echo "PASS  --strict exits 0 on the human-made deck"
else
  echo "FAIL  --strict flunked a clean deck"
  fail=1
fi

# --- the artifact contract: the JSON must name its author ---------------------------------------
python3 "$DET" "$FIX/tells.pptx" --json "$FIX/out.json" >/dev/null
python3 - "$FIX/out.json" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
assert d["detector"] == "check_slide_tells", d.get("detector")
assert d["findings"], "wrote an empty findings list for the deck full of marks"
assert all(f["detector"] == "check_slide_tells" for f in d["findings"])
PY
echo "PASS  qc JSON self-identifies (detector envelope contract)"

rm -f "$FIX/out.json"
[ "$fail" -eq 0 ] || exit 1
echo "----"
echo "slide-tells challenge: all checks passed"
