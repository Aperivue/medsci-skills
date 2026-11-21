#!/usr/bin/env bash
# Regression test: check_density_complaint.py must end the body at a heading, not at a sentence.
#
# The words that end the body ("Supplementary", "Funding", "Conflict", ...) also begin ordinary
# lines. A front-matter or body line such as "Supplementary Table 2 lists the full search
# strings" stopped the count there in BOTH versions, so everything after it went unmeasured: a
# revision that had been cut was reported as unchanged and the gate fired on it.
set -u

REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
DET="$REPO_ROOT/skills/revise/scripts/check_density_complaint.py"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

pass=0
fail=0
ck() {
  local label="$1" expected="$2" actual="$3"
  if [ "$expected" = "$actual" ]; then
    printf '  PASS  %-62s %s\n' "$label" "$actual"
    pass=$((pass + 1))
  else
    printf '  FAIL  %-62s expected=%s actual=%s\n' "$label" "$expected" "$actual"
    fail=$((fail + 1))
  fi
}
field() {  # prints NOJSON when that run wrote no report
  [ -f "$TMP/$1.json" ] || { echo NOJSON; return; }
  python3 -c "import json,sys; d=json.load(open(sys.argv[1])); print($2)" "$TMP/$1.json"
}
n=0
run() {  # run <name> <previous> <revised> -> exit code; each run writes its own report
  rm -f "$TMP/$1.json"
  python3 "$DET" --comments "$TMP/letter.md" --previous "$TMP/$2" --revised "$TMP/$3" \
    --strict --out "$TMP/$1.json" > "$TMP/$1.out" 2>&1
  echo $?
}

printf 'Reviewer 1: The manuscript is too long and should be shortened.\n' > "$TMP/letter.md"

# A manuscript with no Introduction heading whose text has a prose line beginning with one of the
# body-ending words. $1 = number of body sentences after that line.
mk() {  # mk <path> <n body sentences> [words after the References heading]
  local path="$1" n="$2" tail="${3:-}"
  {
    echo "# A synthetic perspective on reader calibration"; echo
    echo "Calibration of readers is rarely reported in imaging studies."; echo
    echo "Supplementary Table 2 lists the full search strings used for the scoping search"; echo
    echo "## The argument"; echo
    i=0
    while [ "$i" -lt "$n" ]; do
      echo "Readers who complete a calibration set agree more often with the reference standard."
      i=$((i + 1))
    done
    echo; echo "## References"; echo
    echo "1. Synthetic A. A placeholder reference. J Synth. 2020;1:1-2."
    [ -n "$tail" ] && echo "$tail"
  } > "$path"
}
mk "$TMP/prev.md" 20
mk "$TMP/shorter.md" 12
mk "$TMP/longer.md" 28

echo "==== the body runs past a prose line that starts with a body-ending word ===="
ck "revision cut below that line: OK, exit 0"                0 "$(run short prev.md shorter.md)"
ck "  the cut is measured (delta < 0)"                       True "$(field short "d['delta_words'] < 0")"
ck "  verdict OK"                                            OK "$(field short "d['verdict']")"
ck "revision grew below that line: exit 1"                   1 "$(run long prev.md longer.md)"
ck "  the growth is measured (delta > 0)"                    True "$(field long "d['delta_words'] > 0")"
ck "  the body ends at the References heading"               references "$(field long "d['measured_span']['revised']['end_marker']")"
ck "  and the span is printed for a human to read"           1 "$(grep -c "^measured revised: lines" "$TMP/long.out")"

echo "==== NEGATIVE CONTROLS: real headings still end the body ===="
mk "$TMP/refs_grew.md" 20 "2. Synthetic B. Another placeholder reference with many extra words here. J Synth. 2021;2:3-4."
ck "words added after '## References' are not body words: exit 1" 1 "$(run refs prev.md refs_grew.md)"
ck "  delta is exactly 0"                                    0 "$(field refs "d['delta_words']")"

# A run-in label and a bare short heading both end the body; text after them is not counted.
{
  echo "Introduction"; echo
  echo "Readers who complete a calibration set agree more often with the reference standard."; echo
  echo "Funding: This synthetic work received no funding and this sentence must not be counted."
} > "$TMP/runin_prev.md"
{
  echo "Introduction"; echo
  echo "Readers who complete a calibration set agree more often with the reference standard."; echo
  echo "Funding: This synthetic work received no funding and this much longer sentence, with a good many additional words, must not be counted either."
} > "$TMP/runin_new.md"
run runin runin_prev.md runin_new.md >/dev/null
ck "a run-in 'Funding:' label ends the body (delta 0)"       0 "$(field runin "d['delta_words']")"
ck "  end marker is funding"                                 funding "$(field runin "d['measured_span']['revised']['end_marker']")"

# Each of these ends the body: text added after it must leave the delta at 0. Each of the prose
# lines does not: text removed after it must be measured as a cut.
ends_body() {  # ends_body <label> <ending line>
  printf 'Introduction\nReaders agreed.\n%s\nA short tail.\n' "$2" > "$TMP/eb_prev.md"
  printf 'Introduction\nReaders agreed.\n%s\nA much longer tail with a good many additional words in it.\n' "$2" > "$TMP/eb_new.md"
  n=$((n + 1))
  ck "ends the body: $1 (exit 1: not shorter)" 1 "$(run "eb$n" eb_prev.md eb_new.md)"
  ck "  delta is 0" 0 "$(field "eb$n" "d['delta_words']")"
}
ends_body "bare 'References' line"            "References"
ends_body "'References.' with a full stop"    "References."
ends_body "'**Funding**: ...' run-in"         "**Funding**: This synthetic work received no funding."
ends_body "'Funding. ...' run-in"             "Funding. This synthetic work received no funding."
ends_body "'## Acknowledgements'"             "## Acknowledgements"
ends_body "'3. References' (numbered)"        "3. References"
ends_body "'## Supplementary Results'"        "## Supplementary Results"
ends_body "'## References ##' (closed)"       "## References ##"
ends_body "bare 'Conflict' line"              "Conflict"
ends_body "'Conflicts of interest: none'"     "Conflicts of interest: none declared."
ends_body "bare 'Supplementary Tables'"       "Supplementary Tables"
ends_body "'Conflict of Interest Disclosure'" "Conflict of Interest Disclosure"
ends_body "'## Competing interests'"          "## Competing interests"
ends_body "'## Bibliography'"                 "## Bibliography"
ends_body "'Funding:None' (no space)"         "Funding:None declared."
ends_body "'## Supplementary analyses by site' (heading prefix)" "## Supplementary analyses by site"

is_prose() {  # is_prose <label> <line that must NOT end the body>
  printf 'Introduction\nReaders agreed.\n%s\nOne two three four five six seven eight nine ten.\n' "$2" > "$TMP/ip_prev.md"
  printf 'Introduction\nReaders agreed.\n%s\nOne two three.\n' "$2" > "$TMP/ip_new.md"
  n=$((n + 1))
  ck "is prose: $1 (exit 0: the cut is seen)" 0 "$(run "ip$n" ip_prev.md ip_new.md)"
  ck "  delta is -7" -7 "$(field "ip$n" "d['delta_words']")"
}
is_prose "'Funding for the registry' (wrapped line)"   "Funding for the registry"
is_prose "'Funding was allocated as follows: ...'"     "Funding was allocated as follows: readers received a fixed fee."
is_prose "'Supplementary Table 2 lists ...'"           "Supplementary Table 2 lists the search strings."
is_prose "'References are listed below.'"              "References are listed below."
is_prose "'Conflicting results were seen.'"            "Conflicting results were seen."
is_prose "'Supplementary analyses ... were consistent.'" "Supplementary analyses by site were consistent."
is_prose "'## Acknowledging limitations' (a body heading)" "## Acknowledging limitations"

echo "==== the reported span is the span that was counted ===="
printf 'Introduction\nReaders agreed.\n## References\nSynthetic A. 2020.\n' > "$TMP/sp1.md"
printf 'Introduction\nReaders agreed.\n' > "$TMP/sp2.md"
run sp sp1.md sp2.md >/dev/null
ck "with an ending heading: last counted line is 2"    2 "$(field sp "d['measured_span']['previous']['end_line']")"
ck "without one (trailing newline): last line is 2"    2 "$(field sp "d['measured_span']['revised']['end_line']")"
ck "start line is 1"                                   1 "$(field sp "d['measured_span']['previous']['start_line']")"
ck "the end marker is the section name"                references "$(field sp "d['measured_span']['previous']['end_marker']")"
printf 'Introduction\nReaders agreed.\n3. References\nSynthetic A. 2020.\n' > "$TMP/sp5.md"
run sp3 sp5.md sp2.md >/dev/null
ck "'3. References': the marker is the name, not the number" references "$(field sp3 "d['measured_span']['previous']['end_marker']")"
printf 'Title\n\nIntroduction\nReaders agreed.\n' > "$TMP/sp3.md"
printf 'References\nSynthetic A. 2020.\n' > "$TMP/sp4.md"
run sp2 sp3.md sp4.md >/dev/null
ck "the start line is the Introduction line, not the blank before it" 3 "$(field sp2 "d['measured_span']['previous']['start_line']")"
ck "a file that ends its body on line 1 counted no lines"  None "$(field sp2 "d['measured_span']['revised']['end_line']")"
ck "  and says so"                                      1 "$(grep -c "^measured revised: no lines" "$TMP/sp2.out")"

echo "----"
echo "test_density_body_bounds: $pass passed, $fail failed"
[ "$fail" -eq 0 ] || { for f in short long refs runin sp sp2 sp3; do echo "--- $f"; cat "$TMP/$f.out"; done; exit 1; }
