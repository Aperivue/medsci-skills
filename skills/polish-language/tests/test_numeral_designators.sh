#!/usr/bin/env bash
# Regression test: a digit that NAMES something is not a counted quantity.
#
# `check_small_numbers` flagged any single digit followed by a lowercase word and told the author to
# spell it out. On nine ordinary clinical sentences it was right twice. The rest were labels:
#
#     "Patients with type 2 diabetes"  ->  "2 diabetes" — spell out   ->  "type two diabetes"
#     "Grade 3 adverse events"         ->  "3 adverse"
#     "Stage 4 disease"                ->  "4 disease"
#     "See Table 2 for details"        ->  "2 for"
#     "At day 7 follow-up"             ->  "7 follow"
#
# Advice that turns a correct sentence into a wrong one is the fastest way to teach an author to stop
# running the linter — and "spell out Table 2" additionally breaks `check_figure_citation`, which
# then cannot find the reference. Across this repo's own markdown the rule produced 1,499 flags; 308
# of them were this.
#
# The exemption is keyed on the word BEFORE the digit, not on what follows: "8 patients" and
# "3 deaths" are genuine counts and look identical from the right-hand side.
set -u

REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
L="$REPO_ROOT/skills/polish-language/scripts/lint_consistency.py"

pass=0
fail=0
ck() {
  local label="$1" expected="$2" actual="$3"
  if [ "$expected" = "$actual" ]; then
    printf '  PASS  %-56s %s\n' "$label" "$actual"
    pass=$((pass + 1))
  else
    printf '  FAIL  %-56s expected=%s actual=%s\n' "$label" "$expected" "$actual"
    fail=$((fail + 1))
  fi
}

flags() {  # flags <sentence> -> number of small-number findings
  python3 - "$L" "$1" <<'PY'
import importlib.util, sys
spec = importlib.util.spec_from_file_location("lc", sys.argv[1])
m = importlib.util.module_from_spec(spec)
sys.modules["lc"] = m
spec.loader.exec_module(m)
print(len(m.check_small_numbers([sys.argv[2]])))
PY
}

echo "==== a designator + digit is a LABEL: must be quiet ===="
for s in \
  "Patients with type 2 diabetes were included." \
  "Grade 3 adverse events occurred in four patients." \
  "Stage 4 disease was present at baseline." \
  "Phase 3 trials confirmed this." \
  "See Table 2 for details." \
  "The CONSORT diagram appears in Figure 1 above." \
  "Section 6 describes the audit." \
  "Group 2 received placebo." \
  "At day 7 follow-up, the effect persisted." \
  "In year 3 of follow-up, attrition rose."
do
  ck "quiet: ${s:0:44}" 0 "$(flags "$s")"
done

echo "==== NEGATIVE CONTROLS — a genuine count must still be flagged ===="
for s in \
  "We enrolled 8 patients." \
  "There were 3 deaths." \
  "A total of 4 centres participated." \
  "The model used 5 covariates." \
  "We excluded 2 records after review."
do
  ck "flags: ${s:0:44}" 1 "$(flags "$s")"
done

echo "==== the exemption is anchored to the word, not merely present in the line ===="
# "type" appears, but the digit belongs to a count later in the sentence.
ck "designator elsewhere does not excuse a count" 1 \
   "$(flags "Among patients with type 2 diabetes we excluded 6 records.")"

echo
echo "  passed=$pass failed=$fail"
[ "$fail" -eq 0 ] || exit 1
echo "OK: labels are left alone, counts are still counted."
