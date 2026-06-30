#!/usr/bin/env bash
# Regression test for the framework-naming audit (check-reporting Step 4e).
# Synthetic, PII-free fixtures reproduce: (a) an AI extension used without naming
# or citing its base instrument (BASE_MISSING), (b) mixed +AI / -AI hyphenation for
# one family (HYPHEN_MIX), (c) vague "adapted per recent guidance" wording
# (VAGUE_GUIDANCE), (d) a self-coined "12-AI" item label (SELF_COINED_LABEL). The
# clean fixture names and cites both base instrument and extension.
# Stdlib-only (python3).
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$HERE/../scripts/check_framework_naming.py"
BAD="$HERE/fixtures/framework_bad.md"
CLEAN="$HERE/fixtures/framework_clean.md"
OUT="$(mktemp -t fw_XXXX).json"
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

# (1) bad manuscript: BASE_MISSING is Major -> exit 1 under --strict
python3 "$SCRIPT" --manuscript "$BAD" --out "$OUT" --strict --quiet >/dev/null 2>&1
check "exit 1 under --strict (Major present)" test "$?" -eq 1
check "JSON artifact written" test -s "$OUT"
check "BASE_MISSING detected (extension without base)" has_verdict BASE_MISSING
check "HYPHEN_MIX detected (PROBAST+AI vs PROBAST-AI)"  has_verdict HYPHEN_MIX
check "VAGUE_GUIDANCE detected (adapted per recent guidance)" has_verdict VAGUE_GUIDANCE
check "SELF_COINED_LABEL detected (12-AI)" has_verdict SELF_COINED_LABEL

# (2) clean manuscript: base named + cited, consistent hyphenation -> exit 0
python3 "$SCRIPT" --manuscript "$CLEAN" --strict --quiet >/dev/null 2>&1
check "exit 0 on clean manuscript (base named + cited)" test "$?" -eq 0

# (3) FP guard (less-defensive, F05): method-level "recent best-practice recommendations"
# with NO reporting context must NOT trigger VAGUE_GUIDANCE.
NOFP="$(mktemp -t fw_nofp_XXXX).md"
trap 'rm -f "$OUT" "$NOFP"' EXIT
cat > "$NOFP" <<'EOF'
# Methods
We performed external validation following recent best-practice recommendations.
The imputation strategy was aligned with current guidance for handling missingness.
EOF
python3 "$SCRIPT" --manuscript "$NOFP" --out "$OUT" --quiet >/dev/null 2>&1
check "no VAGUE_GUIDANCE on method-level recommendations (no reporting cue)" python3 -c "
import json
d=json.load(open('$OUT'))
raise SystemExit(0 if not any(c['verdict']=='VAGUE_GUIDANCE' for c in d['claims']) else 1)
"

echo "fail=$fail"; [[ "$fail" -eq 0 ]] && echo "ALL PASS" || echo "FAILURES: $fail"
exit "$fail"
