#!/usr/bin/env bash
# Regression test for the generated-code quality gate (analyze-stats Phase 3.5).
# Synthetic, PII-free fixtures reproduce reproducibility/integrity slop in both
# Python and R (missing seed, hardcoded absolute path, hand-typed tabular data,
# in-place source overwrite, debug leftover, unused import) and a clean script.
# Absolute-path literals use a synthetic /Users/researcher/ that does not match
# the repo PII blocklist (personal home dirs only).
# Stdlib-only (python3).
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$HERE/../scripts/check_generated_code.py"
BAD_PY="$HERE/fixtures/gen_bad.py"
BAD_R="$HERE/fixtures/gen_bad.R"
CLEAN="$HERE/fixtures/gen_clean.py"
OUT="$(mktemp -t gencode_XXXX).json"
trap 'rm -f "$OUT"' EXIT

fail=0
check() { local label="$1"; shift
    if "$@" >/dev/null 2>&1; then printf '  PASS  %s\n' "$label"
    else printf '  FAIL  %s\n' "$label"; fail=$((fail+1)); fi
}
has_verdict() { python3 -c "
import json,sys
d=json.load(open('$OUT'))
assert any(c['verdict']=='$1' for c in d['claims']), '$1 not found'
"; }

[[ -f "$SCRIPT" ]] || { echo "ENV-ERR: script missing" >&2; exit 2; }

# (1) bad Python script -> exit 1 with all four Major verdicts + flags
python3 "$SCRIPT" "$BAD_PY" --out "$OUT" --strict --quiet >/dev/null 2>&1
check "exit 1 (bad .py)" test "$?" -eq 1
check "MISSING_SEED detected" has_verdict MISSING_SEED
check "HARDCODED_ABS_PATH detected" has_verdict HARDCODED_ABS_PATH
check "HARDCODED_DATA_LITERAL detected" has_verdict HARDCODED_DATA_LITERAL
check "INPLACE_SOURCE_OVERWRITE detected" has_verdict INPLACE_SOURCE_OVERWRITE
check "UNUSED_IMPORT detected" has_verdict UNUSED_IMPORT
check "DEBUG_LEFTOVER detected" has_verdict DEBUG_LEFTOVER

# (2) bad R script -> exit 1 with R-side Major verdicts
python3 "$SCRIPT" "$BAD_R" --out "$OUT" --strict --quiet >/dev/null 2>&1
check "exit 1 (bad .R)" test "$?" -eq 1
check "MISSING_SEED detected (R)" has_verdict MISSING_SEED
check "HARDCODED_ABS_PATH detected (R)" has_verdict HARDCODED_ABS_PATH
check "HARDCODED_DATA_LITERAL detected (R)" has_verdict HARDCODED_DATA_LITERAL
check "INPLACE_SOURCE_OVERWRITE detected (R)" has_verdict INPLACE_SOURCE_OVERWRITE

# (3) clean Python script -> exit 0
python3 "$SCRIPT" "$CLEAN" --strict --quiet >/dev/null 2>&1
check "exit 0 (clean .py)" test "$?" -eq 0

# (4) --code-dir scans the fixtures directory (finds Major issues -> exit 1)
python3 "$SCRIPT" --code-dir "$HERE/fixtures" --strict --quiet >/dev/null 2>&1
check "exit 1 (--code-dir scan)" test "$?" -eq 1

# (5) hex-color palette + data read -> NOT HARDCODED_DATA_LITERAL (WONG-palette
#     false-positive regression); the script is otherwise clean -> exit 0
PALETTE="$HERE/fixtures/gen_palette.py"
python3 "$SCRIPT" "$PALETTE" --out "$OUT" --quiet >/dev/null 2>&1
check "no HARDCODED_DATA_LITERAL on hex-color palette" python3 -c "
import json
d=json.load(open('$OUT'))
assert not any(c['verdict']=='HARDCODED_DATA_LITERAL' for c in d['claims']), 'palette flagged as data literal'
"
python3 "$SCRIPT" "$PALETTE" --strict --quiet >/dev/null 2>&1
check "exit 0 on clean palette script" test "$?" -eq 0

echo "fail=$fail"; [[ "$fail" -eq 0 ]] && echo "ALL PASS" || echo "FAILURES: $fail"
exit "$fail"
