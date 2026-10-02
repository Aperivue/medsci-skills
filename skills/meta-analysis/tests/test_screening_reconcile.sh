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

echo "PASS: test_screening_reconcile.sh (positive + 2 negatives; F1 labels x2, F2 IDs + negative)"
