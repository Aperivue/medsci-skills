#!/usr/bin/env bash
# Regression test for screening_reconcile.py STAGE_TRANSFER_LOSS.
#
# The positive fixture reproduces the defect this check exists to stop: a record that
# passed title/abstract screening, was never entered into the consensus stage, and is
# absent from Table 1. Before the check existed, that record flowed into `qualitative`
# and then into `narrative_only` -- where it is indistinguishable from a study that is
# legitimately narrative-only -- and the script exited 0.
#
# The negative fixture is the case that must NOT fire: a genuine narrative-only study
# (adjudicated at consensus as an include, simply lacking extractable 2x2 data). A
# diagnostic-accuracy review normally has one or two of these, so a check that flags
# them is useless.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RECONCILE="${SCRIPT_DIR}/../scripts/screening_reconcile.py"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

fail() { echo "FAIL: $*" >&2; exit 1; }

# ---------------------------------------------------------------- positive
# id 99: include at screening, absent from consensus entirely, absent from Table 1.
printf 'id\tdecision\n1\tinclude\n2\tinclude\n99\tinclude\n3\texclude\n' > "$TMP/screening.tsv"
printf 'id\tdecision\n1\tinclude\n2\tinclude\n3\texclude\n'             > "$TMP/consensus.tsv"
printf 'id\n1\n2\n'                                                     > "$TMP/table1.csv"

set +e
python3 "$RECONCILE" --screening "$TMP/screening.tsv" --consensus "$TMP/consensus.tsv" \
  --table1 "$TMP/table1.csv" --output "$TMP/pos.json" > /dev/null
rc=$?
set -e
[ "$rc" -eq 1 ] || fail "positive fixture: expected exit 1, got $rc"

python3 - "$TMP/pos.json" <<'PY' || fail "positive fixture: STAGE_TRANSFER_LOSS not reported for id 99"
import json, sys
d = json.load(open(sys.argv[1]))
codes = {i["code"] for i in d["blocking_issues"]}
assert "STAGE_TRANSFER_LOSS" in codes, codes
ids = [i["ids"] for i in d["blocking_issues"] if i["code"] == "STAGE_TRANSFER_LOSS"][0]
assert ids == ["1", "2", "99"][2:], ids
assert d["totals"]["k_stage_transfer_loss"] == 1
assert d["sets"]["narrative_only_unadjudicated"] == ["99"]
assert d["sets"]["narrative_only_adjudicated"] == []
PY

# ---------------------------------------------------------------- negative
# id 7: adjudicated as an include at consensus, but has no extractable 2x2 -> it is
# legitimately narrative-only. Must not fire.
printf 'id\tdecision\n1\tinclude\n2\tinclude\n7\tinclude\n3\texclude\n' > "$TMP/screening_n.tsv"
printf 'id\tdecision\n1\tinclude\n2\tinclude\n7\tinclude\n3\texclude\n' > "$TMP/consensus_n.tsv"
printf 'id\n1\n2\n'                                                     > "$TMP/table1_n.csv"

set +e
python3 "$RECONCILE" --screening "$TMP/screening_n.tsv" --consensus "$TMP/consensus_n.tsv" \
  --table1 "$TMP/table1_n.csv" --output "$TMP/neg.json" > /dev/null
rc=$?
set -e
[ "$rc" -eq 0 ] || fail "negative fixture: expected exit 0, got $rc (false positive)"

python3 - "$TMP/neg.json" <<'PY' || fail "negative fixture: genuine narrative-only misclassified"
import json, sys
d = json.load(open(sys.argv[1]))
assert d["blocking_issues"] == [], d["blocking_issues"]
assert d["totals"]["k_stage_transfer_loss"] == 0
assert d["sets"]["narrative_only"] == ["7"]
assert d["sets"]["narrative_only_adjudicated"] == ["7"]
assert d["sets"]["narrative_only_unadjudicated"] == []
PY

# ------------------------------------------------- negative: no consensus supplied
# With no consensus artifact there is nothing to reconcile against; the check must
# stay silent rather than flag every screened include.
set +e
python3 "$RECONCILE" --screening "$TMP/screening.tsv" --output "$TMP/noc.json" > /dev/null
rc=$?
set -e
[ "$rc" -eq 0 ] || fail "no-consensus fixture: expected exit 0, got $rc"
python3 - "$TMP/noc.json" <<'PY' || fail "no-consensus fixture: fired without a consensus artifact"
import json, sys
d = json.load(open(sys.argv[1]))
assert d["totals"]["k_stage_transfer_loss"] == 0
assert d["blocking_issues"] == []
PY

# ------------------------------------- positive: free-text exclusion labels (F1)
# Labels such as "Exclude: wrong study type" or "ineligible" contain the substrings
# "y", "1" and "eligible". A substring classifier read them as INCLUDE, so excluded
# records 3 and 4 landed in `qualitative` and the run exited 0. Labels are now
# matched as exact tokens (whole label, or its leading word).
printf 'id\tdecision\n1\tInclude\n2\tincluded\n3\tExclude: wrong study type\n4\tineligible\n' > "$TMP/s_lab.tsv"
printf 'id\tdecision\n1\tINCLUDE\n2\tinclude\n3\tEXCLUDE (E1)\n4\tExcluded - not eligible\n'   > "$TMP/c_lab.tsv"
set +e
python3 "$RECONCILE" --screening "$TMP/s_lab.tsv" --consensus "$TMP/c_lab.tsv" \
  --output "$TMP/lab.json" > /dev/null
rc=$?
set -e
[ "$rc" -eq 0 ] || fail "free-text labels: expected exit 0, got $rc"
python3 - "$TMP/lab.json" <<'PY' || fail "free-text labels: excluded records counted as included"
import json, sys
d = json.load(open(sys.argv[1]))
assert d["sets"]["screening_include"] == ["1", "2"], d["sets"]["screening_include"]
assert d["sets"]["consensus_exclude"] == ["3", "4"], d["sets"]["consensus_exclude"]
assert d["sets"]["qualitative"] == ["1", "2"], d["sets"]["qualitative"]
PY

# ---------------------------------- positive: unrecognized label must not pass (F1)
# "maybe" is neither include nor exclude. It used to be read as include (it
# contains "y"); it must now stop the run (exit 2) and name the label.
printf 'id\tdecision\n1\tinclude\n2\tmaybe\n' > "$TMP/s_unk.tsv"
set +e
python3 "$RECONCILE" --screening "$TMP/s_unk.tsv" --output "$TMP/unk.json" > /dev/null 2> "$TMP/unk.err"
rc=$?
set -e
[ "$rc" -eq 2 ] || fail "unrecognized label: expected exit 2, got $rc"
grep -q "maybe" "$TMP/unk.err" || fail "unrecognized label: error does not name the label"

# --------------------------------- positive: IDs sharing a number run (F2)
# Smith2020_1 and Smith2020_2 both reduced to "2020" under first-number-run
# normalization, so Smith2020_2 -- included at screening, absent from consensus --
# was hidden and the run exited 0. IDs are now compared verbatim.
printf 'id\tdecision\nSmith2020_1\tinclude\nSmith2020_2\tinclude\n' > "$TMP/s_id.tsv"
printf 'id\tdecision\nSmith2020_1\tinclude\n'                       > "$TMP/c_id.tsv"
set +e
python3 "$RECONCILE" --screening "$TMP/s_id.tsv" --consensus "$TMP/c_id.tsv" \
  --output "$TMP/id.json" > /dev/null
rc=$?
set -e
[ "$rc" -eq 1 ] || fail "shared-number IDs: expected exit 1 (STAGE_TRANSFER_LOSS), got $rc"
python3 - "$TMP/id.json" <<'PY' || fail "shared-number IDs: Smith2020_2 loss not reported"
import json, sys
d = json.load(open(sys.argv[1]))
assert d["sets"]["stage_transfer_loss"] == ["Smith2020_2"], d["sets"]["stage_transfer_loss"]
PY

# ------------------------------------ negative: distinct string IDs, all adjudicated
printf 'id\tdecision\nSmith2020_1\tinclude\nSmith2020_2\tinclude\nLee2019\texclude\n'        > "$TMP/s_idn.tsv"
printf 'id\tdecision\nSmith2020_1\tinclude\n Smith2020_2 \tinclude\nLee2019\tExclude: E2\n' > "$TMP/c_idn.tsv"
set +e
python3 "$RECONCILE" --screening "$TMP/s_idn.tsv" --consensus "$TMP/c_idn.tsv" \
  --output "$TMP/idn.json" > /dev/null
rc=$?
set -e
[ "$rc" -eq 0 ] || fail "string IDs negative: expected exit 0, got $rc (false positive)"
python3 - "$TMP/idn.json" <<'PY' || fail "string IDs negative: IDs merged or lost"
import json, sys
d = json.load(open(sys.argv[1]))
assert d["blocking_issues"] == [], d["blocking_issues"]
assert sorted(d["sets"]["qualitative"]) == ["Smith2020_1", "Smith2020_2"], d["sets"]["qualitative"]
PY

# ------------------- positive: unadjudicated labels must not read as exclude (R2)
# The leading-word rule once accepted any EXCLUDE value as a leading word, so a
# consensus label "No decision yet" (leading word "no") or "N/A" (leading "n")
# moved a screened include into consensus_exclude: the study dropped out of
# qualitative and the run exited 0. yes/no/y/n/1/0 now count only as the whole
# label; each of these must stop the run (exit 2) and name the label.
for lab in "No decision yet" "No consensus" "N/A" "N/A - full text pending" "0 - pending" "Yes (pending)" "Y/N"; do
  printf 'id\tdecision\n1\tinclude\n2\tinclude\n' > "$TMP/s_pend.tsv"
  printf 'id\tdecision\n1\tinclude\n2\t%s\n' "$lab" > "$TMP/c_pend.tsv"
  set +e
  python3 "$RECONCILE" --screening "$TMP/s_pend.tsv" --consensus "$TMP/c_pend.tsv" \
    --output "$TMP/pend.json" > /dev/null 2> "$TMP/pend.err"
  rc=$?
  set -e
  [ "$rc" -eq 2 ] || fail "unadjudicated label '$lab': expected exit 2, got $rc"
  grep -qF "$lab" "$TMP/pend.err" || fail "unadjudicated label '$lab': error does not name it"
done

# ------------------------- negative: bare whole-label y/n/1/0/yes/no still work
printf 'id\tdecision\n1\tY\n2\t1\n3\tyes\n4\tn\n5\t0\n6\tNo\n' > "$TMP/s_bare.tsv"
printf 'id\tdecision\n1\ty\n2\tTRUE\n3\tno\n'                    > "$TMP/c_bare.tsv"
set +e
python3 "$RECONCILE" --screening "$TMP/s_bare.tsv" --consensus "$TMP/c_bare.tsv" \
  --output "$TMP/bare.json" > /dev/null
rc=$?
set -e
[ "$rc" -eq 0 ] || fail "bare labels negative: expected exit 0, got $rc (false positive)"
python3 - "$TMP/bare.json" <<'PY' || fail "bare labels negative: misclassified"
import json, sys
d = json.load(open(sys.argv[1]))
assert d["sets"]["screening_include"] == ["1", "2", "3"], d["sets"]
assert d["sets"]["consensus_exclude"] == ["3"], d["sets"]
assert d["sets"]["qualitative"] == ["1", "2"], d["sets"]
assert d["blocking_issues"] == [], d["blocking_issues"]
PY

# ------------- negative: 0/1 decision column written as floats ("1.0"/"0.0")
# pandas / Excel write an integer column holding blanks as floats. Main read
# these correctly; exact-token matching must not turn them into exit 2.
printf 'id\tdecision\n1\t1.0\n2\t1.0\n3\t0.0\n' > "$TMP/s_flt.tsv"
printf 'id\tdecision\n1\t1.0\n2\t0.0\n'         > "$TMP/c_flt.tsv"
set +e
python3 "$RECONCILE" --screening "$TMP/s_flt.tsv" --consensus "$TMP/c_flt.tsv" \
  --output "$TMP/flt.json" > /dev/null
rc=$?
set -e
[ "$rc" -eq 0 ] || fail "float labels negative: expected exit 0, got $rc"
python3 - "$TMP/flt.json" <<'PY' || fail "float labels negative: misclassified"
import json, sys
d = json.load(open(sys.argv[1]))
assert d["sets"]["screening_include"] == ["1", "2"], d["sets"]
assert d["sets"]["consensus_exclude"] == ["2"], d["sets"]
assert d["sets"]["qualitative"] == ["1"], d["sets"]
PY

# ------- negative: Table 1 labels studies "Study 1", screening uses "1"
# Main matched these through the first digit run; verbatim IDs must not turn
# them into TABLE1_NOT_IN_QUALITATIVE. The digit-run match is recorded.
printf 'id\tdecision\n1\tinclude\n2\tinclude\n3\texclude\n' > "$TMP/s_t1.tsv"
printf 'id\tdecision\n1\tinclude\n2\tinclude\n3\texclude\n' > "$TMP/c_t1.tsv"
printf 'study_id\nStudy 1\nStudy 2\n'                        > "$TMP/t1.csv"
set +e
python3 "$RECONCILE" --screening "$TMP/s_t1.tsv" --consensus "$TMP/c_t1.tsv" \
  --table1 "$TMP/t1.csv" --output "$TMP/t1.json" > /dev/null
rc=$?
set -e
[ "$rc" -eq 0 ] || fail "Table 1 'Study N' negative: expected exit 0, got $rc"
python3 - "$TMP/t1.json" <<'PY' || fail "Table 1 'Study N' negative: not matched"
import json, sys
d = json.load(open(sys.argv[1]))
assert d["blocking_issues"] == [], d["blocking_issues"]
assert d["sets"]["narrative_only"] == [], d["sets"]
assert d["table1_matched_by_digit_run"] == {"Study 1": "1", "Study 2": "2"}, d
PY

# ------- positive: a Table 1 study that is not in the qualitative set
printf 'study_id\nStudy 1\nStudy 3\n' > "$TMP/t1p.csv"
set +e
python3 "$RECONCILE" --screening "$TMP/s_t1.tsv" --consensus "$TMP/c_t1.tsv" \
  --table1 "$TMP/t1p.csv" --output "$TMP/t1p.json" > /dev/null
rc=$?
set -e
[ "$rc" -eq 1 ] || fail "Table 1 excluded study: expected exit 1, got $rc"
python3 - "$TMP/t1p.json" <<'PY' || fail "Table 1 excluded study: not reported"
import json, sys
d = json.load(open(sys.argv[1]))
codes = {i["code"]: i["ids"] for i in d["blocking_issues"]}
assert codes.get("TABLE1_NOT_IN_QUALITATIVE") == ["Study 3"], codes
PY


# ------- positive: an excluded sibling report must not reach Table 1 through
# the digit-run fallback. Smith2020_2 was excluded, Smith2020_1 is included;
# Table 1 lists Smith2020_2. Main exits 1 TABLE1_NOT_IN_QUALITATIVE here.
printf 'id\tdecision\nSmith2020_1\tinclude\nSmith2020_2\texclude\nJones2019\tinclude\n' > "$TMP/s_sib.tsv"
printf 'study_id\nSmith2020_2\nJones2019\n' > "$TMP/t1_sib.csv"
set +e
python3 "$RECONCILE" --screening "$TMP/s_sib.tsv" \
  --table1 "$TMP/t1_sib.csv" --output "$TMP/sib.json" > /dev/null
rc=$?
set -e
[ "$rc" -eq 1 ] || fail "Table 1 excluded sibling: expected exit 1, got $rc"
python3 - "$TMP/sib.json" <<'PY' || fail "Table 1 excluded sibling: not reported"
import json, sys
d = json.load(open(sys.argv[1]))
codes = {i["code"]: i["ids"] for i in d["blocking_issues"]}
assert codes.get("TABLE1_NOT_IN_QUALITATIVE") == ["Smith2020_2"], codes
assert d["table1_matched_by_digit_run"] == {}, d
PY

# ------- positive: same, but Table 1 writes the excluded sibling in another
# style ("Smith 2020 (2)") whose first digit run is shared by both siblings.
printf 'study_id\nSmith 2020 (2)\nJones2019\n' > "$TMP/t1_sib2.csv"
set +e
python3 "$RECONCILE" --screening "$TMP/s_sib.tsv" \
  --table1 "$TMP/t1_sib2.csv" --output "$TMP/sib2.json" > /dev/null
rc=$?
set -e
[ "$rc" -eq 1 ] || fail "Table 1 ambiguous sibling: expected exit 1, got $rc"

echo "PASS: test_screening_reconcile.sh (positive + 3 negatives; F1 labels x2, F2 IDs + negative, R2 unadjudicated labels x7, float labels, Table 1 digit-run match + positive, excluded sibling x2)"
