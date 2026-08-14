#!/usr/bin/env bash
# Deterministic verifier for the DOI-belongs-to-this-record challenge card. Network-free: the
# fixture ships recorded Crossref responses and the detector reads them with --cache.
#
# Six rows, one per way this goes wrong or is falsely accused:
#
#   R-001 the DOI is right                       SILENT
#   R-002 the DOI belongs to another study       DOI_NOT_THIS_RECORD   <- the false "missed paper"
#   R-003 the DOI is a whole abstract supplement DOI_IS_CONTAINER      <- the paper that isn't there
#   R-004 the DOI does not resolve               DOI_UNRESOLVED        <- reported, not dropped
#   R-005 no DOI at all                          SILENT   (nothing to check is not a finding)
#   R-006 same paper, JATS markup + en dash      SILENT   <- the one that would kill this check
#
# R-006 is the load-bearing negative. Crossref returns titles with <i> tags, typographic dashes and
# its own capitalisation; a comparison that does not normalise those calls EVERY row a mismatch,
# and a check that flags everything is switched off within a day.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
DET="$HERE/../check_doi_record_match.py"
FIX="$HERE/fixture"

fail=0
pass() { echo "PASS  $1"; }
bad()  { echo "FAIL  $1"; fail=1; }

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

out="$(python3 "$DET" --table "$FIX/screening.tsv" --cache "$FIX/cache" || true)"

want_verdict() {  # record, verdict, description
  if grep -qE "\[$2\] \($1\)" <<<"$out"; then
    pass "$3"
  else
    bad "$3"
    echo "$out"
  fi
}

want_verdict R-002 DOI_NOT_THIS_RECORD "a DOI belonging to another study is caught"
want_verdict R-003 DOI_IS_CONTAINER    "a DOI resolving to a whole supplement is caught"
want_verdict R-004 DOI_UNRESOLVED      "an unresolvable DOI is reported, not dropped"

for r in R-001 R-005 R-006; do
  if grep -q "($r)" <<<"$out"; then
    bad "$r was flagged and should not have been"
    echo "$out"
  else
    case "$r" in
      R-001) pass "a correct DOI is silent" ;;
      R-005) pass "a row with no DOI is not a finding (there is nothing to check)" ;;
      R-006) pass "JATS markup, an en dash and different capitalisation are the SAME title" ;;
    esac
  fi
done

# The mismatch has to be readable, or nobody can adjudicate it: both titles, and the measured
# similarity that decided it.
if grep -q "resolved title:" <<<"$out" && grep -qE "similarity 0\.[0-9]{2} <" <<<"$out"; then
  pass "...and the mismatch prints both titles and the similarity that decided it"
else
  bad "the mismatch report is not adjudicable"
  echo "$out"
fi

# A cache with no recorded response is UNRESOLVED, never a silent live lookup: a run that is half
# recorded and half network is reproducible in neither direction.
mkdir -p "$WORK/empty"
n_unresolved="$(python3 "$DET" --table "$FIX/screening.tsv" --cache "$WORK/empty" \
                | grep -c '\[DOI_UNRESOLVED\]' || true)"
if [ "$n_unresolved" -eq 5 ]; then
  pass "an empty cache turns all 5 DOIs into UNRESOLVED and never reaches the network"
else
  bad "an empty cache produced $n_unresolved UNRESOLVED, expected 5"
  python3 "$DET" --table "$FIX/screening.tsv" --cache "$WORK/empty" | head -20
fi

# Missing columns must stop the run. Reading a table whose doi column is called something else and
# reporting "0 findings" is the failure mode this whole card exists to prevent, one level up.
set +e
python3 "$DET" --table "$FIX/screening.tsv" --cache "$FIX/cache" --doi-col identifier \
  >/dev/null 2>"$WORK/err"; rc=$?
set -e
if [ "$rc" -eq 2 ] && grep -q "identifier" "$WORK/err"; then
  pass "a wrong --doi-col name exits 2 and names it (not a hollow 'no findings')"
else
  bad "exit was $rc for a column that does not exist"
  cat "$WORK/err"
fi

if python3 "$DET" --table "$FIX/screening.tsv" --cache "$FIX/cache" --strict >/dev/null 2>&1; then
  bad "--strict returned 0 on a table with a wrong DOI"
else
  pass "--strict exits non-zero, so a screening pipeline can gate on it"
fi

python3 "$DET" --table "$FIX/screening.tsv" --cache "$FIX/cache" --json "$WORK/o.json" >/dev/null
python3 - "$WORK/o.json" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
assert d["detector"] == "check_doi_record_match", d.get("detector")
assert d["source"] == "cache", d.get("source")
assert d["rows_with_doi"] == 5, d.get("rows_with_doi")
assert d["findings"] and all(f["detector"] == "check_doi_record_match" for f in d["findings"])
PY
pass "qc JSON self-identifies and records that it read a cache, not the network"

[ "$fail" -eq 0 ] || exit 1
echo "----"
echo "DOI-record-match challenge: all checks passed"
