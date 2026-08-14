#!/usr/bin/env bash
# Deterministic verifier for the measured-overflow challenge card.
#
# The claim under test is not "text sometimes overflows". It is that OVERFLOW IS MEASURED AND NOT
# ESTIMATED, and the assertions are shaped around the three ways a check like this stops being
# that:
#
#   1. it reports a pass when it did not look         -> no --pdf / no --bbox-xml must EXIT 2
#   2. it compares things that are not comparable     -> a page count != slide count must EXIT 2
#   3. it fires on text that fits                     -> the clean measurement must be SILENT
#
# and, of course, it has to catch the two real failures: a line leaving its block, and a line
# ending in the reserved band at the foot of the slide.
#
# WHAT THIS DOES NOT COVER: the `pdftotext` invocation itself. The card supplies a recorded
# measurement so that it needs neither poppler nor LibreOffice; the parser and the comparison it
# feeds are the same code that runs on a real PDF.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
DET="$HERE/../check_text_overflow.py"

FIX="$(mktemp -d)"
trap 'rm -rf "$FIX"' EXIT
python3 "$HERE/make_fixtures.py" "$FIX" >/dev/null

fail=0
pass() { echo "PASS  $1"; }
bad()  { echo "FAIL  $1"; fail=1; }

# --- 1. it must never answer without measuring ----------------------------------------------------
set +e
python3 "$DET" "$FIX/deck.pptx" >/dev/null 2>"$FIX/err"; rc=$?
set -e
if [ "$rc" -eq 2 ] && grep -q -- "--pdf" "$FIX/err"; then
  pass "with nothing to measure it exits 2 and names --pdf (never a silent pass)"
else
  bad "exit was $rc with no render supplied — a check that answers without looking gets quoted"
  cat "$FIX/err"
fi

# --- 2. it must refuse an incomparable pair -------------------------------------------------------
set +e
python3 "$DET" "$FIX/deck.pptx" --bbox-xml "$FIX/short.xml" >/dev/null 2>"$FIX/err2"; rc=$?
set -e
if [ "$rc" -eq 2 ] && grep -qi "page" "$FIX/err2"; then
  pass "a 1-page render of a 2-slide deck is refused, not silently mapped"
else
  bad "exit was $rc for a page/slide count mismatch"
  cat "$FIX/err2"
fi

# --- 3. text that fits is left alone ---------------------------------------------------------------
if python3 "$DET" "$FIX/deck.pptx" --bbox-xml "$FIX/clean.xml" | grep -q '^OK:'; then
  pass "a measurement where everything fits reports nothing"
else
  bad "the clean measurement produced findings"
  python3 "$DET" "$FIX/deck.pptx" --bbox-xml "$FIX/clean.xml"
fi

out="$(python3 "$DET" "$FIX/deck.pptx" --bbox-xml "$FIX/overflow.xml" || true)"

if grep -q '\[CARD\]' <<<"$out"; then
  pass "a line whose bottom passes the block's bottom is caught"
else
  bad "block overflow missed"; echo "$out"
fi

if grep -q '\[OFF_SLIDE\]' <<<"$out"; then
  pass "a line ending in the reserved band at the foot of the slide is caught"
else
  bad "off-slide overflow missed"; echo "$out"
fi

# The number is the point. "Something overflows" sends you looking; "0.03 in below the block"
# tells you whether to shorten a sentence or rebuild the slide.
if grep -qE '[0-9]+\.[0-9]{2} in' <<<"$out"; then
  pass "...and both report the measured distance, not just a verdict"
else
  bad "no measured distance in the report"; echo "$out"
fi

if python3 "$DET" "$FIX/deck.pptx" --bbox-xml "$FIX/overflow.xml" --strict >/dev/null 2>&1; then
  bad "--strict returned 0 on a deck with measured overflow"
else
  pass "--strict exits non-zero, so a build can gate on it"
fi

python3 "$DET" "$FIX/deck.pptx" --bbox-xml "$FIX/overflow.xml" --json "$FIX/o.json" >/dev/null
python3 - "$FIX/o.json" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
assert d["detector"] == "check_text_overflow", d.get("detector")
assert d["measured_from"].endswith("overflow.xml"), d.get("measured_from")
assert d["findings"] and all(f["detector"] == "check_text_overflow" for f in d["findings"])
PY
pass "qc JSON self-identifies and records what it measured"

[ "$fail" -eq 0 ] || exit 1
echo "----"
echo "measured-overflow challenge: all checks passed"
