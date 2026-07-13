#!/usr/bin/env bash
# Regression test for skills/find-cohort-gap/scripts/build_cohort_profile.py — the
# local-codebook / document input layer (issue #69).
#
# The contract under test is as much about what the adapter REFUSES to do as what it
# extracts: variables are enumerated verbatim with provenance (never paraphrased or
# invented), a sample size that the codebook does not state stays [UNKNOWN], and a serial
# structure is only claimed when a measurement really does repeat.
set -u

REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
B="$REPO_ROOT/skills/find-cohort-gap/scripts/build_cohort_profile.py"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

pass=0
fail=0
ck() {
  local label="$1" expected="$2" actual="$3"
  if [ "$expected" = "$actual" ]; then
    printf '  PASS  %-54s exit=%s\n' "$label" "$actual"
    pass=$((pass + 1))
  else
    printf '  FAIL  %-54s expected=%s actual=%s\n' "$label" "$expected" "$actual"
    fail=$((fail + 1))
  fi
}

# --- a CODEBOOK (rows are variables, one column names them) ---
cat > "$TMP/codebook.csv" <<'CSV'
variable,description,type
subject_id,Study identifier,char
age,Age at baseline in years,num
sex,Biological sex,char
sbp_v1,Systolic blood pressure at visit 1,num
sbp_v2,Systolic blood pressure at visit 2,num
sbp_v3,Systolic blood pressure at visit 3,num
hba1c,Glycated haemoglobin,num
ct_lung_nodule,Lung nodule seen on chest CT,char
phq9_total,PHQ-9 depression score,num
statin_use,Statin prescription at baseline,char
death_date,Date of death from national registry,date
cvd_event,Incident cardiovascular event,char
weird_unmatchable_token,,char
CSV

# --- a DATA EXPORT (columns are the variables; no codebook column) ---
printf 'age,sex,ldl_chol,mri_brain,death_date\n45,M,130,normal,\n' > "$TMP/export.csv"

# --- a markdown codebook (pipe table AND bullet/backtick lines) ---
cat > "$TMP/codebook.md" <<'MD'
| variable | description |
|----------|-------------|
| waist_circumference | Waist circumference (cm) |

Additional variables:

- `alt` — Alanine aminotransferase
MD

# --- a JSON codebook ---
cat > "$TMP/codebook.json" <<'JSON'
{"egfr": "Estimated glomerular filtration rate", "cancer_incidence": "Incident cancer from registry"}
JSON

# 1) a codebook is read and every variable is enumerated
python3 "$B" --codebook "$TMP/codebook.csv" --cohort-name "Test registry" --out-dir "$TMP/o1" > /dev/null 2>&1
ck "codebook (rows = variables) is read" 0 "$?"

python3 - "$TMP/o1/cohort_profile.json" <<'PY'
import json, sys
p = json.load(open(sys.argv[1]))
names = [v["name"] for v in p["variables"]]
assert len(names) == 13, f"expected 13 variables, got {len(names)}: {names}"
# verbatim, not paraphrased
for must in ("sbp_v1", "ct_lung_nodule", "phq9_total", "weird_unmatchable_token"):
    assert must in names, f"{must} missing — variables must be copied verbatim"
# provenance points at the real row
src = {v["name"]: v["source"] for v in p["variables"]}
assert src["age"].endswith(":3"), f"bad provenance for age: {src['age']}"
PY
ck "variables verbatim + provenance (file:row)" 0 "$?"

# 2) clusters are assigned, and an unmatchable variable is NOT forced into a bucket
python3 - "$TMP/o1/cohort_profile.json" <<'PY'
import json, sys
p = json.load(open(sys.argv[1]))
c = {v["name"]: v["cluster"] for v in p["variables"]}
assert c["age"] == "demographics", c["age"]
assert c["hba1c"] == "laboratory", c["hba1c"]
assert c["ct_lung_nodule"] == "imaging", c["ct_lung_nodule"]
assert c["phq9_total"] == "questionnaire", c["phq9_total"]
assert c["statin_use"] == "medication", c["statin_use"]
assert c["weird_unmatchable_token"] == "unclassified", c["weird_unmatchable_token"]
# every assignment shows the keyword that caused it
assert all(v["matched_keyword"] for v in p["variables"] if v["cluster"] != "unclassified")
PY
ck "clusters assigned; unmatched stays 'unclassified'" 0 "$?"

# 2b) the abbreviation false positive: a short keyword must match a whole TOKEN, never a
# substring. `us` (ultrasound) inside `statin_use` once made a statin an imaging variable.
python3 - "$B" <<'PY'
import importlib.util, sys
spec = importlib.util.spec_from_file_location("bcp", sys.argv[1])
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
cases = [
    ("statin_use", "Statin prescription", "medication"),   # not imaging via "us"
    ("lipid_panel", "Lipid panel", "laboratory"),          # not identifier_admin via "id"
    ("ct_lung_nodule", "Chest CT nodule", "imaging"),      # token "ct" still works
    ("sbp_v1", "Systolic BP visit 1", "vital_signs"),
]
for name, desc, want in cases:
    got, kw = m.classify(name, desc)
    assert got == want, f"{name!r} -> {got} (via {kw!r}), expected {want}"
PY
ck "short keywords match whole tokens, not substrings" 0 "$?"

# 3) serial structure detected — the P1 evidence — and only when it really repeats
python3 - "$TMP/o1/cohort_profile.json" <<'PY'
import json, sys
p = json.load(open(sys.argv[1]))
sg = p["serial_groups"]
assert "sbp" in sg, f"sbp_v1/v2/v3 not detected as serial: {sg}"
assert sg["sbp"] == ["sbp_v1", "sbp_v2", "sbp_v3"], sg["sbp"]
# phq9_total ends in a digit but never repeats -> must NOT be claimed as serial
assert "phq" not in sg and "phq9_total" not in sg, f"false serial group: {sg}"
PY
ck "serial group found; a lone digit-suffixed var is not one" 0 "$?"

# 4) endpoints surfaced (P2 evidence)
python3 - "$TMP/o1/cohort_profile.json" <<'PY'
import json, sys
p = json.load(open(sys.argv[1]))
e = set(p["endpoint_candidates"])
assert {"death_date", "cvd_event"} <= e, e
assert "age" not in e
PY
ck "endpoint candidates surfaced (death, cvd event)" 0 "$?"

# 5) THE ANTI-HALLUCINATION CONTRACT: what a codebook cannot state stays UNKNOWN
python3 - "$TMP/o1/cohort_profile.json" "$TMP/o1/cohort_profile.md" <<'PY'
import json, re, sys
p = json.load(open(sys.argv[1]))
must = p["must_ask_user"]
for k in ("n_baseline", "enrollment_period", "followup_duration", "irb_status"):
    assert must[k] == "[UNKNOWN - ask the user]", f"{k} was invented: {must[k]!r}"
md = open(sys.argv[2]).read()
assert "ASK THE USER" in md.upper()
# no fabricated sample size anywhere in the rendered profile
assert not re.search(r"\bN\s*=\s*[\d,]+", md), "a sample size appeared from nowhere"
PY
ck "un-stated facts stay [UNKNOWN], never guessed" 0 "$?"

# 6) a DATA EXPORT (header row = variables) is routed correctly
python3 "$B" --codebook "$TMP/export.csv" --out-dir "$TMP/o2" > /dev/null 2>&1
python3 - "$TMP/o2/cohort_profile.json" <<'PY'
import json, sys
p = json.load(open(sys.argv[1]))
names = [v["name"] for v in p["variables"]]
assert names == ["age", "sex", "ldl_chol", "mri_brain", "death_date"], names
assert not any(v["name"] == "45" for v in p["variables"]), "read a data row as a variable"
PY
ck "data export (header = variables) routed correctly" 0 "$?"

# 7) markdown + json codebooks, and multiple codebooks merge without duplicates
python3 "$B" --codebook "$TMP/codebook.md" --codebook "$TMP/codebook.json" \
  --codebook "$TMP/codebook.csv" --out-dir "$TMP/o3" > /dev/null 2>&1
python3 - "$TMP/o3/cohort_profile.json" <<'PY'
import json, sys
p = json.load(open(sys.argv[1]))
names = [v["name"] for v in p["variables"]]
for must in ("waist_circumference", "alt", "egfr", "cancer_incidence", "sbp_v1"):
    assert must in names, f"{must} missing from merged profile"
assert len(names) == len(set(n.lower() for n in names)), "duplicate variables across codebooks"
PY
ck "markdown + json + csv codebooks merge, de-duplicated" 0 "$?"

# 8) a local document is attached as domain context (no URL needed)
cat > "$TMP/review.md" <<'MD'
# Narrative review: coronary calcium and mortality
Coronary artery calcium scoring predicts cardiovascular events across populations.
Repeated scanning and its incremental value remain debated.
MD
python3 "$B" --codebook "$TMP/codebook.csv" --context "$TMP/review.md" --out-dir "$TMP/o4" > /dev/null 2>&1
ck "local document accepted as domain context" 0 "$?"
grep -q "coronary calcium" "$TMP/o4/context_extract.md"
ck "context text extracted to context_extract.md" 0 "$?"

# 9) a missing file fails loudly rather than proceeding with an empty profile
python3 "$B" --codebook "$TMP/does_not_exist.csv" --out-dir "$TMP/o5" > /dev/null 2>&1
ck "missing codebook fails loudly" 1 "$?"

# 10) an unparseable codebook fails rather than emitting an empty profile
printf 'just some prose with no table and no variables at all\n' > "$TMP/prose.txt"
python3 "$B" --codebook "$TMP/prose.txt" --out-dir "$TMP/o6" > /dev/null 2>&1
ck "codebook with no variables fails (no empty profile)" 1 "$?"

echo "----"
echo "test_cohort_profile: $pass passed, $fail failed"
[ "$fail" -eq 0 ]
