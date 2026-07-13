#!/usr/bin/env bash
# Regression test for skills/peer-review/scripts/check_self_improvement_claims.py.
#
# The negatives carry most of the weight here. Self-refinement is not a defect — a paper that
# self-refines AND validates against human experts or held-out labels has named its signal, and
# the rest is a reviewer's judgment, not a deterministic finding. The gate must fire only when
# the claim is explicit AND no external signal appears anywhere in the text.
set -u

REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
V="$REPO_ROOT/skills/peer-review/scripts/check_self_improvement_claims.py"
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

# --- POSITIVE: an ungrounded loop, judged by the model being judged --------------------------
cat > "$TMP/bad.md" <<'MD'
## Methods
We built our diagnostic agent on GPT-4o. The agent performs iterative self-critique: after each
draft report it critiques its own output and revises, for five rounds of self-refinement.

To measure quality we used GPT-4o as a judge, which scored each report on a 1-5 rubric. Reports
were scored by the judge before and after the refinement loop.

## Results
Mean rubric score improved from 3.1 to 4.2 across the self-improvement loop.
MD

# --- POSITIVE: self-training on synthetic data, no real-data mixing --------------------------
cat > "$TMP/selfdata.md" <<'MD'
## Methods
We generated 40,000 synthetic cases with Llama-3 and used them to fine-tune the classifier.
The model was trained for three epochs on the model-generated data.

## Results
Accuracy on the internal split rose from 0.81 to 0.88.
MD

# --- NEGATIVE: self-refinement, but the judge is validated against human experts -------------
cat > "$TMP/grounded.md" <<'MD'
## Methods
Our agent, built on GPT-4o, performs iterative self-refinement of its draft report.

The LLM-as-judge (GPT-4o) was validated against three board-certified radiologists on a held-out
set of 200 reports; agreement with the expert consensus was substantial. All final reports were
additionally scored against the reference standard from chart review.

## Results
Accuracy against the ground truth improved from 0.72 to 0.79.
MD

# --- NEGATIVE: an ordinary paper with no self-improvement claim at all -----------------------
cat > "$TMP/plain.md" <<'MD'
## Methods
We trained a ResNet-50 on 12,000 chest radiographs and evaluated it on a held-out test set
labelled by two thoracic radiologists.

## Results
AUC was 0.91 (95% CI 0.88-0.94).
MD

# --- NEGATIVE: self-training WITH real-data mixing disclosed ---------------------------------
cat > "$TMP/mixed.md" <<'MD'
## Methods
We generated synthetic cases with Llama-3 and fine-tuned the classifier on a corpus mixed with
the original training data; the real-data fraction was held at 60% in every round. Rare classes
were checked against the held-out labelled set after each round.
MD

# 1) ungrounded loop + same-model judge -> both majors, halts under --strict
python3 "$V" --manuscript "$TMP/bad.md" --strict --quiet > /dev/null 2>&1
ck "ungrounded self-loop + same-model judge halts (--strict)" 1 "$?"

python3 "$V" --manuscript "$TMP/bad.md" --out "$TMP/bad.json" --quiet > /dev/null 2>&1
python3 - "$TMP/bad.json" <<'PY'
import json, sys
r = json.load(open(sys.argv[1]))
v = {f["verdict"] for f in r["findings"]}
assert "UNGROUNDED_SELF_LOOP" in v, v
assert "SELF_CONFIRMING_EVALUATOR" in v, v
assert r["self_improvement_claimed"] is True
assert r["external_signal_named"] is False
# the self-confirming finding must name the shared family, not just assert it
sc = next(f for f in r["findings"] if f["verdict"] == "SELF_CONFIRMING_EVALUATOR")
assert any("gpt" in s for s in sc["evidence"]["shared_family"]), sc["evidence"]
PY
ck "both majors fire; shared model family is named" 0 "$?"

# 2) THE FALSE-POSITIVE GUARD: self-refinement WITH a validated judge must not fire
python3 "$V" --manuscript "$TMP/grounded.md" --strict --quiet > /dev/null 2>&1
ck "self-refinement + expert-validated judge does not fire" 0 "$?"

# 3) a paper with no self-improvement claim must not fire
python3 "$V" --manuscript "$TMP/plain.md" --strict --quiet > /dev/null 2>&1
ck "ordinary supervised paper does not fire" 0 "$?"

# 4) self-training on generated data with no real-data mixing -> minor (collapse risk)
python3 "$V" --manuscript "$TMP/selfdata.md" --out "$TMP/sd.json" --quiet > /dev/null 2>&1
python3 - "$TMP/sd.json" <<'PY'
import json, sys
r = json.load(open(sys.argv[1]))
f = [x for x in r["findings"] if x["verdict"] == "SELF_TRAINING_NO_REAL_DATA"]
assert f, [x["verdict"] for x in r["findings"]]
assert f[0]["severity"] == "minor"
PY
ck "self-training without real-data mixing -> minor" 0 "$?"

# 5) ...and disclosing the real-data fraction clears it
python3 "$V" --manuscript "$TMP/mixed.md" --out "$TMP/mx.json" --quiet > /dev/null 2>&1
python3 - "$TMP/mx.json" <<'PY'
import json, sys
r = json.load(open(sys.argv[1]))
assert not any(f["verdict"] == "SELF_TRAINING_NO_REAL_DATA" for f in r["findings"]), r["findings"]
PY
ck "disclosed real-data mixing clears the collapse flag" 0 "$?"

# 6) a major is reported but tolerated without --strict
python3 "$V" --manuscript "$TMP/bad.md" --quiet > /dev/null 2>&1
ck "major tolerated without --strict" 0 "$?"

# 7) the JSON envelope names the detector (repo-wide artifact contract)
python3 - "$TMP/bad.json" <<'PY'
import json, sys
assert json.load(open(sys.argv[1]))["detector"] == "check_self_improvement_claims"
PY
ck "JSON envelope self-identifies" 0 "$?"

echo "----"
echo "test_self_improvement_claims: $pass passed, $fail failed"
[ "$fail" -eq 0 ]
