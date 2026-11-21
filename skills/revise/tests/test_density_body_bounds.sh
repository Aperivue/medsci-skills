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
field() { python3 -c "import json,sys; d=json.load(open(sys.argv[1])); print($2)" "$TMP/$1.json"; }
run() {  # run <name> <previous> <revised>
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

echo "----"
echo "test_density_body_bounds: $pass passed, $fail failed"
[ "$fail" -eq 0 ] || { for f in short long refs runin; do echo "--- $f"; cat "$TMP/$f.out"; done; exit 1; }
