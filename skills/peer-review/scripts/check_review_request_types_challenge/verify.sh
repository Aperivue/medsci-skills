#!/usr/bin/env bash
# Deterministic verifier for the review-request-type challenge card.
# cd HERE so the reported source path is the stable relative "fixture/...".
# Fixtures (synthetic only — no real review, no manuscript, no PII):
#   undisciplined.md — propagate / bootstrap / a second reader / a subset-vs-parent
#                      P value / modelling, none justified -> COMPUTATION_HEAVY,
#                      COMPUTATION_UNJUSTIFIED, NEW_DATA_REQUESTED,
#                      NESTED_P_REQUESTED, ESTIMATOR_UNNAMED.
#   disciplined.md   — the same review rewritten: disclosure asks, one computation
#                      carrying an explicit "the present tables cannot answer this",
#                      and a subset table requested *without* a significance test
#                      -> OK (no false positive on the ask that declines the invalid test).
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"; DET="$HERE/../check_review_request_types.py"; cd "$HERE"
und="$(python3 "$DET" --review fixture/undisciplined.md)"
dis="$(python3 "$DET" --review fixture/disciplined.md)"
pass=1
diff -u expected/undisciplined.txt <(printf '%s\n' "$und") || { echo "FAIL: undisciplined drift" >&2; pass=0; }
diff -u expected/disciplined.txt  <(printf '%s\n' "$dis") || { echo "FAIL: disciplined drift" >&2; pass=0; }
python3 "$DET" --review fixture/undisciplined.md --strict --quiet >/dev/null 2>&1 && ru=0 || ru=$?
python3 "$DET" --review fixture/disciplined.md   --strict --quiet >/dev/null 2>&1 && rd=0 || rd=$?
[ "${ru:-0}" -eq 1 ] || { echo "FAIL: undisciplined should exit 1 (got ${ru:-0})" >&2; pass=0; }
[ "$rd" -eq 0 ]      || { echo "FAIL: disciplined should exit 0 (got $rd)" >&2; pass=0; }
[ "$pass" -eq 1 ] && echo "PASS: request-type gate flags unjustified computation and clears a disclosure-led review." || exit 1
