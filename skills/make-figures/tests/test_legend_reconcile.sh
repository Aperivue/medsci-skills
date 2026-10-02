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
FX="$HERE/fixtures"
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

# Header on its own line, caption after a blank line: the caption is the next paragraph, not
# the empty header (main read no counts and cleared the stale 1,150).
python3 "$SCRIPT" --flow-config "$FLOW" --manuscript "$FX/manuscript_stale_header_blank.md" --out "$OUT" --strict >/dev/null 2>&1
check "header + blank line: stale caption exits 1" test "$?" -eq 1
check "header + blank line: 1150 flagged" python3 -c "
import json; d=json.load(open('$OUT'))
assert 1150 in d['stale_in_caption'], d"
# Negative control: same layout, caption matches; a later Figure 2 count is not read as Figure 1.
python3 "$SCRIPT" --flow-config "$FLOW" --manuscript "$FX/manuscript_ok_header_blank.md" --out "$OUT" --strict >/dev/null 2>&1
check "header + blank line: matching caption exits 0" test "$?" -eq 0
check "header + blank line: verdict OK, Figure 2 not read" python3 -c "
import json; d=json.load(open('$OUT'))
assert d['verdict']=='OK' and d['caption_counts']==[286, 998, 1284], d"

# A check that could not run is never an OK under --strict.
python3 "$SCRIPT" --flow-config "$FLOW" --manuscript "$FX/manuscript_no_caption.md" --out "$OUT" --strict >/dev/null 2>&1
check "no Figure 1 caption exits 2 under --strict" test "$?" -eq 2
check "no Figure 1 caption verdict NOT_CHECKED" python3 -c "
import json; assert json.load(open('$OUT'))['verdict']=='NOT_CHECKED'"
python3 "$SCRIPT" --flow-config "$FLOW" --manuscript "$FX/manuscript_no_counts.md" --strict >/dev/null 2>&1
check "caption without any 'n = N' exits 2 under --strict" test "$?" -eq 2
python3 "$SCRIPT" --flow-config "$FLOW" --manuscript "$FX/manuscript_no_counts.md" >/dev/null 2>&1
check "caption without any 'n = N' report-only exits 0" test "$?" -eq 0
python3 "$SCRIPT" --flow-config "$FX/manuscript_no_counts.md" --manuscript "$OK" --strict >/dev/null 2>&1
check "flow config with no 'n = N' count exits 2" test "$?" -eq 2

echo "fail=$fail"; [[ "$fail" -eq 0 ]] && echo "ALL PASS" || echo "FAILURES: $fail"
exit "$fail"
