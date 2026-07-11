#!/usr/bin/env bash
# Deterministic verifier for the nested-group-comparison challenge card.
# cd HERE so the reported source path is the stable relative "fixture/...".
# Fixtures (synthetic only — no real manuscript, no PII):
#   nested.md — a P-value table comparing "subset (n=33)" against "full cohort
#               (n=132)" that contains it -> NESTED_GROUP_TEST.
#   clean.md  — disjoint randomised arms (n=66 / n=66) + a valid subset-vs-remainder
#               table (n=33 / n=99), both with P columns -> OK (no false positive).
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"; DET="$HERE/../check_nested_group_comparison.py"; cd "$HERE"
nested="$(python3 "$DET" --manuscript fixture/nested.md)"
clean="$(python3 "$DET" --manuscript fixture/clean.md)"
pass=1
diff -u expected/nested.txt <(printf '%s\n' "$nested") || { echo "FAIL: nested drift" >&2; pass=0; }
diff -u expected/clean.txt  <(printf '%s\n' "$clean")  || { echo "FAIL: clean drift" >&2; pass=0; }
python3 "$DET" --manuscript fixture/nested.md --strict --quiet >/dev/null 2>&1 && rn=0 || rn=$?
python3 "$DET" --manuscript fixture/clean.md  --strict --quiet >/dev/null 2>&1 && rc=0 || rc=$?
[ "${rn:-0}" -eq 1 ] || { echo "FAIL: nested should exit 1 (got ${rn:-0})" >&2; pass=0; }
[ "$rc" -eq 0 ]      || { echo "FAIL: clean should exit 0 (got $rc)" >&2; pass=0; }
[ "$pass" -eq 1 ] && echo "PASS: nested-group gate flags subset-vs-parent and clears disjoint + subset-vs-remainder." || exit 1
