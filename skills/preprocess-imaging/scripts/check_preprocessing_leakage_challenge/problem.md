# Challenge — preprocessing-leakage gate

A medical-imaging preprocessing pipeline can leak the test distribution into training
one stage before the split gate can see it. Given a declarative preprocessing manifest
(JSON), `check_preprocessing_leakage.py` must decide — by rule and by set arithmetic on
the patient IDs, not from prose — whether the pipeline is leakage-safe.

## Task
Run the gate on the two synthetic manifests in `fixture/` and reproduce `expected/`:

- `manifest_leak.json` → three Major verdicts (`NORMALIZATION_LEAKAGE`,
  `PREPROCESS_BEFORE_SPLIT`, `PATIENT_CROSS_SPLIT`) plus a Minor `AUGMENTATION_ON_EVAL`;
  exit 1 under `--strict`.
- `manifest_clean.json` → no claims; exit 0. Note the per-image normalisation runs
  before the split yet does **not** fire: a per-sample transform is leakage-free.

## Verify
```bash
bash verify.sh   # deterministic, network-free
```
