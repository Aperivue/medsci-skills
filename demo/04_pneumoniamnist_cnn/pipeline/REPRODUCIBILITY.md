# Reproducibility

Scaffolded by `model-scaffold` (task: classification, arch: cnn), then run end to end. Every number
in `../results/results.json` comes from that executed run — none is hand-entered.

## The published run

- **Commit**: `9df2686` (2026-07-04).
- **Dataset**: PneumoniaMNIST (MedMNIST v2, CC BY 4.0; Yang et al. 2023), official image-level split;
  test n = 624, prevalence 0.625. Auto-downloaded by `medmnist` — no data is vendored here.
- **Split**: seed-locked at `42` (`../splits/split_assignment.csv`), disjoint by construction and
  proved by set arithmetic in `../qc/split_leakage.json` (`check_split_leakage.py --strict`).
- **Seeds**: `42, 43, 44` applied to random / numpy / torch / torch.cuda; cuDNN deterministic
  (`train.py: seed_everything`). Metrics are reported as mean ± SD over the 3 seeds.
- **Epochs**: 20. **Device**: `mps` (Apple Silicon) — no lab GPU.
- **Package versions**: not captured at run time. This is the one gap in the record; reproducers
  should paste their own `pip freeze` below. Results reproduce up to backend non-determinism,
  bounded by the reported seed SD.

## How to reproduce

```bash
python3 -m venv .venv && . .venv/bin/activate     # Python 3.11–3.13
pip install -r pipeline/requirements.txt
bash reproduce.sh          # gates -> 3-seed train -> evaluate -> calibration/XAI -> figures
```

`reproduce.sh` runs the two deterministic gates (`check_split_leakage.py`,
`check_training_hygiene.py`) before any training, so a leak or a hygiene defect stops the run
instead of surfacing in the results.

## Your environment (fill in when you reproduce)

- python / `pip freeze`:
- device (CPU / MPS / CUDA + driver):
- git commit:
