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

echo "PASS: test_screening_reconcile.sh (positive + 2 negatives)"
