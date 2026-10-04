#!/usr/bin/env bash
# Deterministic verifier for the self-review coverage-ledger challenge card.
# Runs check_review_coverage.py on four synthetic self_review.json files, diffs stdout against
# expected/, and asserts the --strict exit codes and the summary.verdict of each run.
# Stdlib-only, network-free. Fixtures are synthetic (no real manuscript, no PII).
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
DET="$HERE/../check_review_coverage.py"
cd "$HERE"
TMP="$(mktemp -d -t rcov_XXXX)"
trap 'rm -rf "$TMP"' EXIT

pass=1
for f in pass_gap pass_complete revise_gap legacy_no_coverage; do
  out="$(python3 "$DET" --review "fixture/$f.json" 2>/dev/null)"
  if ! diff -u "expected/$f.txt" <(printf '%s\n' "$out"); then
    echo "FAIL: $f stdout drifted from expected/$f.txt" >&2; pass=0
  fi
done

# exit code under --strict, and summary.verdict + claim codes from the JSON artifact
check() {  # check <fixture> <expected rc> <expected summary.verdict> <expected sorted codes, comma-joined>
  local f="$1" want_rc="$2" want_v="$3" want_codes="$4" rc=0
  python3 "$DET" --review "fixture/$f.json" --out "$TMP/$f.json" --strict --quiet 2>/dev/null || rc=$?
  [ "$rc" -eq "$want_rc" ] || { echo "FAIL: $f exit $rc, expected $want_rc" >&2; pass=0; }
  got="$(python3 -c "import json,sys; d=json.load(open(sys.argv[1])); print(d['detector'], d['summary']['verdict'], ','.join(sorted(c['verdict'] for c in d['claims'])))" "$TMP/$f.json")"
  [ "$got" = "check_review_coverage $want_v $want_codes" ] \
    || { echo "FAIL: $f got '$got', expected 'check_review_coverage $want_v $want_codes'" >&2; pass=0; }
}
check pass_gap 1 MAJOR_CANDIDATE COVERAGE_GAP_PASS
check pass_complete 0 OK ""
check revise_gap 0 OK COVERAGE_GAP,COVERAGE_GAP
check legacy_no_coverage 2 NOT_ASSESSED COVERAGE_NOT_RECORDED

if [ "$pass" -eq 1 ]; then
  echo "PASS: a PASS over a not_assessed category is Major; the same review fully covered is silent; gaps under REVISE are Minor and do not fail --strict; a legacy JSON without a ledger is NOT_ASSESSED (exit 2 under --strict)."
else
  exit 1
fi
