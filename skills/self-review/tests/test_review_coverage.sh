#!/usr/bin/env bash
# Regression test for check_review_coverage.py (self-review Phase 3c coverage ledger).
# The challenge card covers the four verdict paths; this test covers input validation (every
# malformed ledger exits 2 and names the field), BOM acceptance, and the legacy path under --strict.
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$HERE/../scripts/check_review_coverage.py"
FIX="$HERE/../scripts/check_review_coverage_challenge/fixture"
WORK="$(mktemp -d -t rcov_test_XXXX)"
trap 'rm -rf "$WORK"' EXIT
fail=0
[[ -f "$SCRIPT" ]] || { echo "ENV-ERR: script missing" >&2; exit 2; }

# mutate <name> <python expression on d> : write a mutated copy of pass_complete.json
mutate() {
  python3 - "$FIX/pass_complete.json" "$WORK/$1.json" "$2" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
exec(sys.argv[3])
open(sys.argv[2], "w").write(json.dumps(d))
PY
}

# expect_err <label> <file> <substring expected on stderr>
expect_err() {
  local rc=0 err
  err="$(python3 "$SCRIPT" --review "$2" --quiet 2>&1 >/dev/null)" || rc=$?
  if [ "$rc" -eq 2 ] && grep -qF -- "$3" <<<"$err"; then printf '  PASS  %s\n' "$1"
  else printf '  FAIL  %s (rc=%s, stderr=%s)\n' "$1" "$rc" "$err"; fail=$((fail+1)); fi
}

mutate missing_letter 'del d["coverage"]["categories"]["K"]'
expect_err "a missing category letter exits 2" "$WORK/missing_letter.json" "coverage.categories: missing ['K']"
mutate unknown_letter 'd["coverage"]["categories"]["M"] = {"status": "assessed", "evidence": ["x"]}'
expect_err "an unknown category key exits 2" "$WORK/unknown_letter.json" "unknown key(s) ['M']"
mutate no_evidence 'd["coverage"]["categories"]["C"] = {"status": "assessed"}'
expect_err "assessed without evidence exits 2" "$WORK/no_evidence.json" "coverage.categories.C.evidence: required"
mutate empty_evidence 'd["coverage"]["categories"]["C"] = {"status": "assessed", "evidence": []}'
expect_err "assessed with an empty evidence list exits 2" "$WORK/empty_evidence.json" "coverage.categories.C.evidence: required"
mutate na_no_reason 'd["coverage"]["categories"]["K"] = {"status": "not_applicable"}'
expect_err "not_applicable without a reason exits 2" "$WORK/na_no_reason.json" "coverage.categories.K.reason: required"
mutate bad_status 'd["coverage"]["categories"]["A"]["status"] = "partial"'
expect_err "an unknown status exits 2" "$WORK/bad_status.json" "coverage.categories.A.status: 'partial'"
mutate bad_probe 'd["coverage"]["probes"]["not_a_module"] = {"status": "assessed", "evidence": ["x"]}'
expect_err "an unknown probe module exits 2" "$WORK/bad_probe.json" "unknown module(s) ['not_a_module']"
mutate no_probes 'del d["coverage"]["probes"]'
expect_err "a ledger without probes exits 2" "$WORK/no_probes.json" "coverage.probes: required"
mutate bad_verdict 'd["verdict"] = "ACCEPT"'
expect_err "an unknown verdict exits 2" "$WORK/bad_verdict.json" "verdict: 'ACCEPT'"
mutate no_verdict 'del d["verdict"]'
expect_err "a missing verdict exits 2" "$WORK/no_verdict.json" "verdict: None"
printf '{"verdict": "PASS", "overall_score": NaN}' > "$WORK/nan.json"
expect_err "NaN is rejected" "$WORK/nan.json" "NaN is not a valid JSON number"
printf '{"verdict": "PASS",' > "$WORK/trunc.json"
expect_err "truncated JSON exits 2" "$WORK/trunc.json" "not valid JSON"
printf '[1, 2]' > "$WORK/list.json"
expect_err "a top-level list exits 2" "$WORK/list.json" "expected a JSON object"
expect_err "a missing file exits 2" "$WORK/absent.json" "cannot read"

# A UTF-8 BOM (Windows editors) is accepted and does not change the result.
printf '\xef\xbb\xbf' > "$WORK/bom.json"; cat "$FIX/pass_complete.json" >> "$WORK/bom.json"
if python3 "$SCRIPT" --review "$WORK/bom.json" --strict --quiet; then printf '  PASS  %s\n' "BOM accepted"
else printf '  FAIL  %s\n' "BOM accepted"; fail=$((fail+1)); fi

# Lenient forms an LLM-written ledger uses: an empty optional reason, evidence as one string.
python3 -c "
import json,sys; d=json.load(open(sys.argv[1]))
c=d['coverage']['categories']
c['A']['evidence']=c['A'].get('evidence',['x'])[0] if c['A']['status']=='assessed' else c['A'].get('evidence')
d['verdict']='REVISE'; c['B']={'status':'not_assessed','reason':''}
json.dump(d,open(sys.argv[2],'w'))" "$FIX/pass_complete.json" "$WORK/lenient.json"
rc=0; python3 "$SCRIPT" --review "$WORK/lenient.json" --strict --quiet || rc=$?
if [ "$rc" -eq 0 ]; then printf '  PASS  %s\n' "empty optional reason and string evidence are accepted"
else printf '  FAIL  %s\n' "lenient ledger forms (rc=$rc)"; fail=$((fail+1)); fi
# Category L is advisory: a not_assessed L under PASS is Minor, not Major.
python3 -c "
import json,sys; d=json.load(open(sys.argv[1]))
d['verdict']='PASS'; d['coverage']['categories']['L']={'status':'not_assessed'}
json.dump(d,open(sys.argv[2],'w'))" "$FIX/pass_complete.json" "$WORK/pass_l_gap.json"
rc=0; python3 "$SCRIPT" --review "$WORK/pass_l_gap.json" --strict --quiet --out "$WORK/pass_l_out.json" || rc=$?
if [ "$rc" -eq 0 ] && python3 -c "
import json,sys; d=json.load(open(sys.argv[1]))
assert d['summary']['n_major']==0 and any(c['verdict']=='COVERAGE_GAP' for c in d['claims'])" "$WORK/pass_l_out.json"
then printf '  PASS  %s\n' "PASS with category L not_assessed: Minor COVERAGE_GAP, exit 0"
else printf '  FAIL  %s\n' "category L under PASS (rc=$rc)"; fail=$((fail+1)); fi

# The legacy path (no coverage object) is NOT_ASSESSED: exit 0 normally, exit 2 under --strict.
rc=0; python3 "$SCRIPT" --review "$FIX/legacy_no_coverage.json" --quiet --out "$WORK/legacy_out.json" || rc=$?
rcs=0; python3 "$SCRIPT" --review "$FIX/legacy_no_coverage.json" --strict --quiet || rcs=$?
if [ "$rc" -eq 0 ] && [ "$rcs" -eq 2 ] && python3 -c "
import json,sys; d=json.load(open(sys.argv[1]))
assert d['detector']=='check_review_coverage' and d['basis']=='declared'
assert d['summary']['verdict']=='NOT_ASSESSED' and d['summary']['n_minor']==1 and d['summary']['n_major']==0
assert d['claims'][0]['verdict']=='COVERAGE_NOT_RECORDED'" "$WORK/legacy_out.json"
then printf '  PASS  %s\n' "legacy JSON: NOT_ASSESSED + COVERAGE_NOT_RECORDED, exit 0 / 2 under --strict"
else printf '  FAIL  %s\n' "legacy JSON path (rc=$rc, strict rc=$rcs)"; fail=$((fail+1)); fi

# A not_assessed probe module under PASS is Major too, not only a category.
mutate probe_gap_pass 'd["coverage"]["probes"]["observational_confounding"] = {"status": "not_assessed"}'
rc=0; python3 "$SCRIPT" --review "$WORK/probe_gap_pass.json" --strict --quiet || rc=$?
if [ "$rc" -eq 1 ]; then printf '  PASS  %s\n' "PASS over a not_assessed probe module exits 1 under --strict"
else printf '  FAIL  %s (rc=%s)\n' "probe gap under PASS" "$rc"; fail=$((fail+1)); fi

echo "fail=$fail"; [[ "$fail" -eq 0 ]] && echo "ALL PASS" || echo "FAILURES: $fail"
exit "$fail"
