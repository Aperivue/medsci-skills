#!/usr/bin/env bash
# Deterministic verifier for the baseline-drift challenge card.
# Network-free, stdlib-only. The gate is advisory, so every run must exit 0 -- framing
# drift is a judgment call the author owns; the gate flags it, it never blocks.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
DET="$HERE/../check_baseline_drift.py"
cd "$HERE"

pass=1
check() {  # name  args...
  local name="$1"; shift
  local got; got="$(python3 "$DET" "$@")"
  if ! diff -u "expected/$name.txt" <(printf '%s\n' "$got"); then
    echo "FAIL: $name output drifted from expected/$name.txt" >&2; pass=0
  fi
  python3 "$DET" "$@" --strict --quiet >/dev/null 2>&1 && rc=0 || rc=$?
  if [ "${rc:-0}" -ne 0 ]; then
    echo "FAIL: $name must exit 0 (advisory, even under --strict); got ${rc:-0}" >&2; pass=0
  fi
}

check drifted    --manuscript fixture/drifted.md    --baseline fixture/baseline.md
check overhedged --manuscript fixture/overhedged.md --baseline fixture/baseline.md
check stable     --manuscript fixture/stable.md     --baseline fixture/baseline.md
check nobaseline --manuscript fixture/baseline.md

# The inflated draft must carry all three inflation verdicts in the JSON artifact;
# the legitimate reword (stable) and the no-baseline path must carry none.
tmp="$(mktemp)"
python3 "$DET" --manuscript fixture/drifted.md --baseline fixture/baseline.md --out "$tmp" --quiet
for v in STRENGTH_INFLATION SIGNIFICANCE_INFLATION_DRIFT SCOPE_INFLATION_DRIFT; do
  grep -q "\"verdict\": \"$v\"" "$tmp" || { echo "FAIL: drifted JSON missing $v" >&2; pass=0; }
done
python3 "$DET" --manuscript fixture/stable.md --baseline fixture/baseline.md --out "$tmp" --quiet
grep -q '"verdict": "OK"' "$tmp" || { echo "FAIL: stable JSON should be OK (no drift)" >&2; pass=0; }
python3 "$DET" --manuscript fixture/baseline.md --out "$tmp" --quiet
grep -q '"n_claims": 0' "$tmp" || { echo "FAIL: no-baseline JSON should have 0 findings" >&2; pass=0; }
rm -f "$tmp"

if [ "$pass" -eq 1 ]; then
  echo "PASS: baseline-drift flags strength/significance/scope inflation and cumulative hedge accretion vs the human baseline, clears a legitimate reword, and is a no-op without a baseline."
else
  exit 1
fi
