#!/usr/bin/env bash
# Deterministic verifier for the test-statistic-vs-P challenge card. cd HERE for a stable
# relative source path. Pure stdlib (regularized incomplete beta / gamma) — no scipy.
# Fixtures (synthetic only — no real manuscript, no PII):
#   stat_bad.md — t(48) = 2.10, P = .041 (two-sided P 0.0410, consistent) and
#                 t(28) = 1.50, P = .03, whose two-sided P is 0.1435-0.1461 over the
#                 statistic's rounding interval [1.495, 1.505] -> 1x P_STAT_DECISION_ERROR.
#   stat_ok.md  — the same with the second P corrected to .14 -> OK.
# Reference values: scipy 1.17.1, 2*scipy.stats.t.sf(2.10, 48) = 0.041009;
#   2*scipy.stats.t.sf(1.495, 28) = 0.146101; 2*scipy.stats.t.sf(1.505, 28) = 0.143522.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"; DET="$HERE/../check_test_statistic_p.py"; cd "$HERE"
bad="$(python3 "$DET" --manuscript fixture/stat_bad.md)"; ok="$(python3 "$DET" --manuscript fixture/stat_ok.md)"
pass=1
diff -u expected/bad.txt <(printf '%s\n' "$bad") || { echo "FAIL: bad drift" >&2; pass=0; }
diff -u expected/ok.txt  <(printf '%s\n' "$ok")  || { echo "FAIL: ok drift" >&2; pass=0; }
python3 "$DET" --manuscript fixture/stat_bad.md --strict --quiet >/dev/null 2>&1 && rb=0 || rb=$?
python3 "$DET" --manuscript fixture/stat_ok.md  --strict --quiet >/dev/null 2>&1 && ro=0 || ro=$?
[ "${rb:-0}" -eq 1 ] || { echo "FAIL: bad should exit 1 (got ${rb:-0})" >&2; pass=0; }
[ "$ro" -eq 0 ]      || { echo "FAIL: ok should exit 0 (got $ro)" >&2; pass=0; }
[ "$pass" -eq 1 ] && echo "PASS: test-statistic gate flags the P that t(28) = 1.50 cannot give and clears the corrected sentence." || exit 1
