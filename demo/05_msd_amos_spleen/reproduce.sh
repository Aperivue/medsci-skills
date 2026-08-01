#!/usr/bin/env bash
# Reproduce Demo 5's tier A: everything this repository can honestly promise on a laptop.
#
# The published run needed two ~25 GB public datasets and ~50 GPU-hours in a CUDA container, so
# "reproduce.sh trains the model" would be a lie. What ships instead is every artifact the training
# consumed or produced -- the seed-locked split, the preprocessing manifests, the per-case scores --
# so the parts that are checkable are checked here, for real, and the parts that are not are printed
# with what they need.
#
# The two leakage gates are the MedSci Skills scripts, called from ../../skills/ rather than
# vendored: this demo tests the shipped code, not a copy of it.
set -euo pipefail
cd "$(dirname "$0")"
SK="../../skills"
PY="${PYTHON:-python3}"

echo "=============================================================="
echo " Demo 5 tier A — gates + analysis (no dataset, no GPU)"
echo "=============================================================="

echo
echo "[1/5] split-leakage gate: patient disjointness by set arithmetic"
"$PY" "$SK/model-validation/scripts/check_split_leakage.py" \
    --splits splits/split_assignment.csv --id-col patient_id --split-col split \
    --out qc/split_leakage.json --strict

echo
echo "[2/5] preprocessing-leakage gate: the manifest the published run actually used"
"$PY" "$SK/preprocess-imaging/scripts/check_preprocessing_leakage.py" \
    --manifest manifests/preprocessing_manifest.json \
    --out qc/preprocessing_leakage.json --strict

echo
echo "[3/5] the counterfactual — the SAME gate must REJECT the obvious way of using nnU-Net"
echo "      (dropping every case into nnUNet_raw and splitting afterwards fits the fingerprint,"
echo "       including its resampling target and CT intensity statistics, on the held-out set)"
if "$PY" "$SK/preprocess-imaging/scripts/check_preprocessing_leakage.py" \
        --manifest manifests/preprocessing_manifest_naive.json \
        --out qc/preprocessing_leakage_naive.json --strict; then
    echo "FAIL: the naive manifest passed the gate. A gate that cannot fail proves nothing." >&2
    exit 1
fi
echo "      -> rejected, as it must be."

echo
echo "[4/5] metric unit tests (synthetic volumes, answers derived on paper)"
if "$PY" -c "import nibabel, scipy" 2>/dev/null; then
    "$PY" pipeline/test_evaluate_segmentation.py
else
    echo "      SKIPPED — needs nibabel + scipy (pip install -r pipeline/requirements.txt)"
fi

echo
echo "[5/5] across-cohort analysis from the shipped per-case CSVs"
"$PY" pipeline/aggregate_results.py \
    --results-dir results \
    --out results/summary_across_cohorts.md \
    --figure figures/across_cohorts_dice.png >/dev/null
echo "      wrote results/summary_across_cohorts.md + figures/across_cohorts_dice.png"
echo "      The markdown is deterministic (bootstrap seed 20260725) and should be byte-identical to"
echo "      the shipped file — 'git diff results/summary_across_cohorts.md' should print nothing."
echo "      The PNG may differ by matplotlib version; that is a renderer difference, not a result."

cat <<'TIERS'

==============================================================
 Not run here — what each remaining tier needs
==============================================================

 tier B — the imaging steps (needs the two datasets on disk, no GPU)
   aws s3 sync --no-sign-request s3://msd-for-monai/Task09_Spleen data/msd_spleen
   # AMOS22: Zenodo record 7262581 -> data/amos22
   python3 pipeline/eda_imaging.py                  # -> eda/*_profile.json
   python3 ../../skills/profile-imaging/scripts/check_dataset_profile.py --strict   # -> qc/dataset_profile_*.json
   python3 pipeline/build_split.py                  # -> splits/split_assignment.csv (seed 42)
   python3 pipeline/make_nnunet_dataset.py          # aborts if a held-out case reaches nnUNet_raw
   python3 pipeline/build_amos_views.py             # CT / MRI views by label-file inspection
   python3 pipeline/prepare_inference_inputs.py     # relative symlinks (see FRICTION.md 4)
   python3 pipeline/evaluate_segmentation.py --gt-dir inference/<arm>/labels \
       --pred-dir inference/<arm>/pred --gt-label 1 --arm <arm> --out results/per_case_<arm>.csv
   python3 pipeline/normalizer_modality_evidence.py --images inference/<arm>/images \
       --plans inference/<arm>/pred/plans.json --arm <arm> --out results/normalizer_evidence_<arm>.json

 tier C — training and inference (~50 GPU-hours, CUDA container)
   nnU-Net v2 (github.com/MIC-DKFZ/nnUNet), 3d_fullres, 5 folds x 100 epochs.
   Set nnUNet_compile=f on pre-Volta GPUs (see FRICTION.md 2).
   Scheduler orchestration was site-specific and is deliberately not shipped; FRICTION.md 1 and 3
   say why encoding one lab's conventions would be a liability elsewhere.

TIERS
echo "DONE — tier A complete. See README.md, results/, qc/, FRICTION.md"
