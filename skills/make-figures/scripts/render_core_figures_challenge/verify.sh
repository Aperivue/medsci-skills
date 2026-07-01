#!/usr/bin/env bash
# Deterministic verifier for the core-figure render challenge (make-figures).
# Network-free. Renders the ten canonical clinical figures from a synthetic fixture and
# asserts each figure's load-bearing elements; then confirms the structural gate FAILS on
# mutated inputs (so the assertions are proven to bite). Exit 0 = all expectations hold.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
GEN="$HERE/../render_core_figures.py"
FIX="$HERE/fixture/synthetic_inputs.json"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT

[ -f "$GEN" ] || { echo "ENV-ERR: render_core_figures.py missing" >&2; exit 2; }
python3 -c "import matplotlib, numpy" 2>/dev/null \
  || { echo "SKIP: matplotlib/numpy unavailable on this host"; exit 0; }

# (1) Positive: all ten figures render + every structural invariant holds.
python3 "$GEN" --inputs "$FIX" --out-dir "$TMP/out" >"$TMP/log" 2>&1 \
  || { echo "FAIL: valid fixture did not render/verify" >&2; cat "$TMP/log" >&2; exit 1; }
for k in km roc calibration dca forest bland_altman confusion mrmc_roc manhattan timeline; do
  [ -s "$TMP/out/$k.png" ] || { echo "FAIL: $k.png not written" >&2; exit 1; }
done
grep -q "PASS: 10 figure" "$TMP/log" || { echo "FAIL: not all ten figures verified" >&2; cat "$TMP/log" >&2; exit 1; }

# (2) Negative — the assertions must actually fire on malformed inputs.
# (2a) a KM survival curve mutated to be non-monotonic.
python3 - "$FIX" "$TMP/bad_km.json" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
d["km"]["groups"][0]["surv"] = [1.0, 0.92, 0.95, 0.74, 0.68]  # 0.81 -> 0.95 (increasing)
json.dump(d, open(sys.argv[2], "w"))
PY
if python3 "$GEN" --inputs "$TMP/bad_km.json" --out-dir "$TMP/bk" >/dev/null 2>&1; then
  echo "FAIL: a non-monotonic KM survival curve was NOT caught" >&2; exit 1
fi
# (2b) a non-square confusion matrix (label/shape mismatch).
python3 - "$FIX" "$TMP/bad_cm.json" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
d["confusion"]["matrix"] = [[85, 15, 0], [10, 90, 0]]  # 2x3, not square
json.dump(d, open(sys.argv[2], "w"))
PY
if python3 "$GEN" --inputs "$TMP/bad_cm.json" --out-dir "$TMP/bc" >/dev/null 2>&1; then
  echo "FAIL: a non-square confusion matrix was NOT caught" >&2; exit 1
fi

echo "PASS: 10 core figures render + structurally verify; the gate fails on a non-monotonic KM curve and a non-square confusion matrix."
