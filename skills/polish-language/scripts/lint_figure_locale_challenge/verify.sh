#!/usr/bin/env bash
# Deterministic verifier for the figure-SOURCE locale-drift challenge card.
# Network-free, no committed binaries (the .pptx is written at runtime via python-pptx).
#   Positive: genuine UK words in a .py label and a .pptx <a:t> run are flagged in a US manuscript.
#   Negative: universal words (characteristics / analysis / organisms) sitting in the SAME
#             sources must stay silent — the precision trap the shared families used to fail.
#   Negative: US-spelled sources are clean; a missing figures dir exits 0 (nothing judged).
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
DET="$HERE/../lint_figure_locale.py"
tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT

[ -f "$DET" ] || { echo "ENV-ERR: lint_figure_locale.py missing" >&2; exit 2; }

figs="$tmp/figures"; mkdir -p "$figs"
cat > "$tmp/manuscript.md" <<'MD'
---
title: Test manuscript
spelling: US
---

We analyzed the baseline characteristics and the analysis of tumor color in the center.
MD

# A plotting script whose labels mix a genuine UK word with two universals.
cat > "$figs/panel.py" <<'PY'
ax.set_title("Behavioural alignment")
ax.set_xlabel("Baseline characteristics")
ax.set_ylabel("Analysis of organisms")
PY

have_pptx=0
if python3 -c "import pptx" 2>/dev/null; then
  have_pptx=1
  python3 - "$figs/panel.pptx" <<'PY'
import sys
from pptx import Presentation
from pptx.util import Inches
prs = Presentation(); s = prs.slides.add_slide(prs.slide_layouts[6])
tb = s.shapes.add_textbox(Inches(1), Inches(1), Inches(6), Inches(1))
tb.text_frame.text = "Randomised centre — analysis of characteristics"
prs.save(sys.argv[1])
PY
else
  echo "NOTE: python-pptx unavailable — the .pptx source stage is skipped (script stage still runs)."
fi

# (1) Positive + (2) precision guard, in one scan.
python3 "$DET" --manuscript "$tmp/manuscript.md" --figures-dir "$figs" \
  --strict --quiet --out "$tmp/drift.json" && { echo "FAIL: UK drift in a US manuscript did not flag" >&2; exit 1; }

python3 - "$tmp/drift.json" "$have_pptx" <<'PY'
import json, os, sys
d = json.load(open(sys.argv[1])); have_pptx = sys.argv[2] == "1"
assert d["detector"] == "lint_figure_locale", "envelope does not self-identify"
assert d["spelling"] == "us", d["spelling"]
words = {f["word"].lower() for f in d["findings"]}
# Positive: genuine UK spellings are caught.
assert "behavioural" in words, f"missed the .py UK label: {words}"
if have_pptx:
    assert "randomised" in words, f"missed a .pptx <a:t> UK word: {words}"
    assert "centre" in words, f"missed a .pptx <a:t> UK word: {words}"
# Negative (precision guard): universals in the SAME sources must be silent.
for universal in ("characteristics", "analysis", "organisms", "characteristic", "analyses", "organism"):
    assert universal not in words, (
        f"FALSE POSITIVE — '{universal}' is identical in US and UK spelling: {sorted(words)}")
print(f"OK-POSITIVE+PRECISION: flagged {sorted(words)}; universals stayed silent")
PY

# (3) Negative — US-spelled sources in a US manuscript are clean.
clean="$tmp/clean_figs"; mkdir -p "$clean"
cat > "$clean/panel.py" <<'PY'
ax.set_title("Behavioral alignment")
ax.set_xlabel("Baseline characteristics")
ax.set_ylabel("Analysis of organisms")
PY
python3 "$DET" --manuscript "$tmp/manuscript.md" --figures-dir "$clean" \
  --strict --quiet --out "$tmp/clean.json" || { echo "FAIL: clean US sources flagged (false positive)" >&2; cat "$tmp/clean.json" >&2; exit 1; }
grep -qE '"kind":' "$tmp/clean.json" && { echo "FAIL: clean fixture produced a finding" >&2; cat "$tmp/clean.json" >&2; exit 1; }
echo "OK-CLEAN: US-spelled figure sources are silent"

# (4) No figures directory -> exit 0 (nothing to judge), never an error.
python3 "$DET" --manuscript "$tmp/manuscript.md" --figures-dir "$tmp/nope" --quiet \
  || { echo "FAIL: a missing figures dir must exit 0" >&2; exit 1; }
echo "OK-NOSOURCE: a missing figures directory exits 0"

echo "PASS: figure-source locale drift flags genuine UK spellings in .py labels and .pptx runs, stays silent on universals (characteristics/analysis/organisms) and on US-spelled sources."
