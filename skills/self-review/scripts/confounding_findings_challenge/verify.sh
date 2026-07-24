#!/usr/bin/env bash
# Deterministic verifier for the confounding-completeness findings-contract challenge.
#
# `findings` is the DEFECT list. It used to be the whole per-covariate audit table, and two of
# that table's three verdicts mean "this is fine": ADJUSTED says the covariate WAS handled,
# and EXPOSURE_DEFINING_EXEMPT records a deliberate exemption (adjusting for a component of
# the exposure's own diagnostic criteria is over-adjustment, probe O7).
#
# Nothing was wrong with the analysis. What was wrong is that every consumer aggregating a
# project's qc/ directory counts entries in `findings`, so a run reporting "four covariates
# examined, none of them a problem" arrived as FOUR FINDINGS. In one real project three such
# runs contributed ~45 pseudo-findings — enough to make this the loudest detector in the
# suite and to put a 0.00 precision row into the ledger built on top of it. The measurement
# that was supposed to grade the detectors was being corrupted by one detector's envelope.
#
# So: the full table is still emitted, as `covariates`, and the human-readable render walks
# that. `findings` carries only UNADJUSTED_IMBALANCED, each with a severity and a message —
# the two fields it never had, and the reason its entries showed up blank in every report.
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
DET="$HERE/../check_confounding_completeness.py"
FIX="$HERE/fixture"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT

pass=0; fail=0
ck() { if [ "$2" = "$3" ]; then printf '  PASS  %-56s got=%s\n' "$1" "$3"; pass=$((pass+1));
       else printf '  FAIL  %-56s want=%s got=%s\n' "$1" "$2" "$3"; fail=$((fail+1)); fi; }
jq_() { python3 -c "import json,sys; d=json.load(open(sys.argv[1])); print(eval(sys.argv[2]))" "$1" "$2"; }

run() { python3 "$DET" --table1 "$1" --adjusted "$FIX/adjusted.txt" \
          --exposure-defining "$FIX/defining.txt" --out "$2" 2>&1; }

echo "== a genuine defect: one finding, carrying the fields it must carry =="
OUT="$(run "$FIX/table1.csv" "$TMP/defect.json")"
ck "the audit table still holds every imbalanced covariate" 5 "$(jq_ "$TMP/defect.json" "len(d['covariates'])")"
ck "but findings holds only the defect"                     1 "$(jq_ "$TMP/defect.json" "len(d['findings'])")"
ck "the finding is UNADJUSTED_IMBALANCED"      "UNADJUSTED_IMBALANCED" "$(jq_ "$TMP/defect.json" "d['findings'][0]['verdict']")"
ck "it carries a severity"                                  "major" "$(jq_ "$TMP/defect.json" "d['findings'][0]['severity']")"
ck "and a non-empty message"                                True "$(jq_ "$TMP/defect.json" "len(d['findings'][0].get('message','')) > 40")"
ck "the covariate is named in it"                           True "$(jq_ "$TMP/defect.json" "'Prior cardiovascular disease' in d['findings'][0]['message']")"

echo "== THE REGRESSION: a status row must never reach findings =="
ck "no ADJUSTED in findings"        0 "$(jq_ "$TMP/defect.json" "sum(1 for f in d['findings'] if f['verdict']=='ADJUSTED')")"
ck "no EXEMPT in findings"          0 "$(jq_ "$TMP/defect.json" "sum(1 for f in d['findings'] if f['verdict']=='EXPOSURE_DEFINING_EXEMPT')")"
# NB: no braces in these expressions — the shell brace-expands them into separate words.
ck "though both ARE in the audit table" True "$(jq_ "$TMP/defect.json" "set(c['verdict'] for c in d['covariates']) >= set(['ADJUSTED','EXPOSURE_DEFINING_EXEMPT'])")"

echo "== a run with nothing wrong reports nothing wrong =="
grep -v "Prior cardiovascular" "$FIX/table1.csv" > "$TMP/clean.csv"
run "$TMP/clean.csv" "$TMP/clean.json" >/dev/null 2>&1
ck "four covariates examined"       4 "$(jq_ "$TMP/clean.json" "len(d['covariates'])")"
ck "ZERO findings (it reported 4 before)" 0 "$(jq_ "$TMP/clean.json" "len(d['findings'])")"

echo "== the human-readable table is unchanged: it walks covariates =="
OUT="$(run "$FIX/table1.csv" "$TMP/x.json")"
ck "adjusted rows still rendered"   True "$(python3 -c "print('Age (years)' in '''$OUT''')")"
ck "exempt rows still rendered"     True "$(python3 -c "print('exposure-defining' in '''$OUT''')")"

echo "== counts and exit codes are unchanged =="
ck "n_imbalanced counts the whole table"      5 "$(jq_ "$TMP/defect.json" "d['n_imbalanced']")"
ck "n_unadjusted_imbalanced"                  1 "$(jq_ "$TMP/defect.json" "d['n_unadjusted_imbalanced']")"
ck "n_exposure_defining_exempt"               2 "$(jq_ "$TMP/defect.json" "d['n_exposure_defining_exempt']")"
python3 "$DET" --table1 "$FIX/table1.csv" --adjusted "$FIX/adjusted.txt" \
  --exposure-defining "$FIX/defining.txt" --strict >/dev/null 2>&1
ck "--strict still fails on a real defect" 1 "$?"
python3 "$DET" --table1 "$TMP/clean.csv" --adjusted "$FIX/adjusted.txt" \
  --exposure-defining "$FIX/defining.txt" --strict >/dev/null 2>&1
ck "--strict still passes when there is none" 0 "$?"

echo "== the artifact names its own author =="
ck "qc JSON carries the detector key" True "$(jq_ "$TMP/defect.json" "d.get('detector')=='check_confounding_completeness'")"

echo
printf 'confounding findings-contract challenge: %d passed, %d failed\n' "$pass" "$fail"
[ "$fail" -eq 0 ] || exit 1
