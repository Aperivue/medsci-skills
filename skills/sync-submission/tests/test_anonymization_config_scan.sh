#!/usr/bin/env bash
# Regression test: a figure builder's CONFIG is as much a figure source as its script.
#
# `check_asset_anonymization` scanned `.r` and `.py` under `figures/`. But `/make-figures` documents
# its STROBE builder as `build_strobe_template.py --config figures/figure1_strobe.yaml`, and the
# first box of a STROBE flow diagram is exactly where "Patients screened at <Hospital>" lives. So
# the identical institution string blocked in one file and passed in the other:
#
#   figures/figure1_strobe.py    ->  FAIL: institution-like token in figure script
#   figures/figure1_strobe.yaml  ->  PASS: no anonymization leak   ({'figure_scripts': 0})
#
# For a double-blind submission that is an anonymity leak which the anonymisation gate declared
# clean — and the `figure_scripts: 0` in that PASS line is the tell: a gate reporting success over
# an empty input set looks exactly like a gate that passed.
set -u

REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
A="$REPO_ROOT/skills/sync-submission/scripts/check_asset_anonymization.py"
WORK="$(mktemp -d -t anon_config_test.XXXXXX)"
trap 'rm -rf "$WORK"' EXIT

pass=0
fail=0
ck() {
  local label="$1" expected="$2" actual="$3"
  if [ "$expected" = "$actual" ]; then
    printf '  PASS  %-52s %s\n' "$label" "$actual"
    pass=$((pass + 1))
  else
    printf '  FAIL  %-52s expected=%s actual=%s\n' "$label" "$expected" "$actual"
    fail=$((fail + 1))
  fi
}

LEAK='Patients screened at Seoul National University Hospital (n = 4,102)'

run_on() {  # run_on <relative path> <content> -> exit code; output at $WORK/out
  local rel="$1" content="$2" d="$WORK/p$RANDOM"
  mkdir -p "$d/$(dirname "$rel")"
  printf '%s\n' "$content" > "$d/$rel"
  python3 "$A" --dir "$d" --strict > "$WORK/out" 2>&1
  local rc=$?
  cp "$WORK/out" "$WORK/last.out"
  echo $rc
}

echo "==== a config under figures/ is scanned, whatever its format ===="
ck "figures/*.yaml with an institution"  1 \
   "$(run_on figures/f1.yaml "spine:
  - {text: \"$LEAK\"}")"
ck "  and the file is named" yes \
   "$(grep -q 'figures/f1.yaml' "$WORK/last.out" && echo yes || echo no)"
ck "figures/*.yml with an institution"   1 "$(run_on figures/f1.yml "text: \"$LEAK\"")"
ck "figures/*.json with an institution"  1 "$(run_on figures/panel.json "{\"title\": \"$LEAK\"}")"

echo "==== the path that already worked must keep working ===="
ck "figures/*.py with an institution"    1 "$(run_on figures/f1.py "title = \"$LEAK\"")"
ck "figures/*.R with an institution"     1 "$(run_on figures/f1.R "title <- \"$LEAK\"")"

echo "==== NEGATIVE CONTROLS ===="
ck "a clean config passes"               0 \
   "$(run_on figures/clean.yaml "spine:
  - {text: \"Analytic cohort (n = 3,655)\"}")"
# The counter is the difference between "looked and found nothing" and "looked at nothing".
ck "  and the run reports it scanned it" yes \
   "$(grep -q "'figure_scripts': 1" "$WORK/last.out" && echo yes || echo no)"
# Scope is still figures/: a config elsewhere in the tree is not a figure source.
ck "same leak outside figures/ is not scanned" 0 \
   "$(run_on config/app.yaml "site: \"$LEAK\"")"

echo
echo "  passed=$pass failed=$fail"
[ "$fail" -eq 0 ] || { echo "--- last run ---"; cat "$WORK/last.out"; exit 1; }
echo "OK: the config that draws the figure is scanned like the script that draws it."
