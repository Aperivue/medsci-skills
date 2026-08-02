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
STATS="$HERE/fixtures/panel_stats_lens.json"
ONE="$HERE/fixtures/panel_one_returned.json"
ROSTER4="$HERE/fixtures/roster_4.json"
ROSTER3="$HERE/fixtures/roster_3.json"
MONOSUB="$HERE/fixtures/roster_mono_substrate.json"
INDEPSUB="$HERE/fixtures/roster_indep_substrate.json"
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

# (4) a statistics reviewer using reader-study / agreement vocabulary (kappa, bootstrap,
#     permutation, odds ratio, ICC) must register as covering the 'statistics' axis, so an
#     sr_ma panel spanning all three expected axes fires NO UNCOVERED_AXIS. Regression:
#     before the statistics lexicon was broadened these classified as 'other' and the axis
#     looked uncovered, producing a false Major.
python3 "$SCRIPT" --panel "$STATS" --out "$OUT" --strict --quiet >/dev/null 2>&1
check "exit 0 (stats reviewer covers the statistics axis)" test "$?" -eq 0
check "no UNCOVERED_AXIS when statistics is covered by reader-study vocabulary" no_verdict UNCOVERED_AXIS

# (5) roster of 4 spawned reviewers, only 1 returned -> PANEL_UNDERRETURN (Major), exit 1.
#     The failure this exists for: reviewers spawn, return nothing, and the thin/empty panel
#     JSON reads as a completed run because nothing errors. The roster makes the absence visible.
python3 "$SCRIPT" --panel "$ONE" --roster "$ROSTER4" --out "$OUT" --strict --quiet >/dev/null 2>&1
check "exit 1 (1 of 4 rostered reviewers returned)" test "$?" -eq 1
check "PANEL_UNDERRETURN on under-return" has_verdict PANEL_UNDERRETURN

# (6) roster == returned set -> no PANEL_UNDERRETURN
python3 "$SCRIPT" --panel "$GOOD" --roster "$ROSTER3" --out "$OUT" --quiet >/dev/null 2>&1
check "no PANEL_UNDERRETURN when roster == returned" no_verdict PANEL_UNDERRETURN

# (7) roster-gated: without --roster the same 1-reviewer panel does NOT emit PANEL_UNDERRETURN
python3 "$SCRIPT" --panel "$ONE" --out "$OUT" --quiet >/dev/null 2>&1
check "no PANEL_UNDERRETURN without a roster (backward compatible)" no_verdict PANEL_UNDERRETURN

# (8) every returned reviewer shares the generator's substrate -> SUBSTRATE_MONOCULTURE (Major),
#     exit 1. A same-model panel inherits the generator's blind spots; it is not an independent
#     check. The roster ids match GOOD's returned set, so PANEL_UNDERRETURN does not confound.
python3 "$SCRIPT" --panel "$GOOD" --roster "$MONOSUB" --out "$OUT" --strict --quiet >/dev/null 2>&1
check "exit 1 (all reviewers share the generator substrate)" test "$?" -eq 1
check "SUBSTRATE_MONOCULTURE detected" has_verdict SUBSTRATE_MONOCULTURE

# (9) at least one different-substrate lens (codex, human) -> no SUBSTRATE_MONOCULTURE, exit 0
python3 "$SCRIPT" --panel "$GOOD" --roster "$INDEPSUB" --out "$OUT" --strict --quiet >/dev/null 2>&1
check "exit 0 (an independent lens breaks the monoculture)" test "$?" -eq 0
check "no SUBSTRATE_MONOCULTURE with an independent lens" no_verdict SUBSTRATE_MONOCULTURE

# (10) substrate-gated: a bare roster (no substrate fields) does NOT emit SUBSTRATE_MONOCULTURE
python3 "$SCRIPT" --panel "$GOOD" --roster "$ROSTER3" --out "$OUT" --quiet >/dev/null 2>&1
check "no SUBSTRATE_MONOCULTURE without substrate info (backward compatible)" no_verdict SUBSTRATE_MONOCULTURE

# (11) LENS_COLLAPSE must NOT fire on a reviewer declared on a DIFFERENT substrate from the
#      generator. In COLLAPSE, R3's families are fully subsumed by R1's; under INDEPSUB, R3 is
#      the non-claude lens — the very one whose presence stops SUBSTRATE_MONOCULTURE (case 9).
#      Firing here told the editor that the panel's only independent lens "added no independent
#      axis", i.e. to consider dropping it. Agreement reached from another substrate is
#      corroboration, not a redundant assignment. Observed live in a Codex-reviewer panel.
python3 "$SCRIPT" --panel "$COLLAPSE" --roster "$INDEPSUB" --out "$OUT" --strict --quiet >/dev/null 2>&1
check "exit 0 (cross-substrate reviewer is not a collapsed lens)" test "$?" -eq 0
check "no LENS_COLLAPSE on a cross-substrate reviewer" no_verdict LENS_COLLAPSE
check "the exemption is recorded, not silent" python3 -c "
import json
d=json.load(open('$OUT'))
ex=d['summary'].get('lens_collapse_substrate_exempt')
assert ex == ['R3'], f'expected R3 recorded as exempt, got {ex!r}'
"

# (12) ...and the exemption is NOT a blanket disable: the same panel with an all-same-substrate
#      roster must still raise LENS_COLLAPSE on R3. Without this, case (11) could be passed by
#      simply deleting the check.
python3 "$SCRIPT" --panel "$COLLAPSE" --roster "$MONOSUB" --out "$OUT" --quiet >/dev/null 2>&1
check "LENS_COLLAPSE still fires when the redundant lens shares the generator substrate" \
    has_verdict LENS_COLLAPSE
check "nothing exempted when every substrate matches the generator" python3 -c "
import json
d=json.load(open('$OUT'))
ex=d['summary'].get('lens_collapse_substrate_exempt')
assert ex == [], f'expected no exemptions, got {ex!r}'
"

# (13) substrate-gated, as everywhere else: with no substrate info the pre-existing behaviour
#      is unchanged — LENS_COLLAPSE fires exactly as it did before this exemption existed.
python3 "$SCRIPT" --panel "$COLLAPSE" --roster "$ROSTER3" --out "$OUT" --quiet >/dev/null 2>&1
check "LENS_COLLAPSE unchanged on a roster without substrate fields" has_verdict LENS_COLLAPSE

echo "fail=$fail"; [[ "$fail" -eq 0 ]] && echo "ALL PASS" || echo "FAILURES: $fail"
exit "$fail"
