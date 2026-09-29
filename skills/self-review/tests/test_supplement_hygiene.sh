#!/usr/bin/env bash
# Regression test for the supplement-hygiene gate (self-review §J supplement pass).
# Synthetic, PII-free fixtures reproduce reader-facing supplement residue: a §/§L
# internal label, an unfilled placeholder (SX / [Authors] / figure-glob / build-dir
# path), a build marker ([VERIFY]/TODO), response-to-reviewers framing, and pre-
# execution planning residue; plus a body↔supplement cross-reference that does not
# resolve. The clean fixture is a normal reader-facing supplement.
# Stdlib-only (python3).
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$HERE/../scripts/check_supplement_hygiene.py"
DIRTY="$HERE/fixtures/supp_dirty.md"
CLEAN="$HERE/fixtures/supp_clean.md"
XBODY="$HERE/fixtures/supp_xref_body.md"
XSUPP="$HERE/fixtures/supp_xref_supp.md"
OUT="$(mktemp -t supphyg_XXXX).json"
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

# (1) dirty supplement: all five residue verdicts, Major present -> exit 1 under --strict
python3 "$SCRIPT" --supplement "$DIRTY" --out "$OUT" --strict --quiet >/dev/null 2>&1
check "exit 1 under --strict (Major present)" test "$?" -eq 1
check "JSON artifact written" test -s "$OUT"
check "SUPP_INTERNAL_LABEL detected"   has_verdict SUPP_INTERNAL_LABEL
check "SUPP_PLACEHOLDER detected"      has_verdict SUPP_PLACEHOLDER
check "SUPP_BUILD_MARKER detected"     has_verdict SUPP_BUILD_MARKER
check "SUPP_RESPONSE_FRAMING detected" has_verdict SUPP_RESPONSE_FRAMING
check "SUPP_PLANNING_RESIDUE detected" has_verdict SUPP_PLANNING_RESIDUE

# (2) clean supplement: no residue -> exit 0
python3 "$SCRIPT" --supplement "$CLEAN" --strict --quiet >/dev/null 2>&1
check "exit 0 on clean supplement" test "$?" -eq 0

# (3) body cites Supplementary Table 2 (present) + Figure 9 (absent) -> exactly one
#     SUPP_XREF_UNRESOLVED for the unresolved callout
python3 "$SCRIPT" --supplement "$XSUPP" --manuscript "$XBODY" --out "$OUT" --quiet >/dev/null 2>&1
check "SUPP_XREF_UNRESOLVED detected" has_verdict SUPP_XREF_UNRESOLVED
check "only the unresolved callout fires (Table 2 resolves)" python3 -c "
import json
d=json.load(open('$OUT'))
x=[c for c in d['claims'] if c['verdict']=='SUPP_XREF_UNRESOLVED']
assert len(x)==1 and '9' in x[0]['detail'], x
"

# (3b) S-prefixed / plural / range callouts, matched by KIND. The old callout regex saw
#      only "Supplementary <Kind> <digits>", so "Supplementary Figures S2 and S3" and
#      "Figs S6–S8" matched nothing, and "Supplementary Figure 4" resolved against a
#      "Table S4" by number alone. Expected unresolved: Figure 3 (plural list), Figure 7
#      (range interior), Figure 4 (only a Table S4 exists). Table S1 / Fig. S1 / Figure
#      S2 / S6 / S8 / Table S4 resolve; main-text "Table 1" / "Figures 1–3" are ignored.
KBODY="$HERE/fixtures/supp_xref_kind_body.md"
KSUPP="$HERE/fixtures/supp_xref_kind_supp.md"
KCAPS="$HERE/fixtures/supp_xref_kind_captions.md"
python3 "$SCRIPT" --supplement "$KSUPP" --manuscript "$KBODY" --out "$OUT" --strict --quiet >/dev/null 2>&1
check "exit 1 under --strict on cited-but-absent supplementary figures" test "$?" -eq 1
check "exactly Figure 3, 4, 7 unresolved (S-prefix list, range, kind mismatch)" python3 -c "
import json, re
d=json.load(open('$OUT'))
got={re.search(r\"'Supplementary (\w+) (\d+)'\", c['detail']).groups()
     for c in d['claims'] if c['verdict']=='SUPP_XREF_UNRESOLVED'}
assert got=={('Figure','3'),('Figure','4'),('Figure','7')}, got
"
# Negative control: the same body resolves once a captions file defines the missing figures
# as caption lines ("**Figure S3.** ...", "Figure S7: ..."), not headings.
python3 "$SCRIPT" --supplement "$KSUPP" --supplement "$KCAPS" --manuscript "$KBODY" --out "$OUT" --strict --quiet >/dev/null 2>&1
check "exit 0 when a captions file defines the cited figures" test "$?" -eq 0

# (4) missing --supplement -> usage error (exit 2)
python3 "$SCRIPT" --manuscript "$XBODY" --quiet >/dev/null 2>&1
check "exit 2 when no --supplement given" test "$?" -eq 2

# (5) participant-PII tie: a pseudonym + name tied to an individual response row ->
#     SUPP_PARTICIPANT_PII_TIE; a byline/roster with only aggregate responses -> clean.
PIILEAK="$HERE/fixtures/supplement_pii_tie.md"
PIICLEAN="$HERE/fixtures/supplement_pii_clean.md"
python3 "$SCRIPT" --supplement "$PIILEAK" --out "$OUT" --quiet >/dev/null 2>&1
check "SUPP_PARTICIPANT_PII_TIE on identity+individual-response row" python3 -c "
import json
d=json.load(open('$OUT'))
assert any(c['verdict']=='SUPP_PARTICIPANT_PII_TIE' for c in d['claims']), 'not flagged'
"
python3 "$SCRIPT" --supplement "$PIICLEAN" --out "$OUT" --quiet >/dev/null 2>&1
check "no PII tie on a byline/roster with aggregate responses" python3 -c "
import json
d=json.load(open('$OUT'))
assert not any(c['verdict']=='SUPP_PARTICIPANT_PII_TIE' for c in d['claims']), 'roster false positive'
"

echo "fail=$fail"; [[ "$fail" -eq 0 ]] && echo "ALL PASS" || echo "FAILURES: $fail"
exit "$fail"
