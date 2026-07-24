#!/usr/bin/env bash
# Deterministic verifier for the cohort-arithmetic NUMBER-BINDING challenge.
#
# The arithmetic in this detector was never wrong. What was wrong is which numbers it fed
# into it: on a real manuscript every one of its three observed fires was false, because each
# capture latched onto a digit belonging to something else.
#
#   "882 KSAR S4-1 events occurred"        -> bound the 1 of the label "S4-1" as the event
#                                             count, and declared 2.48 per 100 PY irreconcilable
#                                             with 1 event.
#   "over 35,581.3 person-years"           -> the integer part could not reach the noun past
#                                             the decimal point, so the FRACTIONAL DIGIT matched:
#                                             a cohort of "3 person-years".
#   "| Characteristic | Normal | ... |"     -> the one-letter column hint "n" matched the word
#                                             "Normal", so each characteristic row's value was
#                                             summed as a stratum size: 8,299 against a
#                                             "stated total" of 194. (The identical
#                                             one-character-substring bug was fixed once in
#                                             check_confounding_completeness and never here.)
#
# A detector whose every observed fire is false teaches its user to skip the whole class, and
# this class — rate back-calculation, exclusion cascades, tier partitions — is one nothing else
# covers. So the fix is binding, not thresholds: when a number cannot be bound to its quantity,
# the check now says NOTHING. An unbindable numerator is not evidence of an arithmetic error.
#
# Which makes the second half of this card the important half: the genuine defects must still
# fire, or the fix has merely bought silence.
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
DET="$HERE/../check_cohort_arithmetic.py"
FIX="$HERE/fixture"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT

pass=0; fail=0
ck() { if [ "$2" = "$3" ]; then printf '  PASS  %-58s got=%s\n' "$1" "$3"; pass=$((pass+1));
       else printf '  FAIL  %-58s want=%s got=%s\n' "$1" "$2" "$3"; fail=$((fail+1)); fi; }
has() { if echo "$2" | grep -q "$3"; then ck "$1" 0 0; else ck "$1" 0 1; fi; }
hasnt() { if echo "$2" | grep -q "$3"; then ck "$1" 0 1; else ck "$1" 0 0; fi; }

echo "== the three real false positives are silent =="
python3 "$DET" --manuscript "$FIX/real_negatives.md" --strict >/dev/null 2>&1
ck "a manuscript whose arithmetic closes -> exit 0" 0 "$?"
OUT="$(python3 "$DET" --manuscript "$FIX/real_negatives.md" 2>&1)"
hasnt "no rate back-calculation fired"        "$OUT" "RATE_BACKCALC"
hasnt "no partition overlap fired"            "$OUT" "PARTITION_OVERLAP"
hasnt "and the label digit was never read as a count" "$OUT" "1 events"
hasnt "nor the decimal tail as the person-time"       "$OUT" "/ 3 PY"

echo "== a Table 1 is not a stratum partition =="
# The header that broke it. "Normal" must not answer to the hint "n".
printf '| Characteristic | Normal | Adverse |\n|---|---|---|\n| Age, years | 52.1 | 56.8 |\n| Male, n (%%) | 4,051 | 6,054 |\n| Body mass index | 23.1 | 29.7 |\n| Total, n | 194 | 6,054 |\n' > "$TMP/t1.md"
OUT="$(python3 "$DET" --manuscript "$TMP/t1.md" 2>&1)"
hasnt "an exposure-stratified Table 1 stays silent" "$OUT" "PARTITION_OVERLAP"

echo "== THE OTHER HALF: genuine defects must still fire =="
python3 "$DET" --manuscript "$FIX/genuine_defects.md" --strict >/dev/null 2>&1
ck "a real discrepancy -> exit 1" 1 "$?"
OUT="$(python3 "$DET" --manuscript "$FIX/genuine_defects.md" 2>&1)"
has "the impossible rate is named"            "$OUT" "RATE_BACKCALC"
has "with the correct recomputation"          "$OUT" "10 per 100"
has "the non-disjoint partition is named"     "$OUT" "PARTITION_OVERLAP"
has "with the correct sum"                    "$OUT" "9,500"

echo "== decimal person-time is now READ, not skipped =="
# The fix must not buy its silence by ignoring fractional person-time: here the same decimal
# figure is present and the rate really is wrong, so it must fire — and with the full number.
python3 "$DET" --manuscript "$FIX/decimal_person_time.md" --strict >/dev/null 2>&1
ck "a wrong rate over fractional person-time -> exit 1" 1 "$?"
OUT="$(python3 "$DET" --manuscript "$FIX/decimal_person_time.md" 2>&1)"
has "the whole person-time is used, not its tail" "$OUT" "35,581.3 PY"
hasnt "and not the fractional digit"              "$OUT" "/ 3 PY"

echo "== a column genuinely called n still resolves =="
printf '| Stratum | n | Events |\n|---|---|---|\n| A | 10 | 1 |\n| B | 20 | 2 |\n| Total | 40 | 3 |\n' > "$TMP/n.md"
OUT="$(python3 "$DET" --manuscript "$TMP/n.md" 2>&1)"
has "an exact one-letter header still matches" "$OUT" "PARTITION_OVERLAP"

echo "== the artifact names its own author =="
python3 "$DET" --manuscript "$FIX/genuine_defects.md" --out "$TMP/r.json" >/dev/null 2>&1
has "qc JSON carries the detector key" "$(cat "$TMP/r.json")" '"detector": "check_cohort_arithmetic"'

echo
printf 'cohort-arithmetic binding challenge: %d passed, %d failed\n' "$pass" "$fail"
[ "$fail" -eq 0 ] || exit 1
