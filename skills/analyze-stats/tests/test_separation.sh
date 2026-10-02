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

# --- false-clearance regressions (F1: tied-boundary continuous; F2: joint separation) -------
python3 - "$TMP" <<'PY'
import csv, random, sys
from pathlib import Path
out = Path(sys.argv[1])
def write(name, rows):
    with (out / name).open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)
# F1 positive: the two outcome ranges meet ONLY at the tied value 3 (two y=0 and one y=1 there).
# Quasi-complete separation: glm returns a slope of ~180 with SE ~ 7e4 and p = 1.
x0 = [1, 2, 3, 3, 2.5, 1.5, 2.2, 1.1, 2.9, 0.5, 0.7, 1.9]
x1 = [3, 4, 5, 3.5, 4.4, 6, 7, 5.5, 4.1, 8, 9, 3.3]
write("tie.csv", [{"y": 0, "x": v} for v in x0] + [{"y": 1, "x": v} for v in x1])
# F1 negative: same data, but one y=1 case moved inside the y=0 range -> genuine overlap.
write("tie_overlap.csv", [{"y": 0, "x": v} for v in x0] + [{"y": 1, "x": v} for v in [2.0] + x1[1:]])
# F2 positive: y = 1[x1 > x2]. Each predictor overlaps fully on its own; together they
# classify every case, and glm returns coefficients of +/-400 with p ~ 0.98.
rng = random.Random(7)
ms = []
for _ in range(200):
    a, b = round(rng.uniform(0, 10), 2), round(rng.uniform(0, 10), 2)
    if a == b:
        b += 0.01
    ms.append({"y": int(a > b), "x1": a, "x2": b, "grp": rng.choice("ABC")})
write("multi.csv", ms)
# F2 positive, quasi-complete and mixed types: the score threshold is 50 when sign = 0 and
# 60 when sign = 1, and the two boundary points (0, 50) and (1, 60) carry BOTH outcomes.
# Each sign level has both outcomes and plenty of each; the score ranges overlap across
# 50-60. Only the combination score - 10*sign splits the outcome, with ties on the boundary.
mq = []
for sign, cut in ((0, 50), (1, 60)):
    for score in range(30, 81, 2):
        if score != cut:
            mq.append({"y": int(score > cut), "sign": sign, "score": score})
    mq += [{"y": 0, "sign": sign, "score": cut}, {"y": 1, "sign": sign, "score": cut}]
write("multi_quasi.csv", mq)
# F2 negative: y depends on x1 - x2 but with noise -> overlap, a finite MLE exists.
mn = []
for r in ms:
    mn.append({"y": int(r["x1"] - r["x2"] + rng.gauss(0, 3) > 0), "x1": r["x1"], "x2": r["x2"],
               "grp": r["grp"]})
write("multi_noisy.csv", mn)
PY

# 9) F1 positive: ranges that touch only at a tied boundary value are quasi-complete separation
python3 "$V" --data "$TMP/tie.csv" --outcome y --predictor x --out "$TMP/t.json" --strict --quiet > /dev/null 2>&1
ck "tied-boundary continuous predictor fires (--strict)" 1 "$?"
python3 - "$TMP/t.json" <<'PY'
import json, sys
r = json.load(open(sys.argv[1]))
f = r["findings"]
assert len(f) == 1 and f[0]["verdict"] == "QUASI_SEPARATION", [x["verdict"] for x in f]
assert "does not exist" in f[0]["detail"] and r["model_safe"] is False
PY
ck "tied boundary reported as QUASI_SEPARATION, MLE absent" 0 "$?"

# 10) F1 negative: a genuine overlap must stay silent
python3 "$V" --data "$TMP/tie_overlap.csv" --outcome y --predictor x --strict --quiet > /dev/null 2>&1
ck "genuinely overlapping continuous predictor does not fire" 0 "$?"

# 11) F2 positive: y = 1[x1 > x2] passes each predictor alone, fails jointly
python3 "$V" --data "$TMP/multi.csv" --outcome y --predictor x1 --predictor x2 --out "$TMP/m.json" --strict --quiet > /dev/null 2>&1
ck "joint (linear-combination) separation fires (--strict)" 1 "$?"
python3 - "$TMP/m.json" <<'PY'
import json, sys
r = json.load(open(sys.argv[1]))
f = r["findings"]
assert len(f) == 1 and f[0]["verdict"] == "COMPLETE_SEPARATION", [x["verdict"] for x in f]
assert f[0]["cell"]["joint"] == ["x1", "x2"], f[0]["cell"]
assert r["joint_check"]["status"] == "separated" and r["model_safe"] is False
PY
ck "joint separation is COMPLETE and names x1, x2" 0 "$?"
python3 "$V" --data "$TMP/multi.csv" --outcome y --predictor x1 --strict --quiet > /dev/null 2>&1
ck "each of those predictors alone does not fire" 0 "$?"

# 12) F2 positive, quasi-complete, categorical x continuous
python3 "$V" --data "$TMP/multi_quasi.csv" --outcome y --predictor sign --predictor score --out "$TMP/mq.json" --strict --quiet > /dev/null 2>&1
ck "joint quasi-complete separation (sign + score) fires" 1 "$?"
python3 - "$TMP/mq.json" <<'PY'
import json, sys
r = json.load(open(sys.argv[1]))
f = r["findings"]
assert [x["verdict"] for x in f] == ["QUASI_SEPARATION"], [x["verdict"] for x in f]
assert f[0]["cell"]["joint"] == ["score", "sign"] and f[0]["cell"]["n_tied"] == 4, f[0]["cell"]
assert r["joint_check"]["status"] == "separated"
PY
ck "joint quasi finding is QUASI, names both, 4 ties" 0 "$?"

# 13) F2 negative: noisy y = 1[x1 - x2 + e > 0] overlaps jointly -> clean, and certified
python3 "$V" --data "$TMP/multi_noisy.csv" --outcome y --predictor x1 --predictor x2 --predictor grp --out "$TMP/mn.json" --strict --quiet > /dev/null 2>&1
ck "jointly overlapping predictors do not fire" 0 "$?"
python3 - "$TMP/mn.json" <<'PY'
import json, sys
r = json.load(open(sys.argv[1]))
assert r["findings"] == [] and r["joint_check"]["status"] == "clear" and r["model_safe"] is True, r["joint_check"]
PY
ck "joint check ran and cleared; model_safe" 0 "$?"

# 14) without scipy the joint check cannot run: the report must say so and not certify the model
python3 - "$V" "$TMP/multi.csv" <<'PY' > "$TMP/noscipy.txt" 2>&1
import runpy, sys
sys.modules["scipy"] = None; sys.modules["scipy.optimize"] = None
v, data = sys.argv[1], sys.argv[2]
sys.argv = [v, "--data", data, "--outcome", "y", "--predictor", "x1", "--predictor", "x2",
            "--out", data + ".json"]
try:
    runpy.run_path(v, run_name="__main__")
except SystemExit as e:
    assert not e.code, e.code
import json
r = json.load(open(data + ".json"))
assert r["joint_check"]["status"] == "not_run" and r["model_safe"] is False, r["joint_check"]
PY
rc=$?
if [ "$rc" -eq 0 ] && grep -q "NOT checked" "$TMP/noscipy.txt" && ! grep -q "MLE exists" "$TMP/noscipy.txt"; then rc=0; else rc=1; fi
ck "no scipy: joint check reported NOT run, model not certified" 0 "$rc"

echo "----"
echo "test_separation: $pass passed, $fail failed"
[ "$fail" -eq 0 ]
