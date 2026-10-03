#!/usr/bin/env bash
# Regression test for the Model Card / Datasheet completeness gate (model-card).
# Synthetic, PII-free. Stdlib-only (python3).
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DET="$HERE/../scripts/check_model_card_complete.py"
CH="$HERE/../scripts/check_model_card_complete_challenge"
REF="$HERE/../references"
OUT="$(mktemp -t mcc_XXXX).json"
trap 'rm -f "$OUT"' EXIT

fail=0
check() { local label="$1"; shift
    if "$@" >/dev/null 2>&1; then printf '  PASS  %s\n' "$label"
    else printf '  FAIL  %s\n' "$label"; fail=$((fail+1)); fi
}
has() { python3 -c "
import json
d=json.load(open('$OUT'))
assert any(c['verdict']=='$1' for c in d['claims']), '$1 not found'"; }
count() { python3 -c "
import json
d=json.load(open('$OUT'))
assert len(d['claims'])==$1, f\"{len(d['claims'])} != $1\""; }

[[ -f "$DET" ]] || { echo "ENV-ERR: detector missing" >&2; exit 2; }

# (1) complete card + datasheet -> OK, exit 0
python3 "$DET" --card "$CH/fixture/complete/MODEL_CARD.md" --datasheet "$CH/fixture/complete/DATASHEET.md" --strict --quiet >/dev/null 2>&1
check "complete card+datasheet passes (exit 0)" test "$?" -eq 0

# (2) incomplete card -> exit 1, MISSING + EMPTY
python3 "$DET" --card "$CH/fixture/incomplete/MODEL_CARD.md" --out "$OUT" --strict --quiet >/dev/null 2>&1
check "incomplete card exits 1" test "$?" -eq 1
check "MISSING_SECTION detected" has MISSING_SECTION
check "EMPTY_REQUIRED_SECTION detected" has EMPTY_REQUIRED_SECTION

# (3) unfilled Model Card template -> all 9 required sections empty
python3 "$DET" --card "$REF/model_card_template.md" --out "$OUT" --strict --quiet >/dev/null 2>&1
check "unfilled card template exits 1" test "$?" -eq 1
check "9 empty sections in unfilled card template" count 9

# (4) unfilled card + datasheet templates -> 9 + 7 = 16 empty
python3 "$DET" --card "$REF/model_card_template.md" --datasheet "$REF/datasheet_template.md" --out "$OUT" --quiet >/dev/null 2>&1
check "16 empty sections across both unfilled templates" count 16

# (5) "N/A" / "None" count as a filled answer (not flagged empty)
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"; rm -f "$OUT"' EXIT
cat > "$TMP/card.md" <<'MD'
# Model Card: t
## Model Details
- **Type**: U-Net
## Intended Use
- triage
## Out-of-Scope Use
- N/A
## Training Data
- 100 patients
## Evaluation Data
- internal split
## Metrics
- Dice with CI
## Quantitative Analyses
- Dice 0.8
## Ethical Considerations
- None
## Caveats and Recommendations
- single centre
MD
python3 "$DET" --card "$TMP/card.md" --out "$OUT" --strict --quiet >/dev/null 2>&1
check "N/A and None count as filled (exit 0)" test "$?" -eq 0

# Variants of the complete fixture, one targeted edit each (python: portable substitution).
GOOD="$CH/fixture/complete/MODEL_CARD.md"
variant() { # $1 out-file, $2 old text, $3 new text
    python3 - "$GOOD" "$1" "$2" "$3" <<'PY'
import sys
src, out, old, new = sys.argv[1:5]
s = open(src, encoding="utf-8").read()
assert old in s, old
open(out, "w", encoding="utf-8").write(s.replace(old, new, 1))
PY
}
only() { python3 -c "
import json
d=json.load(open('$OUT'))
v=[c['verdict'] for c in d['claims']]
assert v==['$1'], v
assert '$2' in d['claims'][0]['detail'], d['claims'][0]['detail']"; }

# (6) F1 — a single unfilled field in an otherwise-filled section is flagged (UNFILLED_FIELD)
variant "$TMP/lic.md" "CC BY-NC 4.0 (confirmed by the developing group)" "[NEEDS INPUT — state the licence the user confirmed; do not assume]"
python3 "$DET" --card "$TMP/lic.md" --out "$OUT" --strict --quiet >/dev/null 2>&1
check "unfilled License field exits 1" test "$?" -eq 1
check "unfilled License -> UNFILLED_FIELD in Model Details" only UNFILLED_FIELD "License"

variant "$TMP/sub.md" "Dice 0.74 for lesions under 2 cm vs 0.85 over 2 cm; comparable across the two scanner vendors." "[NEEDS INPUT: performance by the Factors above]"
python3 "$DET" --card "$TMP/sub.md" --out "$OUT" --strict --quiet >/dev/null 2>&1
check "unfilled subgroup-performance field exits 1" test "$?" -eq 1
check "unfilled subgroup field -> UNFILLED_FIELD in Quantitative Analyses" only UNFILLED_FIELD "Disaggregated"

variant "$TMP/ver.md" "inter-reader Dice 0.86." "inter-reader Dice [VERIFY]."
python3 "$DET" --card "$TMP/ver.md" --out "$OUT" --strict --quiet >/dev/null 2>&1
check "a residual [VERIFY] field -> UNFILLED_FIELD" only UNFILLED_FIELD "Training Data"

# (7) F1 — templates with only the first field of each required section filled still fail
python3 - "$REF/model_card_template.md" "$TMP/part_card.md" "$REF/datasheet_template.md" "$TMP/part_ds.md" <<'PY'
import re, sys
def first_per_section(src, out):
    parts = re.split(r"(?m)^(## .*)$", open(src, encoding="utf-8").read())
    for i in range(2, len(parts), 2):
        parts[i] = re.sub(r"\[NEEDS INPUT[^\]]*\]", "filled", parts[i], count=1)
    open(out, "w", encoding="utf-8").write("".join(parts))
first_per_section(sys.argv[1], sys.argv[2]); first_per_section(sys.argv[3], sys.argv[4])
PY
python3 "$DET" --card "$TMP/part_card.md" --datasheet "$TMP/part_ds.md" --out "$OUT" --strict --quiet >/dev/null 2>&1
check "partly filled templates exit 1" test "$?" -eq 1
check "partly filled templates -> UNFILLED_FIELD" has UNFILLED_FIELD

# (8) F2 — N/A is not an answer for Quantitative Analyses (whole section N/A -> EMPTY)
variant "$TMP/qna.md" "- **Overall performance**: mean Dice 0.81 (95% CI 0.78-0.84), HD95 7.2 mm, on the held-out cohort.
- **Disaggregated / subgroup performance**: Dice 0.74 for lesions under 2 cm vs 0.85 over 2 cm; comparable across the two scanner vendors." "- **Overall performance**: N/A
- **Disaggregated / subgroup performance**: N/A"
python3 "$DET" --card "$TMP/qna.md" --out "$OUT" --strict --quiet >/dev/null 2>&1
check "all-N/A Quantitative Analyses exits 1" test "$?" -eq 1
check "all-N/A Quantitative Analyses -> EMPTY_REQUIRED_SECTION" only EMPTY_REQUIRED_SECTION "Quantitative Analyses"

# (9) F2 — a null word in hint text / a stray token does not rescue an unfilled field
variant "$TMP/hint.md" "- Not validated for non-contrast CT, for paediatric patients, or for scanners outside the two vendors in the training set; must not be used autonomously without a radiologist in the loop." "- [NEEDS INPUT] (write none if no exclusions)"
python3 "$DET" --card "$TMP/hint.md" --out "$OUT" --strict --quiet >/dev/null 2>&1
check "unfilled field with 'none' hint exits 1" test "$?" -eq 1
variant "$TMP/na.md" "- Not validated for non-contrast CT, for paediatric patients, or for scanners outside the two vendors in the training set; must not be used autonomously without a radiologist in the loop." "- [NEEDS INPUT] (ask Dr Na)"
python3 "$DET" --card "$TMP/na.md" --out "$OUT" --strict --quiet >/dev/null 2>&1
check "unfilled field next to token 'Na' exits 1" test "$?" -eq 1

# (10) negative controls — must stay clean
variant "$TMP/nullword.md" "comparable across the two scanner vendors." "none of the vendor subgroups differed (Dice 0.80 vs 0.81)."
python3 "$DET" --card "$TMP/nullword.md" --strict --quiet >/dev/null 2>&1
check "control: null word inside a real Quantitative value stays clean" test "$?" -eq 0
variant "$TMP/comment.md" "## Metrics" "## Metrics
<!-- fill every [NEEDS INPUT] from executed results -->"
python3 "$DET" --card "$TMP/comment.md" --strict --quiet >/dev/null 2>&1
check "control: [NEEDS INPUT] only inside an HTML comment stays clean" test "$?" -eq 0
variant "$TMP/ethna.md" "- Errors could lead to missed lesions; automation bias is a risk if used without independent review. The training cohort is single-centre and may not represent other populations." "- **Equity concerns**: N/A."
python3 "$DET" --card "$TMP/ethna.md" --strict --quiet >/dev/null 2>&1
check "control: whole-value N/A in Ethical Considerations stays clean" test "$?" -eq 0

# (11) negative controls — markdown link text starting with 'verify' is not a placeholder
CAV="Performance on small lesions is weaker and should be communicated to users."
variant "$TMP/link.md" "$CAV" "$CAV
- Before local deployment, [verify the acquisition protocol against the checklist](https://example.org/protocol-checklist)."
python3 "$DET" --card "$TMP/link.md" --strict --quiet >/dev/null 2>&1
check "control: '[verify ...](url)' link in Caveats stays clean" test "$?" -eq 0
variant "$TMP/link2.md" "$CAV" "$CAV
- See [Verifying model outputs](https://example.org/verifying)."
python3 "$DET" --card "$TMP/link2.md" --strict --quiet >/dev/null 2>&1
check "control: '[Verifying ...](url)' link stays clean" test "$?" -eq 0
variant "$TMP/link3.md" "$CAV" "$CAV
- [VERIFY]"
python3 "$DET" --card "$TMP/link3.md" --out "$OUT" --strict --quiet >/dev/null 2>&1
check "a bare [VERIFY] (not a link) in Caveats is still UNFILLED_FIELD" only UNFILLED_FIELD "Caveats"

# (12) negative control — whole-value 'N/A,' in Ethical Considerations stays clean
variant "$TMP/ethna2.md" "- Errors could lead to missed lesions; automation bias is a risk if used without independent review. The training cohort is single-centre and may not represent other populations." "N/A,"
python3 "$DET" --card "$TMP/ethna2.md" --strict --quiet >/dev/null 2>&1
check "control: whole-value 'N/A,' in Ethical Considerations stays clean" test "$?" -eq 0

# (13) negative controls — reference-style links and link definitions are not placeholders
variant "$TMP/ref1.md" "$CAV" "$CAV
- See [Verify the protocol][proto] before deployment.

[proto]: https://example.org/protocol-checklist"
python3 "$DET" --card "$TMP/ref1.md" --strict --quiet >/dev/null 2>&1
check "control: '[Verify ...][ref]' reference link stays clean" test "$?" -eq 0
variant "$TMP/ref2.md" "$CAV" "$CAV
- Check the protocol against the [verify] checklist.

[verify]: https://example.org/protocol-checklist"
python3 "$DET" --card "$TMP/ref2.md" --strict --quiet >/dev/null 2>&1
check "control: '[verify]: url' link definition stays clean" test "$?" -eq 0
variant "$TMP/ref3.md" "$CAV" "$CAV
- See [VERIFY][proto].

[VERIFY]: https://example.org/protocol-checklist"
python3 "$DET" --card "$TMP/ref3.md" --strict --quiet >/dev/null 2>&1
check "control: upper-case '[VERIFY][ref]' + '[VERIFY]: url' stays clean" test "$?" -eq 0

# (14) negative controls — a token inside a fenced code block is not an unfilled field
variant "$TMP/fence1.md" "$CAV" "$CAV
\`\`\`
- **Placeholder syntax**: [VERIFY]
\`\`\`"
python3 "$DET" --card "$TMP/fence1.md" --strict --quiet >/dev/null 2>&1
check "control: [VERIFY] inside a \`\`\` fence stays clean" test "$?" -eq 0
variant "$TMP/fence2.md" "$CAV" "$CAV
~~~text
[NEEDS INPUT: example token]
~~~"
python3 "$DET" --card "$TMP/fence2.md" --strict --quiet >/dev/null 2>&1
check "control: [NEEDS INPUT] inside a ~~~ fence stays clean" test "$?" -eq 0
variant "$TMP/fence3.md" "$CAV" "$CAV
\`\`\`
example
\`\`\`
- [VERIFY: source of this caveat]"
python3 "$DET" --card "$TMP/fence3.md" --out "$OUT" --strict --quiet >/dev/null 2>&1
check "a [VERIFY: ...] after a closed fence is still UNFILLED_FIELD" only UNFILLED_FIELD "Caveats"

# (15) case-sensitive: only the template's upper-case tokens are fields
variant "$TMP/lc.md" "$CAV" "$CAV
- Sites should [verify] scanner settings locally."
python3 "$DET" --card "$TMP/lc.md" --strict --quiet >/dev/null 2>&1
check "control: lower-case '[verify]' prose bracket stays clean" test "$?" -eq 0
variant "$TMP/uc.md" "$CAV" "$CAV
- [NEEDS INPUT — deployment caveat]"
python3 "$DET" --card "$TMP/uc.md" --out "$OUT" --strict --quiet >/dev/null 2>&1
check "an upper-case [NEEDS INPUT — ...] is still UNFILLED_FIELD" only UNFILLED_FIELD "Caveats"

# (16) negative control — whole-value 'N/A!' in Ethical Considerations stays clean
variant "$TMP/ethna3.md" "- Errors could lead to missed lesions; automation bias is a risk if used without independent review. The training cohort is single-centre and may not represent other populations." "N/A!"
python3 "$DET" --card "$TMP/ethna3.md" --strict --quiet >/dev/null 2>&1
check "control: whole-value 'N/A!' in Ethical Considerations stays clean" test "$?" -eq 0

echo "fail=$fail"; [[ "$fail" -eq 0 ]] && echo "ALL PASS" || echo "FAILURES: $fail"
exit "$fail"
