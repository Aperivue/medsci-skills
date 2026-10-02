#!/usr/bin/env bash
# Deterministic verifier for the density-complaint challenge card.
#
# The bug this gate exists to catch is not hypothetical: a revision answers a "too dense" comment
# point-by-point and comes back LONGER than the version that drew the complaint, every named term
# higher than before. Point-by-point response rewards adding text, and "too long" is the one
# comment adding text cannot answer.
#
# So the fixtures reproduce that arithmetic:
#   v_prev       -> what the reviewers saw
#   v20_longer   -> answered point-by-point, body got LONGER   -> DENSITY_COMPLAINT_UNADDRESSED
#   v21_shorter  -> actually cut, body got SHORTER             -> OK
#
# And the half that keeps the gate honest: a decision letter with NO density complaint must stay
# silent no matter what the word count did — the gate is not a "shorter is always better" nag.
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
DET="$HERE/../check_density_complaint.py"
FIX="$HERE/fixture"

pass=0; fail=0
ck() { if [ "$2" = "$3" ]; then printf '  PASS  %-52s exit=%s\n' "$1" "$3"; pass=$((pass+1));
       else printf '  FAIL  %-52s want=%s got=%s\n' "$1" "$2" "$3"; fail=$((fail+1)); fi; }

# 1) the revision that got LONGER under a density complaint -> fires
python3 "$DET" --comments "$FIX/decision_letter.md" --previous "$FIX/v_prev.md" \
  --revised "$FIX/v20_longer.md" --strict >/dev/null 2>&1
ck "point-by-point revision got longer -> UNADDRESSED" 1 "$?"

# ...and it must NAME the verdict, not merely exit nonzero
python3 "$DET" --comments "$FIX/decision_letter.md" --previous "$FIX/v_prev.md" \
  --revised "$FIX/v20_longer.md" 2>&1 | grep "DENSITY_COMPLAINT_UNADDRESSED" >/dev/null \
  && ck "the verdict token is printed" 0 0 || ck "the verdict token is printed" 0 1

# 2) the revision that actually CUT -> silent
python3 "$DET" --comments "$FIX/decision_letter.md" --previous "$FIX/v_prev.md" \
  --revised "$FIX/v21_shorter.md" --strict >/dev/null 2>&1
ck "revision got shorter -> OK" 0 "$?"

# 3) NEGATIVE: a decision letter with no density complaint -> silent even if it got longer
cat > "$FIX/_no_complaint.md" <<'EOF'
Reviewer 1: Please add a sensitivity analysis and report the calibration slope.
Reviewer 2: The methods are sound. Add one sentence on generalizability.
EOF
python3 "$DET" --comments "$FIX/_no_complaint.md" --previous "$FIX/v_prev.md" \
  --revised "$FIX/v20_longer.md" --strict >/dev/null 2>&1
ck "no density complaint -> not a shorter-is-better nag" 0 "$?"
rm -f "$FIX/_no_complaint.md"

# 4) the JSON report carries the arithmetic a downstream consumer needs
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
python3 "$DET" --comments "$FIX/decision_letter.md" --previous "$FIX/v_prev.md" \
  --revised "$FIX/v20_longer.md" --out "$TMP/d.json" >/dev/null 2>&1
python3 - "$TMP/d.json" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
assert d["verdict"] == "DENSITY_COMPLAINT_UNADDRESSED", d["verdict"]
assert d["delta_words"] > 0 and d["density_complaints"], d
print("  PASS  JSON report has verdict + delta + complaints")
PY

# 5) a body LINE that starts with an end-section word is not a heading. "Supplementary Table S3
#    gives ..." in Results used to end the body there, so a longer revision measured shorter.
FILL="The cohort included adults with suspected disease who underwent imaging and follow up at the study centre."
printf 'Reviewer 1: The manuscript is too long and should be shortened.\n' > "$TMP/letter.md"
printf '## Introduction\n%s\n%s\n## Results\n%s\n%s\n## Discussion\n%s\n## References\n1. Ref.\n' \
  "$FILL" "$FILL" "$FILL" "$FILL" "$FILL" > "$TMP/prev.md"
printf '## Introduction\n%s\n%s\n## Results\n%s\nSupplementary Table S3 gives the per-site estimates.\n%s\n%s\n%s\n## Discussion\n%s\n%s\n## References\n1. Ref.\n' \
  "$FILL" "$FILL" "$FILL" "$FILL" "$FILL" "$FILL" "$FILL" "$FILL" > "$TMP/rev_supp.md"
python3 "$DET" --comments "$TMP/letter.md" --previous "$TMP/prev.md" --revised "$TMP/rev_supp.md" --strict >/dev/null 2>&1
ck "body line 'Supplementary Table ...' is not a heading" 1 "$?"
printf '## Introduction\n%s\nFunding sources had no role in the design of this study.\n%s\n%s\n## Results\n%s\n%s\n## Discussion\n%s\n## References\n1. Ref.\n' \
  "$FILL" "$FILL" "$FILL" "$FILL" "$FILL" "$FILL" > "$TMP/rev_fund.md"
python3 "$DET" --comments "$TMP/letter.md" --previous "$TMP/prev.md" --revised "$TMP/rev_fund.md" --strict >/dev/null 2>&1
ck "body line 'Funding sources had ...' is not a heading" 1 "$?"
# controls: real headings still end the body, as plain .docx-style lines, bold, or numbered,
# so a genuinely cut revision still clears.
printf 'Introduction\n%s\n%s\nResults\n%s\n%s\nDiscussion\n%s\nSupplementary Material\n%s\n%s\n%s\nReferences\n1. Ref.\n' \
  "$FILL" "$FILL" "$FILL" "$FILL" "$FILL" "$FILL" "$FILL" "$FILL" > "$TMP/prev_plain.md"
printf 'Introduction\n%s\n%s\nResults\n%s\nDiscussion\n%s\nSupplementary Material\n%s\n%s\n%s\n%s\nReferences\n1. Ref.\n' \
  "$FILL" "$FILL" "$FILL" "$FILL" "$FILL" "$FILL" "$FILL" "$FILL" > "$TMP/rev_plain_cut.md"
python3 "$DET" --comments "$TMP/letter.md" --previous "$TMP/prev_plain.md" --revised "$TMP/rev_plain_cut.md" --strict >/dev/null 2>&1
ck "plain-line 'Supplementary Material' heading still ends body" 0 "$?"
printf '## 1. Introduction\n%s\n## 2. Results\n%s\n**Funding**\n%s\n%s\n%s\n' \
  "$FILL" "$FILL" "$FILL" "$FILL" "$FILL" > "$TMP/rev_num_cut.md"
python3 "$DET" --comments "$TMP/letter.md" --previous "$TMP/prev.md" --revised "$TMP/rev_num_cut.md" --strict >/dev/null 2>&1
ck "numbered + bold headings bound a cut revision" 0 "$?"

# 6) run-in declaration headings ("Funding: None.", "Data availability: The data ...") still
#    end the body. A cut revision that adds a run-in data statement must still clear.
printf 'The manuscript is too long and should be shortened. Please also add a data availability statement.\n' > "$TMP/letter_da.md"
printf 'Introduction\n%s\n%s\nResults\n%s\n%s\nDiscussion\n%s\nFunding: None.\nReferences\n1. Ref.\n' \
  "$FILL" "$FILL" "$FILL" "$FILL" "$FILL" > "$TMP/prev_runin.md"
DA="Data availability: The de-identified data and the analysis code are available from the corresponding author on reasonable request after approval by the institutional review board."
printf 'Introduction\n%s\n%s\nResults\n%s\nDiscussion\n%s\n%s\nFunding: None.\nReferences\n1. Ref.\n' \
  "$FILL" "$FILL" "$FILL" "$FILL" "$DA" > "$TMP/rev_runin_cut.md"
python3 "$DET" --comments "$TMP/letter_da.md" --previous "$TMP/prev_runin.md" --revised "$TMP/rev_runin_cut.md" --strict >/dev/null 2>&1
ck "run-in 'Data availability: ...' ends the body" 0 "$?"
printf 'Introduction\n%s\n%s\nResults\n%s\nDiscussion\n%s\n**Conflicts of interest:** none declared.\n%s\n%s\nReferences.\n1. Ref.\n' \
  "$FILL" "$FILL" "$FILL" "$FILL" "$FILL" "$FILL" > "$TMP/rev_runin_bold.md"
python3 "$DET" --comments "$TMP/letter_da.md" --previous "$TMP/prev_runin.md" --revised "$TMP/rev_runin_bold.md" --strict >/dev/null 2>&1
ck "bold run-in 'Conflicts of interest:' ends the body" 0 "$?"
printf 'Introduction\n%s\n%s\nResults\n%s\nDiscussion\n%s\nFunding. None.\n%s\n%s\nReferences\n1. Ref.\n' \
  "$FILL" "$FILL" "$FILL" "$FILL" "$FILL" "$FILL" > "$TMP/rev_runin_period.md"
python3 "$DET" --comments "$TMP/letter_da.md" --previous "$TMP/prev_runin.md" --revised "$TMP/rev_runin_period.md" --strict >/dev/null 2>&1
ck "run-in 'Funding. None.' ends the body" 0 "$?"
printf 'Introduction\n%s\n%s\nResults\n%s\nDiscussion\n%s\nReferences.\n%s\n%s\n%s\n' \
  "$FILL" "$FILL" "$FILL" "$FILL" "$FILL" "$FILL" "$FILL" > "$TMP/rev_refs_period.md"
python3 "$DET" --comments "$TMP/letter_da.md" --previous "$TMP/prev_runin.md" --revised "$TMP/rev_refs_period.md" --strict >/dev/null 2>&1
ck "'References.' with a trailing period ends the body" 0 "$?"
# ...while a body sentence with a colon after a non-keyword lead is still body text
printf 'Introduction\n%s\n%s\nResults\n%s\n%s\nSupplementary Table S3: per-site estimates are given there.\n%s\n%s\nDiscussion\n%s\nFunding: None.\nReferences\n1. Ref.\n' \
  "$FILL" "$FILL" "$FILL" "$FILL" "$FILL" "$FILL" "$FILL" > "$TMP/rev_supp_colon.md"
python3 "$DET" --comments "$TMP/letter_da.md" --previous "$TMP/prev_runin.md" --revised "$TMP/rev_supp_colon.md" --strict >/dev/null 2>&1
ck "body line 'Supplementary Table S3: ...' is not a heading" 1 "$?"

echo
echo "  $pass passed, $fail failed"
[ "$fail" -eq 0 ] || exit 1
