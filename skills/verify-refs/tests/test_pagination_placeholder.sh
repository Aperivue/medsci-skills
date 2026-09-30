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

# The run above is offline, so every record is UNVERIFIED before Gate 6 runs and the status
# assertion cannot fail. Online, a resolved reference is OK — call the gate on such a record
# directly. (Gate 6 once compared against a "VERIFIED" status the script never emits, so an
# in-press/e000 reference stayed OK and passed --strict.)
gate6() { python3 - "$SCRIPT" "$1" <<'PY'
import importlib.util, sys
spec = importlib.util.spec_from_file_location("vr", sys.argv[1]); vr = importlib.util.module_from_spec(spec)
sys.modules["vr"] = vr; spec.loader.exec_module(vr)
rec = vr.RefRecord(ref_id="x", raw="Smith J. A trial. J Test. 2026;e000-e000. In press.")
rec.status = sys.argv[2]
vr.flag_pagination_placeholder(rec)
print(rec.status)
PY
}
check "resolved (OK) placeholder entry downgraded to UNVERIFIED" test "$(gate6 OK)" = UNVERIFIED
check "worse status (MISMATCH) left unchanged" test "$(gate6 MISMATCH)" = MISMATCH

echo "fail=$fail"; [[ "$fail" -eq 0 ]] && echo "ALL PASS" || echo "FAILURES: $fail"
exit "$fail"
