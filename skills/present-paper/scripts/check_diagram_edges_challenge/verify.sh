#!/usr/bin/env bash
# Deterministic verifier for the diagram-edge-clip challenge card.
#
# The claim: a stroke laid on the canvas boundary is half-removed by the render, and on a slide it
# does not read as a crop — it reads as a line that is not there. People find these one at a time;
# the check finds all of them.
#
# Four assertions, and the fourth is the one that keeps the check usable:
#   a box drawn ON the edge          FIRES
#   the same box inset               SILENT
#   a short run along one edge       FIRES        (the instance a person walks past)
#   a full-bleed image               SILENT       (a photograph is not a clipped diagram)
#
# No network. Pillow draws the fixtures; Pillow + numpy run the detector (both arrive with
# python-pptx, which this skill already requires — so this card runs in CI rather than skipping).
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
DET="$HERE/../check_diagram_edges.py"

python3 -c "import PIL, numpy" 2>/dev/null \
  || { echo "ENV-ERR: Pillow and numpy are required (they ship with python-pptx)" >&2; exit 2; }

FIX="$(mktemp -d)"
trap 'rm -rf "$FIX"' EXIT
python3 "$HERE/make_fixtures.py" "$FIX" >/dev/null

fail=0
pass() { echo "PASS  $1"; }
bad()  { echo "FAIL  $1"; fail=1; }

if python3 "$DET" "$FIX/clipped.png" | grep -q DIAGRAM_EDGE_CLIP; then
  pass "a box whose side sits on the canvas edge is caught"
else
  bad "the clipped box passed"
  python3 "$DET" "$FIX/clipped.png"
fi

if python3 "$DET" "$FIX/margin.png" | grep -q '^OK:'; then
  pass "the same box, inset, is left alone"
else
  bad "an inset diagram was flagged — the check would be switched off"
  python3 "$DET" "$FIX/margin.png"
fi

if python3 "$DET" "$FIX/corner.png" | grep -q DIAGRAM_EDGE_CLIP; then
  pass "a short run of ink along one edge is caught (the instance an eye walks past)"
else
  bad "a partial edge touch passed"
  python3 "$DET" "$FIX/corner.png"
fi

if python3 "$DET" "$FIX/bleed.png" | grep -q '^OK:'; then
  pass "a full-bleed image is not a clipped diagram"
else
  bad "a solid image was reported — this would fire on every photograph in a deck"
  python3 "$DET" "$FIX/bleed.png"
fi

# A directory argument is how this is actually used: point it at diagrams/ after savefig.
if python3 "$DET" "$FIX" | grep -qE '2 of 4 image'; then
  pass "a directory is walked, and the accounting names how many of how many"
else
  bad "walking a directory did not report 2 of 4"
  python3 "$DET" "$FIX"
fi

if python3 "$DET" "$FIX/clipped.png" --strict >/dev/null 2>&1; then
  bad "--strict returned 0 on a clipped diagram"
else
  pass "--strict exits non-zero, so savefig can gate on it"
fi

python3 "$DET" "$FIX/clipped.png" --json "$FIX/o.json" >/dev/null
python3 - "$FIX/o.json" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
assert d["detector"] == "check_diagram_edges", d.get("detector")
assert d["findings"] and all(f["detector"] == "check_diagram_edges" for f in d["findings"])
PY
pass "qc JSON self-identifies"

[ "$fail" -eq 0 ] || exit 1
echo "----"
echo "diagram-edge challenge: all checks passed"
