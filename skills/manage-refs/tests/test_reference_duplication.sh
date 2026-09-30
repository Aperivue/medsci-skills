#!/usr/bin/env bash
# Regression test for the duplicate-bibliography gate (manage-refs / sync-submission).
# Synthetic, PII-free fixtures: a rendered manuscript with TWO reference lists
# (a hand-typed list + a second list concatenated after the figure legends, the
# pandoc-citeproc-duplication pattern) vs a clean single-list manuscript.
# Stdlib-only (python3).
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$HERE/../scripts/check_reference_duplication.py"
DUP="$HERE/fixtures/refdup_text.md"
CLEAN="$HERE/fixtures/refclean_text.md"
OUT="$(mktemp -t refdup_XXXX).json"
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

echo "test_reference_duplication:"

# (1) duplicated bibliography -> Major -> exit 1 under --strict
python3 "$SCRIPT" --text "$DUP" --out "$OUT" --strict --quiet >/dev/null 2>&1
check "exit 1 under --strict (Major present)" test "$?" -eq 1
check "JSON artifact written" test -s "$OUT"
check "DUP_REF_HEADING detected (two References headings)" has_verdict DUP_REF_HEADING
check "REF_NUMBER_RESTART detected (entry '1.' twice)"     has_verdict REF_NUMBER_RESTART
check "REF_SIGNATURE_DUP detected (whole list repeated)"   has_verdict REF_SIGNATURE_DUP

# (2) single bibliography -> exit 0, no claim
python3 "$SCRIPT" --text "$CLEAN" --out "$OUT" --strict --quiet >/dev/null 2>&1
check "exit 0 on single reference list" test "$?" -eq 0
check "no claims on clean fixture" bash -c "
python3 -c \"import json; d=json.load(open('$OUT')); assert not d['claims']\"
"

# (3) every entry counts: a surname with a lowercase particle ("van der ...", "de ...")
#     and a year-leading guideline entry used to fail ENTRY_RE, so a 4-entry list was
#     reported as 1 entry.
PART="$HERE/fixtures/refcount_particles.md"
python3 "$SCRIPT" --text "$PART" --out "$OUT" --strict --quiet >/dev/null 2>&1
check "exit 0 on a single particle/guideline list" test "$?" -eq 0
check "4-entry list with particle + year-leading entries counts 4" python3 -c "
import json; d=json.load(open('$OUT')); assert d['ref_entries']==4, d['ref_entries']
"

# (4) the same list duplicated (no second heading) -> the entries the old regex dropped
#     are what carry the restart/signature evidence, so the duplication must now be Major.
PDUP="$HERE/fixtures/refdup_particles.md"
python3 "$SCRIPT" --text "$PDUP" --out "$OUT" --strict --quiet >/dev/null 2>&1
check "exit 1 under --strict on a duplicated particle/guideline list" test "$?" -eq 1
check "REF_SIGNATURE_DUP on a duplicated particle/guideline list" has_verdict REF_SIGNATURE_DUP

if [[ "$fail" -eq 0 ]]; then echo "  ALL PASS"; else echo "  $fail FAILED"; fi
exit "$fail"
