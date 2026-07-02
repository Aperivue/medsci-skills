#!/usr/bin/env bash
# Regression test for the claim-vs-artifact cross-check (self-review Phase 2.5f).
# Synthetic fixture reproduces: (a) a primary re-designated at manuscript stage,
# (b) an E-value (2.79) that does not recompute from its stated primary HR 1.34,
# (c) a correctly-arithmetic E-value attached to a non-primary (cancer) estimate.
# Stdlib-only (python3).
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$HERE/../scripts/check_claim_artifact.py"
MAN="$HERE/fixtures/claim_manuscript.md"
PRE="$HERE/fixtures/claim_prereg.md"
OUT="$(mktemp -t ca_XXXX).json"
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

python3 "$SCRIPT" --manuscript "$MAN" --prereg "$PRE" --out "$OUT" --strict >/dev/null 2>&1
check "exit 1 under --strict (Major present)" test "$?" -eq 1
check "JSON artifact written" test -s "$OUT"
check "PRIMARY_REASSIGNED detected"  has_verdict PRIMARY_REASSIGNED
check "EVALUE_ARITHMETIC detected (2.79 vs HR 1.34)" has_verdict EVALUE_ARITHMETIC
check "EVALUE_NON_PRIMARY detected (cancer sHR)"     has_verdict EVALUE_NON_PRIMARY

# Clean case: primary matches prereg, correct primary E-value, no reassignment.
CLEAN="$(mktemp -t ca_clean_XXXX).md"
trap 'rm -f "$OUT" "$CLEAN"' EXIT
cat > "$CLEAN" <<'EOF'
## Methods
The primary analysis was the association between emphysema and all-cause mortality
in the complete-case multivariable Cox model.
## Results
The E-value for the primary association (HR 1.34) was 2.02.
EOF
python3 "$SCRIPT" --manuscript "$CLEAN" --prereg "$PRE" --strict >/dev/null 2>&1
check "exit 0 on clean manuscript (matching primary, correct E-value)" test "$?" -eq 0

# Advisory case (less-defensive trim): a bare honest manuscript-stage disclosure —
# WITHOUT explicit re-designation/after-results language — is PRIMARY_DISCLOSURE_NOTE
# (advisory), NOT PRIMARY_REASSIGNED (Major). estimand-provenance guidance recommends
# writing this, so it must not fail --strict on its own.
DISC="$(mktemp -t ca_disc_XXXX).md"
trap 'rm -f "$OUT" "$CLEAN" "$DISC"' EXIT
cat > "$DISC" <<'EOF'
## Methods
The primary analysis was the association between emphysema and all-cause mortality
in the complete-case multivariable Cox model. Using the multiple-imputation model as
the estimation approach was a manuscript-stage analytical decision, disclosed here and
reported coequally with the pre-specified complete-case analysis.
## Results
The E-value for the primary association (HR 1.34) was 2.02.
EOF
python3 "$SCRIPT" --manuscript "$DISC" --prereg "$PRE" --out "$OUT" --strict >/dev/null 2>&1
check "exit 0 on honest manuscript-stage disclosure (advisory, not Major)" test "$?" -eq 0
check "PRIMARY_DISCLOSURE_NOTE emitted (advisory)" has_verdict PRIMARY_DISCLOSURE_NOTE
check "no PRIMARY_REASSIGNED on bare disclosure" python3 -c "
import json
d=json.load(open('$OUT'))
raise SystemExit(0 if not any(c['verdict']=='PRIMARY_REASSIGNED' for c in d['claims']) else 1)
"

# Structured-prereg anchor: a project.yaml with explicit primary_* keys + a
# manuscript whose primary is substantively consistent -> the estimand check anchors
# on the structured field VALUES (not a `# PRIMARY — locked` comment or a lexically
# dissimilar free-text paragraph) and does NOT allege ESTIMAND_DRIFT. Regression for
# the false Major at overlap 0.26 on a reconciled estimand.
SMAN="$HERE/fixtures/claim_manuscript_structured.md"
SPRE="$HERE/fixtures/claim_prereg_structured.md"
python3 "$SCRIPT" --manuscript "$SMAN" --prereg "$SPRE" --out "$OUT" >/dev/null 2>&1
check "no ESTIMAND_DRIFT on a structured, consistent prereg" python3 -c "
import json
d=json.load(open('$OUT'))
raise SystemExit(0 if not any(c['verdict']=='ESTIMAND_DRIFT' for c in d['claims']) else 1)
"
python3 "$SCRIPT" --manuscript "$SMAN" --prereg "$SPRE" --strict >/dev/null 2>&1
check "exit 0 on structured consistent prereg (no Major)" test "$?" -eq 0

# Code-label reconciliation (--scripts): a manuscript asserting a SINGLE primary vs an
# analysis script annotating a model 'co-primary' -> PRIMARY_LABEL_CODE_DRIFT (advisory,
# not Major). A consistent scripts dir and the no-flag backward-compatible default.
SP="$HERE/fixtures/claim_manuscript_single_primary.md"
python3 "$SCRIPT" --manuscript "$SP" --scripts "$HERE/fixtures/claim_scripts_coprimary" --out "$OUT" >/dev/null 2>&1
check "PRIMARY_LABEL_CODE_DRIFT on code co-primary vs single-primary manuscript" has_verdict PRIMARY_LABEL_CODE_DRIFT
python3 "$SCRIPT" --manuscript "$SP" --scripts "$HERE/fixtures/claim_scripts_coprimary" --strict >/dev/null 2>&1
check "code-label drift is advisory (exit 0 under --strict)" test "$?" -eq 0
python3 "$SCRIPT" --manuscript "$SP" --scripts "$HERE/fixtures/claim_scripts_consistent" --out "$OUT" >/dev/null 2>&1
check "no drift when scripts carry no co-primary label" python3 -c "
import json
d=json.load(open('$OUT'))
raise SystemExit(0 if not any(c['verdict']=='PRIMARY_LABEL_CODE_DRIFT' for c in d['claims']) else 1)
"

echo "fail=$fail"; [[ "$fail" -eq 0 ]] && echo "ALL PASS" || echo "FAILURES: $fail"
exit "$fail"
