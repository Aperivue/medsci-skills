#!/usr/bin/env bash
# Regression tests for generate-codebook/scripts/generate_codebook.py.
# Self-contained: builds a synthetic dataset (no committed data) and asserts
# role inference, the needs_dictionary flag, and the no-hallucination invariant.

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
SCRIPT="$REPO_ROOT/skills/generate-codebook/scripts/generate_codebook.py"
TMP="$(mktemp -d -t codebook.XXXXXX)"
trap 'rm -rf "$TMP"' EXIT

[[ -f "$SCRIPT" ]] || { echo "ENV-ERR: script missing" >&2; exit 2; }
python3 -c "import pandas, numpy" 2>/dev/null || { echo "SKIP: pandas/numpy not installed"; exit 0; }

# Build a realistic synthetic dataset (seeded, no real data).
python3 - "$TMP" <<'PY'
import sys, numpy as np, pandas as pd
out = sys.argv[1]
rng = np.random.default_rng(42); n = 200
pd.DataFrame({
    "patient_id": np.arange(10001, 10001+n),
    "age": rng.integers(30, 85, n),
    "sex": rng.integers(1, 3, n),                       # coded -> needs_dictionary
    "fatty_liver_grade": rng.integers(0, 5, n),         # coded -> needs_dictionary
    "bmi": rng.normal(25, 3, n).round(1),               # continuous
    "visit_date": pd.to_datetime("2023-01-01") + pd.to_timedelta(rng.integers(0,365,n), unit="D"),
    "smoking_status": rng.choice(["never","former","current"], n),  # labelled -> NOT needs_dictionary
}).to_csv(f"{out}/data.csv", index=False)
PY

python3 "$SCRIPT" "$TMP/data.csv" --out-dir "$TMP/out" >/dev/null 2>&1

fail=0; ran=0
assert() {
    local label="$1" cond="$2"
    ran=$((ran+1))
    if [[ "$cond" == "1" ]]; then printf '  PASS  %s\n' "$label"
    else printf '  FAIL  %s\n' "$label"; fail=$((fail+1)); fi
}

# Outputs exist.
assert "codebook.json written" "$([[ -f "$TMP/out/codebook.json" ]] && echo 1 || echo 0)"
assert "codebook.md written"   "$([[ -f "$TMP/out/codebook.md" ]] && echo 1 || echo 0)"

# Role inference + needs_dictionary + no-hallucination, asserted from JSON.
while IFS=$'\t' read -r status label; do
    [[ -z "$label" ]] && continue
    assert "$label" "$([[ "$status" == "PASS" ]] && echo 1 || echo 0)"
done < <(python3 - "$TMP/out/codebook.json" <<'PY'
import json, sys
cb = json.load(open(sys.argv[1]))
col = {c["name"]: c for c in cb["columns"]}
checks = {
    "role: patient_id=id": col["patient_id"]["role"] == "id",
    "role: age=continuous": col["age"]["role"] == "continuous",
    "role: bmi=continuous": col["bmi"]["role"] == "continuous",
    "role: sex=binary": col["sex"]["role"] == "binary",
    "role: fatty_liver_grade=categorical": col["fatty_liver_grade"]["role"] == "categorical",
    "role: visit_date=date": col["visit_date"]["role"] == "date",
    "role: smoking_status=categorical": col["smoking_status"]["role"] == "categorical",
    "needs_dict: sex flagged": col["sex"]["needs_dictionary"] is True,
    "needs_dict: fatty_liver_grade flagged": col["fatty_liver_grade"]["needs_dictionary"] is True,
    "needs_dict: smoking_status NOT flagged": col["smoking_status"]["needs_dictionary"] is False,
    "needs_dict: bmi NOT flagged": col["bmi"]["needs_dictionary"] is False,
    "no-hallucination: labels null": all(c["label"] is None for c in cb["columns"]),
    "no-hallucination: units null": all(c["units"] is None for c in cb["columns"]),
    "count: needs_dictionary_count==2": cb["needs_dictionary_count"] == 2,
}
for k, v in checks.items():
    print(("PASS" if v else "FAIL") + "\t" + k)
PY
)

printf '\n%d/%d checks passed\n' "$((ran-fail))" "$ran"
[[ "$fail" -eq 0 ]] || exit 1
