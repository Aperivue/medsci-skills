#!/usr/bin/env bash
# Deterministic verifier for the Model Card / Datasheet completeness challenge.
# Network-free, stdlib-only. Exit 0 = the gate passes a complete card+datasheet and
# flags an incomplete one (missing section + unfilled placeholder).
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
DET="$HERE/../check_model_card_complete.py"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT

# (1) complete card + datasheet -> OK, exit 0
python3 "$DET" --card "$HERE/fixture/complete/MODEL_CARD.md" \
  --datasheet "$HERE/fixture/complete/DATASHEET.md" --strict --quiet \
  || { echo "FAIL: a complete Model Card + Datasheet should pass (exit 0)" >&2; exit 1; }

# (2) incomplete card -> exit 1 with MISSING_SECTION (Out-of-Scope) + EMPTY (Caveats)
python3 "$DET" --card "$HERE/fixture/incomplete/MODEL_CARD.md" --out "$TMP/inc.json" --strict --quiet \
  && { echo "FAIL: an incomplete Model Card should exit 1 under --strict" >&2; exit 1; } || true
python3 - "$TMP/inc.json" <<'PY' || exit 1
import json, sys
d = json.load(open(sys.argv[1]))
v = {c["verdict"] for c in d["claims"]}
assert "MISSING_SECTION" in v, "expected MISSING_SECTION (Out-of-Scope Use absent)"
assert "EMPTY_REQUIRED_SECTION" in v, "expected EMPTY_REQUIRED_SECTION (Caveats unfilled)"
det = " ".join(c["detail"] for c in d["claims"])
assert "Out-of-Scope Use" in det and "Caveats" in det, det
print("  incomplete card flagged: MISSING(Out-of-Scope) + EMPTY(Caveats)")
PY

# (3) the unfilled templates themselves must fail (the gate exists to force filling)
python3 "$DET" --card "$HERE/../../references/model_card_template.md" --strict --quiet \
  && { echo "FAIL: the unfilled template should not pass" >&2; exit 1; } || true
echo "  unfilled template correctly fails"

echo "PASS: completeness gate accepts a filled Model Card+Datasheet and flags missing/unfilled sections."
