#!/usr/bin/env bash
# Regression test for the editorial-impression / defensiveness gate (self-review §L).
# Synthetic, PII-free fixtures: (a) an over-defensive manuscript that trips all six
# probes (HEDGE_DENSITY, HEDGE_REPEAT, AUDIT_IN_BODY, LIMITATIONS_VOLUME,
# ABSTRACT_CAVEAT_LOAD, BURIED_DEFENSE); (b) a confident clean manuscript that trips
# none (false-positive guard). The gate is advisory and non-blocking — it must exit 0
# even under --strict, since it emits no Major.
# Stdlib-only (python3).
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$HERE/../scripts/check_editorial_impression.py"
DEF="$HERE/fixtures/editorial_defensive.md"
CLEAN="$HERE/fixtures/editorial_clean.md"
OUT="$(mktemp -t editorial_XXXX).json"
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

# (1) defensive fixture -> all six verdicts fire
python3 "$SCRIPT" --manuscript "$DEF" --out "$OUT" --quiet >/dev/null 2>&1
for v in HEDGE_DENSITY HEDGE_REPEAT AUDIT_IN_BODY LIMITATIONS_VOLUME ABSTRACT_CAVEAT_LOAD BURIED_DEFENSE; do
    check "$v detected (defensive)" has_verdict "$v"
done

# (2) every claim carries a SUBTRACTION action in {REMOVE, MOVE, TIGHTEN}
check "every claim has a REMOVE/MOVE/TIGHTEN action" python3 -c "
import json
d=json.load(open('$OUT'))
assert d['claims'], 'expected findings'
assert all(c.get('action') in ('REMOVE','MOVE','TIGHTEN') for c in d['claims']), 'bad action'
assert all(c.get('severity')=='Minor' for c in d['claims']), 'all findings must be Minor (advisory)'
"

# (3) advisory / non-blocking: exit 0 even under --strict on a fully-flagged manuscript
python3 "$SCRIPT" --manuscript "$DEF" --strict --quiet >/dev/null 2>&1
check "exit 0 under --strict (non-blocking)" test "$?" -eq 0

# (4) clean fixture -> zero claims (false-positive guard)
python3 "$SCRIPT" --manuscript "$CLEAN" --out "$OUT" --quiet >/dev/null 2>&1
check "clean manuscript yields no flags" python3 -c "
import json
d=json.load(open('$OUT'))
assert d['summary']['n_claims']==0, d['claims']
"
python3 "$SCRIPT" --manuscript "$CLEAN" --strict --quiet >/dev/null 2>&1
check "exit 0 on clean manuscript" test "$?" -eq 0

# (5) YAML front matter is not narrative. The clean manuscript with a changelog block that
#     says "hypothesis-generating" four times used to fire HEDGE_REPEAT ("appears 4 times")
#     although the body never says it.
FM="$HERE/fixtures/editorial_frontmatter_hedges.md"
python3 "$SCRIPT" --manuscript "$FM" --out "$OUT" --quiet >/dev/null 2>&1
check "hedge tokens only in YAML front matter yield no flags" python3 -c "
import json
d=json.load(open('$OUT'))
assert d['summary']['n_claims']==0, d['claims']
"
# Positive control: the same front matter + three body mentions -> HEDGE_REPEAT counts the
# body's 3, not 3 + the YAML's 4.
FMPOS="$(mktemp -t editorial_fmpos_XXXX).md"
trap 'rm -f "$OUT" "$FMPOS"' EXIT
python3 - "$FM" "$FMPOS" <<'PY'
import sys
src = open(sys.argv[1]).read()
extra = ("\n## Conclusion\n\nThe marker is hypothesis-generating. Its subgroup result is "
         "hypothesis-generating. The threshold analysis is hypothesis-generating.\n")
open(sys.argv[2], "w").write(src + extra)
PY
python3 "$SCRIPT" --manuscript "$FMPOS" --out "$OUT" --quiet >/dev/null 2>&1
check "body hedges still fire, counted without the YAML (appears 3 times)" python3 -c "
import json
d=json.load(open('$OUT'))
r=[c for c in d['claims'] if c['verdict']=='HEDGE_REPEAT' and 'hypothesis_generating' in c['detail']]
assert r and 'appears 3 times' in r[0]['detail'], d['claims']
"

echo "fail=$fail"; [[ "$fail" -eq 0 ]] && echo "ALL PASS" || echo "FAILURES: $fail"
exit "$fail"
