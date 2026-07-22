#!/usr/bin/env bash
# Deterministic verifier for the exclusion-code-validity challenge card.
#   Positive: a code excludes a design the protocol INCLUDES (single-arm), plus an
#             unregistered code and a renumbered code -> 3 verdicts, exit 1.
#   Negative: the SAME "no comparative data" code is correct because the protocol
#             REQUIRES a comparator -> 0 verdicts, exit 0.
# No network. Exit 0 = both stages match expectations.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
DET="$HERE/../check_exclusion_code_validity.py"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

# --- Positive: must flag the study-loss code, the unregistered code, the rename ---
set +e
python3 "$DET" \
  --protocol "$HERE/fixture/protocol_positive.md" \
  --screening "$HERE/fixture/screening_positive.tsv" \
  --strict --quiet --out "$tmp/pos.json"
pos_rc=$?
set -e

for v in CODE_CONTRADICTS_ELIGIBILITY CODE_NOT_REGISTERED CODE_RENUMBERED; do
  if ! grep -q "\"verdict\": \"$v\"" "$tmp/pos.json"; then
    echo "FAIL: positive fixture did not emit $v" >&2
    cat "$tmp/pos.json" >&2
    exit 1
  fi
done
if [ "$pos_rc" -ne 1 ]; then
  echo "FAIL: positive fixture must exit 1 under --strict (2 Major); got $pos_rc" >&2
  exit 1
fi
if ! grep -q '"detector": "check_exclusion_code_validity"' "$tmp/pos.json"; then
  echo "FAIL: JSON envelope does not self-identify the detector" >&2
  exit 1
fi

# --- Negative: the same code is correct here; nothing must fire ---
set +e
python3 "$DET" \
  --protocol "$HERE/fixture/protocol_negative.md" \
  --screening "$HERE/fixture/screening_negative.tsv" \
  --strict --quiet --out "$tmp/neg.json"
neg_rc=$?
set -e

if [ "$neg_rc" -ne 0 ]; then
  echo "FAIL: negative fixture must exit 0; got $neg_rc" >&2
  cat "$tmp/neg.json" >&2
  exit 1
fi
if grep -qE '"verdict": "CODE_' "$tmp/neg.json"; then
  echo "FAIL: negative fixture emitted a claim verdict (false positive)" >&2
  cat "$tmp/neg.json" >&2
  exit 1
fi

echo "PASS: positive flags CONTRADICTS+NOT_REGISTERED+RENUMBERED (exit 1); negative is clean (exit 0)."
