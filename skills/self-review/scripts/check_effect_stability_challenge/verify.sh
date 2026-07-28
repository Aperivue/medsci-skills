#!/usr/bin/env bash
# Deterministic verifier for the effect-stability challenge card.
# Runs check_effect_stability.py on two synthetic manuscripts and diffs stdout
# against expected/. Stdlib-only, network-free. Exit 0 = both match and exit codes
# are correct. cd into HERE so the reported source path is the stable relative
# "fixture/..." (portable across CI checkout locations).
#
# Fixtures (synthetic only — no real manuscript, no PII):
#   effect_bad.md — Conclusions "OR 50.9; 95% CI 5.8-443.6" (76-fold, no caveat) +
#                   Methods "19 events for 2 covariates" (EPV 9.5)
#                   -> UNSTABLE_EFFECT_ESTIMATE + EPV_LOW.
#   effect_ok.md  — a tight CI (OR 2.4; 1.3-4.4, ratio 3.4) plus the SAME wide CI
#                   explicitly labelled "exploratory and imprecise ... a direction
#                   rather than a magnitude" -> silent (caveat suppresses the flag,
#                   tight CI is below threshold). The precision control.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
DET="$HERE/../check_effect_stability.py"
cd "$HERE"

bad="$(python3 "$DET" --manuscript fixture/effect_bad.md)"
ok="$(python3 "$DET" --manuscript fixture/effect_ok.md)"

pass=1
if ! diff -u expected/bad.txt <(printf '%s\n' "$bad"); then
  echo "FAIL: bad-fixture output drifted from expected/bad.txt" >&2; pass=0
fi
if ! diff -u expected/ok.txt <(printf '%s\n' "$ok"); then
  echo "FAIL: ok-fixture output drifted from expected/ok.txt" >&2; pass=0
fi

python3 "$DET" --manuscript fixture/effect_bad.md --strict --quiet >/dev/null 2>&1 && rc_bad=0 || rc_bad=$?
python3 "$DET" --manuscript fixture/effect_ok.md  --strict --quiet >/dev/null 2>&1 && rc_ok=0  || rc_ok=$?
[ "${rc_bad:-0}" -eq 1 ] || { echo "FAIL: bad fixture should exit 1 under --strict (got ${rc_bad:-0})" >&2; pass=0; }
[ "$rc_ok" -eq 0 ]       || { echo "FAIL: ok fixture should exit 0 under --strict (got $rc_ok)" >&2; pass=0; }

if [ "$pass" -eq 1 ]; then
  echo "PASS: effect-stability gate flags the 76-fold interval + low EPV and clears the tight CI + caveat-labelled control."
else
  exit 1
fi
