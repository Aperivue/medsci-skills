#!/usr/bin/env bash
# Test scripts/check_cross_artifact_stale.py — the A3 cross-artifact staleness gate.
# Synthetic, PII-free fixtures: a body that corrects two labeled values, a stale
# supplement that disagrees, a checklist built against an older manuscript version,
# and a clean supplement that agrees.
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$HERE/../scripts/check_cross_artifact_stale.py"
PASS=0
FAIL=0
ok()  { echo "  PASS: $1"; PASS=$((PASS+1)); }
bad() { echo "  FAIL: $1"; FAIL=$((FAIL+1)); }

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

# body (v8 in filename) — corrected values
cat > "$WORK/manuscript_v8.md" <<'EOF'
## Results
The complete-case analysis included 95.7% of the cohort.
Inter-rater agreement was substantial (kappa = 0.923).
EOF

# stale supplement: disagreeing values for the same labels
mkdir -p "$WORK/aux"
cat > "$WORK/aux/supplement.md" <<'EOF'
Footnote: complete-case retention was 7.5% after exclusions.
Reliability sub-analysis: kappa = 0.904.
EOF

# checklist built against an older manuscript version
cat > "$WORK/aux/strobe_checklist.md" <<'EOF'
Target manuscript: cohort study v6 (2026-04-20)
Item 13: see Results, line 42.
EOF

# clean supplement that agrees with the body
mkdir -p "$WORK/clean"
cat > "$WORK/clean/supplement.md" <<'EOF'
Footnote: complete-case retention was 95.7%.
Reliability: kappa = 0.923.
EOF

run() { python3 "$SCRIPT" "$@" 2>/dev/null; }

# 1. drift + version-stale -> exit 1
run --manuscript "$WORK/manuscript_v8.md" --aux "$WORK/aux" --quiet
[ $? -eq 1 ] && ok "stale aux + old checklist version -> exit 1" || bad "should fail"

# 2. JSON reports both finding types
run --manuscript "$WORK/manuscript_v8.md" --aux "$WORK/aux" --out "$WORK/r.json" --quiet
python3 -c "
import json,sys
d=json.load(open('$WORK/r.json'))
types={f['type'] for f in d['findings']}
sys.exit(0 if {'labeled_value_drift','checklist_version_stale'} <= types
         and d['summary']['stale'] >= 2 and d['summary']['version_stale'] >= 1 else 1)
" && ok "JSON: labeled_value_drift (kappa+complete_case) + version_stale" || bad "JSON findings incomplete"

# 3. explicit --manuscript-version overrides filename inference
run --manuscript "$WORK/manuscript_v8.md" --aux "$WORK/aux/strobe_checklist.md" \
    --manuscript-version v8 --out "$WORK/r2.json" --quiet
python3 -c "
import json,sys
d=json.load(open('$WORK/r2.json'))
sys.exit(0 if d['summary']['version_stale'] == 1 else 1)
" && ok "explicit --manuscript-version flags stale checklist" || bad "version flag failed"

# 4. clean supplement that agrees -> exit 0
run --manuscript "$WORK/manuscript_v8.md" --aux "$WORK/clean" --quiet
[ $? -eq 0 ] && ok "agreeing supplement passes" || bad "agreeing supplement should pass"

# 5. missing --aux -> usage error (exit 2)
run --manuscript "$WORK/manuscript_v8.md" --quiet
[ $? -eq 2 ] && ok "missing --aux -> exit 2" || bad "missing --aux should be usage error"

# --- retired-term / old-value survivor scan (reframe-drift + claim-site propagation) ---
mkdir -p "$WORK/reframe"
# body reframed to "overall pooled"; a superseded headline value 1.72 -> 2.03
cat > "$WORK/reframe/manuscript.md" <<'EOF'
## Results
The overall pooled estimate was 2.03.
EOF
# supplement kept the retired framing AND the old value
cat > "$WORK/reframe/supplement.md" <<'EOF'
Supplementary Table S3. Location-stratified benchmark.
The dome benchmark hazard ratio was 1.72.
EOF
# a clean supplement matching the reframed body
cat > "$WORK/reframe/clean_suppl.md" <<'EOF'
Supplementary Table S3. Overall pooled estimate 2.03.
EOF

# 6. retired framing term survives in the supplement -> exit 1
run --manuscript "$WORK/reframe/manuscript.md" --aux "$WORK/reframe/supplement.md" \
    --retired-term "location-stratified benchmark" --out "$WORK/r3.json" --quiet
[ $? -eq 1 ] && ok "retired framing survivor in supplement -> exit 1" || bad "retired-term survivor should fail"
python3 -c "
import json,sys
d=json.load(open('$WORK/r3.json'))
sys.exit(0 if any(f['type']=='retired_framing_survivor' for f in d['findings']) else 1)
" && ok "JSON: retired_framing_survivor" || bad "missing retired_framing_survivor finding"

# 7. superseded value survives in the supplement -> exit 1
run --manuscript "$WORK/reframe/manuscript.md" --aux "$WORK/reframe/supplement.md" \
    --old-value 1.72 --out "$WORK/r4.json" --quiet
python3 -c "
import json,sys
d=json.load(open('$WORK/r4.json'))
sys.exit(0 if any(f['type']=='stale_old_value' for f in d['findings']) else 1)
" && ok "JSON: stale_old_value" || bad "missing stale_old_value finding"

# 8. retired term survives in the BODY itself (un-touched paragraph) -> exit 1
cat > "$WORK/reframe/body_stale.md" <<'EOF'
## Results
The overall pooled estimate was 2.03. As shown in the location-stratified benchmark, the dome stratum led.
EOF
run --manuscript "$WORK/reframe/body_stale.md" --retired-term "location-stratified benchmark" --quiet
[ $? -eq 1 ] && ok "retired survivor in body paragraph -> exit 1" || bad "body survivor should fail"

# 9. numeric boundary: --old-value 1.72 must NOT match 11.723 -> exit 0
cat > "$WORK/reframe/numbound.md" <<'EOF'
The value is 11.723 throughout.
EOF
run --manuscript "$WORK/reframe/numbound.md" --old-value 1.72 --quiet
[ $? -eq 0 ] && ok "old-value 1.72 does not match 11.723 (numeric boundary)" || bad "numeric boundary false positive"

# 10. reframed body + matching supplement, retired term absent -> exit 0
run --manuscript "$WORK/reframe/manuscript.md" --aux "$WORK/reframe/clean_suppl.md" \
    --retired-term "location-stratified benchmark" --old-value 1.72 --quiet
[ $? -eq 0 ] && ok "no survivors after full reframe -> exit 0" || bad "clean reframe should pass"

echo ""
echo "test_cross_artifact_stale: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]
