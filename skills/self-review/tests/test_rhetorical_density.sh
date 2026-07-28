#!/usr/bin/env bash
# Regression test for the rhetorical-construction density gate (P27 / §J — antithesis
# parallelism and cleft, the two sentence-structure AI tells a per-instance rule misses).
# Synthetic, PII-free fixtures. Two cases carrying the SAME argument, differing only in how
# their sentences are built:
#   (1) rhetorical_dense.md — a run of "rather than" / "not X but Y" / "X, not Y" plus
#       sentence-initial "What … is …" / "It is … that …" -> ANTITHESIS_DENSITY AND
#       CLEFT_DENSITY both fire.
#   (2) rhetorical_clean.md — the same argument written in plain subject-verb order, with
#       exactly ONE functional "rather than" and ONE cleft used sparingly -> silent. The
#       single cleft's density even clears the per-1000 line; it stays silent because the
#       raw count (1) is below the floor (3), which is the AND(floor, density) contract.
# Run at shipped defaults so the test exercises the real thresholds. Stdlib-only.
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$HERE/../scripts/check_rhetorical_density.py"
FX="$HERE/fixtures"
OUT="$(mktemp -t rhetorical_XXXX).json"
trap 'rm -f "$OUT"' EXIT

fail=0
check() { local label="$1"; shift
    if "$@" >/dev/null 2>&1; then printf '  PASS  %s\n' "$label"
    else printf '  FAIL  %s\n' "$label"; fail=$((fail+1)); fi
}
run() { python3 "$SCRIPT" --manuscript "$1" --out "$OUT" --quiet >/dev/null 2>&1; }
has_verdict() { python3 -c "import json,sys; d=json.load(open('$OUT')); sys.exit(0 if '$1' in {f['verdict'] for f in d['findings']} else 1)"; }
no_findings() { python3 -c "import json,sys; sys.exit(0 if not json.load(open('$OUT'))['findings'] else 1)"; }

[[ -f "$SCRIPT" ]] || { echo "ENV-ERR: script missing" >&2; exit 2; }

# (1) antithesis + cleft dense prose -> both verdicts fire
run "$FX/rhetorical_dense.md"
check "dense fixture fires ANTITHESIS_DENSITY" has_verdict ANTITHESIS_DENSITY
check "dense fixture fires CLEFT_DENSITY" has_verdict CLEFT_DENSITY

# (2) explanatory prose (same argument, sparse functional use) -> silent
run "$FX/rhetorical_clean.md"
check "clean fixture does not fire (functional antithesis + one sparing cleft)" no_findings
check "clean fixture: one cleft below the count floor stays silent despite crossing density" python3 -c "
import json
d = json.load(open('$OUT'))
assert not d['findings'], d['findings']
# the single functional cleft pushes density over the 2.5 line, yet count (1) < floor (3)
assert d['metrics']['cleft_per_1000'] > 2.5, d['metrics']
"

# (3) the JSON envelope names its own detector (check_detector_envelopes contract)
check "envelope self-identifies the detector" python3 -c "
import json
assert json.load(open('$OUT'))['detector'] == 'check_rhetorical_density'
"

echo "fail=$fail"; [[ "$fail" -eq 0 ]] && echo "ALL PASS" || echo "FAILURES: $fail"
exit "$fail"
