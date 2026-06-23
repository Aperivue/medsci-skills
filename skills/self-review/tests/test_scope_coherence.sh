#!/usr/bin/env bash
# Regression test for the scope-coherence gate (self-review §D).
# Synthetic, PII-free fixtures reproduce: (a) a cross-sectional design with a
# prognostic/surveillance conclusion (CROSS_SECTIONAL_PROGNOSTIC), (b) a binary
# surrogate endpoint driving a care directive (SURROGATE_CARE_DIRECTIVE). The clean
# fixture is a longitudinal cohort with an association conclusion.
# Stdlib-only (python3).
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$HERE/../scripts/check_scope_coherence.py"
BAD="$HERE/fixtures/scope_bad.md"
SURR="$HERE/fixtures/scope_surrogate.md"
CLEAN="$HERE/fixtures/scope_clean.md"
OUT="$(mktemp -t scope_XXXX).json"
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

[[ -f "$SCRIPT" ]] || { echo "ENV-ERR: script missing" >&2; exit 2; }

# (1) cross-sectional + prognostic conclusion -> CROSS_SECTIONAL_PROGNOSTIC, exit 1
python3 "$SCRIPT" --manuscript "$BAD" --out "$OUT" --strict --quiet >/dev/null 2>&1
check "exit 1 (cross-sectional prognostic)" test "$?" -eq 1
check "CROSS_SECTIONAL_PROGNOSTIC detected" has_verdict CROSS_SECTIONAL_PROGNOSTIC

# (2) binary surrogate + care directive -> SURROGATE_CARE_DIRECTIVE, exit 1
python3 "$SCRIPT" --manuscript "$SURR" --out "$OUT" --strict --quiet >/dev/null 2>&1
check "exit 1 (surrogate care directive)" test "$?" -eq 1
check "SURROGATE_CARE_DIRECTIVE detected" has_verdict SURROGATE_CARE_DIRECTIVE

# (3) longitudinal cohort + association conclusion -> exit 0
python3 "$SCRIPT" --manuscript "$CLEAN" --strict --quiet >/dev/null 2>&1
check "exit 0 on clean manuscript" test "$?" -eq 0

# (4) cross-sectional + yield/detection-rate language, undefined -> Minor flag
YIELD="$HERE/fixtures/scope_yield.md"
YDEF="$HERE/fixtures/scope_yield_defined.md"
python3 "$SCRIPT" --manuscript "$YIELD" --out "$OUT" --quiet >/dev/null 2>&1
check "CROSS_SECTIONAL_YIELD_LANGUAGE detected" has_verdict CROSS_SECTIONAL_YIELD_LANGUAGE
python3 "$SCRIPT" --manuscript "$YIELD" --strict --quiet >/dev/null 2>&1
check "yield flag is Minor (no Major -> exit 0 under --strict)" test "$?" -eq 0

# (5) yield explicitly defined as cross-sectional prevalence -> suppressed
python3 "$SCRIPT" --manuscript "$YDEF" --out "$OUT" --quiet >/dev/null 2>&1
check "yield definition suppresses the flag" python3 -c "
import json
d=json.load(open('$OUT'))
assert not any(c['verdict']=='CROSS_SECTIONAL_YIELD_LANGUAGE' for c in d['claims'])
"

# (6) cross-sectional design + a DISCLAIMED surveillance/prognostic token
#     ("... rather than surveillance intervals ... which would require prospective
#     data ...") -> NO CROSS_SECTIONAL_PROGNOSTIC, exit 0 (regression).
DISC="$HERE/fixtures/scope_disclaimer.md"
python3 "$SCRIPT" --manuscript "$DISC" --out "$OUT" --quiet >/dev/null 2>&1
check "no CROSS_SECTIONAL_PROGNOSTIC when disclaimed" python3 -c "
import json
d=json.load(open('$OUT'))
assert not any(c['verdict']=='CROSS_SECTIONAL_PROGNOSTIC' for c in d['claims']), 'disclaimer flagged as prognostic claim'
"
python3 "$SCRIPT" --manuscript "$DISC" --strict --quiet >/dev/null 2>&1
check "exit 0 on disclaimer manuscript" test "$?" -eq 0

echo "fail=$fail"; [[ "$fail" -eq 0 ]] && echo "ALL PASS" || echo "FAILURES: $fail"
exit "$fail"
