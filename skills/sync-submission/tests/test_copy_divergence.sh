#!/usr/bin/env bash
# Regression test for the multi-copy manuscript divergence detector (Phase 8).
# Synthetic fixtures: an SSOT and two copies — one reworded but claim-complete
# (OK), one missing an SSOT claim (p = 0.074, an unpropagated edit). Stdlib-only.
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$HERE/../scripts/detect_copy_divergence.py"
SSOT="$HERE/fixtures/ssot.md"
OKC="$HERE/fixtures/copy_ok.md"
STALE="$HERE/fixtures/copy_stale.md"
OUT="$(mktemp -t cd_XXXX).json"
trap 'rm -f "$OUT"' EXIT

fail=0
check() { local label="$1"; shift
    if "$@" >/dev/null 2>&1; then printf '  PASS  %s\n' "$label"
    else printf '  FAIL  %s\n' "$label"; fail=$((fail+1)); fi
}

[[ -f "$SCRIPT" ]] || { echo "ENV-ERR: script missing" >&2; exit 2; }

# OK copy alone -> exit 0.
python3 "$SCRIPT" --ssot "$SSOT" --copy "$OKC" --strict >/dev/null 2>&1
check "exit 0 when the copy carries every SSOT claim" test "$?" -eq 0

# Stale copy -> exit 1, flags the unpropagated claim.
python3 "$SCRIPT" --ssot "$SSOT" --copy "$OKC" --copy "$STALE" --out "$OUT" --strict >/dev/null 2>&1
check "exit 1 when a copy is missing an SSOT claim" test "$?" -eq 1
check "verdict DIVERGENT" python3 -c "
import json; assert json.load(open('$OUT'))['verdict']=='DIVERGENT'"
check "stale copy flags the unpropagated p-value" python3 -c "
import json
d=json.load(open('$OUT'))
stale=[c for c in d['copies'] if c['verdict']=='STALE_COPY']
assert stale and any('p=0.074' in u for u in stale[0]['unpropagated_to_copy'])"
check "OK copy not flagged" python3 -c "
import json
d=json.load(open('$OUT'))
ok=[c for c in d['copies'] if c['copy'].endswith('copy_ok.md')]
assert ok and ok[0]['verdict']=='OK'"

# (F2) A copy that received the new number but KEPT the old one beside it carries every
# SSOT claim, so a set difference alone cleared it. A numeric claim only the copy makes
# is a stale number left behind -> STALE_COPY.
WORK="$(mktemp -d -t cd_work_XXXX)"
trap 'rm -f "$OUT"; rm -rf "$WORK"' EXIT
cp "$SSOT" "$WORK/leftover.md"
printf '%s\n' "Sensitivity analysis: the analytic cohort comprised n = 990 participants." >> "$WORK/leftover.md"
python3 "$SCRIPT" --ssot "$SSOT" --copy "$WORK/leftover.md" --out "$OUT" --strict >/dev/null 2>&1
check "exit 1 when a copy keeps a number the SSOT no longer states" test "$?" -eq 1
check "stale_in_copy names the leftover n" python3 -c "
import json
d=json.load(open('$OUT')); c=d['copies'][0]
assert c['verdict']=='STALE_COPY' and c['stale_in_copy']==['n=990'] and not c['unpropagated_to_copy']"

# NEGATIVE: a copy-only HEADING (a circulation cover note) stays advisory, not stale.
cp "$SSOT" "$WORK/note.md"
printf '%s\n' "## Note to co-authors" "Please send comments by Friday." >> "$WORK/note.md"
python3 "$SCRIPT" --ssot "$SSOT" --copy "$WORK/note.md" --out "$OUT" --strict >/dev/null 2>&1
check "exit 0 when a copy only adds a heading" test "$?" -eq 0
check "copy-only heading listed but verdict OK" python3 -c "
import json
d=json.load(open('$OUT')); c=d['copies'][0]
assert c['verdict']=='OK' and c['copy_only']==['h:notetoco-authors'] and c['stale_in_copy']==[]"

# A named --copy that does not exist is an input error (exit 2), never a clean pass.
python3 "$SCRIPT" --ssot "$SSOT" --copy "$WORK/does_not_exist.md" --strict >/dev/null 2>&1
check "exit 2 when a named copy is missing" test "$?" -eq 2

echo "fail=$fail"; [[ "$fail" -eq 0 ]] && echo "ALL PASS" || echo "FAILURES: $fail"
exit "$fail"
