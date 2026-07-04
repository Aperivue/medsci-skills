#!/usr/bin/env bash
# Reproduce Demo 4 end to end. Gates are the MedSci Skills scripts (referenced from the repo, not
# vendored). Run from this folder; outputs land in ./splits, ./results, ./figures. Every number comes
# from this executed run — nothing is hand-entered.
set -euo pipefail
cd "$(dirname "$0")"
export PYTHONPATH="$PWD/pipeline"          # so `from dataset import ...` resolves
SK="../../skills"                          # repo-relative path to the deterministic gates
PY="${PYTHON:-python3}"

echo "[1/6] official split + disjointness proof (model-validation)"
"$PY" pipeline/build_split.py              # writes ./splits/split_assignment.csv
"$PY" "$SK/model-validation/scripts/check_split_leakage.py" \
    --splits splits/split_assignment.csv --id-col sample_id --split-col split \
    --out qc/split_leakage.json --strict

echo "[2/6] training-hygiene proof (model-scaffold)"
"$PY" "$SK/model-scaffold/scripts/check_training_hygiene.py" --repo pipeline \
    --out qc/training_hygiene.json --strict

echo "[3/6] 3-seed training + held-out metrics -> results/results.json"
"$PY" pipeline/experiment.py

echo "[4/6] single-seed checkpoint for interpretability -> best.pt"
"$PY" pipeline/train.py

echo "[5/6] calibration + Grad-CAM + Adebayo sanity"
"$PY" pipeline/explain.py

echo "[6/6] figures"
"$PY" pipeline/make_figs.py
echo "DONE — see results/results.json, figures/, qc/"
