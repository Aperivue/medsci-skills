#!/usr/bin/env bash
# Regression tests for sync-submission scope_drift_check.py.
#
# Synthetic fixtures only. No network needed.

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
SCRIPT="$REPO_ROOT/skills/sync-submission/scripts/scope_drift_check.py"
TMP="$(mktemp -d -t scope_drift.XXXXXX)"
trap 'rm -rf "$TMP"' EXIT

[[ -f "$SCRIPT" ]] || { echo "ENV-ERR: script missing" >&2; exit 2; }
command -v python3 >/dev/null 2>&1 || { echo "ENV-ERR: python3 missing" >&2; exit 2; }

fail=0
ran=0
assert_exit() {
    local label="$1" expected="$2" actual="$3"
    ran=$((ran + 1))
    if [[ "$expected" == "$actual" ]]; then
        printf '  PASS  %-50s exit=%s\n' "$label" "$actual"
    else
        printf '  FAIL  %-50s expected=%s actual=%s\n' "$label" "$expected" "$actual"
        fail=$((fail + 1))
    fi
}

# --------------------------------------------------------------------------
# Case 1: well-formed manuscript. AUC appears in Methods, Results, Limitations.
# --------------------------------------------------------------------------
MS1="$TMP/case1.md"
cat > "$MS1" <<'EOF'
## **METHODS**
We computed the area under the curve (AUC) on the held-out test set. The
primary metric is AUC = 0.820.

## **RESULTS**
The pooled AUC was 0.820 (95% CI 0.78 to 0.86).

## **DISCUSSION**

### Limitations
A sensitivity analysis on the primary AUC of 0.820 was not pre-specified.
EOF
python3 "$SCRIPT" --manuscript "$MS1" --out "$TMP/case1.json" --quiet
assert_exit "case 1: consistent anchor (0.820 in all)" 0 $?

# --------------------------------------------------------------------------
# Case 2: AUC 0.869 appears only in Limitations. Should FAIL.
# --------------------------------------------------------------------------
MS2="$TMP/case2.md"
cat > "$MS2" <<'EOF'
## **METHODS**
We computed AUC on the held-out test set.

## **RESULTS**
The pooled AUC was 0.820 (95% CI 0.78 to 0.86).

## **DISCUSSION**

### Limitations
A leave-pair-out sensitivity analysis produced an envelope of AUC values:
primary pool of 0.869 (95% CI 0.81 to 0.92), with neighborhood values
0.851, 0.872, 0.881, and 0.890.
EOF
python3 "$SCRIPT" --manuscript "$MS2" --out "$TMP/case2.json" --quiet
assert_exit "case 2: 0.869 limits-only anchor" 1 $?
python3 - "$TMP/case2.json" <<'PY' || fail=$((fail + 1))
import json, sys
with open(sys.argv[1]) as fh: rep = json.load(fh)
anchors = [a["anchor"] for a in rep["limitations_only_anchors"]]
assert "0.869" in anchors, anchors
PY

# --------------------------------------------------------------------------
# Case 3: PROSPERO commits to Freeman-Tukey but Methods does not.
# --------------------------------------------------------------------------
MS3="$TMP/case3.md"
PR3="$TMP/case3_prospero.md"
cat > "$MS3" <<'EOF'
## **METHODS**
Pooled estimates were computed in Python with descriptive statistics only.

## **RESULTS**
Pooled value 0.50.
EOF
cat > "$PR3" <<'EOF'
# PROSPERO Record

Synthesis: Freeman-Tukey transformation followed by random-effects pooling
(DerSimonian-Laird estimator).
EOF
python3 "$SCRIPT" --manuscript "$MS3" --prospero "$PR3" --out "$TMP/case3.json" --quiet
assert_exit "case 3: PROSPERO Freeman-Tukey, methods absent" 1 $?
python3 - "$TMP/case3.json" <<'PY' || fail=$((fail + 1))
import json, sys
with open(sys.argv[1]) as fh: rep = json.load(fh)
methods_listed = [s["method"] for s in rep["synthesis_method_drift"]]
assert "Freeman-Tukey" in methods_listed, methods_listed
PY

# --------------------------------------------------------------------------
# Case 4: no prospero supplied + clean manuscript = PASS.
# --------------------------------------------------------------------------
MS4="$TMP/case4.md"
cat > "$MS4" <<'EOF'
## **METHODS**
AUC = 0.700 on the validation set.

## **RESULTS**
External AUC = 0.700 (95% CI 0.65 to 0.75).

## **DISCUSSION**
The external AUC of 0.700 demonstrates ...
EOF
python3 "$SCRIPT" --manuscript "$MS4" --out "$TMP/case4.json" --quiet
assert_exit "case 4: clean, no prospero" 0 $?

echo ""
echo "ran=$ran fail=$fail"
[[ $fail -eq 0 ]]
