#!/usr/bin/env bash
# Regression test for the model-provenance gate (model-selection).
# Synthetic, PII-free JSON dossiers reproduce each verdict class. Stdlib-only (python3).
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$HERE/../scripts/check_model_provenance.py"
CH="$HERE/../scripts/check_model_provenance_challenge"
TMP="$(mktemp -d -t modprov_XXXX)"
OUT="$TMP/out.json"
trap 'rm -rf "$TMP"' EXIT

fail=0
check() { local label="$1"; shift
    if "$@" >/dev/null 2>&1; then printf '  PASS  %s\n' "$label"
    else printf '  FAIL  %s\n' "$label"; fail=$((fail+1)); fi
}
has_verdict() { python3 -c "
import json
d=json.load(open('$OUT'))
assert any(c['verdict']=='$1' for c in d['claims']), '$1 not found'
"; }
no_verdict() { python3 -c "
import json
d=json.load(open('$OUT'))
assert not any(c['verdict']=='$1' for c in d['claims']), '$1 unexpectedly present'
"; }

[[ -f "$SCRIPT" ]] || { echo "ENV-ERR: script missing" >&2; exit 2; }

# (1) contradictory facts
python3 "$SCRIPT" --dossier "$CH/fixture/dossier_defect.json" --out "$OUT" --strict --quiet >/dev/null 2>&1
check "exit 1 (contradictory dossier)" test "$?" -eq 1
for v in BENCHMARK_PROVENANCE_CONFLICT EVAL_DATA_IN_TRAINING LICENCE_INCOMPATIBLE \
         LICENCE_UNVERIFIED TASK_MISMATCH NO_VERSION_PIN VALIDATION_UNREPORTED HARDWARE_UNVERIFIED; do
  check "$v detected" has_verdict "$v"
done

# (2) absent facts -- a different failure mode
python3 "$SCRIPT" --dossier "$CH/fixture/dossier_unstated.json" --out "$OUT" --strict --quiet >/dev/null 2>&1
check "exit 1 (unstated dossier)" test "$?" -eq 1
check "LICENCE_UNSTATED detected" has_verdict LICENCE_UNSTATED
check "WEIGHTS_PROVENANCE_UNKNOWN detected" has_verdict WEIGHTS_PROVENANCE_UNKNOWN
check "an unstated licence does not also read as incompatible" no_verdict LICENCE_INCOMPATIBLE

# (3) fully stated dossier -> silent
python3 "$SCRIPT" --dossier "$CH/fixture/dossier_clean.json" --out "$OUT" --strict --quiet >/dev/null 2>&1
check "exit 0 (clean dossier)" test "$?" -eq 0
check "being developed on a benchmark you do NOT evaluate on is not a finding" \
      no_verdict BENCHMARK_PROVENANCE_CONFLICT
check "no LICENCE_UNVERIFIED once the licence file is recorded" no_verdict LICENCE_UNVERIFIED
check "no HARDWARE_UNVERIFIED once the claim has been executed" no_verdict HARDWARE_UNVERIFIED

# (4) dataset names are matched as token sequences, never as substrings
mk() { python3 - "$1" "$2" "$3" <<'PY'
import json, sys
out, dev, arm = sys.argv[1], sys.argv[2], sys.argv[3]
json.dump({"model": "m", "source": {"commit": "c"},
           "licence": {"spdx": "Apache-2.0", "verified_from": "LICENSE"},
           "intended_use": "research", "weights": {"pretrained": False},
           "task": {"model": "t", "study": "t"},
           "reported_validation": [{"dataset": "x", "metric": "Dice", "source": "s"}],
           "developed_on": [dev],
           "evaluation_arms": [{"name": "a", "dataset": arm}],
           "hardware": {}}, open(out, "w"))
PY
}
mk "$TMP/d.json" "MSD" "MSD Task09 Spleen"
python3 "$SCRIPT" --dossier "$TMP/d.json" --out "$OUT" --quiet >/dev/null 2>&1
check "'MSD Task09 Spleen' matches the family 'MSD'" has_verdict BENCHMARK_PROVENANCE_CONFLICT

mk "$TMP/d.json" "Medical Segmentation Decathlon" "MSD Task09 Spleen"
python3 "$SCRIPT" --dossier "$TMP/d.json" --out "$OUT" --quiet >/dev/null 2>&1
check "the spelled-out family name resolves to the same corpus" has_verdict BENCHMARK_PROVENANCE_CONFLICT

mk "$TMP/d.json" "MSD" "MS Cohort 2026"
python3 "$SCRIPT" --dossier "$TMP/d.json" --out "$OUT" --quiet >/dev/null 2>&1
check "'MS Cohort 2026' does NOT match 'MSD' (no substring matching)" \
      no_verdict BENCHMARK_PROVENANCE_CONFLICT

mk "$TMP/d.json" "MSD" "AMOS22"
python3 "$SCRIPT" --dossier "$TMP/d.json" --out "$OUT" --quiet >/dev/null 2>&1
check "an unrelated external cohort does not match" no_verdict BENCHMARK_PROVENANCE_CONFLICT

# (5) a non-commercial licence is only a conflict under a restricted intended use
python3 - "$TMP/nc.json" <<'PY'
import json, sys
json.dump({"model": "m", "source": {"commit": "c"},
           "licence": {"spdx": "CC-BY-NC-4.0", "verified_from": "LICENSE"},
           "intended_use": "research", "weights": {"pretrained": False},
           "task": {"model": "t", "study": "t"},
           "reported_validation": [{"dataset": "x", "metric": "Dice", "source": "s"}],
           "developed_on": [], "evaluation_arms": [{"name": "a", "dataset": "z"}],
           "hardware": {}}, open(sys.argv[1], "w"))
PY
python3 "$SCRIPT" --dossier "$TMP/nc.json" --out "$OUT" --quiet >/dev/null 2>&1
check "a non-commercial licence under research use is not a conflict" no_verdict LICENCE_INCOMPATIBLE

# (6) aliases resolve inside suffixed family names (F1)
mk "$TMP/d.json" "MSD" "Medical Segmentation Decathlon Task03 Liver"
python3 "$SCRIPT" --dossier "$TMP/d.json" --out "$OUT" --quiet >/dev/null 2>&1
check "spelled-out family + task suffix matches 'MSD'" has_verdict BENCHMARK_PROVENANCE_CONFLICT
mk "$TMP/d.json" "Medical Segmentation Decathlon" "Medical Segmentation Decathlon Task03 Liver"
python3 "$SCRIPT" --dossier "$TMP/d.json" --out "$OUT" --quiet >/dev/null 2>&1
check "suffixed spelled-out family matches the bare spelled-out family" has_verdict BENCHMARK_PROVENANCE_CONFLICT
mk "$TMP/d.json" "MSD" "Decathlon Task03 Liver"
python3 "$SCRIPT" --dossier "$TMP/d.json" --out "$OUT" --quiet >/dev/null 2>&1
check "'Decathlon Task03 Liver' matches 'MSD'" has_verdict BENCHMARK_PROVENANCE_CONFLICT
mk "$TMP/d.json" "Medical Segmentation Decathlon" "Medical Imaging Cohort 2026"
python3 "$SCRIPT" --dossier "$TMP/d.json" --out "$OUT" --quiet >/dev/null 2>&1
check "control: an unrelated name opening with 'Medical' does not match" no_verdict BENCHMARK_PROVENANCE_CONFLICT

# variant builder: a clean base dossier, then a Python statement edits the dict d
mkv() { python3 - "$1" "$2" <<'PY'
import json, sys
d = {"model": "m", "source": {"commit": "c"},
     "licence": {"spdx": "Apache-2.0", "verified_from": "LICENSE"},
     "intended_use": "research", "weights": {"pretrained": False},
     "task": {"model": "t", "study": "t"},
     "reported_validation": [{"dataset": "x", "metric": "Dice", "source": "s"}],
     "developed_on": ["ExampleBench"],
     "evaluation_arms": [{"name": "a", "dataset": "OtherCohort"}],
     "hardware": {}}
exec(sys.argv[2])
json.dump(d, open(sys.argv[1], "w"))
PY
}
run() { rm -f "$OUT"; python3 "$SCRIPT" --dossier "$TMP/v.json" --out "$OUT" --strict --quiet >/dev/null 2>&1; }

mkv "$TMP/v.json" 'pass'
run; check "control: base variant dossier exits 0 under --strict" test "$?" -eq 0

# (7) a string where a list belongs is an input error, not a silent clearance (F2)
mkv "$TMP/v.json" 'd["developed_on"]="ExampleBench"; d["evaluation_arms"]=[{"name":"a","dataset":"ExampleBench Task03"}]'
run; check "developed_on as a bare string -> exit 2" test "$?" -eq 2
mkv "$TMP/v.json" 'd["weights"]={"pretrained":True,"trained_on":"ExampleBench"}; d["evaluation_arms"]=[{"name":"a","dataset":"ExampleBench"}]'
run; check "weights.trained_on as a bare string -> exit 2" test "$?" -eq 2
mkv "$TMP/v.json" 'd["weights"]={"pretrained":True,"trained_on":["ExampleBench"]}; d["evaluation_arms"]=[{"name":"a","dataset":"ExampleBench"}]'
run; check "control: trained_on as a list still fires EVAL_DATA_IN_TRAINING" has_verdict EVAL_DATA_IN_TRAINING

# (8) an absent key is a finding; an explicit empty list is a statement (F3)
mkv "$TMP/v.json" 'del d["developed_on"]'
run; check "absent developed_on -> exit 1 under --strict" test "$?" -eq 1
check "absent developed_on -> DEVELOPED_ON_UNSTATED" has_verdict DEVELOPED_ON_UNSTATED
mkv "$TMP/v.json" 'del d["evaluation_arms"]'
run; check "absent evaluation_arms -> exit 1 under --strict" test "$?" -eq 1
check "absent evaluation_arms -> EVALUATION_ARMS_UNSTATED" has_verdict EVALUATION_ARMS_UNSTATED
mkv "$TMP/v.json" 'del d["intended_use"]; d["licence"]["spdx"]="CC-BY-NC-4.0"'
run; check "absent intended_use -> exit 1 under --strict" test "$?" -eq 1
check "absent intended_use -> INTENDED_USE_UNSTATED" has_verdict INTENDED_USE_UNSTATED
mkv "$TMP/v.json" 'd["developed_on"]=[]; d["evaluation_arms"]=[]'
run; check "control: explicit empty lists exit 0" test "$?" -eq 0
check "control: explicit empty developed_on is not DEVELOPED_ON_UNSTATED" no_verdict DEVELOPED_ON_UNSTATED

# (9) intended_use and licence spellings are token-normalised (F4)
for use in "clinical deployment" "Clinical-Deployment" "Commercial"; do
  mkv "$TMP/v.json" "d['licence']['spdx']='CC-BY-NC-4.0'; d['intended_use']='$use'"
  run; check "NC licence + '$use' -> LICENCE_INCOMPATIBLE" has_verdict LICENCE_INCOMPATIBLE
done
for lic in "CC BY NC 4.0" "Non Commercial Research License"; do
  mkv "$TMP/v.json" "d['licence']['spdx']='$lic'; d['intended_use']='commercial'"
  run; check "'$lic' + commercial -> LICENCE_INCOMPATIBLE" has_verdict LICENCE_INCOMPATIBLE
done
for use in "clinical" "Commercial product"; do
  mkv "$TMP/v.json" "d['licence']['spdx']='CC-BY-NC-4.0'; d['intended_use']='$use'"
  run; check "unrecognised intended_use '$use' -> exit 2" test "$?" -eq 2
done
mkv "$TMP/v.json" 'd["licence"]["spdx"]="CC BY NC 4.0"; d["intended_use"]="Research"'
run; check "control: spaced NC licence under research use exits 0" test "$?" -eq 0
mkv "$TMP/v.json" 'd["licence"]["spdx"]="Apache 2.0"; d["intended_use"]="clinical deployment"'
run; check "control: permissive licence under clinical deployment exits 0" test "$?" -eq 0
check "control: permissive licence under clinical deployment is not incompatible" no_verdict LICENCE_INCOMPATIBLE

# (10) the shipped challenge card reproduces
check "challenge verify.sh passes" bash "$CH/verify.sh"

echo
if [[ "$fail" -eq 0 ]]; then echo "ALL PASS (model-provenance gate)"; else echo "$fail FAILURE(S)"; exit 1; fi
