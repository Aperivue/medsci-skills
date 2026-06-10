#!/usr/bin/env bash
# Test scripts/preflight_gate.py — the A6 submission pre-flight orchestrator.
# Builds synthetic, PII-free fixture projects in a temp dir and asserts the gate
# halts on a deterministic blocker, passes a clean package, tolerates absent
# inputs (skipped, not blocker), normalizes the inverted cover_letter exit code,
# and honors --require / --skip. Stdlib-only; offline (no network).
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$HERE/../scripts/preflight_gate.py"
PASS=0
FAIL=0
ok()  { echo "  PASS: $1"; PASS=$((PASS+1)); }
bad() { echo "  FAIL: $1"; FAIL=$((FAIL+1)); }

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

DIRTY="$WORK/dirty"
CLEAN="$WORK/clean"
mkdir -p "$DIRTY/manuscript" "$CLEAN/manuscript" "$CLEAN/submission/chest/manuscript"

# dirty: an unresolved [@NEW:] placeholder + a TODO; bib does not define the marker
cat > "$DIRTY/manuscript/manuscript.md" <<'EOF'
# Introduction

We follow prior work [@smith2020] and a competing-risk model [@NEW:competing-risk].

## Methods

Analysis used R. TODO: cite the package.

## References
EOF
cat > "$DIRTY/refs.bib" <<'EOF'
@article{smith2020, title={A real paper}, author={Smith, John}, journal={NEJM}, year={2020}, doi={10.1056/x}}
EOF

# clean: no markers, every cited key defined
cat > "$CLEAN/manuscript/manuscript.md" <<'EOF'
# Introduction

We follow prior work [@smith2020] using a competing-risk model.

## Methods

Analysis used R version 4.3.

## References
EOF
cat > "$CLEAN/refs.bib" <<'EOF'
@article{smith2020, title={A real paper}, author={Smith, John}, journal={NEJM}, year={2020}, doi={10.1056/x}}
EOF

J() { python3 -c "import json,sys; d=json.load(open(sys.argv[1])); print(d[sys.argv[2]] if sys.argv[2] in d else json.dumps(d))" "$@"; }
STATUS() { python3 -c "import json,sys; d=json.load(open(sys.argv[1])); c=[x for x in d['checks'] if x['id']==sys.argv[2]][0]; print(c['status'])" "$@"; }

# 1. dirty halts with exit 1
python3 "$SCRIPT" --project-root "$DIRTY" --quiet
[ $? -eq 1 ] && ok "dirty package halts (exit 1)" || bad "dirty package should halt"

# 2. report: halt true, placeholders blocker, absent inputs skipped (tolerance)
RPT="$DIRTY/qc/preflight_gate_report.json"
[ "$(J "$RPT" halt)" = "True" ] && ok "report halt=true" || bad "report halt should be true"
[ "$(STATUS "$RPT" placeholders)" = "blocker" ] && ok "placeholders is a blocker" || bad "placeholders should block"
[ "$(STATUS "$RPT" cover_letter_drift)" = "skipped" ] && ok "cover_letter_drift skipped (no cover letter)" || bad "cover_letter_drift should skip"
[ "$(STATUS "$RPT" copy_divergence)" = "skipped" ] && ok "copy_divergence skipped (no copies)" || bad "copy_divergence should skip"
[ "$(STATUS "$RPT" sync_drift)" = "skipped" ] && ok "sync_drift skipped (no journal)" || bad "sync_drift should skip"

# 3. references is a P1 warn (offline unverified), never a blocker by itself
[ "$(STATUS "$RPT" references)" = "warn" ] && ok "references offline -> warn (non-halting)" || bad "references should warn offline"

# 4. clean package passes (exit 0)
python3 "$SCRIPT" --project-root "$CLEAN" --quiet
[ $? -eq 0 ] && ok "clean package passes (exit 0)" || bad "clean package should pass"
[ "$(J "$CLEAN/qc/preflight_gate_report.json" submission_safe)" = "True" ] && ok "clean report submission_safe=true" || bad "clean should be submission_safe"

# 5. inverted cover-letter exit code normalized to warn (default), blocker under --require
cat > "$CLEAN/submission/chest/cover_letter.md" <<'EOF'
Dear Editor, the manuscript is approximately 8000 words with 99 references. Sincerely,
EOF
python3 "$SCRIPT" --project-root "$CLEAN" --journal chest --quiet
[ $? -eq 0 ] && ok "cover-letter drift warns (P1, non-halting by default)" || bad "cover drift should not halt by default"
RC="$CLEAN/qc/preflight_gate_report.json"
python3 -c "
import json,sys
d=json.load(open('$RC')); c=[x for x in d['checks'] if x['id']=='cover_letter_drift'][0]
sys.exit(0 if c['exit_code']==2 and c['status']=='warn' else 1)
" && ok "cover_letter inverted exit 2 normalized to warn" || bad "cover_letter exit normalization wrong"

python3 "$SCRIPT" --project-root "$CLEAN" --journal chest --require cover_letter_drift --quiet
[ $? -eq 1 ] && ok "--require cover_letter_drift promotes to blocker (halt)" || bad "--require should halt on cover drift"

# 6. --strict promotes all P1 to halting (cover drift now blocks)
python3 "$SCRIPT" --project-root "$CLEAN" --journal chest --strict --quiet
[ $? -eq 1 ] && ok "--strict promotes P1 cover drift to halt" || bad "--strict should halt on cover drift"

# 7. --skip removes a check
python3 "$SCRIPT" --project-root "$CLEAN" --journal chest --strict --skip cover_letter_drift --quiet
[ $? -eq 0 ] && ok "--skip cover_letter_drift drops it (clean pass under --strict)" || bad "--skip should drop the check"

# 8. --require on a check that cannot run -> gate error (exit 2)
python3 "$SCRIPT" --project-root "$DIRTY" --require sync_drift --quiet
[ $? -eq 2 ] && ok "--require sync_drift (no journal) -> gate error exit 2" || bad "required-but-unrunnable should exit 2"

# 9. unknown check id -> exit 2
python3 "$SCRIPT" --project-root "$CLEAN" --require nonsense --quiet 2>/dev/null
[ $? -eq 2 ] && ok "unknown --require id -> exit 2" || bad "unknown id should exit 2"

echo ""
echo "test_preflight_gate: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]
