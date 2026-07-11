#!/usr/bin/env bash
# Deterministic verifier for the reported-P-from-counts challenge card. cd HERE for
# a stable relative source path. Pure stdlib (math.comb / math.erfc) — no scipy.
# Fixtures (synthetic only — no real manuscript, no PII):
#   p_bad.md — a 2-group baseline table; the Male row reproduces at 0.237
#              (uncorrected Pearson, so the family calibrates) while the
#              Adenocarcinoma row claims P<0.001 whose true value is ~0.06 under
#              every family -> 1x P_NOT_REPRODUCIBLE.
#   p_ok.md  — same table with the Adenocarcinoma P corrected to 0.060 -> OK.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"; DET="$HERE/../check_reported_p_from_counts.py"; cd "$HERE"
bad="$(python3 "$DET" --manuscript fixture/p_bad.md)"; ok="$(python3 "$DET" --manuscript fixture/p_ok.md)"
pass=1
diff -u expected/bad.txt <(printf '%s\n' "$bad") || { echo "FAIL: bad drift" >&2; pass=0; }
diff -u expected/ok.txt  <(printf '%s\n' "$ok")  || { echo "FAIL: ok drift" >&2; pass=0; }
python3 "$DET" --manuscript fixture/p_bad.md --strict --quiet >/dev/null 2>&1 && rb=0 || rb=$?
python3 "$DET" --manuscript fixture/p_ok.md  --strict --quiet >/dev/null 2>&1 && ro=0 || ro=$?
[ "${rb:-0}" -eq 1 ] || { echo "FAIL: bad should exit 1 (got ${rb:-0})" >&2; pass=0; }
[ "$ro" -eq 0 ]      || { echo "FAIL: ok should exit 0 (got $ro)" >&2; pass=0; }
[ "$pass" -eq 1 ] && echo "PASS: reported-P gate flags the non-reproducible p<0.001 and clears the corrected table." || exit 1
