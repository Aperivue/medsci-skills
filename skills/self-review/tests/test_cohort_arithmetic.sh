#!/usr/bin/env bash
# Regression test for the cohort-arithmetic gate (self-review Phase 2.5 / 2.5b).
# Synthetic, PII-free fixtures reproduce: (a) an incidence rate that does not
# recompute from its events/person-years, (b) a complete-case footnote that does
# not balance (total - missing != complete), (c) an ordinal tier partition whose
# stratum denominators and events sum above the stated total.
# Stdlib-only (python3).
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$HERE/../scripts/check_cohort_arithmetic.py"
BAD="$HERE/fixtures/cohort_bad.md"
CLEAN="$HERE/fixtures/cohort_clean.md"
PART="$HERE/fixtures/cohort_partition.csv"
OUT="$(mktemp -t coh_XXXX).json"
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

# (1) bad manuscript: all three discrepancies, Major present -> exit 1 under --strict
python3 "$SCRIPT" --manuscript "$BAD" --out "$OUT" --strict --quiet >/dev/null 2>&1
check "exit 1 under --strict (Major present)" test "$?" -eq 1
check "JSON artifact written" test -s "$OUT"
check "RATE_BACKCALC detected (5.0 vs 120/50000*1000=2.4)" has_verdict RATE_BACKCALC
check "CASCADE_SUM detected (4252-583=3669 != 3667)"       has_verdict CASCADE_SUM
check "PARTITION_OVERLAP detected (sum 12498 != 12019)"     has_verdict PARTITION_OVERLAP

# (2) clean manuscript: everything balances -> exit 0
python3 "$SCRIPT" --manuscript "$CLEAN" --strict --quiet >/dev/null 2>&1
check "exit 0 on clean manuscript (all arithmetic balances)" test "$?" -eq 0

# (3) --data CSV partition: stratum n sum above total -> PARTITION_OVERLAP, exit 1
python3 "$SCRIPT" --manuscript "$CLEAN" --data "$PART" --out "$OUT" --strict --quiet >/dev/null 2>&1
check "exit 1 with overlapping --data partition CSV" test "$?" -eq 1
check "PARTITION_OVERLAP from --data CSV" has_verdict PARTITION_OVERLAP

# (4) analysis-unit: 10 records / 7 subjects + manuscript that discloses neither
#     the analysis unit nor a one-record-per-subject sensitivity -> ANALYSIS_UNIT_
#     UNDISCLOSED (auto-detected 'mockid' column), exit 1.
REPEAT="$HERE/fixtures/cohort_repeat_subjects.csv"
UNDISC="$HERE/fixtures/cohort_unit_undisclosed.md"
DISC="$HERE/fixtures/cohort_unit_disclosed.md"
python3 "$SCRIPT" --manuscript "$UNDISC" --data "$REPEAT" --out "$OUT" --strict --quiet >/dev/null 2>&1
check "exit 1 (analysis unit undisclosed, auto-detect)" test "$?" -eq 1
check "ANALYSIS_UNIT_UNDISCLOSED detected" has_verdict ANALYSIS_UNIT_UNDISCLOSED
check "reconciliation reports 7 unique subjects" python3 -c "
import json
d=json.load(open('$OUT'))
c=next(c for c in d['claims'] if c['verdict']=='ANALYSIS_UNIT_UNDISCLOSED')
assert 'unique_subjects=7' in c['detail'] and 'max_visits=3' in c['detail'], c['detail']
"

# (5) explicit --id-col also fires
python3 "$SCRIPT" --manuscript "$UNDISC" --data "$REPEAT" --id-col mockid --out "$OUT" --strict --quiet >/dev/null 2>&1
check "exit 1 (analysis unit, explicit --id-col)" test "$?" -eq 1

# (6) disclosed manuscript (states analysis unit + first-visit sensitivity) -> no fire
python3 "$SCRIPT" --manuscript "$DISC" --data "$REPEAT" --strict --quiet >/dev/null 2>&1
check "exit 0 when analysis unit disclosed" test "$?" -eq 0

# (7) a tier label ("stratum 1") and "incident rate" sitting near a small integer
#     must NOT mis-bind the numerator: the rate recomputes from 882 events /
#     35,581 PY -> NO RATE_BACKCALC false positive, exit 0 (regression).
RFP="$HERE/fixtures/cohort_rate_tier_fp.md"
python3 "$SCRIPT" --manuscript "$RFP" --out "$OUT" --quiet >/dev/null 2>&1
check "no RATE_BACKCALC false positive (tier + incident-rate)" python3 -c "
import json
d=json.load(open('$OUT'))
assert not any(c['verdict']=='RATE_BACKCALC' for c in d['claims']), 'numerator mis-bound -> false RATE_BACKCALC'
"
python3 "$SCRIPT" --manuscript "$RFP" --strict --quiet >/dev/null 2>&1
check "exit 0 on correct-rate manuscript" test "$?" -eq 0

# (8) PROSE partition: an in-text exhaustive split whose counts do not sum to the
#     stated total (37 + 185 + 103 = 325 != 289, % = 112.4) -> PARTITION_OVERLAP,
#     exit 1.
PPROSE="$HERE/fixtures/cohort_partition_prose.md"
python3 "$SCRIPT" --manuscript "$PPROSE" --out "$OUT" --strict --quiet >/dev/null 2>&1
check "exit 1 on prose partition that does not reconcile" test "$?" -eq 1
check "PARTITION_OVERLAP from prose enumeration"          has_verdict PARTITION_OVERLAP

# (9) PRECISION: the corrected split (37+149+103=289, %=100), a no-% cross-tab,
#     and an overlapping-comorbidity enumeration WITH %s but no partition cue must
#     all stay silent -> exit 0. The last is the case a naive count-sum check
#     would false-fire on.
PPCLEAN="$HERE/fixtures/cohort_partition_prose_clean.md"
python3 "$SCRIPT" --manuscript "$PPCLEAN" --strict --quiet >/dev/null 2>&1
check "exit 0 on corrected + cross-tab + cue-less overlapping prose" test "$?" -eq 0

# (10) FOLLOWUP_VS_CRITERION: reported "median follow-up 102 days" against a ">= 24
#      months stability" criterion with no total-observation window -> Minor flag.
FUC="$HERE/fixtures/cohort_followup_criterion.md"
python3 "$SCRIPT" --manuscript "$FUC" --out "$OUT" --quiet >/dev/null 2>&1
check "FOLLOWUP_VS_CRITERION when follow-up < a criterion duration" has_verdict FOLLOWUP_VS_CRITERION
# (11) silent once the total-observation window is distinctly reported.
FUOK="$HERE/fixtures/cohort_followup_ok.md"
python3 "$SCRIPT" --manuscript "$FUOK" --out "$OUT" --quiet >/dev/null 2>&1
check "no FOLLOWUP_VS_CRITERION when total observation window is reported" python3 -c "
import json
d=json.load(open('$OUT'))
raise SystemExit(0 if not any(c['verdict']=='FOLLOWUP_VS_CRITERION' for c in d['claims']) else 1)
"

# (N) a subgroup rendered twice with divergent CIs: two rows share the SAME estimate AND
#     identical n/events but print different confidence intervals (independent bootstraps)
#     -> SUBGROUP_DUPLICATE_CI (Minor). Two DISTINCT subgroups with a coincidentally equal
#     estimate but different n/events must NOT fire (the precision guard).
DUPCI="$HERE/fixtures/cohort_dup_ci.md"
DUPCICLEAN="$HERE/fixtures/cohort_dup_ci_clean.md"
python3 "$SCRIPT" --manuscript "$DUPCI" --out "$OUT" --quiet >/dev/null 2>&1
check "SUBGROUP_DUPLICATE_CI on same estimate+n+events with divergent CI" has_verdict SUBGROUP_DUPLICATE_CI
python3 "$SCRIPT" --manuscript "$DUPCICLEAN" --out "$OUT" --quiet >/dev/null 2>&1
check "no SUBGROUP_DUPLICATE_CI when n/events differ (distinct subgroups, same OR)" python3 -c "
import json
d=json.load(open('$OUT'))
raise SystemExit(0 if not any(c['verdict']=='SUBGROUP_DUPLICATE_CI' for c in d['claims']) else 1)
"

# (N) nested prediction models all embedding a common covariate set (age + sex) report a
#     C-index but there is no base-model (age+sex-only) row and no incremental deltaC ->
#     NESTED_MODEL_NO_BASELINE (Minor). Adding the base-model row must suppress it.
NEST="$HERE/fixtures/cohort_nested_models.md"
NESTBASE="$HERE/fixtures/cohort_nested_models_base.md"
python3 "$SCRIPT" --manuscript "$NEST" --out "$OUT" --quiet >/dev/null 2>&1
check "NESTED_MODEL_NO_BASELINE when nested models share covariates with no base row" has_verdict NESTED_MODEL_NO_BASELINE
python3 "$SCRIPT" --manuscript "$NESTBASE" --out "$OUT" --quiet >/dev/null 2>&1
check "no NESTED_MODEL_NO_BASELINE when the base-model (age+sex) row is present" python3 -c "
import json
d=json.load(open('$OUT'))
raise SystemExit(0 if not any(c['verdict']=='NESTED_MODEL_NO_BASELINE' for c in d['claims']) else 1)
"

echo "fail=$fail"; [[ "$fail" -eq 0 ]] && echo "ALL PASS" || echo "FAILURES: $fail"
exit "$fail"
