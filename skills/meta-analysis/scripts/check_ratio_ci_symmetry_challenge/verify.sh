#!/usr/bin/env bash
# Deterministic verifier for the ratio-CI symmetry challenge card.
#   Positive: a transcription slip in one bound and an undeclared exact CI
#             (RATIO_CI_ASYMMETRIC, Minor), a lower bound above the estimate and a
#             negative bound (RATIO_CI_IMPOSSIBLE, Major) -> exit 1 under --strict.
#   Negative: Wald CIs (two decimals, three decimals at 90%, one decimal where
#             rounding alone looks asymmetric), declared exact/profile CIs and a
#             non-ratio row -> no claim, exit 0, derived SEs match R.
# No network. Exit 0 = every stage matches.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
DET="$HERE/../check_ratio_ci_symmetry.py"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

set +e
python3 "$DET" --extraction "$HERE/fixture/extraction_positive.csv" --strict \
  --out "$tmp/pos.json" > "$tmp/pos.out"
pos_rc=$?
set -e
if [ "$pos_rc" -ne 1 ]; then
  echo "FAIL: positive fixture must exit 1 under --strict; got $pos_rc" >&2
  cat "$tmp/pos.out" >&2
  exit 1
fi
python3 - "$tmp/pos.json" <<'PY'
import json, sys
r = json.load(open(sys.argv[1]))
assert r["detector"] == "check_ratio_ci_symmetry", r.get("detector")
got = [(c["study"], c["verdict"], c["severity"]) for c in r["claims"]]
want = [("Study A", "RATIO_CI_ASYMMETRIC", "Minor"),
        ("Study B", "RATIO_CI_ASYMMETRIC", "Minor"),
        ("Study C", "RATIO_CI_IMPOSSIBLE", "Major"),
        ("Study D", "RATIO_CI_IMPOSSIBLE", "Major")]
assert got == want, got
assert r["summary"]["verdict"] == "MAJOR_CANDIDATE", r["summary"]
PY
grep -q '^MAJOR candidate:' "$tmp/pos.out" || { echo "FAIL: positive final line" >&2; exit 1; }

set +e
python3 "$DET" --extraction "$HERE/fixture/extraction_negative.csv" --strict \
  --out "$tmp/neg.json" > "$tmp/neg.out"
neg_rc=$?
set -e
if [ "$neg_rc" -ne 0 ]; then
  echo "FAIL: negative fixture must exit 0; got $neg_rc" >&2
  cat "$tmp/neg.out" >&2
  exit 1
fi
python3 - "$tmp/neg.json" <<'PY'
import json, sys
r = json.load(open(sys.argv[1]))
assert r["claims"] == [], r["claims"]
assert r["summary"]["verdict"] == "OK", r["summary"]
rows = {x["study"]: x for x in r["rows"]}
# Expected SEs: R 4.3.3, se <- function(l,u,lev=0.95) (log(u)-log(l))/(2*qnorm(1-(1-lev)/2))
#   se(1.35,2.96) = 0.2002803832; se(0.42,0.82) = 0.170679062; se(0.679,0.943,0.90) = 0.09984023797
for study, want in (("Study A", 0.2002803832), ("Study B", 0.170679062),
                    ("Study C", 0.09984023797)):
    assert abs(rows[study]["se_log"] - want) < 1e-9, (study, rows[study]["se_log"])
assert rows["Study D"]["symmetry"] == "SKIPPED_DECLARED_METHOD", rows["Study D"]
assert rows["Study E"]["symmetry"] == "SKIPPED_DECLARED_METHOD", rows["Study E"]
assert rows["Study F"]["symmetry"] == "OK", rows["Study F"]
assert "Study G" not in rows and r["summary"]["n_skipped_measure"] == 1, r["summary"]
PY
grep -q '^OK:' "$tmp/neg.out" || { echo "FAIL: negative final line" >&2; exit 1; }

echo "PASS: positive flags 2 IMPOSSIBLE (Major) + 2 ASYMMETRIC (Minor), exit 1; negative is clean, exit 0, SEs match R."
