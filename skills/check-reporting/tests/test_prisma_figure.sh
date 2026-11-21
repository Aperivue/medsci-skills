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
BROKEN="$HERE/fixtures/prisma_fig_broken_assessed.md"
OUT="$(mktemp -t prisma_fig_XXXX).json"
trap 'rm -f "$OUT"' EXIT

for f in "$SCRIPT" "$BODY" "$CLEAN" "$MM" "$BROKEN"; do
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

# 4. Broken retrieved -> assessed link (190 retrieved, 200 assessed; every other
#    subtraction holds), used as both body and figure -> MISMATCH on
#    'assessed = sought - not_retrieved', exit 1. Before the fix this passed.
out="$(python3 "$SCRIPT" --md "$BROKEN" --figure "$BROKEN" --out "$OUT" 2>&1)"; rc=$?
if [[ $rc -eq 1 && "$out" == *"assessed = sought - not_retrieved"* ]] \
   && python3 -c "import json,sys; d=json.load(open('$OUT')); r=[x for x in d['arithmetic_figure'] if x['eq']=='assessed = sought - not_retrieved']; sys.exit(0 if (not d['audit_safe'] and r and r[0]['status']=='MISMATCH' and r[0]['lhs']==200 and r[0]['rhs']==190) else 1)"; then
  pass "assessed != sought - not_retrieved -> MISMATCH, exit 1"
else
  bad "broken assessed link rc=$rc (expected 1 + assessed MISMATCH)"
fi

# 5. Negative control: the clean figure used as both body and figure stays clean,
#    and its assessed link is checked (PRESENT), not skipped.
python3 "$SCRIPT" --md "$CLEAN" --figure "$CLEAN" --out "$OUT" >/dev/null 2>&1; rc=$?
if [[ $rc -eq 0 ]] \
   && python3 -c "import json,sys; d=json.load(open('$OUT')); r=[x for x in d['arithmetic_figure'] if x['eq']=='assessed = sought - not_retrieved']; sys.exit(0 if (d['audit_safe'] and r and r[0]['status']=='PRESENT') else 1)"; then
  pass "clean figure as body+figure -> assessed link PRESENT, exit 0"
else
  bad "clean self-check rc=$rc (expected 0 + assessed PRESENT)"
fi

# 6. A figure source the parser reads no PRISMA number from (a caption with no counts, an
#    image placeholder). Nothing was compared, so this is "not assessed" (exit 2, the documented
#    code for unparsable input), not a mismatch (exit 1) and not a file to cite as evidence.
#    Every run below writes its own output file, so no assertion can read an earlier run's JSON.
WORK="$(mktemp -d)"
trap 'rm -f "$OUT"; rm -rf "$WORK"' EXIT
printf '# Figure 1\n\n![PRISMA flow diagram](figures/prisma.png)\n\nStudy selection.\n' > "$WORK/emptyfig.md"
printf '## Results\n\nStudy selection is summarised in Figure 1.\n' > "$WORK/emptybody.md"

err="$(python3 "$SCRIPT" --md "$BODY" --figure "$WORK/emptyfig.md" --out "$WORK/o6.json" 2>&1)"; rc=$?
if [[ $rc -eq 2 && "$err" == *"UNPARSEABLE_FIGURE_SOURCE"* && "$err" != *"Traceback"* ]] \
   && python3 -c "import json,sys; d=json.load(open('$WORK/o6.json')); sys.exit(0 if (d['status']=='not_assessed' and d['audit_safe'] is False and d['figure_numbers']=={} and d['body_numbers'] and any('UNPARSEABLE_FIGURE_SOURCE' in a for a in d['action_items'])) else 1)"; then
  pass "no PRISMA numbers in the figure source -> not_assessed, exit 2"
else
  bad "unparsable figure rc=$rc (expected 2 + status not_assessed): $err"
fi

# 7. The same for a manuscript body with no PRISMA numbers.
err="$(python3 "$SCRIPT" --md "$WORK/emptybody.md" --figure "$CLEAN" --out "$WORK/o7.json" 2>&1)"; rc=$?
if [[ $rc -eq 2 && "$err" == *"UNPARSEABLE_BODY"* ]] \
   && python3 -c "import json,sys; d=json.load(open('$WORK/o7.json')); sys.exit(0 if (d['status']=='not_assessed' and d['audit_safe'] is False and d['body_numbers']=={} and d['figure_numbers'] and any('UNPARSEABLE_BODY' in a for a in d['action_items'])) else 1)"; then
  pass "no PRISMA numbers in the body -> not_assessed, exit 2"
else
  bad "unparsable body rc=$rc (expected 2 + status not_assessed)"
fi

# 8. Assessed runs say so: clean stays exit 0 and a mismatch stays exit 1, both status "assessed".
python3 "$SCRIPT" --md "$BODY" --figure "$CLEAN" --out "$WORK/o8a.json" >/dev/null 2>&1; rc0=$?
s0="$(python3 -c "import json; print(json.load(open('$WORK/o8a.json'))['status'])")"
python3 "$SCRIPT" --md "$BODY" --figure "$MM" --out "$WORK/o8b.json" >/dev/null 2>&1; rc1=$?
s1="$(python3 -c "import json; print(json.load(open('$WORK/o8b.json'))['status'])")"
if [[ $rc0 -eq 0 && $rc1 -eq 1 && "$s0" == "assessed" && "$s1" == "assessed" ]]; then
  pass "assessed runs keep exit 0 / exit 1 and status assessed"
else
  bad "assessed status rc0=$rc0 rc1=$rc1 s0=$s0 s1=$s1"
fi

# 9. A mismatch found on the side that WAS read is not lost. The broken figure fails its own
#    arithmetic while the body has no counts: still exit 2 and not_assessed (nothing was
#    cross-checked), with the mismatch and the unparsable body both in action_items.
out="$(python3 "$SCRIPT" --md "$WORK/emptybody.md" --figure "$BROKEN" --out "$WORK/o9.json" 2>&1)"; rc=$?
if [[ $rc -eq 2 && "$out" == *"UNPARSEABLE_BODY"* && "$out" == *"figure arithmetic"* ]] \
   && python3 -c "import json,sys; d=json.load(open('$WORK/o9.json')); a=d['action_items']; sys.exit(0 if (d['status']=='not_assessed' and d['audit_safe'] is False and any('UNPARSEABLE_BODY' in x for x in a) and any('figure arithmetic' in x for x in a)) else 1)"; then
  pass "unreadable body + broken figure arithmetic -> exit 2, both reported"
else
  bad "masked mismatch rc=$rc (expected 2 + both action items)"
fi

if [[ $fail -eq 0 ]]; then echo "  OK"; exit 0; else echo "  $fail check(s) failed"; exit 1; fi
