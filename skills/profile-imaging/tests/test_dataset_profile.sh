#!/usr/bin/env bash
# Regression test for the dataset-profile gate (profile-imaging).
# Synthetic, PII-free JSON profiles reproduce each verdict class. Stdlib-only (python3).
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$HERE/../scripts/check_dataset_profile.py"
CH="$HERE/../scripts/check_dataset_profile_challenge"
TMP="$(mktemp -d -t dsprof_XXXX)"
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

# (1) defect fixture -> every verdict class + exit 1
python3 "$SCRIPT" --profile "$CH/fixture/profile_defect.json" --out "$OUT" --strict --quiet >/dev/null 2>&1
check "exit 1 (defect profile)" test "$?" -eq 1
for v in LABEL_SHAPE_MISMATCH LABEL_EMPTY LABEL_VALUE_UNEXPECTED TEST_SET_UNLABELLED \
         ACCURACY_UNDER_IMBALANCE LABEL_MISSING SPACING_HETEROGENEOUS ORIENTATION_MIXED \
         INTENSITY_SCALE_INCONSISTENT EXTREME_IMBALANCE; do
  check "$v detected" has_verdict "$v"
done

# (2) clean fixture -> exit 0, nothing fires
python3 "$SCRIPT" --profile "$CH/fixture/profile_clean.json" --out "$OUT" --strict --quiet >/dev/null 2>&1
check "exit 0 (clean profile)" test "$?" -eq 0
check "no SPACING_HETEROGENEOUS when resampling declared" no_verdict SPACING_HETEROGENEOUS
check "no ORIENTATION_MIXED when reorientation declared" no_verdict ORIENTATION_MIXED
check "no EXTREME_IMBALANCE when a Dice-family loss is declared" no_verdict EXTREME_IMBALANCE
check "no ACCURACY_UNDER_IMBALANCE when accuracy is not reported" no_verdict ACCURACY_UNDER_IMBALANCE
check "no TEST_SET_UNLABELLED when the held-out split is labelled" no_verdict TEST_SET_UNLABELLED

# (3) thresholds are honoured — a permissive ratio silences the spacing flag
python3 "$SCRIPT" --profile "$CH/fixture/profile_defect.json" --spacing-ratio 99 --out "$OUT" --quiet >/dev/null 2>&1
check "spacing flag silenced by --spacing-ratio 99" no_verdict SPACING_HETEROGENEOUS

# (4) a multi-structure atlas used for a single-structure study.
# foreground_fraction pools every annotated organ, so the imbalance verdicts read the
# union rather than the target -- and the union is always the larger number, so it is the
# one that clears the threshold. The gate has to say the target was never named.
write_atlas() {  # $1=out path  $2=target_label ("none" to omit)  $3=foreground fraction
  python3 - "$1" "$2" "$3" <<'PY'
import json, sys
out, target, frac = sys.argv[1], sys.argv[2], float(sys.argv[3])
p = {"dataset": "multi-organ atlas",
     "declared_labels": {"0": "background", "1": "spleen", "2": "liver", "3": "pancreas"},
     "plan": {"resample": True, "reorient": True, "loss": "cross_entropy",
              "metrics": ["dice", "hd95"]},
     "splits": [{"name": "external_ct", "labelled": True}],
     "cases": [{"case": "c%d" % i, "split": "external_ct", "shape": [512, 512, 100],
                "spacing_mm": [0.8, 0.8, 5.0], "orientation": "RAS",
                "voxel_volume_mm3": 3.2, "label_values": [0, 1, 2, 3],
                "foreground_fraction": frac, "target_volume_ml": 200.0,
                "intensity": {"min": -1024.0, "p01": -1000.0, "p50": 40.0,
                              "p99": 300.0, "max": 1500.0}, "flags": []}
               for i in range(4)]}
if target != "none":
    p["target_label"] = target
json.dump(p, open(out, "w"))
PY
}

# 4a) three structures declared, no target named -> fires. 3.2 % pooled foreground sits
#     ABOVE the 1 % threshold, so the imbalance verdict stays silent while the real
#     target (0.2 %) is far below it: the exact false negative this verdict exists for.
write_atlas "$TMP/atlas_undeclared.json" none 0.032
python3 "$SCRIPT" --profile "$TMP/atlas_undeclared.json" --out "$OUT" --quiet >/dev/null 2>&1
check "TARGET_LABEL_UNDECLARED on a multi-structure atlas with no target" \
      has_verdict TARGET_LABEL_UNDECLARED
check "pooled foreground clears the threshold, so EXTREME_IMBALANCE stays silent" \
      no_verdict EXTREME_IMBALANCE

# 4b) same atlas, target named, target-specific foreground -> the imbalance is visible
write_atlas "$TMP/atlas_target.json" 1 0.002
python3 "$SCRIPT" --profile "$TMP/atlas_target.json" --out "$OUT" --quiet >/dev/null 2>&1
check "no TARGET_LABEL_UNDECLARED once a target label is declared" \
      no_verdict TARGET_LABEL_UNDECLARED
check "target-specific foreground now trips EXTREME_IMBALANCE" has_verdict EXTREME_IMBALANCE

# 4c) 'all' is a declaration too -- a genuinely multi-class study
write_atlas "$TMP/atlas_all.json" all 0.032
python3 "$SCRIPT" --profile "$TMP/atlas_all.json" --out "$OUT" --quiet >/dev/null 2>&1
check "no TARGET_LABEL_UNDECLARED when 'all' is declared" no_verdict TARGET_LABEL_UNDECLARED

# 4d) a single-structure dataset never raises the question
python3 "$SCRIPT" --profile "$CH/fixture/profile_clean.json" --out "$OUT" --quiet >/dev/null 2>&1
check "no TARGET_LABEL_UNDECLARED on a binary dataset" no_verdict TARGET_LABEL_UNDECLARED

# (5) split names carry qualifiers in real projects. An exact-set membership test misses
# every one of them, which is the worst way for TEST_SET_UNLABELLED to fail: the split it
# exists for is the split it cannot see.
write_qualified() {  # $1=out  $2=split name  $3=labelled(true/false)
  python3 - "$1" "$2" "$3" <<'PY'
import json, sys
out, name, lab = sys.argv[1], sys.argv[2], sys.argv[3] == "true"
case = {"case": "c1", "split": name, "shape": [512, 512, 100],
        "spacing_mm": [0.8, 0.8, 5.0], "orientation": "RAS", "voxel_volume_mm3": 3.2,
        "label_values": [0, 1] if lab else None,
        "foreground_fraction": 0.004 if lab else None,
        "target_volume_ml": 200.0 if lab else None,
        "intensity": {"min": -1024.0, "p01": -1000.0, "p50": 40.0, "p99": 300.0,
                      "max": 1500.0}, "flags": []}
json.dump({"dataset": "d", "declared_labels": {"0": "background", "1": "spleen"},
           "target_label": "1",
           "plan": {"resample": True, "reorient": True, "loss": "dice_ce",
                    "metrics": ["dice", "hd95"]},
           "splits": [{"name": name, "labelled": lab}], "cases": [case]},
          open(out, "w"))
PY
}
for qname in amos_test external_ct held-out-set test-fold1 testing_set; do
  write_qualified "$TMP/q.json" "$qname" false
  python3 "$SCRIPT" --profile "$TMP/q.json" --out "$OUT" --quiet >/dev/null 2>&1
  check "TEST_SET_UNLABELLED on qualified split name '$qname'" has_verdict TEST_SET_UNLABELLED
done
write_qualified "$TMP/q.json" amos_test true
python3 "$SCRIPT" --profile "$TMP/q.json" --out "$OUT" --quiet >/dev/null 2>&1
check "no TEST_SET_UNLABELLED when the qualified split IS labelled" no_verdict TEST_SET_UNLABELLED
for safe in train contest pretest protest_cohort validation; do
  write_qualified "$TMP/q.json" "$safe" false
  python3 "$SCRIPT" --profile "$TMP/q.json" --out "$OUT" --quiet >/dev/null 2>&1
  check "no TEST_SET_UNLABELLED on unlabelled split named '$safe'" no_verdict TEST_SET_UNLABELLED
done

# (6) challenge card reproduces
check "challenge card verify.sh" bash "$CH/verify.sh"

echo
if [[ "$fail" -eq 0 ]]; then echo "ALL PASS (dataset-profile gate)"; else echo "$fail FAILURE(S)"; exit 1; fi
