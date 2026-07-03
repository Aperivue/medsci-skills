#!/usr/bin/env bash
# Regression test for the explainability-report rigor gate (explainability).
# Synthetic, PII-free JSON manifests reproduce each verdict class. Stdlib-only (python3).
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$HERE/../scripts/check_explainability_report.py"
CH="$HERE/../scripts/check_explainability_report_challenge"
TMP="$(mktemp -d -t xai_XXXX)"
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

[[ -f "$SCRIPT" ]] || { echo "ENV-ERR: script missing" >&2; exit 2; }

# (1) weak fixture -> 2 Major + exit 1
python3 "$SCRIPT" --manifest "$CH/fixture/report_weak.json" --out "$OUT" --strict --quiet >/dev/null 2>&1
check "exit 1 (weak report)" test "$?" -eq 1
check "NO_SANITY_CHECK detected" has_verdict NO_SANITY_CHECK
check "NO_LOCALIZATION_METRIC detected" has_verdict NO_LOCALIZATION_METRIC
check "CHERRY_PICKED_EXAMPLES detected" has_verdict CHERRY_PICKED_EXAMPLES

# (2) strong fixture -> exit 0, no Major
python3 "$SCRIPT" --manifest "$CH/fixture/report_strong.json" --strict --quiet >/dev/null 2>&1
check "exit 0 (strong report)" test "$?" -eq 0

# (3) saliency framed as causal/validation -> SALIENCY_AS_VALIDATION (Major)
cat > "$TMP/causal.json" <<'EOF'
{"method": "saliency", "n_examples": 100, "cohort_level": true,
 "localization_metric": "iou", "localization_value": 0.5,
 "sanity_checks": ["model_randomization", "data_randomization"],
 "interpretation": "causal"}
EOF
python3 "$SCRIPT" --manifest "$TMP/causal.json" --out "$OUT" --quiet >/dev/null 2>&1
check "SALIENCY_AS_VALIDATION detected" has_verdict SALIENCY_AS_VALIDATION
python3 "$SCRIPT" --manifest "$TMP/causal.json" --strict --quiet >/dev/null 2>&1
check "causal framing exits 1 under --strict" test "$?" -eq 1

# (4) only one randomisation axis -> INSUFFICIENT_SANITY (Minor), exit 0
cat > "$TMP/onesanity.json" <<'EOF'
{"method": "gradcam++", "n_examples": 100, "cohort_level": true,
 "localization_metric": "pointing_game", "localization_value": 0.8,
 "sanity_checks": ["model_randomization"], "interpretation": "localization"}
EOF
python3 "$SCRIPT" --manifest "$TMP/onesanity.json" --out "$OUT" --quiet >/dev/null 2>&1
check "INSUFFICIENT_SANITY detected" has_verdict INSUFFICIENT_SANITY
python3 "$SCRIPT" --manifest "$TMP/onesanity.json" --strict --quiet >/dev/null 2>&1
check "insufficient-sanity is Minor (exit 0 under --strict)" test "$?" -eq 0

# (5) no method named -> MISSING_METHOD (Minor)
cat > "$TMP/nomethod.json" <<'EOF'
{"n_examples": 100, "cohort_level": true, "localization_metric": "iou",
 "sanity_checks": ["model_randomization", "data_randomization"], "interpretation": "attribution"}
EOF
python3 "$SCRIPT" --manifest "$TMP/nomethod.json" --out "$OUT" --quiet >/dev/null 2>&1
check "MISSING_METHOD detected" has_verdict MISSING_METHOD

# (6) descriptive 'attribution' framing without a localisation metric -> does NOT force NO_LOCALIZATION_METRIC
cat > "$TMP/attribution.json" <<'EOF'
{"method": "integrated_gradients", "n_examples": 100, "cohort_level": true,
 "localization_metric": "none",
 "sanity_checks": ["model_randomization", "data_randomization"], "interpretation": "attribution"}
EOF
python3 "$SCRIPT" --manifest "$TMP/attribution.json" --out "$OUT" --quiet >/dev/null 2>&1
check "attribution framing does NOT fire NO_LOCALIZATION_METRIC" no_verdict NO_LOCALIZATION_METRIC
python3 "$SCRIPT" --manifest "$TMP/attribution.json" --strict --quiet >/dev/null 2>&1
check "exit 0 on rigorous attribution report" test "$?" -eq 0

# (7) the shipped challenge card passes
check "challenge verify.sh passes" bash "$CH/verify.sh"

echo "fail=$fail"; [[ "$fail" -eq 0 ]] && echo "ALL PASS" || echo "FAILURES: $fail"
exit "$fail"
