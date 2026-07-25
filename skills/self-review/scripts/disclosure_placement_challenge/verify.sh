#!/usr/bin/env bash
# Deterministic verifier for the AI-disclosure PLACEMENT challenge.
#
# INBODY_AI_DISCLOSURE used to assert a placement it could not know: "for a classical /
# senior-MA target this belongs on the title page". That is true for some journals and false
# for others, and the profiles in this repo already said so, in their own words:
#
#   npj Digital Medicine        "document use in Methods section"
#   Investigative Radiology     "disclosed in cover letter and Acknowledgments section"
#   Diabetes & Metabolism J.    "must be declared on title page"
#   British J. of Radiology     "AI disclosure in the cover letter is required"
#
# So the verdict fired identically at a journal that wants the paragraph exactly where it is
# and at one that forbids it there — telling the author to move something correct. Across five
# real projects this produced eight fires, and NOT ONE of them could be scored real or
# spurious, because the answer depended on a target nobody had told the detector. A verdict
# that cannot be scored can never be shown to work.
#
# Now the target decides: body-legitimate -> silent, title-page/cover-letter-only -> Major,
# and NO target recorded -> Minor, naming the ambiguity instead of asserting a placement.
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
DET="$HERE/../check_classical_style.py"
FIX="$HERE/fixture"
PROF="$HERE/../../../write-paper/references/journal_profiles"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT

pass=0; fail=0
ck() { if [ "$2" = "$3" ]; then printf '  PASS  %-58s got=%s\n' "$1" "$3"; pass=$((pass+1));
       else printf '  FAIL  %-58s want=%s got=%s\n' "$1" "$2" "$3"; fail=$((fail+1)); fi; }
fires() { python3 "$DET" --manuscript "$FIX/manuscript.md" "$@" 2>&1 | grep -c "INBODY_AI_DISCLOSURE"; }
sev()  { python3 "$DET" --manuscript "$FIX/manuscript.md" "$@" 2>&1 \
           | grep "INBODY_AI_DISCLOSURE" | grep -oE "Major|Minor" | head -1; }

echo "== the journals disagree, and each profile is obeyed =="
ck "npj Digital Medicine (Methods) -> silent"        0 "$(fires --profile "$PROF/npj_Digital_Medicine.md")"
# the case that exposed a stem bug: "Acknowledgments" is a BODY section, so the body is correct
ck "Investigative Radiology (cover + Acknowledgments) -> silent" 0 "$(fires --profile "$PROF/Investigative_Radiology.md")"
ck "EJPC (cover + Methods/Acknowledgements) -> silent" 0 "$(fires --profile "$PROF/European_Journal_of_Preventive_Cardiology.md")"
ck "Diabetes & Metabolism J. (title page) -> fires"   1 "$(fires --profile "$PROF/Diabetes_Metabolism_Journal.md")"
ck "British J. of Radiology (cover letter) -> fires"  1 "$(fires --profile "$PROF/British_Journal_of_Radiology.md")"

# A body location whose section name contains none of the body tokens: the "(body)" marker is
# the convention that keeps it readable. JACC: Advances is the real instance.
ck "a body section named nothing like 'Methods' -> silent, via (body)" 0 "$(fires --profile "$PROF/JACC_Advances.md")"
ck "and the same string without the marker would fire" 1 "$(fires --disclosure-placement 'Declaration section immediately above the References')"

echo "== every populated profile behaves per its OWN stated policy =="
# Populated from each profile's own prose; a wrong line here produces wrong advice, so the
# whole set is asserted rather than a sample.
for j in npj_Digital_Medicine Investigative_Radiology JNIS Journal_of_Stroke Liver_International \
         PLOS_Medicine RYAI The_Lancet The_Lancet_Digital_Health World_Journal_of_Hepatology \
         Korean_Journal_of_Internal_Medicine Korean_Circulation_Journal KJR \
         Hepatology_Communications Lancet_Gastroenterology_and_Hepatology \
         Journal_of_Clinical_Endocrinology_and_Metabolism; do
  ck "body-legitimate: $j" 0 "$(fires --profile "$PROF/$j.md")"
done
for j in Academic_Radiology JKMS British_Journal_of_Radiology Diabetes_Metabolism_Journal; do
  ck "not-in-body: $j" 1 "$(fires --profile "$PROF/$j.md")"
done

echo "== severity follows knowledge, not house style =="
ck "a declared title-page target is Major" "Major" "$(sev --profile "$PROF/Diabetes_Metabolism_Journal.md")"
ck "no target recorded is only Minor"      "Minor" "$(sev)"
OUT="$(python3 "$DET" --manuscript "$FIX/manuscript.md" 2>&1)"
if echo "$OUT" | grep -q "no target journal is recorded"; then ck "and it names the ambiguity" 0 0
else ck "and it names the ambiguity" 0 1; fi
if echo "$OUT" | grep -q "belongs on the title page"; then ck "never asserting a placement it cannot know" 0 1
else ck "never asserting a placement it cannot know" 0 0; fi

echo "== --strict: an unknown target must not fail a build =="
python3 "$DET" --manuscript "$FIX/manuscript.md" --strict >/dev/null 2>&1
ck "no target -> exit 0 (Minor)" 0 "$?"
python3 "$DET" --manuscript "$FIX/manuscript.md" --profile "$PROF/Diabetes_Metabolism_Journal.md" --strict >/dev/null 2>&1
ck "title-page target -> exit 1 (Major)" 1 "$?"
python3 "$DET" --manuscript "$FIX/manuscript.md" --profile "$PROF/npj_Digital_Medicine.md" --strict >/dev/null 2>&1
ck "Methods target -> exit 0 (silent)" 0 "$?"

echo "== the inline override, for a target with no profile on disk =="
ck "--disclosure-placement 'title page' fires"  1 "$(fires --disclosure-placement 'title page')"
ck "--disclosure-placement 'Methods' silent"    0 "$(fires --disclosure-placement 'Methods')"
ck "inline beats the profile"                   1 "$(fires --profile "$PROF/npj_Digital_Medicine.md" --disclosure-placement 'title page')"

echo "== pre-existing behaviour is untouched =="
N="$(python3 "$DET" --manuscript "$FIX/about_disclosure.md" 2>&1 | grep -c "INBODY_AI_DISCLOSURE")"
ck "a paper ABOUT disclosure still does not fire" 0 "$N"
printf '# T\n\nSee Methods §2 for the model.\n' > "$TMP/sec.md"
S="$(python3 "$DET" --manuscript "$TMP/sec.md" 2>&1 | grep -c "SECTION_SYMBOL")"
ck "the section-symbol verdict is unaffected" 1 "$S"

echo "== the artifact names its own author =="
python3 "$DET" --manuscript "$FIX/manuscript.md" --profile "$PROF/npj_Digital_Medicine.md" \
  --out "$TMP/r.json" >/dev/null 2>&1
R="$(python3 -c "import json;d=json.load(open('$TMP/r.json'));print(d.get('detector')=='check_classical_style' and d.get('disclosure_placement') is not None)")"
ck "qc JSON names the detector AND records the placement" "True" "$R"

echo
printf 'AI-disclosure placement challenge: %d passed, %d failed\n' "$pass" "$fail"
[ "$fail" -eq 0 ] || exit 1
