#!/usr/bin/env bash
# Regression test for the claim-vs-artifact cross-check (self-review Phase 2.5f).
# Synthetic fixture reproduces: (a) a primary re-designated at manuscript stage,
# (b) an E-value (3.10) that does not recompute from its stated primary HR 1.52,
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
check "EVALUE_ARITHMETIC detected (3.10 vs HR 1.52)" has_verdict EVALUE_ARITHMETIC
check "EVALUE_NON_PRIMARY detected (cancer sHR)"     has_verdict EVALUE_NON_PRIMARY

# Clean case: primary matches prereg, correct primary E-value, no reassignment.
CLEAN="$(mktemp -t ca_clean_XXXX).md"
trap 'rm -f "$OUT" "$CLEAN"' EXIT
cat > "$CLEAN" <<'EOF'
## Methods
The primary analysis was the association between emphysema and all-cause mortality
in the complete-case multivariable Cox model.
## Results
The E-value for the primary association (HR 1.52) was 2.41.
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
The E-value for the primary association (HR 1.52) was 2.41.
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

# Registration chronology (manuscript-internal, no --prereg needed): a
# "prospectively registered" claim whose registration date (16 Apr 2026) postdates
# search completion (31 Mar 2026) -> REGISTRATION_CHRONOLOGY (Major), exit 1.
RB="$HERE/fixtures/claim_registration_bad.md"
python3 "$SCRIPT" --manuscript "$RB" --out "$OUT" --strict >/dev/null 2>&1
check "exit 1 on retrospective registration under a prospective claim" test "$?" -eq 1
check "REGISTRATION_CHRONOLOGY detected" has_verdict REGISTRATION_CHRONOLOGY
# Silent when registration precedes search-end, and when no "prospective" claim is made.
RC="$HERE/fixtures/claim_registration_clean.md"
python3 "$SCRIPT" --manuscript "$RC" --strict >/dev/null 2>&1
check "exit 0 on genuinely-prospective + no-prospective-claim registrations" test "$?" -eq 0

# YAML front matter is not body prose. A project that honestly records "the primary
# endpoint was changed ..." in a `changelog:` block was handed PRIMARY_REASSIGNED — a P0 —
# for keeping a good record. The same sentence in the BODY is a real self-admission and
# must still fire, which is what makes the first assertion mean something.
FM="$HERE/fixtures/claim_frontmatter_changelog.md"
python3 "$SCRIPT" --manuscript "$FM" --out "$OUT" --strict >/dev/null 2>&1
check "a changelog in YAML front matter is not a self-admission" test "$?" -eq 0
check "...and no PRIMARY_REASSIGNED is recorded" python3 -c "
import json
d=json.load(open('$OUT'))
raise SystemExit(0 if not any(c['verdict']=='PRIMARY_REASSIGNED' for c in d['claims']) else 1)
"
BR="$HERE/fixtures/claim_body_reassign.md"
python3 "$SCRIPT" --manuscript "$BR" --out "$OUT" --strict >/dev/null 2>&1
check "the same sentence in the body still fires (P0 preserved)" test "$?" -eq 1
check "PRIMARY_REASSIGNED detected in body" has_verdict PRIMARY_REASSIGNED

# E-value phrasings. The sentence window used to split on every '.', so the decimal
# point inside "HR 1.52" cut the estimate out of the window (EVALUE_UNVERIFIABLE), and
# "E-value = 3.10" / "(E-value 3.10)" were never read at all. HR 1.52 recomputes to
# 2.41; each wrong 3.10 must be EVALUE_ARITHMETIC (exit 1), each correct 2.41 must clear.
EV="$(mktemp -t ca_ev_XXXX).md"
trap 'rm -f "$OUT" "$CLEAN" "$DISC" "$EV"' EXIT
ev_case() {  # $1 expected exit, $2 expected verdict, $3 sentence
    printf '## Results\n\n%s\n' "$3" > "$EV"
    python3 "$SCRIPT" --manuscript "$EV" --out "$OUT" --strict >/dev/null 2>&1
    check "exit $1: $3" test "$?" -eq "$1"
    check "$2: $3" python3 -c "
import json
d=json.load(open('$OUT'))
ev=[c['verdict'] for c in d['claims'] if c['type']=='evalue']
raise SystemExit(0 if ev==['$2'] else 1)
"
}
ev_case 1 EVALUE_ARITHMETIC "The primary HR was 1.52 (95% CI 1.20-1.93); the E-value was 3.10."
ev_case 1 EVALUE_ARITHMETIC "The primary HR was 1.52; the E-value was 3.10."
ev_case 1 EVALUE_ARITHMETIC "The E-value was 3.10 for the primary HR of 1.52."
ev_case 1 EVALUE_ARITHMETIC "Primary HR 1.52, E-value = 3.10."
ev_case 1 EVALUE_ARITHMETIC "Hazard ratio 1.52 (E-value 3.10)."
ev_case 0 OK "The primary HR was 1.52 (95% CI 1.20-1.93); the E-value was 2.41."
ev_case 0 OK "Primary HR 1.52, E-value = 2.41."
ev_case 0 OK "Hazard ratio 1.52 (E-value 2.41)."
# The near-null CI-limit E-value phase2_5f asks for (HR 1.80, CI 1.20-2.70: 1.69).
ev_case 0 OK "The primary adjusted HR was 1.80 (95% CI 1.20-2.70); the E-value for the lower confidence limit was 1.69."
# Two estimates in one sentence: the E-value is correct for the adjusted HR 1.52 (2.41)
# though the unadjusted HR 1.80 (3.00) sits nearer. A value that fits a bound estimate
# clears; when the sentence names more than one estimate and the value fits none that
# could be read (here "HR for the primary outcome was 1.52" is too far apart to bind),
# it is EVALUE_UNVERIFIABLE (which estimate?), never EVALUE_ARITHMETIC.
ev_case 0 OK "The adjusted HR was 1.52 (95% CI 1.20-1.93) and the unadjusted HR was 1.80; the E-value was 2.41."
ev_case 0 EVALUE_UNVERIFIABLE "The adjusted HR for the primary outcome was 1.52 (95% CI 1.20-1.93) and the unadjusted HR was 1.80; the E-value was 2.41."
ev_case 0 EVALUE_UNVERIFIABLE "The adjusted HR for the primary outcome was 1.52 (95% CI 1.20-1.93) and the unadjusted HR was 1.80; the E-value was 4.50."
# The only estimate bound sits in a parenthetical aside outside the E-value phrase, and the
# E-value names another quantity: which estimate it is for cannot be read (main: advisory,
# rc 0), so it stays EVALUE_UNVERIFIABLE. A parenthetical INSIDE the phrase still binds.
ev_case 0 EVALUE_UNVERIFIABLE "The risk difference was 5.2% (HR 1.52 for death), and the E-value for the risk difference was 1.90."
ev_case 1 EVALUE_ARITHMETIC "The E-value for the primary association (HR 1.52) was 3.10."
# "the value" is not an E-value: no evalue claim at all.
printf '## Results\n\nThe primary HR was 1.52, and the value to use when the pilot is thin is 0.50.\n' > "$EV"
python3 "$SCRIPT" --manuscript "$EV" --out "$OUT" --strict >/dev/null 2>&1
check "'the value ... is 0.50' is not read as an E-value" python3 -c "
import json
d=json.load(open('$OUT'))
raise SystemExit(0 if not any(c['type']=='evalue' for c in d['claims']) else 1)
"

echo "fail=$fail"; [[ "$fail" -eq 0 ]] && echo "ALL PASS" || echo "FAILURES: $fail"
exit "$fail"
