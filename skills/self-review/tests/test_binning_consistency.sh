#!/usr/bin/env bash
# Regression test for the cross-script categorical / definition-consistency gate
# (Phase 2.5b/c). Synthetic, PII-free fixtures cover two failure modes:
#   BINNING_DRIFT     — a derived `age_band` binned with two different cut
#                       signatures (45/50/60 right=FALSE vs 44/49/59 right=TRUE)
#                       across two scripts, plus a clean pair sharing one signature.
#   DERIVED_DEF_DRIFT — a composite indicator (`mets_bp`/`mets_fg`) defined with a
#                       dropped OR-clause across two scripts, plus a clean pair that
#                       is identical up to clause order / whitespace / outer parens /
#                       commutative `&`-operand order.
# Stdlib-only (python3).
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$HERE/../scripts/check_binning_consistency.py"
DRIFT="$HERE/fixtures/binning_drift"
CLEAN="$HERE/fixtures/binning_clean"
DDRIFT="$HERE/fixtures/derived_drift"
DCLEAN="$HERE/fixtures/derived_clean"
OUT="$(mktemp -t bin_XXXX).json"
trap 'rm -f "$OUT"' EXIT

fail=0
check() { local label="$1"; shift
    if "$@" >/dev/null 2>&1; then printf '  PASS  %s\n' "$label"
    else printf '  FAIL  %s\n' "$label"; fail=$((fail+1)); fi
}
has_verdict() { python3 -c "
import json
d=json.load(open('$OUT'))
assert any(c['verdict']=='$1' for c in d['claims']), '$1 not found'
"; }

[[ -f "$SCRIPT" ]] || { echo "ENV-ERR: script missing" >&2; exit 2; }

echo "test_binning_consistency:"

# (1) drift fixtures: BINNING_DRIFT (Major) -> exit 1 under --strict
python3 "$SCRIPT" --root "$DRIFT" --out "$OUT" --strict --quiet >/dev/null 2>&1
check "exit 1 under --strict (Major present)" test "$?" -eq 1
check "JSON artifact written" test -s "$OUT"
check "BINNING_DRIFT detected (45/50/60 right=FALSE vs 44/49/59 right=TRUE)" has_verdict BINNING_DRIFT

# (2) clean fixtures: identical cut signature -> exit 0, no claim
python3 "$SCRIPT" --root "$CLEAN" --strict --quiet >/dev/null 2>&1
check "exit 0 on consistent binning" test "$?" -eq 0
python3 "$SCRIPT" --root "$CLEAN" --out "$OUT" --quiet >/dev/null 2>&1
check "no BINNING_DRIFT on clean fixtures" bash -c "
python3 -c \"import json; d=json.load(open('$OUT')); assert not d['claims']\"
"

# (3) composite-definition drift: DERIVED_DEF_DRIFT (Major) -> exit 1 under --strict
python3 "$SCRIPT" --root "$DDRIFT" --out "$OUT" --strict --quiet >/dev/null 2>&1
check "exit 1 under --strict (composite clause dropped)" test "$?" -eq 1
check "DERIVED_DEF_DRIFT detected (mets_bp/mets_fg clause omission)" has_verdict DERIVED_DEF_DRIFT

# (4) clean composite fixtures: same atom SET (reordered / whitespace / parens /
#     commutative &) -> exit 0, no claim
python3 "$SCRIPT" --root "$DCLEAN" --strict --quiet >/dev/null 2>&1
check "exit 0 on order-/whitespace-/paren-equivalent composite defs" test "$?" -eq 0
python3 "$SCRIPT" --root "$DCLEAN" --out "$OUT" --quiet >/dev/null 2>&1
check "no DERIVED_DEF_DRIFT on clean composite fixtures" bash -c "
python3 -c \"import json; d=json.load(open('$OUT')); assert not d['claims']\"
"

if [[ "$fail" -eq 0 ]]; then echo "  ALL PASS"; else echo "  $fail FAILED"; fi
exit "$fail"
