#!/usr/bin/env bash
# Deterministic verifier for the incorporation-bias challenge card.
# Runs check_incorporation_bias.py on two synthetic manuscripts and diffs stdout
# against expected/. Stdlib-only, network-free. cd into HERE so the reported source
# path is the stable relative "fixture/...".
#
# Fixtures (synthetic only — no real manuscript, no PII):
#   incorp_bad.md — reference standard defines benign by resolution/decrease/stability
#                   (a size trajectory) AND Results reports "Growth ... associated with
#                   malignancy (OR 50.9)" -> INCORPORATION_BIAS (the predictor is the
#                   reference standard).
#   incorp_ok.md  — reference standard is surgical pathology + imaging follow-up (no
#                   trajectory tier); the growth-OR is then independent -> silent.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
DET="$HERE/../check_incorporation_bias.py"
cd "$HERE"

bad="$(python3 "$DET" --manuscript fixture/incorp_bad.md)"
ok="$(python3 "$DET" --manuscript fixture/incorp_ok.md)"

pass=1
diff -u expected/bad.txt <(printf '%s\n' "$bad") || { echo "FAIL: bad drifted" >&2; pass=0; }
diff -u expected/ok.txt  <(printf '%s\n' "$ok")  || { echo "FAIL: ok drifted"  >&2; pass=0; }
python3 "$DET" --manuscript fixture/incorp_bad.md --strict --quiet >/dev/null 2>&1 && rb=0 || rb=$?
python3 "$DET" --manuscript fixture/incorp_ok.md  --strict --quiet >/dev/null 2>&1 && ro=0 || ro=$?
[ "${rb:-0}" -eq 1 ] || { echo "FAIL: bad should exit 1 (got ${rb:-0})" >&2; pass=0; }
[ "$ro" -eq 0 ]      || { echo "FAIL: ok should exit 0 (got $ro)" >&2; pass=0; }

[ "$pass" -eq 1 ] && echo "PASS: incorporation-bias gate flags the trajectory-standard/trajectory-predictor overlap and clears the pathology-standard control." || exit 1
