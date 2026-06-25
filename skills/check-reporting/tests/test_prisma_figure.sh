#!/usr/bin/env bash
# Regression test for the PRISMA Figure 1 arithmetic + cross-reference audit
# (check-reporting Step 4d / check_prisma_figure.py). Synthetic, PII-free fixtures.
# Stdlib-only (python3); no network, no pandoc.
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$HERE/../scripts/check_prisma_figure.py"
BODY="$HERE/fixtures/prisma_body.md"
CLEAN="$HERE/fixtures/prisma_fig_clean.md"
MM="$HERE/fixtures/prisma_fig_mismatch.md"
OUT="$(mktemp -t prisma_fig_XXXX).json"
trap 'rm -f "$OUT"' EXIT

for f in "$SCRIPT" "$BODY" "$CLEAN" "$MM"; do
  [[ -f "$f" ]] || { echo "ENV-ERR: missing $f" >&2; exit 2; }
done

fail=0
pass() { printf '  PASS  %s\n' "$1"; }
bad()  { printf '  FAIL  %s\n' "$1"; fail=$((fail+1)); }

echo "test_prisma_figure:"

# 1. Clean figure (numbers match body, arithmetic consistent) -> audit_safe, exit 0.
python3 "$SCRIPT" --md "$BODY" --figure "$CLEAN" --out "$OUT" >/dev/null 2>&1; rc=$?
if [[ $rc -eq 0 ]] && python3 -c "import json,sys; sys.exit(0 if json.load(open('$OUT'))['audit_safe'] else 1)"; then
  pass "clean body/figure -> audit_safe, exit 0"
else
  bad "clean case rc=$rc (expected 0 + audit_safe)"
fi

# 2. Mismatched figure (included 149 vs body 150) -> MISMATCH, exit 1, PRISMA-FIGURE flag.
out="$(python3 "$SCRIPT" --md "$BODY" --figure "$MM" --out "$OUT" 2>&1)"; rc=$?
if [[ $rc -eq 1 && "$out" == *"[PRISMA-FIGURE]"* ]] \
   && python3 -c "import json,sys; d=json.load(open('$OUT')); sys.exit(0 if (not d['audit_safe'] and d['action_items']) else 1)"; then
  pass "mismatched figure -> MISMATCH flagged, exit 1"
else
  bad "mismatch case rc=$rc (expected 1 + [PRISMA-FIGURE] + action_items)"
fi

# 3. Missing input -> clean error, exit 2 (no traceback).
err="$(python3 "$SCRIPT" --md /nonexistent_prisma.md --figure "$CLEAN" --out "$OUT" 2>&1)"; rc=$?
if [[ $rc -eq 2 && "$err" == *"not found"* && "$err" != *"Traceback"* ]]; then
  pass "missing manuscript -> clean error, exit 2"
else
  bad "missing-input case rc=$rc: $err"
fi

if [[ $fail -eq 0 ]]; then echo "  OK"; exit 0; else echo "  $fail check(s) failed"; exit 1; fi
