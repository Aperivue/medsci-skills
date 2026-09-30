#!/usr/bin/env bash
# Regression test for the model-provenance gate (model-sourcing).
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

# (6) the shipped challenge card reproduces
check "challenge verify.sh passes" bash "$CH/verify.sh"

echo
if [[ "$fail" -eq 0 ]]; then echo "ALL PASS (model-provenance gate)"; else echo "$fail FAILURE(S)"; exit 1; fi
