#!/usr/bin/env bash
# Deterministic verifier for the CRediT-integrity challenge card.
#
# CRediT terms are published with the paper and every co-author reads them, but nothing ties a
# term to anything. During one byline negotiation three terms were requested in sequence —
# Visualization, Methodology, Formal analysis — each unsupported by the project record; a
# fourth, Conceptualization, was entirely legitimate and had no repository artifact at all,
# because it lived in email and in a critique that drove a restructure.
#
# That asymmetry is the whole design. The taxonomy is checkable; the work behind it often is
# not. So the manuscript-only verdicts are majors, and corroboration is a prompt that can be
# answered with an attestation.
#
# The positive fixture carries four separable defects:
#   "Statistical analysis" / "Manuscript writing"  -> CREDIT_TERM_INVALID  (not the fourteen)
#   K.W., who is in no byline                      -> CREDIT_INITIALS_UNRESOLVED
#   Sam Poe, credited nowhere                      -> CREDIT_AUTHOR_UNLISTED
#   Visualization on a paper with no figures       -> CREDIT_UNCORROBORATED (prompt)
#
# The negatives are what keep it usable:
#   a correct CRediT section on a paper WITH a figure -> silent
#   a manuscript with no contributions section at all -> exit 2, asserts nothing
#   a byline it cannot resolve -> the author/initials cross-check is SKIPPED, not guessed;
#     a wrong byline would otherwise accuse every author at once
#   author ORDER and equal-contribution are never mentioned by any verdict — they are
#     negotiated, and gating them is what this deliberately does not do
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
DET="$HERE/../check_credit_integrity.py"
FIX="$HERE/fixture"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

pass=0; fail=0
ck() { if [ "$2" = "$3" ]; then printf '  PASS  %-56s exit=%s\n' "$1" "$3"; pass=$((pass+1));
       else printf '  FAIL  %-56s want=%s got=%s\n' "$1" "$2" "$3"; fail=$((fail+1)); fi; }
has() { if echo "$2" | grep -q "$3"; then ck "$1" 0 0; else ck "$1" 0 1; fi; }
hasnt() { if echo "$2" | grep -q "$3"; then ck "$1" 0 1; else ck "$1" 0 0; fi; }

echo "== positive: a taxonomy that does not describe the work =="
python3 "$DET" --manuscript "$FIX/manuscript_bad.md" --quiet >/dev/null 2>&1
ck "a defective CRediT section exits 1" 1 "$?"
OUT="$(python3 "$DET" --manuscript "$FIX/manuscript_bad.md" 2>&1)"
has "a non-CRediT term is named"             "$OUT" "CREDIT_TERM_INVALID"
has "and the right replacement is offered"   "$OUT" "closest is Formal analysis"
has "orphan initials are named"              "$OUT" "CREDIT_INITIALS_UNRESOLVED"
has "an uncredited byline author is named"   "$OUT" "CREDIT_AUTHOR_UNLISTED"
has "Visualization with no figure is queried" "$OUT" "CREDIT_UNCORROBORATED"
# a section that says "CRediT" means the fourteen, so an invalid term there is major
has "an invalid term is MAJOR when CRediT is declared" "$OUT" "major] CREDIT_TERM_INVALID"

echo "== the line this gate must never cross =="
hasnt "author order is never mentioned"      "$OUT" "[Oo]rder"
hasnt "equal contribution is never mentioned" "$OUT" "equal"

echo "== negative: a correct section on a paper that has a figure =="
python3 "$DET" --manuscript "$FIX/manuscript_good.md" --quiet >/dev/null 2>&1
ck "a correct CRediT section -> silent" 0 "$?"
OUT="$(python3 "$DET" --manuscript "$FIX/manuscript_good.md" 2>&1)"
has   "and it really did read the terms"     "$OUT" "7 CRediT term"
hasnt "with nothing invented"                "$OUT" "CREDIT_"

echo "== negative: nothing to check asserts nothing =="
cat > "$TMP/no_credit.md" <<'EOF'
# A manuscript with no contributions section

Jane Doe, Alex Roe

## Methods

Nothing here declares who did what.
EOF
python3 "$DET" --manuscript "$TMP/no_credit.md" --quiet >/dev/null 2>&1
ck "no contributions section -> skipped" 2 "$?"

echo "== an unresolvable byline is skipped, not guessed =="
# One name only: the bijection would accuse every initial in the section. It must stand down.
cat > "$TMP/thin_byline.md" <<'EOF'
# A manuscript whose byline cannot be parsed

## Author Contributions

CRediT: J.D. Conceptualization. A.R. Methodology. S.P. Supervision.
EOF
OUT="$(python3 "$DET" --manuscript "$TMP/thin_byline.md" 2>&1)"
has   "it says the cross-check was skipped"  "$OUT" "cross-check skipped"
hasnt "and accuses nobody"                   "$OUT" "CREDIT_INITIALS_UNRESOLVED"
hasnt "nor invents an unlisted author"       "$OUT" "CREDIT_AUTHOR_UNLISTED"

echo "== an optional contribution record, when the project keeps one =="
printf 'J.D.: figures/flow.png, analysis/model.R\nA.R.: analysis/model.R\n' > "$TMP/record.yaml"
OUT="$(python3 "$DET" --manuscript "$FIX/manuscript_good.md" --contribution-record "$TMP/record.yaml" 2>&1)"
has "an author absent from the record is queried" "$OUT" "S.P. is credited"
has "and only as a prompt"                        "$OUT" "minor] CREDIT_UNCORROBORATED"
# without the record that half must not run at all
OUT="$(python3 "$DET" --manuscript "$FIX/manuscript_good.md" 2>&1)"
hasnt "no record -> that half does not run"       "$OUT" "is credited in the manuscript but"

echo "== the artifact names its own author =="
python3 "$DET" --manuscript "$FIX/manuscript_bad.md" --out "$TMP/r.json" >/dev/null 2>&1
has "qc JSON carries the detector key" "$(cat "$TMP/r.json")" '"detector": "check_credit_integrity"'

echo
printf 'credit-integrity challenge: %d passed, %d failed\n' "$pass" "$fail"
[ "$fail" -eq 0 ] || exit 1
