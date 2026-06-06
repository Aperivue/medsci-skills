#!/usr/bin/env bash
# Regression test for verify-refs Gate 6 (pagination-placeholder detection).
# Offline (no network): a bib entry whose pages are "e000--e000" with an "in press"
# note must get note="pagination_placeholder"; a normal entry must not. verify-refs
# stays manuscript-agnostic — it only flags; the P0/centrality call is /self-review's.
# Stdlib-only (python3).
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$HERE/../scripts/verify_refs.py"
BIB="$HERE/fixtures/pagination_placeholder.bib"
ROOT="$(mktemp -d -t vrp_XXXX)"
trap 'rm -rf "$ROOT"' EXIT

fail=0
check() { local label="$1"; shift
    if "$@" >/dev/null 2>&1; then printf '  PASS  %s\n' "$label"
    else printf '  FAIL  %s\n' "$label"; fail=$((fail+1)); fi
}

[[ -f "$SCRIPT" ]] || { echo "ENV-ERR: script missing" >&2; exit 2; }

python3 "$SCRIPT" "$BIB" --project-root "$ROOT" --offline >/dev/null 2>&1
AUDIT="$ROOT/qc/reference_audit.json"
check "audit JSON written" test -s "$AUDIT"

assert_py() { python3 -c "
import json
d = json.load(open('$AUDIT'))
recs = {r['ref_id']: r for r in d['records']}
$1
"; }

check "placeholder entry flagged note=pagination_placeholder" \
    assert_py "assert 'pagination_placeholder' in recs['methodref_inpress'].get('note',''), recs['methodref_inpress']"
check "placeholder entry status UNVERIFIED" \
    assert_py "assert recs['methodref_inpress']['status']=='UNVERIFIED', recs['methodref_inpress']['status']"
check "normal entry NOT flagged" \
    assert_py "assert 'pagination_placeholder' not in recs['normalref_2025'].get('note',''), recs['normalref_2025']"

echo "fail=$fail"; [[ "$fail" -eq 0 ]] && echo "ALL PASS" || echo "FAILURES: $fail"
exit "$fail"
