#!/usr/bin/env bash
# Deterministic verifier for the portal-field-residue challenge card.
#   Positive: two paste-verbatim .txt files carry all six residue kinds + the "≥/≤"
#             char-expansion advisory -> exit 1.
#   Negative: clean text with the FP traps (significance stars, ~approx, 1~2 range,
#             bare URL, and a "×"/en-dash the portal leaves alone) -> nothing fires, exit 0.
# No network. Exit 0 = both stages match expectations.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
DET="$HERE/../check_portal_field_residue.py"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

# --- Positive: every residue kind must be flagged ---
set +e
python3 "$DET" --dir "$HERE/fixture/positive" --quiet --out "$tmp/pos.json"
pos_rc=$?
set -e

for k in hr bold heading link superscript subscript char_expansion; do
  if ! grep -q "\"kind\": \"$k\"" "$tmp/pos.json"; then
    echo "FAIL: positive fixture did not flag residue kind '$k'" >&2
    cat "$tmp/pos.json" >&2
    exit 1
  fi
done
if [ "$pos_rc" -ne 1 ]; then
  echo "FAIL: positive fixture must exit 1 (residue found); got $pos_rc" >&2
  exit 1
fi
if ! grep -q '"detector": "check_portal_field_residue"' "$tmp/pos.json"; then
  echo "FAIL: JSON envelope does not self-identify the detector" >&2
  exit 1
fi

# --- Negative: the FP traps must NOT fire ---
set +e
python3 "$DET" --dir "$HERE/fixture/negative" --quiet --out "$tmp/neg.json"
neg_rc=$?
set -e

if [ "$neg_rc" -ne 0 ]; then
  echo "FAIL: negative fixture must exit 0; got $neg_rc" >&2
  cat "$tmp/neg.json" >&2
  exit 1
fi
if grep -qE '"kind":' "$tmp/neg.json"; then
  echo "FAIL: negative fixture flagged residue (false positive)" >&2
  cat "$tmp/neg.json" >&2
  exit 1
fi

echo "PASS: positive flags all six residue kinds + the ≥/≤ char-expansion advisory (exit 1); negative with FP traps (incl. × and en-dash) is clean (exit 0)."
