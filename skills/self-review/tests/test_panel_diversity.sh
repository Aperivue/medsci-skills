#!/usr/bin/env bash
# Regression test for the panel lens-diversity gate (self-review Phase 2.6).
# Synthetic, PII-free reviewer-output fixtures reproduce: (a) a healthy panel
# spanning three distinct axes (clean), (b) a monoculture where every major
# falls in one family AND two expected axes are uncovered (UNCOVERED_AXIS +
# FAMILY_MONOCULTURE), (c) a fully-redundant reviewer lens (LENS_COLLAPSE).
# Stdlib-only (python3).
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$HERE/../scripts/check_panel_diversity.py"
GOOD="$HERE/fixtures/panel_good.json"
MONO="$HERE/fixtures/panel_monoculture.json"
COLLAPSE="$HERE/fixtures/panel_collapse.json"
OUT="$(mktemp -t paneldiv_XXXX).json"
trap 'rm -f "$OUT"' EXIT

fail=0
check() { local label="$1"; shift
    if "$@" >/dev/null 2>&1; then printf '  PASS  %s\n' "$label"
    else printf '  FAIL  %s\n' "$label"; fail=$((fail+1)); fi
}
has_verdict() { python3 -c "
import json,sys
d=json.load(open('$OUT'))
assert any(c['verdict']=='$1' for c in d['claims']), '$1 not found'
"; }
no_verdict() { python3 -c "
import json,sys
d=json.load(open('$OUT'))
assert all(c['verdict']!='$1' for c in d['claims']), '$1 unexpectedly found'
"; }

[[ -f "$SCRIPT" ]] || { echo "ENV-ERR: script missing" >&2; exit 2; }

# (1) healthy diverse panel (sr_ma) -> exit 0, no Major claims
python3 "$SCRIPT" --panel "$GOOD" --out "$OUT" --strict --quiet >/dev/null 2>&1
check "exit 0 (diverse panel)" test "$?" -eq 0
check "no UNCOVERED_AXIS on clean panel" no_verdict UNCOVERED_AXIS
check "no FAMILY_MONOCULTURE on clean panel" no_verdict FAMILY_MONOCULTURE

# (2) monoculture + uncovered axes -> exit 1 with both Major verdicts
python3 "$SCRIPT" --panel "$MONO" --out "$OUT" --strict --quiet >/dev/null 2>&1
check "exit 1 (monoculture)" test "$?" -eq 1
check "UNCOVERED_AXIS detected" has_verdict UNCOVERED_AXIS
check "FAMILY_MONOCULTURE detected" has_verdict FAMILY_MONOCULTURE

# (3) fully-redundant reviewer (no research type) -> LENS_COLLAPSE flag, exit 0
python3 "$SCRIPT" --panel "$COLLAPSE" --out "$OUT" --strict --quiet >/dev/null 2>&1
check "exit 0 (collapse is flag-only)" test "$?" -eq 0
check "LENS_COLLAPSE detected" has_verdict LENS_COLLAPSE
check "no UNCOVERED_AXIS without research type" no_verdict UNCOVERED_AXIS

echo "fail=$fail"; [[ "$fail" -eq 0 ]] && echo "ALL PASS" || echo "FAILURES: $fail"
exit "$fail"
