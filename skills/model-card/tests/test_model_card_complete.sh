#!/usr/bin/env bash
# Regression test for the Model Card / Datasheet completeness gate (model-card).
# Synthetic, PII-free. Stdlib-only (python3).
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DET="$HERE/../scripts/check_model_card_complete.py"
CH="$HERE/../scripts/check_model_card_complete_challenge"
REF="$HERE/../references"
OUT="$(mktemp -t mcc_XXXX).json"
trap 'rm -f "$OUT"' EXIT

fail=0
check() { local label="$1"; shift
    if "$@" >/dev/null 2>&1; then printf '  PASS  %s\n' "$label"
    else printf '  FAIL  %s\n' "$label"; fail=$((fail+1)); fi
}
has() { python3 -c "
import json
d=json.load(open('$OUT'))
assert any(c['verdict']=='$1' for c in d['claims']), '$1 not found'"; }
count() { python3 -c "
import json
d=json.load(open('$OUT'))
assert len(d['claims'])==$1, f\"{len(d['claims'])} != $1\""; }

[[ -f "$DET" ]] || { echo "ENV-ERR: detector missing" >&2; exit 2; }

# (1) complete card + datasheet -> OK, exit 0
python3 "$DET" --card "$CH/fixture/complete/MODEL_CARD.md" --datasheet "$CH/fixture/complete/DATASHEET.md" --strict --quiet >/dev/null 2>&1
check "complete card+datasheet passes (exit 0)" test "$?" -eq 0

# (2) incomplete card -> exit 1, MISSING + EMPTY
python3 "$DET" --card "$CH/fixture/incomplete/MODEL_CARD.md" --out "$OUT" --strict --quiet >/dev/null 2>&1
check "incomplete card exits 1" test "$?" -eq 1
check "MISSING_SECTION detected" has MISSING_SECTION
check "EMPTY_REQUIRED_SECTION detected" has EMPTY_REQUIRED_SECTION

# (3) unfilled Model Card template -> all 9 required sections empty
python3 "$DET" --card "$REF/model_card_template.md" --out "$OUT" --strict --quiet >/dev/null 2>&1
check "unfilled card template exits 1" test "$?" -eq 1
check "9 empty sections in unfilled card template" count 9

# (4) unfilled card + datasheet templates -> 9 + 7 = 16 empty
python3 "$DET" --card "$REF/model_card_template.md" --datasheet "$REF/datasheet_template.md" --out "$OUT" --quiet >/dev/null 2>&1
check "16 empty sections across both unfilled templates" count 16

# (5) "N/A" / "None" count as a filled answer (not flagged empty)
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"; rm -f "$OUT"' EXIT
cat > "$TMP/card.md" <<'MD'
# Model Card: t
## Model Details
- **Type**: U-Net
## Intended Use
- triage
## Out-of-Scope Use
- N/A
## Training Data
- 100 patients
## Evaluation Data
- internal split
## Metrics
- Dice with CI
## Quantitative Analyses
- Dice 0.8
## Ethical Considerations
- None
## Caveats and Recommendations
- single centre
MD
python3 "$DET" --card "$TMP/card.md" --out "$OUT" --strict --quiet >/dev/null 2>&1
check "N/A and None count as filled (exit 0)" test "$?" -eq 0

echo "fail=$fail"; [[ "$fail" -eq 0 ]] && echo "ALL PASS" || echo "FAILURES: $fail"
exit "$fail"
