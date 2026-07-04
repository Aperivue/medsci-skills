#!/usr/bin/env bash
# Regression test for the uncertainty/OOD reporting-rigor gate (uncertainty-imaging).
# Synthetic, PII-free JSON manifests reproduce each verdict class + the suppressions.
# Stdlib-only (python3).
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$HERE/../scripts/check_uncertainty_reporting.py"
CH="$HERE/../scripts/check_uncertainty_reporting_challenge"
TMP="$(mktemp -d -t unc_XXXX)"
OUT="$TMP/out.json"
trap 'rm -rf "$TMP"' EXIT

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
no_verdict() { python3 -c "
import json,sys
d=json.load(open('$OUT'))
assert not any(c['verdict']=='$1' for c in d['claims']), '$1 unexpectedly present'
"; }
run() { python3 "$SCRIPT" --manifest "$1" --out "$OUT" --quiet >/dev/null 2>&1; }

[[ -f "$SCRIPT" ]] || { echo "ENV-ERR: script missing" >&2; exit 2; }

# --- each verdict class from a targeted synthetic manifest ---
printf '{"deployment_claim":true,"uncertainty_method":"none"}' > "$TMP/ptpred.json"
run "$TMP/ptpred.json"
check "POINT_PREDICTION_NO_UNCERTAINTY fires (deployment + no UQ)" has_verdict POINT_PREDICTION_NO_UNCERTAINTY

printf '{"deployment_claim":true,"uncertainty_method":"conformal","coverage_validated":false,"calibration_under_shift":true}' > "$TMP/conf.json"
run "$TMP/conf.json"
check "CONFORMAL_NO_COVERAGE_VALIDATION fires (conformal, coverage unmeasured)" has_verdict CONFORMAL_NO_COVERAGE_VALIDATION

printf '{"uncertainty_method":"conformal","coverage_validated":true,"calibration_under_shift":true,"ood_method":"mahalanobis","ood_heldout_set":null}' > "$TMP/ood.json"
run "$TMP/ood.json"
check "OOD_NO_HELDOUT_SET fires (OOD claim, no held-out set)" has_verdict OOD_NO_HELDOUT_SET

printf '{"deployment_claim":true,"uncertainty_method":"deep_ensemble","ensemble_members":5,"ensemble_independent":false,"calibration_under_shift":true}' > "$TMP/ens.json"
run "$TMP/ens.json"
check "ENSEMBLE_NOT_INDEPENDENT fires (shared-seed ensemble)" has_verdict ENSEMBLE_NOT_INDEPENDENT

printf '{"deployment_claim":true,"uncertainty_method":"mc_dropout","mc_dropout_active_at_inference":false,"calibration_under_shift":true}' > "$TMP/mcd.json"
run "$TMP/mcd.json"
check "MCDROPOUT_DISABLED_AT_INFERENCE fires (dropout off at inference)" has_verdict MCDROPOUT_DISABLED_AT_INFERENCE

printf '{"uncertainty_method":"conformal","coverage_validated":true,"calibration_under_shift":true,"selective_prediction":true,"selective_target":null}' > "$TMP/sel.json"
run "$TMP/sel.json"
check "SELECTIVE_NO_TARGET fires (abstention, no target)" has_verdict SELECTIVE_NO_TARGET

printf '{"deployment_claim":true,"uncertainty_method":"deep_ensemble","ensemble_members":5,"ensemble_independent":true,"calibration_under_shift":false}' > "$TMP/shift.json"
run "$TMP/shift.json"
check "NO_CALIBRATION_UNDER_SHIFT fires (in-distribution only)" has_verdict NO_CALIBRATION_UNDER_SHIFT

# --- method-gating: MC-dropout/ensemble checks do not fire on a conformal pipeline ---
run "$CH/fixture/uncertainty_strong.json"
check "strong fixture: no POINT_PREDICTION_NO_UNCERTAINTY" no_verdict POINT_PREDICTION_NO_UNCERTAINTY
check "strong fixture: no CONFORMAL_NO_COVERAGE_VALIDATION" no_verdict CONFORMAL_NO_COVERAGE_VALIDATION
check "strong fixture: no OOD_NO_HELDOUT_SET" no_verdict OOD_NO_HELDOUT_SET
check "strong fixture: no ENSEMBLE_NOT_INDEPENDENT (method-gated)" no_verdict ENSEMBLE_NOT_INDEPENDENT
check "strong fixture: no MCDROPOUT_DISABLED_AT_INFERENCE (method-gated)" no_verdict MCDROPOUT_DISABLED_AT_INFERENCE
check "strong fixture: no NO_CALIBRATION_UNDER_SHIFT" no_verdict NO_CALIBRATION_UNDER_SHIFT
check "strong fixture: exit 0 under --strict" python3 "$SCRIPT" --manifest "$CH/fixture/uncertainty_strong.json" --strict --quiet

# --- exit codes ---
python3 "$SCRIPT" --manifest "$CH/fixture/uncertainty_weak.json" --strict --quiet >/dev/null 2>&1 && rc=0 || rc=$?
check "weak fixture: exit 1 under --strict (Major present)" test "${rc:-0}" -eq 1

# --- challenge card verifier ---
check "challenge verify.sh passes" bash "$CH/verify.sh"

echo "fail=$fail"; [[ "$fail" -eq 0 ]] && echo "ALL PASS" || echo "FAILURES: $fail"
exit "$fail"
