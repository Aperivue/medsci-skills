#!/usr/bin/env bash
# Regression test for the Figure 1 caption ↔ flow-SSOT reconciler.
# Synthetic fixtures: a flow config with counts {1284, 286, 998}; an OK caption
# that matches, and a stale caption citing 1,150 (absent from the diagram).
# Stdlib-only (python3).
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$HERE/../scripts/derive_figure_legend_counts.py"
FLOW="$HERE/fixtures/figure1_flow.yaml"
OK="$HERE/fixtures/manuscript_ok.md"
STALE="$HERE/fixtures/manuscript_stale.md"
OUT="$(mktemp -t fl_XXXX).json"
trap 'rm -f "$OUT"' EXIT

fail=0
check() { local label="$1"; shift
    if "$@" >/dev/null 2>&1; then printf '  PASS  %s\n' "$label"
    else printf '  FAIL  %s\n' "$label"; fail=$((fail+1)); fi
}

[[ -f "$SCRIPT" ]] || { echo "ENV-ERR: script missing" >&2; exit 2; }

python3 "$SCRIPT" --flow-config "$FLOW" --manuscript "$OK" --strict >/dev/null 2>&1
check "exit 0 when caption matches the flow SSOT" test "$?" -eq 0

python3 "$SCRIPT" --flow-config "$FLOW" --manuscript "$STALE" --out "$OUT" --strict >/dev/null 2>&1
check "exit 1 when caption cites a count absent from the flow SSOT" test "$?" -eq 1
check "stale count 1150 flagged" python3 -c "
import json; d=json.load(open('$OUT'))
assert 1150 in d['stale_in_caption'], d['stale_in_caption']"
check "verdict MISMATCH" python3 -c "
import json; assert json.load(open('$OUT'))['verdict']=='MISMATCH'"

echo "fail=$fail"; [[ "$fail" -eq 0 ]] && echo "ALL PASS" || echo "FAILURES: $fail"
exit "$fail"
