#!/usr/bin/env bash
# Deterministic verifier for the paired-difference-estimator challenge card. cd HERE
# for a stable relative source path.
# Fixtures (synthetic only — no real manuscript, no PII):
#   paired_bad.md — "median paired difference 0.5" over n=153 (odd) 4-point integer
#                   scores, a 95% CI of 0.5–0.5, and no estimator named
#                   -> MEDIAN_PARITY + DEGENERATE_CI + ESTIMATOR_UNNAMED.
#   paired_ok.md  — a Hodges–Lehmann pseudomedian 0.5 (95% CI 0.0 to 1.0) with the
#                   estimator named -> OK (a pseudomedian may be half-integer).
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"; DET="$HERE/../check_paired_difference_estimator.py"; cd "$HERE"
bad="$(python3 "$DET" --manuscript fixture/paired_bad.md)"; ok="$(python3 "$DET" --manuscript fixture/paired_ok.md)"
pass=1
diff -u expected/bad.txt <(printf '%s\n' "$bad") || { echo "FAIL: bad drift" >&2; pass=0; }
diff -u expected/ok.txt  <(printf '%s\n' "$ok")  || { echo "FAIL: ok drift" >&2; pass=0; }
python3 "$DET" --manuscript fixture/paired_bad.md --strict --quiet >/dev/null 2>&1 && rb=0 || rb=$?
python3 "$DET" --manuscript fixture/paired_ok.md  --strict --quiet >/dev/null 2>&1 && ro=0 || ro=$?
[ "${rb:-0}" -eq 1 ] || { echo "FAIL: bad should exit 1 (got ${rb:-0})" >&2; pass=0; }
[ "$ro" -eq 0 ]      || { echo "FAIL: ok should exit 0 (got $ro)" >&2; pass=0; }
[ "$pass" -eq 1 ] && echo "PASS: paired-difference gate flags the impossible median + degenerate CI + unnamed estimator." || exit 1
