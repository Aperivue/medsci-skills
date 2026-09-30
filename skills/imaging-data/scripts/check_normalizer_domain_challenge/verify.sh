#!/usr/bin/env bash
# Deterministic verifier for the normaliser-domain challenge card.
# Runs check_normalizer_domain.py on two synthetic profiles against one synthetic CT contract and
# diffs stdout against expected/. No network, no imaging library, no pixels — every verdict is
# decided by comparing five summary numbers per case against the contract. Exit 0 = both match and
# both exit codes are correct.
#
# Fixtures (synthetic only — no real patients, no PII):
#   profile_hu.json         12 cases, every one with an air floor near -1024. Under a CT contract
#                           this MUST be clean: it is exactly the cohort the contract was fit on,
#                           and a check that rejects its own training domain is worse than none.
#   profile_arbitrary.json  10 cases with no negative voxel at all (NORMALIZER_DOMAIN_MISMATCH,
#                           Major) plus a pool where 6 of 10 bottom out near air and the rest do
#                           not (NORMALIZER_SPLIT_DIVERGENCE, Flag).
#   plan_ct.json            an nnU-Net-shaped plan declaring CTNormalization.
#
# The third case this card guards is the contract loader: an unreadable contract must FAIL rather
# than score as "assumes arbitrary" and return OK. A gate that passes on input it could not read
# looks exactly like a gate that passed.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
DET="$HERE/../check_normalizer_domain.py"

clean="$(python3 "$DET" --profile "$HERE/fixture/profile_hu.json"        --contract "$HERE/fixture/plan_ct.json")"
bad="$(  python3 "$DET" --profile "$HERE/fixture/profile_arbitrary.json" --contract "$HERE/fixture/plan_ct.json")"

ok=1
diff -u "$HERE/expected/hu_clean.txt"            <(printf '%s\n' "$clean") || { echo "FAIL: HU fixture drifted" >&2; ok=0; }
diff -u "$HERE/expected/arbitrary_mismatch.txt"  <(printf '%s\n' "$bad")   || { echo "FAIL: mismatch fixture drifted" >&2; ok=0; }

python3 "$DET" --profile "$HERE/fixture/profile_hu.json"        --contract "$HERE/fixture/plan_ct.json" --strict >/dev/null 2>&1 && rc_clean=0 || rc_clean=$?
python3 "$DET" --profile "$HERE/fixture/profile_arbitrary.json" --contract "$HERE/fixture/plan_ct.json" --strict >/dev/null 2>&1 && rc_bad=0   || rc_bad=$?
[ "$rc_clean" -eq 0 ]     || { echo "FAIL: the contract's own CT domain must exit 0 (got $rc_clean)" >&2; ok=0; }
[ "${rc_bad:-0}" -eq 1 ]  || { echo "FAIL: the domain mismatch must exit 1 under --strict (got ${rc_bad:-0})" >&2; ok=0; }

# an unreadable contract must refuse, not quietly pass
echo '{"not_a_contract": true}' > "$HERE/.tmp_bad_contract.json"
python3 "$DET" --profile "$HERE/fixture/profile_hu.json" --contract "$HERE/.tmp_bad_contract.json" >/dev/null 2>&1 && rc_unread=0 || rc_unread=$?
rm -f "$HERE/.tmp_bad_contract.json"
[ "${rc_unread:-0}" -ne 0 ] || { echo "FAIL: an unreadable contract must not return success" >&2; ok=0; }

if [ "$ok" -eq 1 ]; then
  echo "PASS: the gate clears its own CT domain, flags an arbitrary-unit cohort and a mixed split, and refuses an unreadable contract."
else
  exit 1
fi
