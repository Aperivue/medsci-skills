#!/usr/bin/env bash
# Regression test for skills/analyze-stats/scripts/check_separation.py.
#
# The positive fixture is the real shape: a pathognomonic imaging sign (100% specific, 100%
# PPV) entered as a covariate. Its cross-tab against the outcome has an empty cell, so the
# logistic MLE does not exist — but glm still returns, with OR ~ 0, p ~ 0.99, and an AUC that
# would have been reported as a result. The gate must catch that from the DATA, before any
# model is fitted.
#
# The negatives matter just as much: a balanced predictor and an overlapping continuous one
# must stay silent, and an identifier column must be skipped rather than flagged.
set -u

REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
V="$REPO_ROOT/skills/analyze-stats/scripts/check_separation.py"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

pass=0
fail=0
ck() {
  local label="$1" expected="$2" actual="$3"
  if [ "$expected" = "$actual" ]; then
    printf '  PASS  %-56s exit=%s\n' "$label" "$actual"
    pass=$((pass + 1))
  else
    printf '  FAIL  %-56s expected=%s actual=%s\n' "$label" "$expected" "$actual"
    fail=$((fail + 1))
  fi
}

# --- the pathognomonic sign: mismatch=1 occurs ONLY in idh_mutant=1 (specificity 100%) ------
# sex is balanced; age overlaps; patient_id is an identifier.
python3 - "$TMP" <<'PY'
import csv, random
from pathlib import Path
rows = []
# 12 sign-positive, all mutant  -> the empty cell: (mismatch=1, idh=0) has n=0
for i in range(12):
    rows.append({"patient_id": f"P{i:03d}", "t2flair_mismatch": 1, "idh_mutant": 1,
                 "sex": i % 2, "age": 40 + (i % 20), "ki67": 10 + (i % 30)})
# 20 sign-negative mutant, 25 sign-negative wildtype
for i in range(12, 32):
    rows.append({"patient_id": f"P{i:03d}", "t2flair_mismatch": 0, "idh_mutant": 1,
                 "sex": i % 2, "age": 35 + (i % 25), "ki67": 5 + (i % 40)})
for i in range(32, 57):
    rows.append({"patient_id": f"P{i:03d}", "t2flair_mismatch": 0, "idh_mutant": 0,
                 "sex": i % 2, "age": 45 + (i % 25), "ki67": 8 + (i % 35)})
with (Path(sys.argv[1] if False else __import__("sys").argv[1]) / "sep.csv").open("w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0]))
    w.writeheader(); w.writerows(rows)

# quasi-separation: EVERY cell is non-empty, but one is tiny. rare_sign=1 occurs in 18
# wildtype cases and only 2 mutant ones -> (rare_sign=1, mutant) = 2, below the floor of 5.
# (An empty cell would be COMPLETE separation, which is a different verdict.)
q = [dict(r) for r in rows]
n_mut = n_wt = 0
for r in q:
    if r["idh_mutant"] == 1 and n_mut < 2:
        r["rare_sign"] = 1; n_mut += 1
    elif r["idh_mutant"] == 0 and n_wt < 18:
        r["rare_sign"] = 1; n_wt += 1
    else:
        r["rare_sign"] = 0
with (Path(__import__("sys").argv[1]) / "quasi.csv").open("w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(q[0]))
    w.writeheader(); w.writerows(q)

# continuous perfect separation: marker ranges do not overlap across the outcome
c = []
for i in range(30):
    c.append({"patient_id": f"C{i:03d}", "idh_mutant": 1, "marker": 10 + i * 0.5, "age": 40 + i % 20})
for i in range(30):
    c.append({"patient_id": f"D{i:03d}", "idh_mutant": 0, "marker": 40 + i * 0.5, "age": 45 + i % 20})
with (Path(__import__("sys").argv[1]) / "cont.csv").open("w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(c[0]))
    w.writeheader(); w.writerows(c)
PY

# 1) the pathognomonic sign is caught, before any model is fitted
python3 "$V" --data "$TMP/sep.csv" --outcome idh_mutant --predictor t2flair_mismatch --strict --quiet > /dev/null 2>&1
ck "pathognomonic sign fires COMPLETE_SEPARATION (--strict)" 1 "$?"

python3 "$V" --data "$TMP/sep.csv" --outcome idh_mutant --predictor t2flair_mismatch \
  --out "$TMP/s.json" --quiet > /dev/null 2>&1
python3 - "$TMP/s.json" <<'PY'
import json, sys
r = json.load(open(sys.argv[1]))
f = r["findings"]
assert len(f) == 1, [x["verdict"] for x in f]
assert f[0]["verdict"] == "COMPLETE_SEPARATION"
assert f[0]["cell"]["n"] == 0
assert r["model_safe"] is False
# the message must name BOTH remedies — the choice is a design decision
d = f[0]["detail"].lower()
assert "firth" in d, "Firth remedy not named"
assert "two-stage" in d, "two-stage remedy not named"
PY
ck "empty cell reported; both remedies named" 0 "$?"

# 2) a balanced predictor must stay silent — a gate that fires on everything is noise
python3 "$V" --data "$TMP/sep.csv" --outcome idh_mutant --predictor sex --strict --quiet > /dev/null 2>&1
ck "balanced binary predictor does not fire" 0 "$?"

# 3) an overlapping continuous predictor must stay silent
python3 "$V" --data "$TMP/sep.csv" --outcome idh_mutant --predictor age --strict --quiet > /dev/null 2>&1
ck "overlapping continuous predictor does not fire" 0 "$?"

# 4) a continuous predictor whose ranges do NOT overlap is the same failure
python3 "$V" --data "$TMP/cont.csv" --outcome idh_mutant --predictor marker --out "$TMP/c.json" --quiet > /dev/null 2>&1
python3 - "$TMP/c.json" <<'PY'
import json, sys
f = json.load(open(sys.argv[1]))["findings"]
assert len(f) == 1 and f[0]["verdict"] == "COMPLETE_SEPARATION", [x["verdict"] for x in f]
PY
ck "non-overlapping continuous predictor fires" 0 "$?"

# 5) a sparse (non-zero) cell is quasi-separation, not complete
python3 "$V" --data "$TMP/quasi.csv" --outcome idh_mutant --predictor rare_sign --out "$TMP/q.json" --quiet > /dev/null 2>&1
python3 - "$TMP/q.json" <<'PY'
import json, sys
r = json.load(open(sys.argv[1]))
v = {f["verdict"] for f in r["findings"]}
assert "QUASI_SEPARATION" in v, v
assert "COMPLETE_SEPARATION" not in v, "a sparse cell is not an empty one"
PY
ck "sparse cell is QUASI, not COMPLETE" 0 "$?"

# 6) --auto screens every column, and an identifier is skipped rather than flagged
python3 "$V" --data "$TMP/sep.csv" --outcome idh_mutant --auto --out "$TMP/a.json" --quiet > /dev/null 2>&1
python3 - "$TMP/a.json" <<'PY'
import json, sys
r = json.load(open(sys.argv[1]))
assert "t2flair_mismatch" in r["screened"]
assert any(s["predictor"] == "patient_id" for s in r["skipped"]), "identifier should be skipped"
assert not any(f["predictor"] == "patient_id" for f in r["findings"]), "identifier flagged as a predictor"
assert any(f["predictor"] == "t2flair_mismatch" for f in r["findings"])
PY
ck "--auto screens all; identifier skipped, not flagged" 0 "$?"

# 7) a non-binary outcome is a usage error, not a silent pass
python3 "$V" --data "$TMP/sep.csv" --outcome age --predictor sex --quiet > /dev/null 2>&1
ck "non-binary outcome fails loudly" 1 "$?"

# 8) the JSON envelope names the detector (repo-wide artifact contract)
python3 - "$TMP/s.json" <<'PY'
import json, sys
assert json.load(open(sys.argv[1]))["detector"] == "check_separation"
PY
ck "JSON envelope self-identifies" 0 "$?"

echo "----"
echo "test_separation: $pass passed, $fail failed"
[ "$fail" -eq 0 ]
