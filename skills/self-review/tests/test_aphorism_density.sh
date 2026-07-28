#!/usr/bin/env bash
# Regression test for the aphorism-density gate (P26 / §J — the sentence-rhythm AI tell).
# Synthetic, PII-free fixtures. Three cases:
#   (1) aphorism_dense.md  — the same argument written as epigrams -> APHORISM_DENSITY fires
#   (2) aphorism_clean.md  — the same argument written as explanation -> no finding
#   (3) aphorism_frontmatter.md — a `status:`/build-note YAML block full of short negative
#       definitions, over a body of ordinary explanatory prose. The front matter must be
#       stripped before the rhythm is measured; otherwise its lines are counted as body
#       "very short declaratives" and the detector fires on the changelog. Body-only rate
#       is 0/0, so the no-fire here is the fix, not the min-sentences floor (6 sentences).
# Uses --min-sentences 6 so the small A/B fixtures clear the noise floor. Stdlib-only.
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$HERE/../scripts/check_aphorism_density.py"
FX="$HERE/fixtures"
OUT="$(mktemp -t aphorism_XXXX).json"
trap 'rm -f "$OUT"' EXIT

fail=0
check() { local label="$1"; shift
    if "$@" >/dev/null 2>&1; then printf '  PASS  %s\n' "$label"
    else printf '  FAIL  %s\n' "$label"; fail=$((fail+1)); fi
}
run() { python3 "$SCRIPT" --manuscript "$1" --min-sentences 6 --out "$OUT" --quiet >/dev/null 2>&1; }
fired()     { python3 -c "import json,sys; sys.exit(0 if json.load(open('$OUT'))['findings'] else 1)"; }
not_fired() { python3 -c "import json,sys; sys.exit(0 if not json.load(open('$OUT'))['findings'] else 1)"; }

[[ -f "$SCRIPT" ]] || { echo "ENV-ERR: script missing" >&2; exit 2; }

# (1) epigram-dense prose -> APHORISM_DENSITY
run "$FX/aphorism_dense.md"
check "epigram-dense fixture fires APHORISM_DENSITY" fired

# (2) explanatory prose (same argument) -> silent
run "$FX/aphorism_clean.md"
check "explanatory fixture does not fire" not_fired

# (3) YAML front-matter changelog must not be measured as body rhythm
run "$FX/aphorism_frontmatter.md"
check "front-matter build/status block does not fire (stripped before measuring)" not_fired
check "no front-matter line is counted as a short declarative" python3 -c "
import json
d=json.load(open('$OUT'))
lines=[s for f in d['findings'] for s in f.get('short_declaratives',[])]
assert not any('SSOT' in s or 'is not' in s for s in lines), lines
assert d['metrics']['sentences']==6, d['metrics']  # body-only sentence count
"

echo "fail=$fail"; [[ "$fail" -eq 0 ]] && echo "ALL PASS" || echo "FAILURES: $fail"
exit "$fail"
