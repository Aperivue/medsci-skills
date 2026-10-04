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

# (6) an UNSEEDED generator is not a seed (F3 false-clearance regression):
#     default_rng() / np.random.seed(None) / random_state=None / set.seed(NULL)
only_seed_major() { python3 -c "
import json
d=json.load(open('$OUT'))
m=[c['verdict'] for c in d['claims'] if c['severity']=='Major']
assert m==['MISSING_SEED'], m
"; }
for f in gen_unseeded_rng.py gen_seed_none.py gen_seed_null.R; do
    python3 "$SCRIPT" "$HERE/fixtures/$f" --out "$OUT" --strict --quiet >/dev/null 2>&1
    check "exit 1: unseeded RNG is MISSING_SEED ($f)" test "$?" -eq 1
    check "MISSING_SEED is the only Major claim ($f)" only_seed_major
done
#     negative control: a seeded Generator, with random_state=None only as a def default
python3 "$SCRIPT" "$HERE/fixtures/gen_seeded_rng.py" --out "$OUT" --strict --quiet >/dev/null 2>&1
check "exit 0: seeded default_rng(SEED) + def default random_state=None" test "$?" -eq 0

#     the positive case still points at the real call, not the module docstring above it
python3 "$SCRIPT" "$HERE/fixtures/gen_unseeded_rng.py" --out "$OUT" --quiet >/dev/null 2>&1
check "MISSING_SEED line is the real default_rng() call (line 12)" python3 -c "
import json
d=json.load(open('$OUT'))
assert [(c['verdict'], c['line']) for c in d['claims'] if c['severity']=='Major']==[('MISSING_SEED', 12)], d['claims']
"

# (7) negative control: default_rng() / np.random.seed() / RandomState(None) only
#     MENTIONED in a docstring or a comment is not a call (tokenize-based stripping)
python3 "$SCRIPT" "$HERE/fixtures/gen_rng_doc_mention.py" --out "$OUT" --strict --quiet >/dev/null 2>&1
check "exit 0: unseeded calls named only in docstrings/comments" test "$?" -eq 0
check "no claims at all on the docstring/comment-mention fixture" python3 -c "
import json
d=json.load(open('$OUT'))
assert d['claims']==[], d['claims']
"

# (8) API defaults (AS-1), Minor only: never a --strict exit, never on a stated choice
claims_are() { python3 -c "
import json,sys
d=json.load(open('$OUT'))
got=[(c['verdict'], c['severity'], c['line']) for c in d['claims']]
want=$1
assert got==want, got
"; }
python3 "$SCRIPT" "$HERE/fixtures/gen_api_defaults.py" --out "$OUT" --strict --quiet >/dev/null 2>&1
check "exit 0 under --strict: API-default claims are Minor" test "$?" -eq 0
check "ttest_ind without equal_var + default LogisticRegression next to exp(coef_)" \
    claims_are "[('API_DEFAULT_STUDENT_T','Minor',14),('API_DEFAULT_PENALIZED_OR','Minor',16)]"
for f in gen_api_defaults_ok.py gen_api_lr_no_or.py gen_api_ttest.R; do
    python3 "$SCRIPT" "$HERE/fixtures/$f" --out "$OUT" --strict --quiet >/dev/null 2>&1
    check "exit 0 and no claim: stated equal_var / C / penalty, no OR, or R t.test ($f)" claims_are "[]"
done
python3 "$SCRIPT" "$HERE/fixtures/gen_api_unparseable.py" --out "$OUT" --strict --quiet >/dev/null 2>&1
check "exit 0: unparseable file naming ttest_ind is API_DEFAULTS_NOT_ASSESSED" test "$?" -eq 0
check "API_DEFAULTS_NOT_ASSESSED is the only claim on the unparseable fixture" \
    claims_are "[('API_DEFAULTS_NOT_ASSESSED','Minor',3)]"
#     the reference lines the messages cite still say what the messages say they say
REFS="$HERE/../references/analysis_guides"
check "cited rule: test_selection.md:78 is the Welch default" \
    bash -c "sed -n 78p '$REFS/test_selection.md' | grep -q \"Welch's t-test\*\* by default\""
check "cited rule: propensity_score.md:142 is the sklearn L2 default" \
    bash -c "sed -n 142p '$REFS/propensity_score.md' | grep -q 'LogisticRegression. is L2-penalised by default (C = 1.0)'"

echo "fail=$fail"; [[ "$fail" -eq 0 ]] && echo "ALL PASS" || echo "FAILURES: $fail"
exit "$fail"
