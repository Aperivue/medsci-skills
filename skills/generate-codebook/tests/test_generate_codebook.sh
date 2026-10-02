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

# Regression fixture (GC-1, GC-2): coded columns main cleared, integer years
# main turned into epoch-nanosecond "dates", plus negative controls.
python3 - "$TMP" <<'PY'
import sys, numpy as np, pandas as pd
out = sys.argv[1]
rng = np.random.default_rng(7); n = 200
words = ["alpha", "bravo", "charlie", "delta", "echo", "foxtrot", "golf", "hotel",
         "india", "juliet", "kilo", "lima", "mike", "november", "oscar", "papa",
         "quebec", "romeo", "sierra", "tango", "uniform", "victor", "whiskey",
         "xray", "yankee", "zulu", "amber", "cobalt", "indigo", "maroon"]
pd.DataFrame({
    "grade_mixed": rng.choice(["1", "2", "3", "Unknown"], n),         # GC-1 POS: codes + one label
    "site_code": [f"S{(i % 29) + 1:02d}" for i in range(n)],           # GC-1 POS: 29 bare codes -> text
    "year_dx": rng.integers(1990, 2021, n),                            # GC-2 POS: int years
    "smoking_status": rng.choice(["never", "former", "current"], n),  # NEG: labels only
    "free_label": [words[i % 30] for i in range(n)],                   # NEG: 30 readable labels -> text
    "visit_date": (pd.to_datetime("2023-01-01")
                   + pd.to_timedelta(rng.integers(0, 365, n), unit="D")).strftime("%Y-%m-%d"),  # NEG: still a date
    "bmi": rng.normal(25, 3, n).round(1),                              # NEG: continuous
    # NEG: numeric measurements exported as strings because of a sentinel
    "age_str": [str(x) for x in rng.integers(20, 90, n - 5)] + ["unk"] * 5,
    "creat_str": [str(x) for x in rng.integers(40, 200, n - 5)] + ["<40"] * 5,
    "lab_nd": [str(x) for x in rng.normal(5, 1, n - 5).round(2)] + ["ND"] * 5,
}).to_csv(f"{out}/data2.csv", index=False)
PY

python3 "$SCRIPT" "$TMP/data2.csv" --out-dir "$TMP/out2" >/dev/null 2>&1

while IFS=$'\t' read -r status label; do
    [[ -z "$label" ]] && continue
    assert "$label" "$([[ "$status" == "PASS" ]] && echo 1 || echo 0)"
done < <(python3 - "$TMP/out2/codebook.json" <<'PY'
import json, sys
cb = json.load(open(sys.argv[1]))
col = {c["name"]: c for c in cb["columns"]}
y = col["year_dx"]
checks = {
    "GC-1 needs_dict: grade_mixed (1/2/3/Unknown) flagged": col["grade_mixed"]["needs_dictionary"] is True,
    "GC-1 needs_dict: site_code (S01..S29, text) flagged": col["site_code"]["role"] == "text" and col["site_code"]["needs_dictionary"] is True,
    "GC-1 control: smoking_status NOT flagged": col["smoking_status"]["needs_dictionary"] is False,
    "GC-1 control: free_label (30 labels, text) NOT flagged": col["free_label"]["role"] == "text" and col["free_label"]["needs_dictionary"] is False,
    "GC-2 role: year_dx (int) is not a date": y["role"] != "date",
    "GC-2 stats: year_dx range is the integer years": y.get("stats", {}).get("min") == 1990.0 and y.get("stats", {}).get("max") == 2020.0,
    "GC-2 control: string visit_date still a date": col["visit_date"]["role"] == "date",
    "GC-2 control: bmi NOT flagged": col["bmi"]["needs_dictionary"] is False,
    "text control: age_str ('45'..'unk') NOT flagged": col["age_str"]["role"] == "text" and col["age_str"]["needs_dictionary"] is False,
    "text control: creat_str ('88'..'<40') NOT flagged": col["creat_str"]["role"] == "text" and col["creat_str"]["needs_dictionary"] is False,
    "text control: lab_nd ('4.87'..'ND') NOT flagged": col["lab_nd"]["role"] == "text" and col["lab_nd"]["needs_dictionary"] is False,
    "count: needs_dictionary_count==2 (fixture 2)": cb["needs_dictionary_count"] == 2,
}
for k, v in checks.items():
    print(("PASS" if v else "FAIL") + "\t" + k)
PY
)

printf '\n%d/%d checks passed\n' "$((ran-fail))" "$ran"
[[ "$fail" -eq 0 ]] || exit 1
