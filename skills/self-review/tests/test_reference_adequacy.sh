#!/usr/bin/env bash
# Regression test for the reference-adequacy gate (self-review Phase 2.5c-2 /
# write-paper Step 7.3c). Synthetic fixtures reproduce:
#   1. an original-research draft whose Statistical Analysis subsection names a
#      competing-risk model, multiple imputation, the E-value, and an eGFR
#      equation with ZERO citations (the highest-value failure mode);
#   2. the same draft with a citation added in each named-method paragraph;
#   3. a letter whose lower reference target must not false-fail.
# Stdlib-only (python3).
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$HERE/../scripts/check_reference_adequacy.py"
FIX="$HERE/fixtures"
OUT="$(mktemp -t ra_XXXX).json"
trap 'rm -f "$OUT"' EXIT

fail=0
check() { local label="$1"; shift
    if "$@" >/dev/null 2>&1; then printf '  PASS  %s\n' "$label"
    else printf '  FAIL  %s\n' "$label"; fail=$((fail+1)); fi
}
# assert a python boolean expression over the JSON at $OUT; `d` is the parsed dict.
# (No assertion message: the expression embeds single quotes — the check() label
# already names the case on FAIL.)
jassert() { python3 -c "
import json
d=json.load(open('$OUT'))
assert ($1)
"; }

[[ -f "$SCRIPT" ]] || { echo "ENV-ERR: script missing: $SCRIPT" >&2; exit 2; }

echo "== Fixture 1: original research, Methods names methods with 0 citations =="
python3 "$SCRIPT" --manuscript "$FIX/refadeq_original_uncited.md" \
    --article-type original_article --out "$OUT" --strict >/dev/null 2>&1
check "exit 1 under --strict (Major present)"      test "$?" -eq 1
check "JSON artifact written"                       test -s "$OUT"
check "methods_zero_citations is true"              jassert "d['methods_zero_citations'] is True"
check "uncited_named_methods is non-empty"          jassert "len(d['uncited_named_methods']) > 0"
check "Fine-Gray flagged uncited"                   jassert "'Fine-Gray' in d['uncited_named_methods']"
check "reference_count_verdict BELOW_TARGET"        jassert "d['reference_count_verdict'] == 'BELOW_TARGET'"
check "a methods_zero_citations Major finding"      jassert "any(f['subtype']=='methods_zero_citations' and f['severity']=='major' for f in d['findings'])"
check "all findings fixable_by_ai=false"            jassert "all(f['fixable_by_ai'] is False for f in d['findings'])"

echo "== Fixture 2: same draft, each named method now cited =="
python3 "$SCRIPT" --manuscript "$FIX/refadeq_original_fixed.md" \
    --article-type original_article --out "$OUT" --strict >/dev/null 2>&1
check "exit 0 (no Major; Methods gap cleared)"      test "$?" -eq 0
check "methods_zero_citations is false"             jassert "d['methods_zero_citations'] is False"
check "no methods_named_method_uncited finding"     jassert "not any(f['subtype']=='methods_named_method_uncited' for f in d['findings'])"
check "adequacy_safe is true"                        jassert "d['adequacy_safe'] is True"

echo "== Fixture 3: letter (lower target must not false-fail) =="
python3 "$SCRIPT" --manuscript "$FIX/refadeq_letter.md" \
    --article-type letter --out "$OUT" --strict >/dev/null 2>&1
check "exit 0 (letter target met)"                  test "$?" -eq 0
check "verdict ADEQUATE for letter"                 jassert "d['reference_count_verdict'] == 'ADEQUATE'"
check "no adequacy findings"                         jassert "len(d['findings']) == 0"

echo "== Alias map: nhis_cohort routes to original_research target =="
python3 "$SCRIPT" --manuscript "$FIX/refadeq_original_uncited.md" \
    --article-type nhis_cohort --out "$OUT" --quiet >/dev/null 2>&1
check "nhis_cohort -> original_research bucket"      jassert "d['article_bucket'] == 'original_research'"
check "original_research target is [25,45]"         jassert "d['effective_target'] == [25,45]"

echo "fail=$fail"; [[ "$fail" -eq 0 ]] && echo "ALL PASS" || echo "FAILURES: $fail"
exit "$fail"
