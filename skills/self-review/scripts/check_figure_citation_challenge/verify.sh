#!/usr/bin/env bash
# Deterministic verifier for the figure-citation panel-suffix regression.
#   Regression: figures cited ONLY by panel (Figure 1a / 2c) must NOT be orphans -> clean.
#   Positive:   a figure with a caption and no citation in any form -> FIGURE_ORPHAN.
# No network. Exit 0 = both match expectations.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
DET="$HERE/../check_figure_citation.py"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

# --- Regression: panel-cited figures are NOT orphans, and nothing else fires ---
python3 "$DET" --manuscript "$HERE/fixture/panel_regression.md" --quiet --out "$tmp/reg.json"
n=$(python3 -c "import json;print(len(json.load(open('$tmp/reg.json'))['claims']))")
if [ "$n" -ne 0 ]; then
  echo "FAIL: panel-cited manuscript should be clean, got $n claim(s) (the false positive this fixes)" >&2
  cat "$tmp/reg.json" >&2
  exit 1
fi

# --- Positive: a genuinely uncited figure still fires; a panel-cited one does not ---
python3 "$DET" --manuscript "$HERE/fixture/real_orphan.md" --quiet --out "$tmp/orph.json"
python3 - "$tmp/orph.json" <<'PY'
import json, sys
orph = [c for c in json.load(open(sys.argv[1]))["claims"] if c["verdict"] == "FIGURE_ORPHAN"]
assert any("Figure 2 " in c["detail"] for c in orph), "Figure 2 (never cited) should be FIGURE_ORPHAN"
assert not any("Figure 1 " in c["detail"] for c in orph), "Figure 1 (cited via 1a) must NOT be an orphan"
print("orphan detection intact: Figure 2 flagged, Figure 1 (panel-cited) not")
PY

echo "PASS: panel-cited figures are not orphans (regression); a truly uncited figure still fires."
